"""
LLM-specific metrics collection for monitoring AI operations.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class LLMMetricsCollector:
    """Collects metrics specific to LLM operations."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        # LLM request metrics
        self.llm_requests_total = Counter(
            'noleet_llm_requests_total',
            'Total LLM requests',
            ['provider', 'model', 'operation'],
            registry=registry
        )

        self.llm_request_duration_seconds = Histogram(
            'noleet_llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['provider', 'model', 'operation'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0],
            registry=registry
        )

        self.llm_errors_total = Counter(
            'noleet_llm_errors_total',
            'Total LLM errors',
            ['provider', 'model', 'error_type'],
            registry=registry
        )

        # Token usage metrics
        self.llm_tokens_used_total = Counter(
            'noleet_llm_tokens_used_total',
            'Total tokens used by LLM operations',
            ['provider', 'model', 'token_type'],
            registry=registry
        )

        # Cost tracking
        self.llm_cost_usd_total = Counter(
            'noleet_llm_cost_usd_total',
            'Total LLM costs in USD',
            ['provider', 'model'],
            registry=registry
        )

        # Cache metrics for LLM operations
        self.llm_cache_hits_total = Counter(
            'noleet_llm_cache_hits_total',
            'Total LLM cache hits',
            ['provider', 'model'],
            registry=registry
        )

        self.llm_cache_misses_total = Counter(
            'noleet_llm_cache_misses_total',
            'Total LLM cache misses',
            ['provider', 'model'],
            registry=registry
        )

        # Active requests gauge
        self.llm_active_requests = Gauge(
            'noleet_llm_active_requests',
            'Number of active LLM requests',
            ['provider', 'model'],
            registry=registry
        )

        # Model availability
        self.llm_provider_available = Gauge(
            'noleet_llm_provider_available',
            'LLM provider availability status',
            ['provider'],
            registry=registry
        )

    def record_request_start(self, provider: str, model: str, operation: str = 'generate'):
        """Record the start of an LLM request."""
        self.llm_active_requests.labels(provider=provider, model=model).inc()
        self.llm_requests_total.labels(provider=provider, model=model, operation=operation).inc()

    def record_request_complete(self, provider: str, model: str, duration: float,
                              tokens_used: Optional[int] = None,
                              prompt_tokens: Optional[int] = None,
                              completion_tokens: Optional[int] = None,
                              cost_usd: Optional[float] = None):
        """Record the completion of an LLM request."""
        self.llm_active_requests.labels(provider=provider, model=model).dec()
        self.llm_request_duration_seconds.labels(
            provider=provider, model=model, operation='generate'
        ).observe(duration)

        # Record token usage
        if tokens_used is not None:
            self.llm_tokens_used_total.labels(
                provider=provider, model=model, token_type='total'
            ).inc(tokens_used)

        if prompt_tokens is not None:
            self.llm_tokens_used_total.labels(
                provider=provider, model=model, token_type='prompt'
            ).inc(prompt_tokens)

        if completion_tokens is not None:
            self.llm_tokens_used_total.labels(
                provider=provider, model=model, token_type='completion'
            ).inc(completion_tokens)

        # Record cost
        if cost_usd is not None:
            self.llm_cost_usd_total.labels(provider=provider, model=model).inc(cost_usd)

    def record_error(self, provider: str, model: str, error_type: str):
        """Record an LLM error."""
        self.llm_errors_total.labels(
            provider=provider, model=model, error_type=error_type
        ).inc()
        self.llm_active_requests.labels(provider=provider, model=model).dec()

    def record_cache_hit(self, provider: str, model: str):
        """Record LLM cache hit."""
        self.llm_cache_hits_total.labels(provider=provider, model=model).inc()

    def record_cache_miss(self, provider: str, model: str):
        """Record LLM cache miss."""
        self.llm_cache_misses_total.labels(provider=provider, model=model).inc()

    def set_provider_availability(self, provider: str, available: bool):
        """Set provider availability status."""
        self.llm_provider_available.labels(provider=provider).set(1 if available else 0)
