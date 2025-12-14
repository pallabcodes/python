"""
In-memory cache backend implementation.
"""

import time
from typing import Dict, Optional, Union
import threading

from .base import CacheBackend


class MemoryBackend(CacheBackend):
    """In-memory cache backend using a dictionary."""

    def __init__(self, max_memory_mb: Optional[int] = None):
        self._cache: Dict[str, Dict[str, Union[str, bytes, float]]] = {}
        self._lock = threading.RLock()
        self.max_memory_mb = max_memory_mb
        self._current_memory_usage = 0

    def get(self, key: str) -> Optional[Union[str, bytes]]:
        """Get value from memory cache."""
        with self._lock:
            self._cleanup_expired()
            entry = self._cache.get(key)
            if entry and not self._is_expired(entry):
                return entry['value']
            elif entry:
                del self._cache[key]  # Remove expired entry
            return None

    def set(self, key: str, value: Union[str, bytes], ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        with self._lock:
            self._cleanup_expired()

            # Calculate value size
            value_size = len(value) if isinstance(value, (str, bytes)) else 0

            # Check memory limit
            if self.max_memory_mb and self._current_memory_usage + value_size > self.max_memory_mb * 1024 * 1024:
                self._evict_to_free_space(value_size)

            # Remove existing entry size from memory usage
            if key in self._cache:
                old_size = len(self._cache[key]['value']) if isinstance(self._cache[key]['value'], (str, bytes)) else 0
                self._current_memory_usage -= old_size

            # Set new entry
            expiry = time.time() + ttl if ttl else None
            self._cache[key] = {
                'value': value,
                'expiry': expiry,
                'size': value_size
            }

            self._current_memory_usage += value_size
            return True

    def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if isinstance(entry['value'], (str, bytes)):
                    self._current_memory_usage -= len(entry['value'])
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        """Clear all values from memory cache."""
        with self._lock:
            self._cache.clear()
            self._current_memory_usage = 0
            return True

    def has_key(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        with self._lock:
            self._cleanup_expired()
            entry = self._cache.get(key)
            return entry is not None and not self._is_expired(entry)

    def _is_expired(self, entry: Dict[str, Union[str, bytes, float]]) -> bool:
        """Check if cache entry is expired."""
        expiry = entry.get('expiry')
        return expiry is not None and time.time() > expiry

    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = []
        for key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
                if isinstance(entry['value'], (str, bytes)):
                    self._current_memory_usage -= len(entry['value'])

        for key in expired_keys:
            del self._cache[key]

    def _evict_to_free_space(self, required_space: int):
        """Evict entries to free up required space."""
        # Simple FIFO eviction for memory pressure
        entries_by_time = sorted(
            self._cache.items(),
            key=lambda x: x[1].get('expiry', float('inf'))
        )

        freed_space = 0
        evicted_keys = []

        for key, entry in entries_by_time:
            if freed_space >= required_space:
                break

            evicted_keys.append(key)
            entry_size = entry.get('size', 0)
            freed_space += entry_size

        # Remove evicted entries
        for key in evicted_keys:
            if key in self._cache:
                del self._cache[key]

        self._current_memory_usage -= freed_space

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get memory backend statistics."""
        with self._lock:
            self._cleanup_expired()

            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if self._is_expired(entry))
            memory_usage_mb = self._current_memory_usage / (1024 * 1024)

            return {
                'backend_type': 'MemoryBackend',
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'memory_usage_mb': memory_usage_mb,
                'max_memory_mb': self.max_memory_mb,
                'memory_utilization_percent': (memory_usage_mb / self.max_memory_mb) * 100 if self.max_memory_mb else 0,
                'status': 'operational'
            }
