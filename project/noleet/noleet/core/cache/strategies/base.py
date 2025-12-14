"""
Base cache strategy interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False

        from datetime import timedelta
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time

    def touch(self):
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class CacheStrategy(ABC):
    """Abstract base class for cache replacement strategies."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.entries: dict[str, CacheEntry] = {}

    @abstractmethod
    def should_evict(self, key: str, size_bytes: int = 0) -> List[str]:
        """Determine which keys should be evicted to make room for new entry.

        Args:
            key: The key being added
            size_bytes: Size of the value being added

        Returns:
            List of keys to evict
        """
        pass

    @abstractmethod
    def on_access(self, key: str):
        """Called when a key is accessed."""
        pass

    @abstractmethod
    def on_add(self, key: str, entry: CacheEntry):
        """Called when a key is added."""
        pass

    @abstractmethod
    def on_remove(self, key: str):
        """Called when a key is removed."""
        pass

    def is_expired(self, key: str) -> bool:
        """Check if a key is expired."""
        if key in self.entries:
            return self.entries[key].is_expired()
        return False

    def cleanup_expired(self) -> List[str]:
        """Remove expired entries and return their keys."""
        expired_keys = []
        for key, entry in list(self.entries.items()):
            if entry.is_expired():
                expired_keys.append(key)
                del self.entries[key]
        return expired_keys

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        total_accesses = sum(entry.access_count for entry in self.entries.values())
        avg_accesses = total_accesses / len(self.entries) if self.entries else 0

        return {
            'total_entries': len(self.entries),
            'max_size': self.max_size,
            'utilization_percent': (len(self.entries) / self.max_size) * 100,
            'total_accesses': total_accesses,
            'average_accesses': avg_accesses,
            'expired_entries': len(self.cleanup_expired())
        }
