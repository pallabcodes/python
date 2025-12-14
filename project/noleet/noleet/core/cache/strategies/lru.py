"""
Least Recently Used (LRU) cache replacement strategy.
"""

from typing import List, Optional
import heapq
from collections import OrderedDict

from .base import CacheStrategy, CacheEntry


class LRUCache(CacheStrategy):
    """LRU (Least Recently Used) cache replacement strategy."""

    def __init__(self, max_size: int = 1000):
        super().__init__(max_size)
        # Use OrderedDict to maintain insertion order (most recent at end)
        self.access_order: OrderedDict[str, None] = OrderedDict()

    def should_evict(self, key: str, size_bytes: int = 0) -> List[str]:
        """Determine which keys to evict using LRU policy."""
        evictions = []

        # Clean up expired entries first
        expired = self.cleanup_expired()
        evictions.extend(expired)

        # Remove from access order
        for expired_key in expired:
            self.access_order.pop(expired_key, None)

        # If still need space, evict least recently used
        while len(self.entries) >= self.max_size:
            # Get the least recently used key (first in OrderedDict)
            lru_key = next(iter(self.access_order))
            evictions.append(lru_key)
            self.access_order.pop(lru_key)
            del self.entries[lru_key]

        return evictions

    def on_access(self, key: str):
        """Move accessed key to end (most recently used)."""
        if key in self.access_order:
            # Move to end by removing and re-adding
            self.access_order.move_to_end(key)

        if key in self.entries:
            self.entries[key].touch()

    def on_add(self, key: str, entry: CacheEntry):
        """Add key to access order."""
        self.access_order[key] = None
        self.entries[key] = entry

    def on_remove(self, key: str):
        """Remove key from access order."""
        self.access_order.pop(key, None)
        self.entries.pop(key, None)

    def get_lru_key(self) -> Optional[str]:
        """Get the least recently used key."""
        if self.access_order:
            return next(iter(self.access_order))
        return None

    def get_mru_key(self) -> Optional[str]:
        """Get the most recently used key."""
        if self.access_order:
            return next(reversed(self.access_order))
        return None
