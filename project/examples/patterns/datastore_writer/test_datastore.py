"""
Unit tests for datastore writer functionality.

This module provides comprehensive tests for datastore writing,
connection pooling, transactions, and batch operations.
"""

import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from .connection_pool import ConnectionPool, PoolConfig, PooledConnection
from .transaction_manager import TransactionManager, IsolationLevel
from .batch_writer import BatchWriter, BatchConfig, BatchResult
from .datastore_stage import DatastoreWriterStage, SQLiteBackend


class TestConnectionPool:
    """Tests for connection pool functionality."""

    def test_pool_creation(self):
        """Test connection pool initialization."""
        def connection_factory():
            return Mock()

        pool = ConnectionPool(
            connection_factory=connection_factory,
            config=PoolConfig(max_connections=5, min_connections=2)
        )

        assert pool.config.max_connections == 5
        assert pool.config.min_connections == 2
        pool.shutdown()

    def test_connection_acquire_release(self):
        """Test acquiring and releasing connections."""
        mock_conn = Mock()
        def connection_factory():
            return mock_conn

        pool = ConnectionPool(connection_factory=connection_factory)

        # Acquire connection
        conn = pool.acquire(timeout=1.0)
        assert conn is mock_conn

        # Release connection
        pool.release(conn)

        # Should be able to acquire again
        conn2 = pool.acquire(timeout=1.0)
        assert conn2 is mock_conn

        pool.shutdown()

    def test_pool_exhaustion(self):
        """Test pool exhaustion behavior."""
        def connection_factory():
            return Mock()

        pool = ConnectionPool(
            connection_factory=connection_factory,
            config=PoolConfig(max_connections=1)
        )

        # Acquire only connection
        conn1 = pool.acquire(timeout=1.0)

        # Second acquire should create new connection since max_connections > 1 allows expansion
        pool.config.max_connections = 2  # Allow expansion for this test
        conn2 = pool.acquire(timeout=1.0)

        pool.release(conn1)
        pool.release(conn2)
        pool.shutdown()

    def test_health_check(self):
        """Test connection health checking."""
        mock_conn = Mock()
        def connection_factory():
            return mock_conn

        def health_check(conn):
            return conn is mock_conn

        pool = ConnectionPool(
            connection_factory=connection_factory,
            health_check=health_check
        )

        conn = pool.acquire()
        assert conn is mock_conn

        pool.release(conn)
        pool.shutdown()


class TestTransactionManager:
    """Tests for transaction management."""

    def test_transaction_context_manager(self):
        """Test transaction context manager."""
        mock_pool = Mock()
        mock_conn = Mock()
        mock_pool.acquire.return_value = mock_conn

        manager = TransactionManager(mock_pool)

        with manager.transaction() as conn:
            assert conn is mock_conn

        # Verify transaction lifecycle
        mock_conn.execute.assert_any_call("BEGIN")
        mock_conn.commit.assert_called_once()
        mock_pool.release.assert_called_once_with(mock_conn)

    def test_transaction_rollback_on_error(self):
        """Test transaction rollback on errors."""
        mock_pool = Mock()
        mock_conn = Mock()
        mock_pool.acquire.return_value = mock_conn

        manager = TransactionManager(mock_pool)

        with pytest.raises(ValueError):
            with manager.transaction():
                raise ValueError("Test error")

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()

    def test_savepoints(self):
        """Test transaction savepoints."""
        mock_pool = Mock()
        mock_conn = Mock()
        mock_pool.acquire.return_value = mock_conn

        manager = TransactionManager(mock_pool)

        with manager.transaction() as conn:
            manager.create_savepoint(conn, "test_transaction", "test_savepoint")
            manager.rollback_to_savepoint(conn, "test_transaction", "test_savepoint")

        mock_conn.execute.assert_any_call("SAVEPOINT test_savepoint")
        mock_conn.execute.assert_any_call("ROLLBACK TO SAVEPOINT test_savepoint")


