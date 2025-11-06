"""
SQLite utility functions for the analytics pipeline.

This module contains utility functions for data serialization/deserialization
used by the SQLite backend.
"""

import sqlite3
import json
from typing import Dict, Any


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
                result[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result[key] = value
        else:
            result[key] = value

    return result
