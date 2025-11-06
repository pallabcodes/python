"""
Datastore writer pipeline stage.

This module provides a pipeline stage for writing data to various
storage backends with connection pooling, transactions, and batch operations.
"""

import logging
from typing import Any, Dict, List, Optional, Callable, Union
from abc import ABC, abstractmethod

from ..pipeline_core.stage_types import SinkStage
from .connection_pool import ConnectionPool, PoolConfig
from .transaction_manager import TransactionManager, IsolationLevel
from .batch_writer import BatchWriter, BatchConfig, BatchResult


class DatastoreError(Exception):
    """Datastore operation error."""
    pass


class DatastoreBackend(ABC):
    """Abstract base class for datastore backends."""

    @abstractmethod
    def create_connection_factory(self) -> Callable[[], Any]:
        """Create connection factory for this backend."""
        pass

    @abstractmethod
    def create_health_check(self) -> Callable[[Any], bool]:
        """Create health check function for connections."""
        pass

    @abstractmethod
    def execute_write(self, connection: Any, data: Any) -> None:
        """Execute write operation for single data item."""
        pass

    @abstractmethod
    def execute_batch_write(self, connection: Any, data: List[Any]) -> int:
        """Execute batch write operation.

        Returns:
            Number of items successfully written
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get backend name."""
        pass


