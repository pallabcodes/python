"""
SQLite query operations for the analytics pipeline.

This module contains query-related functions for the SQLite backend,
separated for better modularity and to keep file sizes under limits.
"""

from typing import Dict, Any, Optional, List, Iterator, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .sqlite_backend import SQLiteBackend
    from .storage_base import QueryFilter, QueryOptions

import sqlite3


def _execute_query(self: 'SQLiteBackend', conn: sqlite3.Connection, collection: str,
                  filters: Optional[List['QueryFilter']] = None,
                  options: Optional['QueryOptions'] = None) -> Iterator[Dict[str, Any]]:
    """Execute a query with filtering and options.

    Args:
        conn: Database connection
        collection: Table name
        filters: Query filters
        options: Query options

    Returns:
        Iterator over results
    """
    # Ensure table exists
    if not self._table_exists(conn, collection):
        return

    # Build query
    sql, params = _build_query_sql(collection, filters, options)

    cursor = conn.execute(sql, params)

    for row in cursor:
        result = _deserialize_row(row)

        # Apply field selection if specified
        if options and options.fields:
            result = {k: v for k, v in result.items() if k in options.fields}

        yield result


def _build_query_sql(collection: str, filters: Optional[List['QueryFilter']] = None,
                    options: Optional['QueryOptions'] = None) -> Tuple[str, List[Any]]:
    """Build SQL query with filters and options.

    Args:
        collection: Table name
        filters: Query filters
        options: Query options

    Returns:
        Tuple of (SQL query, parameters)
    """
    sql = f"SELECT * FROM {collection}"
    params = []

    # Add WHERE clause for filters
    if filters:
        where_clauses = []
        for filter_obj in filters:
            clause, filter_params = _build_filter_clause(filter_obj)
            where_clauses.append(clause)
            params.extend(filter_params)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

    # Add ORDER BY clause
    if options and options.sort_by:
        direction = "DESC" if options.sort_order.lower() == 'desc' else "ASC"
        sql += f" ORDER BY {options.sort_by} {direction}"

    # Add LIMIT/OFFSET
    if options:
        if options.limit:
            sql += " LIMIT ?"
            params.append(options.limit)
        if options.offset:
            sql += " OFFSET ?"
            params.append(options.offset)

    return sql, params


def _build_filter_clause(filter_obj: 'QueryFilter') -> Tuple[str, List[Any]]:
    """Build SQL clause for a filter.

    Args:
        filter_obj: Query filter

    Returns:
        Tuple of (SQL clause, parameters)
    """
    field = filter_obj.field
    operator = filter_obj.operator.lower()
    value = filter_obj.value

    if operator == 'eq':
        return f"{field} = ?", [value]
    elif operator == 'ne':
        return f"{field} != ?", [value]
    elif operator == 'gt':
        return f"{field} > ?", [value]
    elif operator == 'gte':
        return f"{field} >= ?", [value]
    elif operator == 'lt':
        return f"{field} < ?", [value]
    elif operator == 'lte':
        return f"{field} <= ?", [value]
    elif operator == 'in':
        placeholders = ','.join('?' * len(value))
        return f"{field} IN ({placeholders})", list(value)
    elif operator == 'contains':
        return f"{field} LIKE ?", [f'%{value}%']
    elif operator == 'regex':
        return f"{field} REGEXP ?", [value]
    else:
        # Default to equality
        return f"{field} = ?", [value]


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
