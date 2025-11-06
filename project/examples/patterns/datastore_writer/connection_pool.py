"""
Core connection pooling functionality.

This module contains the main ConnectionPool class and core
pooling logic for managing database connections.
"""

import time
import threading
import logging
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass
from queue import Queue, Empty, Full


@dataclass
class PoolConfig:
    """Configuration for connection pool."""
    max_connections: int = 10
    min_connections: int = 1
    max_idle_time: float = 300.0  # 5 minutes
    max_lifetime: float = 3600.0  # 1 hour
    health_check_interval: float = 60.0  # 1 minute
    acquire_timeout: float = 30.0  # 30 seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """Validate configuration."""
        if self.max_connections < 1:
            raise ValueError("max_connections must be at least 1")
        if self.min_connections < 0:
            raise ValueError("min_connections must be non-negative")
        if self.min_connections > self.max_connections:
            raise ValueError("min_connections cannot exceed max_connections")
        if self.max_idle_time <= 0:
            raise ValueError("max_idle_time must be positive")
        if self.max_lifetime <= 0:
            raise ValueError("max_lifetime must be positive")


@dataclass
class PooledConnection:
    """Wrapper for pooled connections with metadata."""
    connection: Any
    created_at: float
    last_used: float
    last_health_check: float
    is_healthy: bool = True

    @property
    def age(self) -> float:
        """Get connection age in seconds."""
        return time.time() - self.created_at

    @property
    def idle_time(self) -> float:
        """Get idle time in seconds."""
        return time.time() - self.last_used

    def mark_used(self) -> None:
        """Mark connection as recently used."""
        self.last_used = time.time()

    def needs_health_check(self, interval: float) -> bool:
        """Check if connection needs health check."""
        return (time.time() - self.last_health_check) > interval


