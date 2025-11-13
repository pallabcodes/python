"""Prometheus metrics export for LangChain production patterns."""

import logging
from typing import Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    logger.warning("prometheus_client not installed, using mock metrics")


class PrometheusMetrics:
    """
    Prometheus metrics exporter for production LLM operations.
    
    Exports metrics for:
    - Circuit breaker state and transitions
    - Cache hits/misses (exact and semantic)
    - Rate limiting events
    - Request deduplication
    - Connection pool usage
    - Latency percentiles
    """
    
    def __init__(self, service_name: str = "llm_service"):
        self.service_name = service_name
        
        if HAS_PROMETHEUS:
            self._init_prometheus_metrics()
        else:
            self._init_mock_metrics()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half_open, 2=open)",
            ["circuit_name"]
        )
        self.circuit_breaker_transitions = Counter(
            "circuit_breaker_transitions_total",
            "Total circuit breaker state transitions",
            ["circuit_name", "from_state", "to_state"]
        )
        self.circuit_breaker_failures = Counter(
            "circuit_breaker_failures_total",
            "Total failures counted by circuit breaker",
            ["circuit_name"]
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            "cache_hits_total",
            "Total cache hits",
            ["cache_type", "service"]
        )
        self.cache_misses = Counter(
            "cache_misses_total",
            "Total cache misses",
            ["cache_type", "service"]
        )
        self.semantic_cache_hits = Counter(
            "semantic_cache_hits_total",
            "Total semantic cache hits",
            ["service"]
        )
        
        # Rate limiter metrics
        self.rate_limit_exceeded = Counter(
            "rate_limit_exceeded_total",
            "Total rate limit exceeded events",
            ["service"]
        )
        self.rate_limit_tokens = Gauge(
            "rate_limit_tokens_available",
            "Available tokens in rate limiter",
            ["service"]
        )
        
        # Request deduplication metrics
        self.deduplicated_requests = Counter(
            "deduplicated_requests_total",
            "Total deduplicated requests",
            ["service"]
        )
        
        # Connection pool metrics
        self.connection_pool_size = Gauge(
            "connection_pool_size",
            "Current connection pool size",
            ["pool_name", "state"]
        )
        self.connection_pool_waiters = Gauge(
            "connection_pool_waiters",
            "Number of waiters for connection pool",
            ["pool_name"]
        )
        self.connection_pool_exhausted = Counter(
            "connection_pool_exhausted_total",
            "Total connection pool exhaustion events",
            ["pool_name"]
        )
        
        # Latency metrics
        self.request_latency = Histogram(
            "request_latency_seconds",
            "Request latency in seconds",
            ["service", "status"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.request_latency_summary = Summary(
            "request_latency_summary_seconds",
            "Request latency summary",
            ["service"]
        )
        
        # Request metrics
        self.total_requests = Counter(
            "requests_total",
            "Total requests",
            ["service", "status"]
        )
        self.total_tokens = Counter(
            "tokens_total",
            "Total tokens processed",
            ["service"]
        )
    
    def _init_mock_metrics(self):
        """Initialize mock metrics when Prometheus is not available."""
        self._mock_metrics: Dict[str, Any] = defaultdict(int)
        logger.info("Using mock Prometheus metrics (prometheus_client not installed)")
    
    def record_circuit_breaker_state(self, circuit_name: str, state: str):
        """Record circuit breaker state."""
        if HAS_PROMETHEUS:
            state_value = {"closed": 0, "half_open": 1, "open": 2}.get(state, 0)
            self.circuit_breaker_state.labels(circuit_name=circuit_name).set(state_value)
        else:
            self._mock_metrics[f"circuit_breaker_state_{circuit_name}"] = state
    
    def record_circuit_breaker_transition(
        self,
        circuit_name: str,
        from_state: str,
        to_state: str
    ):
        """Record circuit breaker transition."""
        if HAS_PROMETHEUS:
            self.circuit_breaker_transitions.labels(
                circuit_name=circuit_name,
                from_state=from_state,
                to_state=to_state
            ).inc()
        else:
            key = f"circuit_breaker_transition_{circuit_name}_{from_state}_{to_state}"
            self._mock_metrics[key] += 1
    
    def record_circuit_breaker_failure(self, circuit_name: str):
        """Record circuit breaker failure."""
        if HAS_PROMETHEUS:
            self.circuit_breaker_failures.labels(circuit_name=circuit_name).inc()
        else:
            self._mock_metrics[f"circuit_breaker_failures_{circuit_name}"] += 1
    
    def record_cache_hit(self, cache_type: str = "semantic"):
        """Record cache hit."""
        if HAS_PROMETHEUS:
            self.cache_hits.labels(cache_type=cache_type, service=self.service_name).inc()
        else:
            self._mock_metrics[f"cache_hits_{cache_type}"] += 1
    
    def record_cache_miss(self, cache_type: str = "semantic"):
        """Record cache miss."""
        if HAS_PROMETHEUS:
            self.cache_misses.labels(cache_type=cache_type, service=self.service_name).inc()
        else:
            self._mock_metrics[f"cache_misses_{cache_type}"] += 1
    
    def record_semantic_cache_hit(self):
        """Record semantic cache hit."""
        if HAS_PROMETHEUS:
            self.semantic_cache_hits.labels(service=self.service_name).inc()
        else:
            self._mock_metrics["semantic_cache_hits"] += 1
    
    def record_rate_limit_exceeded(self):
        """Record rate limit exceeded."""
        if HAS_PROMETHEUS:
            self.rate_limit_exceeded.labels(service=self.service_name).inc()
        else:
            self._mock_metrics["rate_limit_exceeded"] += 1
    
    def record_rate_limit_tokens(self, tokens: float):
        """Record available tokens in rate limiter."""
        if HAS_PROMETHEUS:
            self.rate_limit_tokens.labels(service=self.service_name).set(tokens)
        else:
            self._mock_metrics["rate_limit_tokens"] = tokens
    
    def record_deduplicated_request(self):
        """Record deduplicated request."""
        if HAS_PROMETHEUS:
            self.deduplicated_requests.labels(service=self.service_name).inc()
        else:
            self._mock_metrics["deduplicated_requests"] += 1
    
    def record_connection_pool_size(
        self,
        pool_name: str,
        state: str,
        size: int
    ):
        """Record connection pool size."""
        if HAS_PROMETHEUS:
            self.connection_pool_size.labels(
                pool_name=pool_name,
                state=state
            ).set(size)
        else:
            self._mock_metrics[f"connection_pool_size_{pool_name}_{state}"] = size
    
    def record_connection_pool_waiters(self, pool_name: str, count: int):
        """Record connection pool waiters."""
        if HAS_PROMETHEUS:
            self.connection_pool_waiters.labels(pool_name=pool_name).set(count)
        else:
            self._mock_metrics[f"connection_pool_waiters_{pool_name}"] = count
    
    def record_connection_pool_exhausted(self, pool_name: str):
        """Record connection pool exhaustion."""
        if HAS_PROMETHEUS:
            self.connection_pool_exhausted.labels(pool_name=pool_name).inc()
        else:
            self._mock_metrics[f"connection_pool_exhausted_{pool_name}"] += 1
    
    def record_request_latency(self, latency: float, status: str = "success"):
        """Record request latency."""
        if HAS_PROMETHEUS:
            self.request_latency.labels(
                service=self.service_name,
                status=status
            ).observe(latency)
            self.request_latency_summary.labels(service=self.service_name).observe(latency)
        else:
            self._mock_metrics[f"request_latency_{status}"] = latency
    
    def record_request(self, status: str = "success"):
        """Record request."""
        if HAS_PROMETHEUS:
            self.total_requests.labels(service=self.service_name, status=status).inc()
        else:
            self._mock_metrics[f"requests_{status}"] += 1
    
    def record_tokens(self, tokens: int):
        """Record tokens processed."""
        if HAS_PROMETHEUS:
            self.total_tokens.labels(service=self.service_name).inc(tokens)
        else:
            self._mock_metrics["tokens"] += tokens
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary (for mock mode)."""
        if not HAS_PROMETHEUS:
            return dict(self._mock_metrics)
        return {}

