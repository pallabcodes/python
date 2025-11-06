"""
Storage backend factory for the analytics pipeline.

This module provides a factory for creating storage backends based on
configuration, supporting multiple backend types with unified interface.
"""

from typing import Dict, Any, Optional

from .storage_base import StorageBackend, StorageConfig
from .sqlite_backend import SQLiteBackend
from .json_backend import JSONBackend
from .cache_backend import CacheBackend


# Import factory methods
from .factory_methods import (
    _create_sqlite_backend, _create_json_backend, _create_cache_backend,
    get_supported_backends, get_backend_config_template, validate_config
)


class StorageBackendFactory:
    """Factory for creating storage backends.

    Provides a unified way to create different storage backends based on
    configuration, with support for backend-specific options and validation.
    """

    @staticmethod
    def create_backend(config: StorageConfig) -> StorageBackend:
        """Create a storage backend based on configuration.

        Args:
            config: Storage configuration

        Returns:
            Configured storage backend instance

        Raises:
            ValueError: If backend type is unsupported or configuration is invalid
        """
        backend_type = config.backend_type.lower()

        if backend_type == 'sqlite':
            return StorageBackendFactory._create_sqlite_backend(config)
        elif backend_type == 'json':
            return StorageBackendFactory._create_json_backend(config)
        elif backend_type == 'cache':
            return StorageBackendFactory._create_cache_backend(config)
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

    @staticmethod
    def create_backend_from_dict(config_dict: Dict[str, Any]) -> StorageBackend:
        """Create a storage backend from a configuration dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Configured storage backend instance

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate required fields
        required_fields = ['backend_type', 'connection_string']
        missing_fields = [field for field in required_fields if field not in config_dict]
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {missing_fields}")

# Methods are implemented in factory_methods.py to keep file under 200 lines
