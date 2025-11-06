"""
SQLite storage backend for the analytics pipeline.

This module provides SQLite-based persistent storage for analytics data,
supporting time-series data, metadata storage, and complex queries.
"""

import sqlite3
import json
import os
from typing import Dict, Any, Optional, List, Iterator, Union
from datetime import datetime

from .storage_base import StorageBackend, StorageConfig, QueryFilter, QueryOptions


# Import SQLite methods
from .sqlite_connection import (
    _create_connection, _close_connection, _setup_database
)
from .sqlite_crud import (
    _store_record, _retrieve_record, _delete_record, _create_table
)
from .sqlite_schema_ops import (
    _ensure_table_exists, _table_exists, _get_table_schema, _create_default_indexes
)
from .sqlite_schema import (
    _serialize_value, _deserialize_row
)
from .sqlite_query_core import (
    _execute_query
)


class SQLiteBackend(StorageBackend):
    """SQLite-based storage backend for persistent analytics data.

    Provides ACID-compliant storage with support for:
    - Time-series data storage
    - Complex queries with filtering
    - Connection pooling
    - Automatic schema management
    - Transaction support
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the SQLite backend.

        Args:
            config: Storage configuration
        """
        super().__init__(config)

        # SQLite-specific configuration
        self._db_path = self._extract_db_path(config.connection_string)
        self._journal_mode = config.__dict__.get('journal_mode', 'WAL')
        self._synchronous_mode = config.__dict__.get('synchronous_mode', 'NORMAL')
        self._cache_size = config.__dict__.get('cache_size', -64000)  # KB

        # Schema cache
        self._table_schemas: Dict[str, Dict[str, str]] = {}

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

    def connect(self) -> None:
        """Establish connection to SQLite database."""
        try:
            # Create initial connection to set up database
            conn = self._create_connection()
            self._setup_database(conn)
            self._return_connection(conn)

            self._connected = True
            self._start_flush_thread()

# Methods are implemented in sqlite_crud.py, sqlite_schema_ops.py, and sqlite_connection.py
# to keep file under 200 lines