class ConnectionPool:
    """Thread-safe connection pool with automatic management."""

    def __init__(
        self,
        connection_factory: Callable[[], Any],
        health_check: Optional[Callable[[Any], bool]] = None,
        config: Optional[PoolConfig] = None
    ):
        """Initialize connection pool.

        Args:
            connection_factory: Function to create new connections
            health_check: Function to check connection health
            config: Pool configuration
        """
        self.config = config or PoolConfig()
        self._connection_factory = connection_factory
        self._health_check = health_check or (lambda conn: True)

        # Thread-safe storage
        self._available = Queue(maxsize=self.config.max_connections)
        self._in_use = set()
        self._lock = threading.RLock()

        # Statistics
        self._created_count = 0
        self._destroyed_count = 0
        self._acquired_count = 0
        self._released_count = 0

        self._logger = logging.getLogger(__name__)
        self._shutdown = False

        # Initialize minimum connections
        self._initialize_pool()

        # Start maintenance thread
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            daemon=True,
            name="ConnectionPool-Maintenance"
        )
        self._maintenance_thread.start()

    def _initialize_pool(self) -> None:
        """Initialize minimum number of connections."""
        for _ in range(self.config.min_connections):
            try:
                conn = self._create_connection()
                self._available.put(conn)
            except Exception as e:
                self._logger.warning(f"Failed to create initial connection: {e}")

    def _create_connection(self) -> PooledConnection:
        """Create a new pooled connection."""
        conn = self._connection_factory()
        pooled = PooledConnection(
            connection=conn,
            created_at=time.time(),
            last_used=time.time(),
            last_health_check=time.time()
        )
        self._created_count += 1
        self._logger.debug(f"Created new connection (total: {self._created_count})")
        return pooled

    def _destroy_connection(self, pooled_conn: PooledConnection) -> None:
        """Destroy a pooled connection."""
        try:
            if hasattr(pooled_conn.connection, 'close'):
                pooled_conn.connection.close()
        except Exception as e:
            self._logger.warning(f"Error closing connection: {e}")

        self._destroyed_count += 1
        self._logger.debug(f"Destroyed connection (total: {self._destroyed_count})")

    def acquire(self, timeout: Optional[float] = None) -> Any:
        """Acquire a connection from the pool.

        Args:
            timeout: Maximum time to wait for connection

        Returns:
            Database connection

        Raises:
            TimeoutError: If no connection available within timeout
        """
        if self._shutdown:
            raise RuntimeError("Connection pool is shut down")

        timeout = timeout or self.config.acquire_timeout

        # Try to get existing connection
        try:
            pooled_conn = self._available.get(timeout=timeout)
            pooled_conn.mark_used()

            # Health check if needed
            if pooled_conn.needs_health_check(self.config.health_check_interval):
                if not self._check_connection_health(pooled_conn):
                    # Connection unhealthy, try to create new one
                    self._destroy_connection(pooled_conn)
                    pooled_conn = self._create_connection()

            with self._lock:
                self._in_use.add(pooled_conn)

            self._acquired_count += 1
            return pooled_conn.connection

        except Empty:
            # No available connections, try to create new one
            if len(self._in_use) < self.config.max_connections:
                try:
                    pooled_conn = self._create_connection()
                    with self._lock:
                        self._in_use.add(pooled_conn)
                    self._acquired_count += 1
                    return pooled_conn.connection
                except Exception as e:
                    self._logger.error(f"Failed to create connection: {e}")
                    raise TimeoutError(f"No connection available within {timeout}s")

            raise TimeoutError(f"No connection available within {timeout}s")

    def release(self, connection: Any) -> None:
        """Release a connection back to the pool.

        Args:
            connection: Connection to release
        """
        if self._shutdown:
            # If shutting down, close connection
            try:
                if hasattr(connection, 'close'):
                    connection.close()
            except Exception:
                pass
            return

        # Find the pooled connection
        pooled_conn = None
        with self._lock:
            for pc in self._in_use:
                if pc.connection is connection:
                    pooled_conn = pc
                    self._in_use.remove(pc)
                    break

        if pooled_conn:
            # Check if connection should be destroyed
            if (pooled_conn.age > self.config.max_lifetime or
                not pooled_conn.is_healthy):
                self._destroy_connection(pooled_conn)
            else:
                # Return to pool
                try:
                    self._available.put(pooled_conn, timeout=1.0)
                    self._released_count += 1
                except Full:
                    # Pool is full, destroy connection
                    self._destroy_connection(pooled_conn)
        else:
            self._logger.warning("Attempted to release unknown connection")

    def _check_connection_health(self, pooled_conn: PooledConnection) -> bool:
        """Check health of a pooled connection."""
        try:
            is_healthy = self._health_check(pooled_conn.connection)
            pooled_conn.is_healthy = is_healthy
            pooled_conn.last_health_check = time.time()
            return is_healthy
        except Exception as e:
            self._logger.warning(f"Health check failed: {e}")
            pooled_conn.is_healthy = False
            return False

    def _maintenance_loop(self) -> None:
        """Background maintenance loop."""
        while not self._shutdown:
            try:
                time.sleep(self.config.health_check_interval)

                if self._shutdown:
                    break

                self._perform_maintenance()

            except Exception as e:
                self._logger.error(f"Maintenance loop error: {e}")
                time.sleep(5)  # Avoid tight error loop

    def _perform_maintenance(self) -> None:
        """Perform pool maintenance tasks."""
        # Clean up idle connections beyond minimum
        available_count = self._available.qsize()
        in_use_count = len(self._in_use)

        if available_count > self.config.min_connections:
            # Remove excess idle connections
            excess = available_count - self.config.min_connections
            for _ in range(excess):
                try:
                    pooled_conn = self._available.get_nowait()
                    if pooled_conn.idle_time > self.config.max_idle_time:
                        self._destroy_connection(pooled_conn)
                    else:
                        # Put back if not too old
                        self._available.put_nowait(pooled_conn)
                except Empty:
                    break

        # Health check in-use connections
        with self._lock:
            for pooled_conn in list(self._in_use):
                if pooled_conn.needs_health_check(self.config.health_check_interval):
                    if not self._check_connection_health(pooled_conn):
                        self._logger.warning("In-use connection found unhealthy")

    def shutdown(self) -> None:
        """Shutdown the connection pool."""
        self._shutdown = True

        # Wait for maintenance thread
        if self._maintenance_thread.is_alive():
            self._maintenance_thread.join(timeout=5.0)

        # Close all connections
        with self._lock:
            for pooled_conn in self._in_use:
                self._destroy_connection(pooled_conn)
            self._in_use.clear()

        # Close available connections
        while not self._available.empty():
            try:
                pooled_conn = self._available.get_nowait()
                self._destroy_connection(pooled_conn)
            except Empty:
                break

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "available": self._available.qsize(),
            "in_use": len(self._in_use),
            "created": self._created_count,
            "destroyed": self._destroyed_count,
            "acquired": self._acquired_count,
            "released": self._released_count,
            "shutdown": self._shutdown,
            "config": {
                "max_connections": self.config.max_connections,
                "min_connections": self.config.min_connections,
                "max_idle_time": self.config.max_idle_time,
                "max_lifetime": self.config.max_lifetime
            }
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

