"""
Time-To-Live (TTL) cache replacement strategy.
"""

from typing import List
from datetime import datetime, timedelta

from .base import CacheStrategy, CacheEntry


class TTLCache(CacheStrategy):
    """TTL (Time-To-Live) cache replacement strategy."""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        super().__init__(max_size)
        self.default_ttl_seconds = ttl_seconds

    def should_evict(self, key: str, size_bytes: int = 0) -> List[str]:
        """Determine which keys to evict based on TTL."""
        evictions = []

        # Always clean up expired entries first
        expired = self.cleanup_expired()
        evictions.extend(expired)

        # If we still need space and are at max capacity,
        # evict the oldest entries (FIFO for TTL)
        while len(self.entries) >= self.max_size:
            # Find the oldest entry
            oldest_key = None
            oldest_time = datetime.now()

            for entry_key, entry in self.entries.items():
                if entry.created_at < oldest_time:
                    oldest_time = entry.created_at
                    oldest_key = entry_key

            if oldest_key:
                evictions.append(oldest_key)
                del self.entries[oldest_key]
            else:
                break

        return evictions

    def on_access(self, key: str):
        """Update access time but don't extend TTL."""
        if key in self.entries:
            # Don't update last_accessed to preserve TTL semantics
            # Only increment access count
            self.entries[key].access_count += 1

    def on_add(self, key: str, entry: CacheEntry):
        """Add entry with TTL."""
        # Set TTL if not already set
        if entry.ttl_seconds is None:
            entry.ttl_seconds = self.default_ttl_seconds

        self.entries[key] = entry

    def on_remove(self, key: str):
        """Remove entry."""
        self.entries.pop(key, None)

    def set_ttl(self, key: str, ttl_seconds: int):
        """Set TTL for an existing entry."""
        if key in self.entries:
            self.entries[key].ttl_seconds = ttl_seconds

    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key in seconds."""
        if key not in self.entries:
            return 0

        entry = self.entries[key]
        if entry.ttl_seconds is None:
            return -1  # No expiration

        expiry_time = entry.created_at + timedelta(seconds=entry.ttl_seconds)
        remaining = expiry_time - datetime.now()

        return max(0, int(remaining.total_seconds()))

    def extend_ttl(self, key: str, additional_seconds: int):
        """Extend TTL for an existing entry."""
        if key in self.entries:
            entry = self.entries[key]
            if entry.ttl_seconds is None:
                entry.ttl_seconds = additional_seconds
            else:
                entry.ttl_seconds += additional_seconds
            # Reset created_at to extend from now
            entry.created_at = datetime.now()

    def get_expiring_soon(self, within_seconds: int = 300) -> List[str]:
        """Get keys that will expire within the specified time."""
        now = datetime.now()
        cutoff_time = now + timedelta(seconds=within_seconds)

        expiring_keys = []
        for key, entry in self.entries.items():
            if entry.ttl_seconds is not None:
                expiry_time = entry.created_at + timedelta(seconds=entry.ttl_seconds)
                if expiry_time <= cutoff_time:
                    expiring_keys.append(key)

        return expiring_keys

    def cleanup_expired(self) -> List[str]:
        """Remove and return expired entries."""
        expired_keys = []
        now = datetime.now()

        for key, entry in list(self.entries.items()):
            if entry.is_expired():
                expired_keys.append(key)
                del self.entries[key]

        return expired_keys

    def get_expiry_stats(self) -> dict:
        """Get statistics about entry expirations."""
        now = datetime.now()
        expiring_soon = self.get_expiring_soon(300)  # Next 5 minutes
        expiring_hour = self.get_expiring_soon(3600)  # Next hour

        return {
            'total_entries': len(self.entries),
            'expiring_within_5min': len(expiring_soon),
            'expiring_within_1hour': len(expiring_hour),
            'expired_count': len(self.cleanup_expired())
        }
