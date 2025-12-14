"""
Base cache backend interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
import asyncio


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Union[str, bytes]]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Union[str, bytes], ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all values from cache."""
        pass

    @abstractmethod
    def has_key(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    def get_many(self, keys: list[str]) -> dict[str, Union[str, bytes]]:
        """Get multiple values from cache."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, key_value_pairs: dict[str, Union[str, bytes]],
                 ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        success = True
        for key, value in key_value_pairs.items():
            if not self.set(key, value, ttl):
                success = False
        return success

    def delete_many(self, keys: list[str]) -> bool:
        """Delete multiple values from cache."""
        success = True
        for key in keys:
            if not self.delete(key):
                success = False
        return success

    # Async versions (optional)
    async def aget(self, key: str) -> Optional[Union[str, bytes]]:
        """Async get value from cache."""
        # Default implementation runs sync version in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get, key)

    async def aset(self, key: str, value: Union[str, bytes], ttl: Optional[int] = None) -> bool:
        """Async set value in cache."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.set, key, value, ttl)

    async def adelete(self, key: str) -> bool:
        """Async delete value from cache."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete, key)

    async def aclear(self) -> bool:
        """Async clear all values from cache."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.clear)

    async def ahas_key(self, key: str) -> bool:
        """Async check if key exists in cache."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.has_key, key)

    def get_stats(self) -> dict[str, Any]:
        """Get backend statistics."""
        return {
            'backend_type': self.__class__.__name__,
            'status': 'operational'
        }
