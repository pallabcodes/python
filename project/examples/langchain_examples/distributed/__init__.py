"""Distributed systems patterns for LangChain production."""

try:
    from distributed.redis_lock import DistributedLock
    __all__ = ["DistributedLock"]
except ImportError:
    __all__ = []

