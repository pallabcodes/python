"""
JSON file-based storage backend for the analytics pipeline.

This module provides simple file-based storage using JSON format,
suitable for development, testing, and small-scale data storage.
"""

import json
import os
import gzip
from typing import Dict, Any, Optional, List, Iterator
from pathlib import Path
from datetime import datetime

from .storage_base import StorageBackend, StorageConfig, QueryFilter, QueryOptions


# Import JSON methods
from .json_core import (
    _extract_base_path, _get_collection_path, _load_collection, _save_collection
)
from .json_ops import (
    _apply_filters, _matches_filter, _get_nested_value
)


class JSONBackend(StorageBackend):
    """JSON file-based storage backend for simple data persistence.

    Provides basic file-based storage with support for:
    - JSON serialization/deserialization
    - Optional compression
    - Simple querying and filtering
    - File-based collections
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the JSON backend.

        Args:
            config: Storage configuration
        """
        super().__init__(config)

        # JSON-specific configuration
        self._base_path = self._extract_base_path(config.connection_string)
        self._use_compression = config.enable_compression
        self._file_extension = 'json.gz' if self._use_compression else 'json'

        # Data cache
        self._data_cache: Dict[str, List[Dict[str, Any]]] = {}

        # Ensure base directory exists
        os.makedirs(self._base_path, exist_ok=True)

    def connect(self) -> None:
        """Establish connection (no-op for file-based storage)."""
        self._connected = True
        self._start_flush_thread()
        self._logger.info(f"Connected to JSON storage at: {self._base_path}")

    def disconnect(self) -> None:
        """Close connection and flush any pending data."""
        self.flush_batch()
        self._connected = False
        self._logger.info("Disconnected from JSON storage")

    def is_connected(self) -> bool:
        """Check if storage is accessible.

        Returns:
            True if base directory is accessible
        """
        return self._connected and os.path.exists(self._base_path)
# Methods are implemented in json_methods.py to keep file under 200 lines
