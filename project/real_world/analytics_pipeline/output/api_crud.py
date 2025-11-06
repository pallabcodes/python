"""
API CRUD operations for the analytics pipeline.

This module contains CRUD (Create, Read, Update, Delete) operations for the DataAPI class,
separated for better modularity and to keep file sizes under limits.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_data import DataAPI
    from .api_core import APIResponse

import json


def query_data(self: 'DataAPI', backend_name: str, collection: str,
              filters: Optional[List[Dict[str, Any]]] = None,
              options: Optional[Dict[str, Any]] = None) -> 'APIResponse':
    """Query data from storage backend.

    Args:
        backend_name: Storage backend name
        collection: Collection/table name
        filters: Query filters
        options: Query options

    Returns:
        API response with query results
    """
    try:
        if backend_name not in self.storage_backends:
            return APIResponse(False, None, f"Storage backend '{backend_name}' not found")

        backend = self.storage_backends[backend_name]

        # Convert filter dictionaries to QueryFilter objects
        query_filters = None
        if filters:
            query_filters = []
            for f in filters:
                query_filters.append(QueryFilter(
                    field=f['field'],
                    operator=f['operator'],
                    value=f['value'],
                    case_sensitive=f.get('case_sensitive', True)
                ))

        # Convert options dictionary to QueryOptions object
        query_options = None
        if options:
            query_options = QueryOptions(
                limit=options.get('limit'),
                offset=options.get('offset', 0),
                sort_by=options.get('sort_by'),
                sort_order=options.get('sort_order', 'asc'),
                fields=options.get('fields')
            )

        # Execute query
        results = list(backend.query(collection, query_filters, query_options))

        return APIResponse(True, results, f"Query executed successfully, {len(results)} results")

    except Exception as e:
        return APIResponse(False, None, "Failed to execute query", str(e))


def store_data(self: 'DataAPI', backend_name: str, collection: str, data: Dict[str, Any]) -> 'APIResponse':
    """Store data in storage backend.

    Args:
        backend_name: Storage backend name
        collection: Collection/table name
        data: Data to store

    Returns:
        API response with operation result
    """
    try:
        if backend_name not in self.storage_backends:
            return APIResponse(False, None, f"Storage backend '{backend_name}' not found")

        backend = self.storage_backends[backend_name]
        record_id = backend.store(collection, data)

        return APIResponse(True, {'id': record_id}, "Data stored successfully")

    except Exception as e:
        return APIResponse(False, None, "Failed to store data", str(e))


def retrieve_data(self: 'DataAPI', backend_name: str, collection: str, record_id: str) -> 'APIResponse':
    """Retrieve data from storage backend.

    Args:
        backend_name: Storage backend name
        collection: Collection/table name
        record_id: Record ID

    Returns:
        API response with retrieved data
    """
    try:
        if backend_name not in self.storage_backends:
            return APIResponse(False, None, f"Storage backend '{backend_name}' not found")

        backend = self.storage_backends[backend_name]
        data = backend.retrieve(collection, record_id)

        if data is None:
            return APIResponse(False, None, f"Record '{record_id}' not found")

        return APIResponse(True, data, "Data retrieved successfully")

    except Exception as e:
        return APIResponse(False, None, "Failed to retrieve data", str(e))


def delete_data(self: 'DataAPI', backend_name: str, collection: str, record_id: str) -> 'APIResponse':
    """Delete data from storage backend.

    Args:
        backend_name: Storage backend name
        collection: Collection/table name
        record_id: Record ID

    Returns:
        API response with operation result
    """
    try:
        if backend_name not in self.storage_backends:
            return APIResponse(False, None, f"Storage backend '{backend_name}' not found")

        backend = self.storage_backends[backend_name]
        success = backend.delete(collection, record_id)

        if success:
            return APIResponse(True, None, "Data deleted successfully")
        else:
            return APIResponse(False, None, f"Record '{record_id}' not found")

    except Exception as e:
        return APIResponse(False, None, "Failed to delete data", str(e))
