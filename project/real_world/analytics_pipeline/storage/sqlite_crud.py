"""
SQLite CRUD operations for the analytics pipeline.

This module contains Create, Read, Update, Delete operations for the SQLite backend,
separated for better modularity and to keep file sizes under limits.
"""

import sqlite3
import json
import uuid
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .sqlite_backend import SQLiteBackend


def _store_record(self: 'SQLiteBackend', conn: sqlite3.Connection,
                 collection: str, data: Dict[str, Any]) -> str:
    """Store a single record in the database.

    Args:
        conn: Database connection
        collection: Table name
        data: Data to store

    Returns:
        Record ID
    """
    # Ensure table exists
    self._ensure_table_exists(conn, collection)

    # Generate record ID if not provided
    record_id = data.get('id') or str(uuid.uuid4())

    # Prepare data for storage
    data_copy = data.copy()
    data_copy['id'] = record_id
    data_copy['_created_at'] = __import__('time').time()
    data_copy['_updated_at'] = __import__('time').time()

    # Get table schema
    schema = self._get_table_schema(conn, collection)

    # Build insert statement
    columns = []
    placeholders = []
    values = []

    for col_name, col_type in schema.items():
        if col_name in data_copy:
            columns.append(col_name)
            placeholders.append('?')
            values.append(_serialize_value(data_copy[col_name], col_type))

    # Add metadata columns
    if '_created_at' not in columns:
        columns.extend(['_created_at', '_updated_at'])
        placeholders.extend(['?', '?'])
        values.extend([data_copy['_created_at'], data_copy['_updated_at']])

    sql = f"""
        INSERT OR REPLACE INTO {collection}
        ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
    """

    conn.execute(sql, values)
    return record_id


def _retrieve_record(self: 'SQLiteBackend', conn: sqlite3.Connection,
                    collection: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a record from the database.

    Args:
        conn: Database connection
        collection: Table name
        record_id: Record ID

    Returns:
        Retrieved data or None
    """
    # Ensure table exists
    if not self._table_exists(conn, collection):
        return None

    cursor = conn.execute(f"SELECT * FROM {collection} WHERE id = ?", (record_id,))
    row = cursor.fetchone()

    if row:
        return _deserialize_row(row)
    return None


def _delete_record(self: 'SQLiteBackend', conn: sqlite3.Connection,
                  collection: str, record_id: str) -> bool:
    """Delete a record from the database.

    Args:
        conn: Database connection
        collection: Table name
        record_id: Record ID

    Returns:
        True if record was deleted
    """
    # Ensure table exists
    if not self._table_exists(conn, collection):
        return False

    cursor = conn.execute(f"DELETE FROM {collection} WHERE id = ?", (record_id,))
    return cursor.rowcount > 0


def _create_table(self: 'SQLiteBackend', conn: sqlite3.Connection,
                 collection: str, schema: Optional[Dict[str, Any]] = None) -> None:
    """Create a table with the given schema.

    Args:
        conn: Database connection
        collection: Table name
        schema: Schema definition
    """
    if schema is None:
        # Default schema for dynamic tables
        schema = {
            'id': 'TEXT PRIMARY KEY',
            'data': 'TEXT',  # JSON data
            '_created_at': 'REAL',
            '_updated_at': 'REAL'
        }

    # Build CREATE TABLE statement
    columns_sql = []
    for col_name, col_type in schema.items():
        columns_sql.append(f"{col_name} {col_type}")

    sql = f"""
        CREATE TABLE IF NOT EXISTS {collection} (
            {', '.join(columns_sql)}
        )
    """

    conn.execute(sql)

    # Store schema in cache
    self._table_schemas[collection] = schema

    # Create indexes for common fields
    self._create_default_indexes(conn, collection)

    conn.commit()


def _serialize_value(value: Any, col_type: str) -> Any:
    """Serialize a value for database storage.

    Args:
        value: Value to serialize
        col_type: Column type

    Returns:
        Serialized value
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    elif isinstance(value, __import__('datetime').datetime):
        return value.timestamp()
    else:
        return value


def _deserialize_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Deserialize a database row to a dictionary.

    Args:
        row: Database row

    Returns:
        Deserialized dictionary
    """
    result = {}
    for key in row.keys():
        value = row[key]

        # Try to parse JSON
        if isinstance(value, str):
            try:
                import json
                result[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result[key] = value
        else:
            result[key] = value

    return result