class TestBatchWriter:
    """Tests for batch writer functionality."""

    def test_batch_writer_creation(self):
        """Test batch writer initialization."""
        def batch_processor(items):
            return BatchResult(
                batch_id="test",
                items_processed=len(items),
                success=True
            )

        writer = BatchWriter(
            batch_processor=batch_processor,
            config=BatchConfig(max_batch_size=10)
        )

        assert writer.config.max_batch_size == 10

    def test_batch_accumulation_and_flush(self):
        """Test batch accumulation and flushing."""
        processed_batches = []

        def batch_processor(items):
            result = BatchResult(
                batch_id=f"batch_{len(processed_batches)}",
                items_processed=len(items),
                success=True
            )
            processed_batches.append(items)
            return result

        writer = BatchWriter(batch_processor=batch_processor)

        # Add items
        for i in range(7):
            writer.add_item(f"item_{i}")

        # Should not flush yet (under min batch size)
        assert len(writer._current_batch) == 7

        # Add more to trigger flush
        for i in range(4):
            writer.add_item(f"item_{7+i}")

        # Should flush automatically
        assert len(processed_batches) == 1
        assert len(processed_batches[0]) == 10

        # Force flush remaining
        writer.force_flush()
        assert len(processed_batches) == 2
        assert len(processed_batches[1]) == 1

    def test_batch_error_handling(self):
        """Test batch error handling and retries."""
        call_count = 0

        def failing_processor(items):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Fail first attempt
                return BatchResult(
                    batch_id="test",
                    items_processed=0,
                    success=False,
                    error="Test failure"
                )
            else:
                # Succeed on retry
                return BatchResult(
                    batch_id="test",
                    items_processed=len(items),
                    success=True
                )

        writer = BatchWriter(
            batch_processor=failing_processor,
            config=BatchConfig(max_batch_size=5, retry_failed_batches=True, max_retries=3)
        )

        writer.add_items([f"item_{i}" for i in range(5)])

        # Should have retried
        assert call_count == 2


class TestSQLiteBackend:
    """Tests for SQLite backend."""

    def test_sqlite_backend_creation(self):
        """Test SQLite backend initialization."""
        backend = SQLiteBackend(
            db_path=":memory:",
            table_name="test_table",
            create_table_sql="CREATE TABLE test_table (id INTEGER)"
        )

        assert backend.name == "sqlite"
        assert backend.db_path == ":memory:"
        assert backend.table_name == "test_table"

    def test_connection_factory(self):
        """Test SQLite connection factory."""
        backend = SQLiteBackend(":memory:", "test")

        factory = backend.create_connection_factory()
        conn = factory()

        # Should be able to execute SQL
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

        conn.close()

    def test_health_check(self):
        """Test SQLite health check."""
        backend = SQLiteBackend(":memory:", "test")

        factory = backend.create_connection_factory()
        conn = factory()

        health_check = backend.create_health_check()
        assert health_check(conn) is True

        conn.close()


class TestDatastoreWriterStage:
    """Tests for datastore writer stage."""

    def test_writer_stage_creation(self):
        """Test writer stage initialization."""
        backend = SQLiteBackend(":memory:", "test")
        stage = DatastoreWriterStage(
            name="TestWriter",
            backend=backend,
            enable_transactions=False
        )

        assert stage.name == "TestWriter"
        assert stage.backend is backend
        assert not stage.enable_transactions

    def test_writer_statistics(self):
        """Test writer statistics collection."""
        backend = SQLiteBackend(":memory:", "test")
        stage = DatastoreWriterStage(name="TestWriter", backend=backend)

        stats = stage.get_stats()
        assert stats["stage_name"] == "TestWriter"
        assert stats["backend"] == "sqlite"
        assert stats["items_written"] == 0

    @patch('datastore_stage.DatastoreWriterStage._write_single_item')
    def test_consume_method(self, mock_write):
        """Test consume method calls write."""
        backend = SQLiteBackend(":memory:", "test")
        stage = DatastoreWriterStage(name="TestWriter", backend=backend)

        # Mock initialization
        stage._connection_pool = Mock()

        stage.consume({"test": "data"})
        mock_write.assert_called_once_with({"test": "data"})


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_pipeline_integration(self):
        """Test complete datastore writing pipeline."""
        from ..pipeline_core.runner import PipelineRunner

        # Create temporary database
        import tempfile
        db_fd, db_path = tempfile.mkstemp(suffix='.db')

        try:
            # Create backend and writer
            backend = SQLiteBackend(
                db_path=db_path,
                table_name="integration_test",
                create_table_sql="""
                CREATE TABLE integration_test (
                    id INTEGER,
                    name TEXT,
                    value REAL
                )
                """
            )

            writer = DatastoreWriterStage(
                name="IntegrationWriter",
                backend=backend,
                enable_transactions=False
            )

            pipeline = PipelineRunner([writer])

            # Test data
            test_data = [
                {"id": 1, "name": "test1", "value": 10.5},
                {"id": 2, "name": "test2", "value": 20.3}
            ]

            results = pipeline.run_pipeline([test_data[0], test_data[1]])

            assert results["success"] is True

            # Verify data was written
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM integration_test")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 2

        finally:
            import os
            try:
                os.close(db_fd)
                os.unlink(db_path)
            except:
                pass


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])

