"""
Batch operations for the storage backend.

This module contains batch processing functionality for the StorageBackend class,
separated for better modularity and to keep file sizes under limits.
"""

import time
import threading
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .storage_operations import StorageBackend


def store_batch(self: 'StorageBackend', collection: str, data_list: List[Dict[str, Any]]) -> List[str]:
    """Store multiple records in batch.
    
    Args:
        collection: Collection/table name
        data_list: List of data dictionaries to store
        
    Returns:
        List of record IDs
    """
    if not self._connected:
        raise RuntimeError("Storage backend not connected")
        
    record_ids = []
    with self._lock:
        for data in data_list:
            try:
                record_id = self.store(collection, data)
                record_ids.append(record_id)
            except Exception as e:
                self._logger.error(f"Failed to store record in batch: {e}")
                # Continue with other records
                
    return record_ids


def flush_batch(self: 'StorageBackend') -> None:
    """Flush pending batch operations.
    
    This method forces immediate processing of any queued batch operations.
    """
    if not self._connected:
        return
        
    with self._lock:
        if self._batch_queue:
            try:
                # Process all queued items
                batch_items = list(self._batch_queue)
                self._batch_queue.clear()
                
                # Group by collection
                collection_batches = {}
                for collection, data in batch_items:
                    if collection not in collection_batches:
                        collection_batches[collection] = []
                    collection_batches[collection].append(data)
                
                # Store each collection batch
                for collection, data_list in collection_batches.items():
                    self.store_batch(collection, data_list)
                    
                self._logger.debug(f"Flushed {len(batch_items)} batch items")
                
            except Exception as e:
                self._logger.error(f"Error flushing batch: {e}")


def add_to_batch(self: 'StorageBackend', collection: str, data: Dict[str, Any]) -> None:
    """Add data to batch queue for later processing.
    
    Args:
        collection: Collection/table name
        data: Data to add to batch
    """
    if not self._connected:
        raise RuntimeError("Storage backend not connected")
        
    with self._lock:
        self._batch_queue.append((collection, data))
        
        # Auto-flush if batch size reached
        if len(self._batch_queue) >= self._config.batch_size:
            self.flush_batch()


def _start_flush_thread(self: 'StorageBackend') -> None:
    """Start the background flush thread."""
    if self._flush_thread and self._flush_thread.is_alive():
        return
        
    self._flush_thread = threading.Thread(
        target=self._flush_worker,
        daemon=True,
        name=f"{self._config.backend_type}-flush"
    )
    self._flush_thread.start()
    self._logger.debug("Started batch flush thread")


def _flush_worker(self: 'StorageBackend') -> None:
    """Background worker for periodic batch flushing."""
    while self._connected and not self._shutdown_event.is_set():
        try:
            # Wait for flush interval or shutdown
            if self._shutdown_event.wait(timeout=self._config.flush_interval):
                break  # Shutdown requested
                
            # Flush pending batches
            self.flush_batch()
            
        except Exception as e:
            self._logger.error(f"Error in batch flush worker: {e}")
            time.sleep(1)  # Avoid tight error loop


def _get_connection(self: 'StorageBackend') -> Any:
    """Get a connection from the pool.
    
    Returns:
        Database connection
    """
    # This is a simplified implementation
    # In practice, you'd implement a proper connection pool
    return self._create_connection()


def _return_connection(self: 'StorageBackend', connection: Any) -> None:
    """Return a connection to the pool.
    
    Args:
        connection: Connection to return
    """
    # This is a simplified implementation
    # In practice, you'd implement proper connection pooling
    self._close_connection(connection)
