"""Redis-based distributed locking for multi-instance deployments."""

import asyncio
import logging
import time
import uuid
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("redis not installed, distributed locking unavailable")


class DistributedLock:
    """
    Redis-based distributed lock implementation.
    
    Features:
    - Lock acquisition with timeout
    - Automatic lock renewal
    - Graceful fallback when Redis unavailable
    - Deadlock prevention
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        lock_key_prefix: str = "lock:",
        default_timeout: float = 30.0,
        renewal_interval: float = 10.0
    ):
        """
        Initialize distributed lock.
        
        Args:
            redis_client: Redis client instance (optional)
            lock_key_prefix: Prefix for lock keys
            default_timeout: Default lock timeout in seconds
            renewal_interval: Interval for lock renewal in seconds
        """
        if not HAS_REDIS:
            raise ImportError("redis package required for distributed locking")
        
        self.redis_client = redis_client
        self.lock_key_prefix = lock_key_prefix
        self.default_timeout = default_timeout
        self.renewal_interval = renewal_interval
        self._lock_holder: Optional[str] = None
        self._renewal_task: Optional[Any] = None
        self._logger = logging.getLogger(f"{__name__}.DistributedLock")
    
    async def acquire(
        self,
        lock_name: str,
        timeout: Optional[float] = None,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire distributed lock.
        
        Args:
            lock_name: Name of the lock
            timeout: Lock timeout in seconds (defaults to default_timeout)
            blocking: Whether to block until lock is acquired
            blocking_timeout: Maximum time to wait for lock acquisition
            
        Returns:
            True if lock acquired, False otherwise
        """
        if not self.redis_client:
            self._logger.warning("Redis client not available, lock acquisition failed")
            return False
        
        timeout = timeout or self.default_timeout
        lock_key = f"{self.lock_key_prefix}{lock_name}"
        lock_value = str(uuid.uuid4())
        start_time = time.time()
        
        while True:
            try:
                # Try to acquire lock
                acquired = self.redis_client.set(
                    lock_key,
                    lock_value,
                    nx=True,
                    ex=int(timeout)
                )
                
                if acquired:
                    self._lock_holder = lock_value
                    self._start_renewal(lock_key, lock_value, timeout)
                    self._logger.debug(f"Acquired lock: {lock_name}")
                    return True
                
                if not blocking:
                    return False
                
                # Check blocking timeout
                if blocking_timeout:
                    elapsed = time.time() - start_time
                    if elapsed >= blocking_timeout:
                        return False
                
                # Wait before retry
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self._logger.error(f"Error acquiring lock {lock_name}: {e}", exc_info=True)
                return False
    
    async def release(self, lock_name: str) -> bool:
        """
        Release distributed lock.
        
        Args:
            lock_name: Name of the lock
            
        Returns:
            True if lock released, False otherwise
        """
        if not self.redis_client or not self._lock_holder:
            return False
        
        lock_key = f"{self.lock_key_prefix}{lock_name}"
        
        try:
            # Lua script for atomic release
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            released = self.redis_client.eval(
                lua_script,
                1,
                lock_key,
                self._lock_holder
            )
            
            if released:
                self._stop_renewal()
                self._lock_holder = None
                self._logger.debug(f"Released lock: {lock_name}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error releasing lock {lock_name}: {e}", exc_info=True)
            return False
    
    def _start_renewal(self, lock_key: str, lock_value: str, timeout: float):
        """Start lock renewal task."""
        async def renew_lock():
            while self._lock_holder == lock_value:
                try:
                    await asyncio.sleep(self.renewal_interval)
                    if self._lock_holder == lock_value:
                        self.redis_client.expire(lock_key, int(timeout))
                except Exception as e:
                    self._logger.error(f"Error renewing lock: {e}", exc_info=True)
                    break
        
        self._renewal_task = asyncio.create_task(renew_lock())
    
    def _stop_renewal(self):
        """Stop lock renewal task."""
        if self._renewal_task:
            self._renewal_task.cancel()
            self._renewal_task = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._lock_holder:
            # Release lock (lock_name needed, but we don't have it here)
            # This is a limitation - use explicit release() instead
            pass


class MockDistributedLock:
    """Mock distributed lock for when Redis is unavailable."""
    
    def __init__(self, *args, **kwargs):
        self._acquired = False
        self._logger = logging.getLogger(f"{__name__}.MockDistributedLock")
    
    async def acquire(self, lock_name: str, **kwargs) -> bool:
        """Mock acquire - always succeeds."""
        self._acquired = True
        self._logger.warning(f"Using mock lock for {lock_name} (Redis unavailable)")
        return True
    
    async def release(self, lock_name: str) -> bool:
        """Mock release."""
        self._acquired = False
        return True


def create_distributed_lock(
    redis_url: Optional[str] = None,
    **kwargs
) -> DistributedLock:
    """
    Create distributed lock with graceful fallback.
    
    Args:
        redis_url: Redis connection URL
        **kwargs: Additional arguments for DistributedLock
        
    Returns:
        DistributedLock or MockDistributedLock
    """
    if not HAS_REDIS:
        return MockDistributedLock(**kwargs)
    
    try:
        if redis_url:
            redis_client = redis.from_url(redis_url)
        else:
            redis_client = redis.Redis()
        
        # Test connection
        redis_client.ping()
        
        return DistributedLock(redis_client=redis_client, **kwargs)
    except Exception as e:
        logger.warning(f"Redis unavailable, using mock lock: {e}")
        return MockDistributedLock(**kwargs)

