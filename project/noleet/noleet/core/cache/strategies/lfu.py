"""
Least Frequently Used (LFU) cache replacement strategy.
"""

from typing import List, Dict, Tuple, Optional
import heapq

from .base import CacheStrategy, CacheEntry


class LFUCache(CacheStrategy):
    """LFU (Least Frequently Used) cache replacement strategy."""

    def __init__(self, max_size: int = 1000):
        super().__init__(max_size)
        # Frequency to list of keys mapping
        self.freq_to_keys: Dict[int, List[str]] = {}
        # Key to frequency mapping
        self.key_to_freq: Dict[str, int] = {}
        # Minimum frequency for eviction
        self.min_freq = 0

    def should_evict(self, key: str, size_bytes: int = 0) -> List[str]:
        """Determine which keys to evict using LFU policy."""
        evictions = []

        # Clean up expired entries first
        expired = self.cleanup_expired()
        evictions.extend(expired)

        # Remove expired keys from frequency tracking
        for expired_key in expired:
            self._remove_key_from_freq(expired_key)

        # If still need space, evict least frequently used
        while len(self.entries) >= self.max_size:
            if not self.freq_to_keys.get(self.min_freq):
                break  # No keys at minimum frequency

            # Get least recently used key from lowest frequency
            lfu_key = self.freq_to_keys[self.min_freq].pop(0)

            if not self.freq_to_keys[self.min_freq]:  # Remove empty frequency list
                del self.freq_to_keys[self.min_freq]
                # Find new minimum frequency
                if self.freq_to_keys:
                    self.min_freq = min(self.freq_to_keys.keys())

            evictions.append(lfu_key)
            del self.key_to_freq[lfu_key]
            del self.entries[lfu_key]

        return evictions

    def on_access(self, key: str):
        """Update frequency when key is accessed."""
        if key not in self.key_to_freq:
            return

        old_freq = self.key_to_freq[key]
        new_freq = old_freq + 1

        # Remove from old frequency list
        self.freq_to_keys[old_freq].remove(key)
        if not self.freq_to_keys[old_freq]:
            del self.freq_to_keys[old_freq]
            # Update min_freq if it was the old frequency
            if old_freq == self.min_freq and self.freq_to_keys:
                self.min_freq = min(self.freq_to_keys.keys())

        # Add to new frequency list
        if new_freq not in self.freq_to_keys:
            self.freq_to_keys[new_freq] = []
        self.freq_to_keys[new_freq].append(key)

        self.key_to_freq[key] = new_freq

        # Update minimum frequency
        if not self.freq_to_keys.get(self.min_freq):
            self.min_freq = min(self.freq_to_keys.keys()) if self.freq_to_keys else 0

        if key in self.entries:
            self.entries[key].touch()

    def on_add(self, key: str, entry: CacheEntry):
        """Add key with initial frequency."""
        self.key_to_freq[key] = 1
        if 1 not in self.freq_to_keys:
            self.freq_to_keys[1] = []
        self.freq_to_keys[1].append(key)

        self.entries[key] = entry
        self.min_freq = min(self.min_freq, 1) if self.min_freq > 0 else 1

    def on_remove(self, key: str):
        """Remove key from frequency tracking."""
        self._remove_key_from_freq(key)
        self.entries.pop(key, None)

    def _remove_key_from_freq(self, key: str):
        """Remove key from frequency tracking structures."""
        if key in self.key_to_freq:
            freq = self.key_to_freq[key]
            if freq in self.freq_to_keys:
                self.freq_to_keys[freq].remove(key)
                if not self.freq_to_keys[freq]:
                    del self.freq_to_keys[freq]
                    # Update min_freq if necessary
                    if freq == self.min_freq and self.freq_to_keys:
                        self.min_freq = min(self.freq_to_keys.keys())
            del self.key_to_freq[key]

    def get_frequency(self, key: str) -> int:
        """Get access frequency of a key."""
        return self.key_to_freq.get(key, 0)

    def get_least_frequent_keys(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Get keys with lowest access frequencies."""
        result = []
        for freq in sorted(self.freq_to_keys.keys()):
            for key in self.freq_to_keys[freq]:
                result.append((key, freq))
                if len(result) >= limit:
                    return result
        return result

    def get_most_frequent_keys(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Get keys with highest access frequencies."""
        result = []
        for freq in sorted(self.freq_to_keys.keys(), reverse=True):
            for key in self.freq_to_keys[freq]:
                result.append((key, freq))
                if len(result) >= limit:
                    return result
        return result
