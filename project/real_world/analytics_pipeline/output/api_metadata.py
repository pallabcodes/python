"""
API metadata operations for the analytics pipeline.

This module contains metadata operations for the DataAPI class,
separated for better modularity and to keep file sizes under limits.
"""

from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .api_data import DataAPI
    from .api_core import APIResponse


def get_collections(self: 'DataAPI', backend_name: str) -> 'APIResponse':
    """Get list of collections/tables in storage backend.

    Args:
        backend_name: Storage backend name

    Returns:
        API response with collection list
    """
    try:
        if backend_name not in self.storage_backends:
            return APIResponse(False, None, f"Storage backend '{backend_name}' not found")

        backend = self.storage_backends[backend_name]
        collections = backend.list_collections()

        return APIResponse(True, collections, f"Found {len(collections)} collections")

    except Exception as e:
        return APIResponse(False, None, "Failed to get collections", str(e))


def get_collection_stats(self: 'DataAPI', backend_name: str, collection: str) -> 'APIResponse':
    """Get statistics for a collection/table.

    Args:
        backend_name: Storage backend name
        collection: Collection/table name

    Returns:
        API response with collection statistics
    """
    try:
        if backend_name not in self.storage_backends:
            return APIResponse(False, None, f"Storage backend '{backend_name}' not found")

        backend = self.storage_backends[backend_name]

        # Get approximate count (this would need to be implemented in backends)
        # For now, return basic info
        stats = {
            'backend': backend_name,
            'collection': collection,
            'estimated_count': 0,  # TODO: Implement count estimation
            'last_modified': datetime.now().isoformat()
        }

        return APIResponse(True, stats, "Collection stats retrieved successfully")

    except Exception as e:
        return APIResponse(False, None, "Failed to get collection stats", str(e))