class DatastoreWriterStage(SinkStage):
    """Pipeline stage for writing data to datastores."""

    def __init__(
        self,
        name: str,
        backend: DatastoreBackend,
        pool_config: Optional[PoolConfig] = None,
        transaction_manager: Optional[TransactionManager] = None,
        batch_config: Optional[BatchConfig] = None,
        isolation_level: Optional[IsolationLevel] = None,
        enable_transactions: bool = True
    ):
        """Initialize datastore writer stage.

        Args:
            name: Stage name
            backend: Datastore backend implementation
            pool_config: Connection pool configuration
            transaction_manager: Custom transaction manager
            batch_config: Batch writing configuration
            isolation_level: Transaction isolation level
            enable_transactions: Whether to use transactions
        """
        super().__init__(name)
        self.backend = backend
        self.pool_config = pool_config or PoolConfig()
        self.batch_config = batch_config or BatchConfig()
        self.isolation_level = isolation_level
        self.enable_transactions = enable_transactions

        # Initialize components
        self._connection_pool = None
        self._transaction_manager = transaction_manager
        self._batch_writer = None

        # Statistics
        self._items_written = 0
        self._batches_processed = 0
        self._errors_encountered = 0

    def on_initialize(self) -> None:
        """Initialize datastore connections and components."""
        # Create connection pool
        connection_factory = self.backend.create_connection_factory()
        health_check = self.backend.create_health_check()

        self._connection_pool = ConnectionPool(
            connection_factory=connection_factory,
            health_check=health_check,
            config=self.pool_config
        )

        # Create transaction manager if enabled
        if self.enable_transactions and self._transaction_manager is None:
            self._transaction_manager = TransactionManager(self._connection_pool)

        # Create batch writer
        self._batch_writer = BatchWriter(
            batch_processor=self._process_batch,
            config=self.batch_config
        )

        self._logger.info(
            f"Initialized datastore writer '{self.name}' with backend '{self.backend.name}'",
            extra={
                "stage_name": self.name,
                "backend": self.backend.name,
                "pool_max_connections": self.pool_config.max_connections,
                "batch_max_size": self.batch_config.max_batch_size
            }
        )

    def consume(self, data: Any) -> None:
        """Consume data by writing to datastore.

        Args:
            data: Data to write
        """
        if self._batch_writer:
            self._batch_writer.add_item(data)
        else:
            self._write_single_item(data)

    def flush(self) -> None:
        """Flush any pending batch writes."""
        if self._batch_writer:
            result = self._batch_writer.force_flush()
            if result:
                self._batches_processed += 1
                if not result.success:
                    self._errors_encountered += 1
                    self._logger.error(
                        f"Batch write failed: {result.error}",
                        extra={
                            "stage_name": self.name,
                            "batch_id": result.batch_id,
                            "error": result.error
                        }
                    )

    def cleanup(self) -> None:
        """Clean up resources."""
        # Flush any remaining batches
        self.flush()

        # Close connection pool
        if self._connection_pool:
            self._connection_pool.shutdown()

        super().cleanup()

    def _write_single_item(self, data: Any) -> None:
        """Write a single data item.

        Args:
            data: Data item to write
        """
        try:
            if self.enable_transactions and self._transaction_manager:
                with self._transaction_manager.transaction(
                    isolation_level=self.isolation_level
                ) as conn:
                    self.backend.execute_write(conn, data)
            else:
                conn = self._connection_pool.acquire()
                try:
                    self.backend.execute_write(conn, data)
                finally:
                    self._connection_pool.release(conn)

            self._items_written += 1

        except Exception as e:
            self._errors_encountered += 1
            self._logger.error(
                f"Failed to write item: {e}",
                extra={
                    "stage_name": self.name,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise DatastoreError(f"Write operation failed: {e}") from e

    def _process_batch(self, items: List[Any]) -> BatchResult:
        """Process a batch of items.

        Args:
            items: Batch of items to write

        Returns:
            Batch operation result
        """
        try:
            if self.enable_transactions and self._transaction_manager:
                with self._transaction_manager.transaction(
                    isolation_level=self.isolation_level
                ) as conn:
                    written = self.backend.execute_batch_write(conn, items)
            else:
                conn = self._connection_pool.acquire()
                try:
                    written = self.backend.execute_batch_write(conn, items)
                finally:
                    self._connection_pool.release(conn)

            self._items_written += written

            return BatchResult(
                batch_id="",  # Will be set by BatchWriter
                items_processed=written,
                success=True
            )

        except Exception as e:
            self._logger.error(
                f"Batch write failed: {e}",
                extra={
                    "stage_name": self.name,
                    "batch_size": len(items),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )

            return BatchResult(
                batch_id="",  # Will be set by BatchWriter
                items_processed=0,
                success=False,
                error=str(e)
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get datastore writer statistics."""
        stats = {
            "stage_name": self.name,
            "backend": self.backend.name,
            "items_written": self._items_written,
            "batches_processed": self._batches_processed,
            "errors_encountered": self._errors_encountered,
            "transactions_enabled": self.enable_transactions,
            "pool_stats": (
                self._connection_pool.get_stats()
                if self._connection_pool else None
            ),
            "batch_stats": (
                self._batch_writer.get_stats()
                if self._batch_writer else None
            )
        }

        return stats


# Example backend implementations

class SQLiteBackend(DatastoreBackend):
    """SQLite datastore backend."""

    def __init__(self, db_path: str, table_name: str, create_table_sql: Optional[str] = None):
        """Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file
            table_name: Table name to write to
            create_table_sql: SQL to create table if it doesn't exist
        """
        self.db_path = db_path
        self.table_name = table_name
        self.create_table_sql = create_table_sql

    @property
    def name(self) -> str:
        return "sqlite"

    def create_connection_factory(self) -> Callable[[], Any]:
        """Create SQLite connection factory."""
        import sqlite3

        def factory():
            conn = sqlite3.connect(self.db_path)
            if self.create_table_sql:
                conn.execute(self.create_table_sql)
                conn.commit()
            return conn

        return factory

    def create_health_check(self) -> Callable[[Any], bool]:
        """Create SQLite health check."""
        def health_check(conn):
            try:
                conn.execute("SELECT 1").fetchone()
                return True
            except Exception:
                return False

        return health_check

    def execute_write(self, connection: Any, data: Any) -> None:
        """Execute write for single item."""
        # This is a simplified example - real implementation would
        # depend on the data structure and table schema
        if isinstance(data, dict):
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())

            sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            connection.execute(sql, values)
            connection.commit()

    def execute_batch_write(self, connection: Any, data: List[Any]) -> int:
        """Execute batch write."""
        if not data:
            return 0

        # Simplified batch insert
        if isinstance(data[0], dict):
            columns = list(data[0].keys())
            columns_str = ', '.join(columns)

            # Build values for all rows
            all_values = []
            for item in data:
                all_values.extend([item.get(col) for col in columns])

            placeholders = ', '.join(['?' for _ in columns])
            row_placeholders = ', '.join([f"({placeholders})" for _ in data])

            sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES {row_placeholders}"
            connection.execute(sql, all_values)
            connection.commit()

        return len(data)


def create_sqlite_writer(
    name: str,
    db_path: str,
    table_name: str,
    create_table_sql: Optional[str] = None,
    **kwargs
) -> DatastoreWriterStage:
    """Create a SQLite datastore writer.

    Args:
        name: Stage name
        db_path: SQLite database file path
        table_name: Table name to write to
        create_table_sql: SQL to create table
        **kwargs: Additional DatastoreWriterStage arguments

    Returns:
        Configured DatastoreWriterStage
    """
    backend = SQLiteBackend(db_path, table_name, create_table_sql)
    return DatastoreWriterStage(name=name, backend=backend, **kwargs)

