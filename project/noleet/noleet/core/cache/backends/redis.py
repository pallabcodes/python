"""
Redis cache backend implementation.
"""

from typing import Optional, Union, Dict, Any
import logging

from .base import CacheBackend

logger = logging.getLogger(__name__)


class RedisBackend(CacheBackend):
    """Redis cache backend."""

    def __init__(self, url: str = "redis://localhost:6379", db: int = 0,
                 key_prefix: str = "", **kwargs):
        try:
            import redis
            self.redis = redis.Redis.from_url(url, db=db, **kwargs)
            self.key_prefix = key_prefix
            # Test connection
            self.redis.ping()
        except ImportError:
            raise ImportError("redis package is required for RedisBackend")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            raise RuntimeError(f"Cannot connect to Redis: {e}")

    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.key_prefix}{key}" if self.key_prefix else key

    def get(self, key: str) -> Optional[Union[str, bytes]]:
        """Get value from Redis."""
        try:
            full_key = self._make_key(key)
            value = self.redis.get(full_key)
            return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Union[str, bytes], ttl: Optional[int] = None) -> bool:
        """Set value in Redis."""
        try:
            full_key = self._make_key(key)
            if ttl:
                return bool(self.redis.setex(full_key, ttl, value))
            else:
                return bool(self.redis.set(full_key, value))
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        try:
            full_key = self._make_key(key)
            return bool(self.redis.delete(full_key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all values from Redis (dangerous - clears entire DB)."""
        try:
            # Only clear keys with our prefix
            if self.key_prefix:
                keys = self.redis.keys(f"{self.key_prefix}*")
                if keys:
                    return bool(self.redis.delete(*keys))
            else:
                # Clear entire database - use with caution
                return bool(self.redis.flushdb())
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def has_key(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            full_key = self._make_key(key)
            return bool(self.redis.exists(full_key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    def get_many(self, keys: list[str]) -> Dict[str, Union[str, bytes]]:
        """Get multiple values from Redis."""
        try:
            full_keys = [self._make_key(key) for key in keys]
            values = self.redis.mget(full_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = value.decode('utf-8') if isinstance(value, bytes) else value
            return result
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return {}

    def set_many(self, key_value_pairs: Dict[str, Union[str, bytes]],
                 ttl: Optional[int] = None) -> bool:
        """Set multiple values in Redis."""
        try:
            # Redis mset doesn't support TTL, so we need to set each key individually
            success = True
            with self.redis.pipeline() as pipe:
                for key, value in key_value_pairs.items():
                    full_key = self._make_key(key)
                    if ttl:
                        pipe.setex(full_key, ttl, value)
                    else:
                        pipe.set(full_key, value)
                pipe.execute()
            return success
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            return False

    def delete_many(self, keys: list[str]) -> bool:
        """Delete multiple values from Redis."""
        try:
            full_keys = [self._make_key(key) for key in keys]
            return bool(self.redis.delete(*full_keys))
        except Exception as e:
            logger.error(f"Redis delete many error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis backend statistics."""
        try:
            info = self.redis.info()
            db_info = info.get('db0', {}) if 'db0' in info else {}

            return {
                'backend_type': 'RedisBackend',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'total_connections_received': info.get('total_connections_received'),
                'keys_count': db_info.get('keys', 0),
                'expires_count': db_info.get('expires', 0),
                'status': 'operational'
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                'backend_type': 'RedisBackend',
                'status': 'error',
                'error': str(e)
            }
