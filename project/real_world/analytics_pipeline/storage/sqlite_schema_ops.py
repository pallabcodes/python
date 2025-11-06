"""
SQLite schema operations for the analytics pipeline.

This module contains schema management operations for the SQLite backend,
separated for better modularity and to keep file sizes under limits.
"""

import sqlite3
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .sqlite_backend import SQLiteBackend


def _ensure_table_exists(self: 'SQLiteBackend', conn: sqlite3.Connection, collection: str) -> None:
    """Ensure a table exists, creating it if necessary.

    Args:
        conn: Database connection
        collection: Table name
    """
    if not self._table_exists(conn, collection):
        self._create_table(conn, collection)


def _table_exists(self: 'SQLiteBackend', conn: sqlite3.Connection, collection: str) -> bool:
    """Check if a table exists.

    Args:
        conn: Database connection
        collection: Table name

    Returns:
        True if table exists
    """
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (collection,))

    return cursor.fetchone() is not None


def _get_table_schema(self: 'SQLiteBackend', conn: sqlite3.Connection,
                     collection: str) -> Dict[str, str]:
    """Get the schema for a table.

    Args:
        conn: Database connection
        collection: Table name

    Returns:
        Column schema dictionary
    """
    # Check cache first
    if collection in self._table_schemas:
        return self._table_schemas[collection]

    # Query schema from database
    cursor = conn.execute(f"PRAGMA table_info({collection})")
    schema = {}

    for row in cursor:
        col_name = row[1]
        col_type = row[2]
        schema[col_name] = col_type

    # Cache the schema
    self._table_schemas[collection] = schema
    return schema


def _create_default_indexes(self: 'SQLiteBackend', conn: sqlite3.Connection, collection: str) -> None:
    """Create default indexes for a table.

    Args:
        conn: Database connection
        collection: Table name
    """
    # Index on ID (already primary key)
    # Index on timestamp fields
    try:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{collection}_created_at ON {collection}(_created_at)")
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{collection}_updated_at ON {collection}(_updated_at)")

        # Record index creation
        conn.execute("""
            INSERT OR IGNORE INTO _indexes (table_name, column_name, index_name, created_at)
            VALUES (?, ?, ?, ?)
        """, (collection, '_created_at', f'idx_{collection}_created_at', __import__('time').time()))

        conn.execute("""
            INSERT OR IGNORE INTO _indexes (table_name, column_name, index_name, created_at)
            VALUES (?, ?, ?, ?)
        """, (collection, '_updated_at', f'idx_{collection}_updated_at', __import__('time').time()))

    except Exception as e:
        self._logger.warning(f"Error creating default indexes for {collection}: {e}")
