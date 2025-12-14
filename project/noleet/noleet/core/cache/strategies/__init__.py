"""
Cache replacement strategies.
"""

from .base import CacheStrategy
from .lru import LRUCache
from .lfu import LFUCache
from .ttl import TTLCache
from .size_limited import SizeLimitedCache
from .composite import CompositeCache

__all__ = [
    'CacheStrategy',
    'LRUCache',
    'LFUCache',
    'TTLCache',
    'SizeLimitedCache',
    'CompositeCache'
]
