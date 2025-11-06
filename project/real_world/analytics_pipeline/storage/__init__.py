"""
Storage backends for the analytics pipeline.

This module contains storage implementations for persisting analytics data:
- SQLite: Time-series data storage using datastore_writer
- JSON: Simple file-based storage
- Cache: In-memory cache layer for hot data
"""

from .backend_factory import StorageBackendFactory
from .sqlite_backend import SQLiteBackend
from .json_backend import JSONBackend
from .cache_backend import CacheBackend

__all__ = [
    'StorageBackendFactory',
    'SQLiteBackend',
    'JSONBackend',
    'CacheBackend'
]
