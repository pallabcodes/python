"""
SQLite connection management for the analytics pipeline.

This module contains connection-related functions for the SQLite backend,
separated for better modularity and to keep file sizes under limits.
"""

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sqlite_backend import SQLiteBackend


def _create_connection(self: 'SQLiteBackend') -> sqlite3.Connection:
    """Create a new SQLite connection.

    Returns:
        SQLite connection
    """
    conn = sqlite3.connect(
        self._db_path,
        timeout=self._config.connection_timeout,
        isolation_level=None  # Enable autocommit mode
    )

    # Enable row factory for dict-like access
    conn.row_factory = sqlite3.Row

    # Configure pragmas
    conn.execute(f"PRAGMA journal_mode = {self._journal_mode}")
    conn.execute(f"PRAGMA synchronous = {self._synchronous_mode}")
    conn.execute(f"PRAGMA cache_size = {self._cache_size}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA temp_store = MEMORY")

    return conn


def _close_connection(self: 'SQLiteBackend', connection: sqlite3.Connection) -> None:
    """Close a SQLite connection.

    Args:
        connection: Connection to close
    """
    try:
        connection.close()
    except Exception as e:
        self._logger.warning(f"Error closing connection: {e}")


def _setup_database(self: 'SQLiteBackend', conn: sqlite3.Connection) -> None:
    """Set up the database with initial schema.

    Args:
        conn: Database connection
    """
    # Create metadata table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            created_at REAL,
            updated_at REAL
        )
    """)

    # Create indexes table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _indexes (
            table_name TEXT,
            column_name TEXT,
            index_name TEXT,
            created_at REAL,
            PRIMARY KEY (table_name, column_name)
        )
    """)

    # Set database version
    conn.execute("""
        INSERT OR REPLACE INTO _metadata (key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """, ('version', '1.0', __import__('time').time(), __import__('time').time()))

    conn.commit()