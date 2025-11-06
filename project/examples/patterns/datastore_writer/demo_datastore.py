"""
Demonstrations of datastore writer functionality.

This module provides practical examples of using datastore writers
for data persistence with connection pooling and transactions.
"""

import os
import tempfile
import logging
from typing import Any, List

from ..pipeline_core.message import create_data_message
from ..pipeline_core.runner import PipelineRunner
from .datastore_stage import DatastoreWriterStage, create_sqlite_writer
from .connection_pool import PoolConfig
from .batch_writer import BatchConfig
from .transaction_manager import IsolationLevel


def demo_basic_datastore_writing() -> None:
    """Demonstrate basic datastore writing."""
    print("=== Basic Datastore Writing Demo ===")

    # Create temporary SQLite database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    try:
        # Create table SQL
        create_table = """
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Create datastore writer
        writer = create_sqlite_writer(
            name="BasicWriter",
            db_path=db_path,
            table_name="test_data",
            create_table_sql=create_table,
            pool_config=PoolConfig(max_connections=5, min_connections=1)
        )

        # Create pipeline
        pipeline = PipelineRunner([writer])

        # Sample data
        test_data = [
            {"id": 1, "name": "item1", "value": 10.5},
            {"id": 2, "name": "item2", "value": 20.3},
            {"id": 3, "name": "item3", "value": 15.7}
        ]

        input_messages = [create_data_message(data) for data in test_data]

        print("Writing data to SQLite database...")
        print(f"Database: {db_path}")
        print("Table: test_data"
        print(f"Sample data: {len(test_data)} items")

        # Run pipeline
        results = pipeline.run_pipeline(input_messages, timeout=15.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        # Check what was written
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_data")
        count = cursor.fetchone()[0]
        conn.close()

        print(f"Records written to database: {count}")

        # Show writer stats
        writer_stats = writer.get_stats()
        print("
Writer Statistics:")
        print(f"  Items written: {writer_stats['items_written']}")
        print(f"  Errors: {writer_stats['errors_encountered']}")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except:
            pass


def demo_batch_writing() -> None:
    """Demonstrate batch writing operations."""
    print("\n=== Batch Writing Demo ===")

    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    try:
        create_table = """
        CREATE TABLE IF NOT EXISTS batch_data (
            id INTEGER,
            batch_id INTEGER,
            data TEXT
        )
        """

        # Configure batch writing
        batch_config = BatchConfig(
            max_batch_size=10,
            max_wait_time=2.0,
            min_batch_size=5
        )

        writer = create_sqlite_writer(
            name="BatchWriter",
            db_path=db_path,
            table_name="batch_data",
            create_table_sql=create_table,
            batch_config=batch_config
        )

        pipeline = PipelineRunner([writer])

        # Generate batch data
        batch_data = []
        for batch_id in range(3):
            for item_id in range(8):  # 8 items per batch
                batch_data.append({
                    "id": batch_id * 8 + item_id,
                    "batch_id": batch_id,
                    "data": f"Item {item_id} in batch {batch_id}"
                })

        input_messages = [create_data_message(data) for data in batch_data]

        print("Demonstrating batch writing...")
        print(f"Total items: {len(batch_data)}")
        print("Batch size: 10 items"
        print("Min batch size: 5 items"
        print("Flush on full batch: enabled")

        # Run pipeline
        results = pipeline.run_pipeline(input_messages, timeout=20.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        # Check database
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count total records
        cursor.execute("SELECT COUNT(*) FROM batch_data")
        total_count = cursor.fetchone()[0]

        # Count batches (assuming batch_id indicates batch)
        cursor.execute("SELECT COUNT(DISTINCT batch_id) FROM batch_data")
        batch_count = cursor.fetchone()[0]

        conn.close()

        print("
Database Results:")
        print(f"  Total records: {total_count}")
        print(f"  Batches processed: {batch_count}")

        # Show batch writer stats
        batch_stats = writer.get_stats()['batch_stats']
        if batch_stats:
            print("
Batch Statistics:")
            print(f"  Total batches: {batch_stats['total_batches']}")
            print(f"  Successful batches: {batch_stats['successful_batches']}")
            print(".1f"
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except:
            pass


def demo_transaction_management() -> None:
    """Demonstrate transaction management."""
    print("\n=== Transaction Management Demo ===")

    # Create database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    try:
        create_table = """
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            balance REAL
        )
        """

        # Create writer with transactions enabled
        writer = create_sqlite_writer(
            name="TransactionalWriter",
            db_path=db_path,
            table_name="accounts",
            create_table_sql=create_table,
            enable_transactions=True,
            isolation_level=IsolationLevel.SERIALIZABLE
        )

        # Simulate financial transactions
        account_data = [
            {"id": 1, "name": "Alice", "balance": 1000.0},
            {"id": 2, "name": "Bob", "balance": 500.0},
            {"id": 3, "name": "Charlie", "balance": 750.0}
        ]

        # Create custom pipeline stage that simulates transactional work
        class TransactionalProcessor:
            def __init__(self, datastore_writer):
                self.writer = datastore_writer

            def process(self, data):
                # This would normally be part of the pipeline
                # For demo, we'll manually write with transaction
                try:
                    # Simulate business logic that requires transaction
                    if isinstance(data, list):
                        # Write all accounts in a transaction
                        with self.writer._transaction_manager.transaction() as conn:
                            for account in data:
                                self.writer.backend.execute_write(conn, account)

                        print(f"Transactionally wrote {len(data)} accounts")
                        return {"status": "success", "accounts_written": len(data)}
                    else:
                        self.writer.consume(data)
                        return {"status": "success", "single_write": True}

                except Exception as e:
                    return {"status": "error", "error": str(e)}

        processor = TransactionalProcessor(writer)

        print("Demonstrating transaction management...")
        print("Writing account data with transactional guarantees")

        # Process data
        result = processor.process(account_data)

        print(f"Transaction result: {result}")

        # Verify data was written
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(balance) FROM accounts")
        count, total_balance = cursor.fetchone()
        conn.close()

        print("
Database verification:")
        print(f"  Accounts created: {count}")
        print(".2f"
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except:
            pass


def demo_connection_pooling() -> None:
    """Demonstrate connection pool management."""
    print("\n=== Connection Pooling Demo ===")

    # Create database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    try:
        create_table = """
        CREATE TABLE pool_test (
            id INTEGER PRIMARY KEY,
            data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Create writer with connection pooling
        pool_config = PoolConfig(
            max_connections=3,
            min_connections=1,
            max_idle_time=30.0,
            health_check_interval=10.0
        )

        writer = create_sqlite_writer(
            name="PooledWriter",
            db_path=db_path,
            table_name="pool_test",
            create_table_sql=create_table,
            pool_config=pool_config
        )

        pipeline = PipelineRunner([writer])

        # Generate many items to test connection pooling
        test_data = [
            {"id": i, "data": f"Test item {i}"}
            for i in range(20)
        ]

        input_messages = [create_data_message(data) for data in test_data]

        print("Testing connection pooling...")
        print(f"Items to write: {len(test_data)}")
        print("Pool config: max=3, min=1 connections"
        print("Health checks: every 10 seconds"

        # Run pipeline
        results = pipeline.run_pipeline(input_messages, timeout=30.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        # Show pool statistics
        pool_stats = writer.get_stats()['pool_stats']
        if pool_stats:
            print("
Connection Pool Statistics:")
            print(f"  Connections created: {pool_stats['created']}")
            print(f"  Connections available: {pool_stats['available']}")
            print(f"  Connections in use: {pool_stats['in_use']}")
            print(f"  Connections acquired: {pool_stats['acquired']}")
            print(f"  Connections released: {pool_stats['released']}")

        # Verify all data was written
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pool_test")
        count = cursor.fetchone()[0]
        conn.close()

        print(f"\nData verification: {count} records written")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except:
            pass


def run_all_datastore_demos() -> None:
    """Run all datastore writer demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Datastore Writer Demonstrations")
    print("=" * 50)

    try:
        demo_basic_datastore_writing()
        demo_batch_writing()
        demo_transaction_management()
        demo_connection_pooling()

        print("\n" + "=" * 50)
        print("All datastore writer demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run demonstrations when executed directly."""
    run_all_datastore_demos()

