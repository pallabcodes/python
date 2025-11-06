"""
Storage backend methods for the analytics pipeline.

This module contains method implementations and dataclasses for the StorageBackend
to keep the main class files focused and under the 200-line limit.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable, Union, Iterator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from ..pipeline_core.message import DataMessage
from .storage_metrics import StorageMetrics, StorageConfig, QueryFilter, QueryOptions

# Import batch operations
from .storage_batch import (
    store_batch, flush_batch, add_to_batch, _start_flush_thread,
    _flush_worker, _get_connection, _return_connection
)


class StorageBackend(ABC):
    """Abstract base class for all storage backends.

    Provides common functionality for data persistence, querying, and management
    across different storage implementations (SQLite, JSON, Cache, etc.).
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the storage backend.

        Args:
            config: Storage configuration
        """
        self._config = config
        self._metrics = StorageMetrics()
        self._logger = logging.getLogger(f"{__name__}.{config.backend_type}")
        self._lock = threading.RLock()
        self._connected = False

        # Connection management
        self._connection_pool: List[Any] = []
        self._pool_lock = threading.Lock()

        # Batch operations
        self._batch_buffer: List[Dict[str, Any]] = []
        self._batch_lock = threading.Lock()

        # Background flush thread
        self._flush_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        self._logger.info(f"Initialized {config.backend_type} storage backend")

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the storage backend."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the storage backend."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the backend is connected and operational.

        Returns:
            True if connected and operational
        """
        pass

    @abstractmethod
    def store(self, collection: str, data: Dict[str, Any]) -> str:
        """Store a single data record.

        Args:
            collection: Collection/table name
            data: Data to store

        Returns:
            Record ID or key
        """
        pass

    @abstractmethod
    def __enter__(self) -> 'StorageBackend':
        """Context manager entry."""
        self.connect()
        return self

    @abstractmethod
    def retrieve(self, collection: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single record.

        Args:
            collection: Collection/table name
            record_id: Record ID

        Returns:
            Retrieved data or None
        """
        pass

    @abstractmethod
    def query(self, collection: str, filters: Optional[List[QueryFilter]] = None,
              options: Optional[QueryOptions] = None) -> Iterator[Dict[str, Any]]:
        """Query records with filtering and options.

        Args:
            collection: Collection/table name
            filters: Query filters
            options: Query options

        Returns:
            Iterator over matching records
        """
        pass

    @abstractmethod
    def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record.

        Args:
            collection: Collection/table name
            record_id: Record ID

        Returns:
            True if record was deleted
        """
        pass

    @abstractmethod
    def create_collection(self, collection: str, schema: Optional[Dict[str, Any]] = None) -> None:
        """Create a new collection/table.

        Args:
            collection: Collection/table name
            schema: Schema definition
        """
        pass

    @abstractmethod
    def drop_collection(self, collection: str) -> None:
        """Drop a collection/table.

        Args:
            collection: Collection/table name
        """
        pass

    @abstractmethod
    def store_message(self, message: DataMessage) -> str:
        """Store a pipeline message.

        Args:
            message: Pipeline message to store

        Returns:
            Record ID
        """
        pass

    @abstractmethod
    def query_messages(self, filters: Optional[List[QueryFilter]] = None,
                      options: Optional[QueryOptions] = None) -> Iterator[DataMessage]:
        """Query pipeline messages.

        Args:
            filters: Query filters
            options: Query options

        Returns:
            Iterator over matching messages
        """
        pass

    @abstractmethod
    def get_metrics(self) -> StorageMetrics:
        """Get storage metrics.

        Returns:
            Storage metrics
        """
        pass

    @abstractmethod

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
