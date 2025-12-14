"""
Cache decorators for easy function caching.
"""

import functools
import hashlib
import json
from typing import Callable, Any, Optional, Union
import logging

from .cache_manager import CacheManager, CacheConfig

logger = logging.getLogger(__name__)


def cached(cache_name: str = "default", ttl: Optional[int] = None,
           key_func: Optional[Callable] = None, backend: str = "memory",
           strategy: str = "lru", condition: Optional[Callable] = None):
    """
    Decorator to cache function results.

    Args:
        cache_name: Name of the cache instance
        ttl: Time-to-live in seconds (overrides cache default)
        key_func: Custom function to generate cache key from arguments
        backend: Cache backend to use
        strategy: Cache strategy to use
        condition: Function that returns True if result should be cached
    """
    def decorator(func: Callable) -> Callable:
        # Get cache instance
        cache_manager = CacheManager()
        cache = cache_manager.get_cache(cache_name, backend=backend, strategy=strategy)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check condition if provided
            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func, args, kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache the result
            try:
                cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result for {func.__name__} with key {cache_key}")
            except Exception as e:
                logger.warning(f"Failed to cache result for {func.__name__}: {e}")

            return result

        # Store cache configuration on the function for introspection
        wrapper._cache_config = {
            'cache_name': cache_name,
            'ttl': ttl,
            'backend': backend,
            'strategy': strategy
        }

        return wrapper
    return decorator


def cache_invalidate(cache_names: Union[str, list[str]], key_func: Optional[Callable] = None):
    """
    Decorator to invalidate cache entries after function execution.

    Args:
        cache_names: Name(s) of cache instances to invalidate
        key_func: Function to generate cache key for invalidation
    """
    if isinstance(cache_names, str):
        cache_names = [cache_names]

    def decorator(func: Callable) -> Callable:
        cache_manager = CacheManager()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function first
            result = func(*args, **kwargs)

            try:
                # Invalidate specified caches
                for cache_name in cache_names:
                    cache = cache_manager.get_cache(cache_name)

                    if key_func:
                        cache_key = key_func(*args, **kwargs)
                        cache.delete(cache_key)
                        logger.debug(f"Invalidated cache {cache_name} key {cache_key}")
                    else:
                        # Clear entire cache
                        cache.clear()
                        logger.debug(f"Cleared entire cache {cache_name}")

            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")

            return result

        return wrapper
    return decorator


def cached_method(cache_name: str = "default", ttl: Optional[int] = None,
                  key_func: Optional[Callable] = None, include_self: bool = False):
    """
    Decorator for caching instance methods.

    Args:
        cache_name: Name of the cache instance
        ttl: Time-to-live in seconds
        key_func: Custom function to generate cache key
        include_self: Whether to include 'self' in cache key generation
    """
    def decorator(func: Callable) -> Callable:
        cache_manager = CacheManager()
        cache = cache_manager.get_cache(cache_name)

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(self, *args, **kwargs)
            else:
                cache_key = _generate_method_cache_key(func, self, args, kwargs, include_self)

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute method
            result = func(self, *args, **kwargs)

            # Cache result
            try:
                cache.set(cache_key, result, ttl=ttl)
            except Exception as e:
                logger.warning(f"Failed to cache method result: {e}")

            return result

        return wrapper
    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Generate a cache key from function call."""
    # Create a hash of the function name, args, and kwargs
    key_data = {
        'func': f"{func.__module__}.{func.__qualname__}",
        'args': args,
        'kwargs': kwargs
    }

    # Convert to JSON string and hash
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def _generate_method_cache_key(func: Callable, self: Any, args: tuple,
                               kwargs: dict, include_self: bool) -> str:
    """Generate a cache key for instance methods."""
    key_data = {
        'func': f"{func.__qualname__}",
        'args': args,
        'kwargs': kwargs
    }

    if include_self:
        key_data['self'] = str(self)

    # Add instance ID for better isolation
    if hasattr(self, 'id'):
        key_data['instance_id'] = self.id
    elif hasattr(self, '__dict__'):
        # Fallback to object hash
        key_data['instance_hash'] = hash(str(self.__dict__))

    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


# Convenience decorators for common caching patterns

def cache_llm_response(ttl: int = 3600):
    """Cache LLM responses for 1 hour by default."""
    return cached(cache_name="llm_responses", ttl=ttl, backend="memory", strategy="ttl")


def cache_embeddings(ttl: int = 7200):
    """Cache embeddings for 2 hours by default."""
    return cached(cache_name="embeddings", ttl=ttl, backend="memory", strategy="lru")


def cache_recommendations(ttl: int = 1800):
    """Cache recommendations for 30 minutes by default."""
    return cached(cache_name="recommendations", ttl=ttl, backend="memory", strategy="ttl")


def cache_semantic_search(ttl: int = 3600):
    """Cache semantic search results for 1 hour by default."""
    return cached(cache_name="semantic_search", ttl=ttl, backend="memory", strategy="lru")


# Cache warming utilities

def warmup_cache(func: Callable, *args_list, cache_name: str = "default", **kwargs):
    """
    Warm up cache by pre-computing results for common argument combinations.

    Args:
        func: Function to warm up
        args_list: List of argument tuples to pre-compute
        cache_name: Name of cache to warm up
        kwargs: Additional keyword arguments for all calls
    """
    cache_manager = CacheManager()
    cache = cache_manager.get_cache(cache_name)

    logger.info(f"Warming up cache '{cache_name}' with {len(args_list)} entries")

    for args in args_list:
        try:
            result = func(*args, **kwargs)
            cache_key = _generate_cache_key(func, args, kwargs)
            cache.set(cache_key, result)
        except Exception as e:
            logger.warning(f"Failed to warm up cache for args {args}: {e}")


# Cache analytics

def get_cache_hit_rate(cache_name: str = "default") -> float:
    """Get cache hit rate as a percentage."""
    cache_manager = CacheManager()
    metrics = cache_manager.get_metrics(cache_name)

    hits = metrics.get('hits', 0)
    misses = metrics.get('misses', 0)

    total = hits + misses
    return (hits / total * 100) if total > 0 else 0.0


def log_cache_performance(cache_name: str = "default"):
    """Log cache performance statistics."""
    hit_rate = get_cache_hit_rate(cache_name)
    cache_manager = CacheManager()
    metrics = cache_manager.get_metrics(cache_name)

    logger.info(
        f"Cache '{cache_name}' performance: "
        f"Hit rate: {hit_rate:.1f}%, "
        f"Hits: {metrics.get('hits', 0)}, "
        f"Misses: {metrics.get('misses', 0)}, "
        f"Errors: {metrics.get('errors', 0)}"
    )
