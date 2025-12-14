"""
Cache manager for coordinating different caching strategies and backends.
Provides unified interface for caching operations across the application.
"""

import asyncio
import hashlib
import json
import pickle
from typing import Any, Dict, Optional, Union, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from .backends.base import CacheBackend
from .backends.memory import MemoryBackend
from .strategies.lru import LRUCache
from .strategies.lfu import LFUCache
from .strategies.ttl import TTLCache

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache manager."""
    default_backend: str = "memory"
    default_strategy: str = "lru"
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 hour default
    enable_compression: bool = False
    enable_serialization: bool = True
    key_prefix: str = "noleet:"
    enable_metrics: bool = True

    # Backend-specific configs
    redis_url: Optional[str] = None
    redis_db: int = 0
    file_cache_dir: str = "/tmp/noleet_cache"
    db_connection_string: Optional[str] = None


class CacheManager:
    """Central cache manager coordinating multiple cache instances."""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.backends: Dict[str, CacheBackend] = {}
        self.strategies: Dict[str, Any] = {}
        self.metrics: Dict[str, Dict[str, int]] = {}

        # Initialize default backends
        self._init_backends()
        self._init_strategies()

    def _init_backends(self):
        """Initialize cache backends."""
        # Memory backend (always available)
        self.backends["memory"] = MemoryBackend()

        # Redis backend (if configured)
        if self.config.redis_url:
            try:
                from .backends.redis import RedisBackend
                self.backends["redis"] = RedisBackend(
                    url=self.config.redis_url,
                    db=self.config.redis_db,
                    key_prefix=self.config.key_prefix
                )
            except ImportError:
                logger.warning("Redis not available, skipping Redis backend")

        # File backend
        try:
            from .backends.file import FileBackend
            self.backends["file"] = FileBackend(
                cache_dir=self.config.file_cache_dir,
                key_prefix=self.config.key_prefix
            )
        except Exception as e:
            logger.warning(f"File backend initialization failed: {e}")

        # Database backend (if configured)
        if self.config.db_connection_string:
            try:
                from .backends.database import DatabaseBackend
                self.backends["database"] = DatabaseBackend(
                    connection_string=self.config.db_connection_string,
                    key_prefix=self.config.key_prefix
                )
            except Exception as e:
                logger.warning(f"Database backend initialization failed: {e}")

    def _init_strategies(self):
        """Initialize cache strategies."""
        self.strategies["lru"] = LRUCache(max_size=self.config.max_size)
        self.strategies["lfu"] = LFUCache(max_size=self.config.max_size)
        self.strategies["ttl"] = TTLCache(ttl_seconds=self.config.ttl_seconds)

    def get_cache(self, name: str, backend: str = None, strategy: str = None) -> 'CacheInstance':
        """Get or create a named cache instance."""
        backend_name = backend or self.config.default_backend
        strategy_name = strategy or self.config.default_strategy

        if backend_name not in self.backends:
            raise ValueError(f"Backend '{backend_name}' not available")

        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy '{strategy_name}' not available")

        return CacheInstance(
            name=name,
            backend=self.backends[backend_name],
            strategy=self.strategies[strategy_name],
            config=self.config,
            metrics_collector=self._collect_metrics if self.config.enable_metrics else None
        )

    def _collect_metrics(self, cache_name: str, operation: str, hit: bool = None):
        """Collect cache metrics."""
        if cache_name not in self.metrics:
            self.metrics[cache_name] = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0,
                'errors': 0
            }

        if operation == 'get':
            if hit:
                self.metrics[cache_name]['hits'] += 1
            else:
                self.metrics[cache_name]['misses'] += 1
        elif operation == 'set':
            self.metrics[cache_name]['sets'] += 1
        elif operation == 'delete':
            self.metrics[cache_name]['deletes'] += 1
        elif operation == 'error':
            self.metrics[cache_name]['errors'] += 1

    def get_metrics(self, cache_name: Optional[str] = None) -> Dict[str, Any]:
        """Get cache metrics."""
        if cache_name:
            return self.metrics.get(cache_name, {})

        # Aggregate metrics across all caches
        total_metrics = {
            'total_hits': 0,
            'total_misses': 0,
            'total_sets': 0,
            'total_deletes': 0,
            'total_errors': 0,
            'hit_rate': 0.0,
            'caches': {}
        }

        for name, metrics in self.metrics.items():
            total_metrics['caches'][name] = metrics.copy()
            total_metrics['total_hits'] += metrics['hits']
            total_metrics['total_misses'] += metrics['misses']
            total_metrics['total_sets'] += metrics['sets']
            total_metrics['total_deletes'] += metrics['deletes']
            total_metrics['total_errors'] += metrics['errors']

        # Calculate overall hit rate
        total_requests = total_metrics['total_hits'] + total_metrics['total_misses']
        if total_requests > 0:
            total_metrics['hit_rate'] = total_metrics['total_hits'] / total_requests

        return total_metrics

    def clear_all(self):
        """Clear all caches."""
        for backend in self.backends.values():
            try:
                backend.clear()
            except Exception as e:
                logger.error(f"Failed to clear backend: {e}")

        self.metrics.clear()
        logger.info("All caches cleared")

    def health_check(self) -> Dict[str, bool]:
        """Check health of all cache backends."""
        health = {}
        for name, backend in self.backends.items():
            try:
                backend.set("health_check", "ok", ttl=10)
                value = backend.get("health_check")
                health[name] = value == "ok"
            except Exception:
                health[name] = False

        return health


class CacheInstance:
    """Individual cache instance with specific backend and strategy."""

    def __init__(self, name: str, backend: CacheBackend, strategy: Any,
                 config: CacheConfig, metrics_collector: Optional[Callable] = None):
        self.name = name
        self.backend = backend
        self.strategy = strategy
        self.config = config
        self.metrics_collector = metrics_collector

    def _make_key(self, key: Any) -> str:
        """Generate a cache key from the input."""
        if isinstance(key, str):
            key_str = key
        else:
            # Serialize complex keys
            key_str = json.dumps(key, sort_keys=True, default=str)

        # Add prefix and hash for consistent key length
        full_key = f"{self.config.key_prefix}{self.name}:{key_str}"
        return hashlib.md5(full_key.encode()).hexdigest()

    def _serialize_value(self, value: Any) -> Union[str, bytes]:
        """Serialize value for storage."""
        if not self.config.enable_serialization:
            return value

        if isinstance(value, (str, int, float, bool)):
            return str(value)
        else:
            # Use pickle for complex objects
            return pickle.dumps(value)

    def _deserialize_value(self, value: Union[str, bytes]) -> Any:
        """Deserialize value from storage."""
        if not self.config.enable_serialization:
            return value

        if isinstance(value, str):
            # Try to parse as JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        else:
            # Try to unpickle
            try:
                return pickle.loads(value)
            except (pickle.UnpicklingError, TypeError):
                return value

    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache."""
        try:
            cache_key = self._make_key(key)

            # Check strategy first (for TTL, size limits, etc.)
            if hasattr(self.strategy, 'is_expired') and self.strategy.is_expired(cache_key):
                if self.metrics_collector:
                    self.metrics_collector(self.name, 'get', hit=False)
                return None

            value = self.backend.get(cache_key)
            if value is not None:
                deserialized_value = self._deserialize_value(value)
                if self.metrics_collector:
                    self.metrics_collector(self.name, 'get', hit=True)
                return deserialized_value
            else:
                if self.metrics_collector:
                    self.metrics_collector(self.name, 'get', hit=False)
                return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            if self.metrics_collector:
                self.metrics_collector(self.name, 'error')
            return None

    def set(self, key: Any, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            cache_key = self._make_key(key)
            serialized_value = self._serialize_value(value)

            # Apply strategy constraints
            if hasattr(self.strategy, 'should_evict'):
                evictions = self.strategy.should_evict(cache_key, len(str(serialized_value)))
                for eviction_key in evictions:
                    self.backend.delete(eviction_key)

            # Set TTL
            effective_ttl = ttl or self.config.ttl_seconds

            success = self.backend.set(cache_key, serialized_value, ttl=effective_ttl)
            if success and self.metrics_collector:
                self.metrics_collector(self.name, 'set')

            return success

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            if self.metrics_collector:
                self.metrics_collector(self.name, 'error')
            return False

    def delete(self, key: Any) -> bool:
        """Delete value from cache."""
        try:
            cache_key = self._make_key(key)
            success = self.backend.delete(cache_key)
            if success and self.metrics_collector:
                self.metrics_collector(self.name, 'delete')
            return success

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            if self.metrics_collector:
                self.metrics_collector(self.name, 'error')
            return False

    def clear(self) -> bool:
        """Clear this cache instance."""
        try:
            # Note: This clears the entire backend, not just this cache instance
            # In production, you'd want prefix-based clearing
            return self.backend.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def has_key(self, key: Any) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None

    async def aget(self, key: Any) -> Optional[Any]:
        """Async version of get."""
        # For backends that support async, delegate to them
        if hasattr(self.backend, 'aget'):
            try:
                cache_key = self._make_key(key)
                value = await self.backend.aget(cache_key)
                if value is not None:
                    deserialized_value = self._deserialize_value(value)
                    if self.metrics_collector:
                        self.metrics_collector(self.name, 'get', hit=True)
                    return deserialized_value
                else:
                    if self.metrics_collector:
                        self.metrics_collector(self.name, 'get', hit=False)
                    return None
            except Exception as e:
                logger.error(f"Async cache get error for key {key}: {e}")
                if self.metrics_collector:
                    self.metrics_collector(self.name, 'error')
                return None
        else:
            # Fall back to sync version in a thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.get, key)

    async def aset(self, key: Any, value: Any, ttl: Optional[int] = None) -> bool:
        """Async version of set."""
        if hasattr(self.backend, 'aset'):
            try:
                cache_key = self._make_key(key)
                serialized_value = self._serialize_value(value)
                effective_ttl = ttl or self.config.ttl_seconds
                success = await self.backend.aset(cache_key, serialized_value, ttl=effective_ttl)
                if success and self.metrics_collector:
                    self.metrics_collector(self.name, 'set')
                return success
            except Exception as e:
                logger.error(f"Async cache set error for key {key}: {e}")
                if self.metrics_collector:
                    self.metrics_collector(self.name, 'error')
                return False
        else:
            # Fall back to sync version in a thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.set, key, value, ttl)


# Global cache manager instance
cache_manager = CacheManager()

# Convenience functions for common caching operations
def get_llm_cache():
    """Get LLM response cache."""
    return cache_manager.get_cache("llm_responses", strategy="ttl")

def get_embedding_cache():
    """Get embedding cache."""
    return cache_manager.get_cache("embeddings", strategy="lru")

def get_recommendation_cache():
    """Get recommendation cache."""
    return cache_manager.get_cache("recommendations", strategy="ttl")

def get_semantic_cache():
    """Get semantic search cache."""
    return cache_manager.get_cache("semantic_search", strategy="lru")
