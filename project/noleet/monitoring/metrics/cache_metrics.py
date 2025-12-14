"""
Cache-specific metrics collection for monitoring cache performance.
"""

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from typing import Optional


class CacheMetricsCollector:
    """Collects metrics specific to cache operations."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        # Cache operation metrics
        self.cache_operations_total = Counter(
            'noleet_cache_operations_total',
            'Total cache operations',
            ['cache_name', 'operation', 'result'],
            registry=registry
        )

        self.cache_operation_duration_seconds = Histogram(
            'noleet_cache_operation_duration_seconds',
            'Cache operation duration in seconds',
            ['cache_name', 'operation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=registry
        )

        # Cache hit/miss metrics (legacy, kept for compatibility)
        self.cache_hits_total = Counter(
            'noleet_cache_hits_total',
            'Total cache hits',
            registry=registry
        )

        self.cache_misses_total = Counter(
            'noleet_cache_misses_total',
            'Total cache misses',
            registry=registry
        )

        # Cache size and utilization
        self.cache_size_items = Gauge(
            'noleet_cache_size_items',
            'Current cache size in items',
            ['cache_name'],
            registry=registry
        )

        self.cache_memory_usage_bytes = Gauge(
            'noleet_cache_memory_usage_bytes',
            'Cache memory usage in bytes',
            ['cache_name'],
            registry=registry
        )

        self.cache_hit_rate_percent = Gauge(
            'noleet_cache_hit_rate_percent',
            'Cache hit rate percentage',
            ['cache_name'],
            registry=registry
        )

        # Cache eviction metrics
        self.cache_evictions_total = Counter(
            'noleet_cache_evictions_total',
            'Total cache evictions',
            ['cache_name', 'reason'],
            registry=registry
        )

        # Cache backend metrics
        self.cache_backend_operations_total = Counter(
            'noleet_cache_backend_operations_total',
            'Total cache backend operations',
            ['backend_type', 'operation'],
            registry=registry
        )

        self.cache_backend_errors_total = Counter(
            'noleet_cache_backend_errors_total',
            'Total cache backend errors',
            ['backend_type', 'error_type'],
            registry=registry
        )

    def record_operation(self, cache_name: str, operation: str, result: str,
                        duration: Optional[float] = None):
        """Record a cache operation."""
        self.cache_operations_total.labels(
            cache_name=cache_name,
            operation=operation,
            result=result
        ).inc()

        if duration is not None:
            self.cache_operation_duration_seconds.labels(
                cache_name=cache_name,
                operation=operation
            ).observe(duration)

        # Legacy hit/miss counters
        if operation == 'get':
            if result == 'hit':
                self.cache_hits_total.inc()
            elif result == 'miss':
                self.cache_misses_total.inc()

    def update_cache_stats(self, cache_name: str, size: int, memory_usage: int,
                          hit_rate: Optional[float] = None):
        """Update cache statistics."""
        self.cache_size_items.labels(cache_name=cache_name).set(size)
        self.cache_memory_usage_bytes.labels(cache_name=cache_name).set(memory_usage)

        if hit_rate is not None:
            self.cache_hit_rate_percent.labels(cache_name=cache_name).set(hit_rate)

    def record_eviction(self, cache_name: str, reason: str = 'capacity'):
        """Record a cache eviction."""
        self.cache_evictions_total.labels(
            cache_name=cache_name,
            reason=reason
        ).inc()

    def record_backend_operation(self, backend_type: str, operation: str):
        """Record backend operation."""
        self.cache_backend_operations_total.labels(
            backend_type=backend_type,
            operation=operation
        ).inc()

    def record_backend_error(self, backend_type: str, error_type: str):
        """Record backend error."""
        self.cache_backend_errors_total.labels(
            backend_type=backend_type,
            error_type=error_type
        ).inc()
