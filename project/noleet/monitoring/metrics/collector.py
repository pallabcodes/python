"""
Metrics collector for NoLeet application.
Defines and collects Prometheus metrics for all application components.
"""

import time
import psutil
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest
)

from .llm_metrics import LLMMetricsCollector
from .cache_metrics import CacheMetricsCollector
from .agent_metrics import AgentMetricsCollector
from .business_metrics import BusinessMetricsCollector


class MetricsCollector:
    """Main metrics collector for NoLeet application."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()

        # HTTP request metrics
        self.http_requests_total = Counter(
            'noleet_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'noleet_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'status'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0],
            registry=self.registry
        )

        # Application health metrics
        self.up = Gauge(
            'noleet_up',
            'Application health status',
            registry=self.registry
        )

        self.start_time = Gauge(
            'noleet_start_time_seconds',
            'Application start time',
            registry=self.registry
        )

        # Performance regression detection
        self.performance_regression_detected_total = Counter(
            'noleet_performance_regression_detected_total',
            'Total performance regressions detected',
            ['component', 'metric'],
            registry=self.registry
        )

        # System resource metrics
        self.system_cpu_usage_percent = Gauge(
            'noleet_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_usage_bytes = Gauge(
            'noleet_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )

        self.system_disk_usage_percent = Gauge(
            'noleet_system_disk_usage_percent',
            'System disk usage percentage',
            registry=self.registry
        )

        # Initialize specialized collectors
        self.llm_metrics = LLMMetricsCollector(self.registry)
        self.cache_metrics = CacheMetricsCollector(self.registry)
        self.agent_metrics = AgentMetricsCollector(self.registry)
        self.business_metrics = BusinessMetricsCollector(self.registry)

        # Set initial values
        self.up.set(1)
        self.start_time.set(time.time())

    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).observe(duration)

    def record_performance_regression(self, component: str, metric: str):
        """Record performance regression detection."""
        self.performance_regression_detected_total.labels(
            component=component,
            metric=metric
        ).inc()

    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage_percent.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage_bytes.set(memory.used)

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage_percent.set(disk_percent)

        except Exception as e:
            # Log error but don't crash
            print(f"Failed to update system metrics: {e}")

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        self.update_system_metrics()
        return generate_latest(self.registry).decode('utf-8')

    def reset(self):
        """Reset all metrics (useful for testing)."""
        # Note: Prometheus counters can't be reset, but we can clear the registry
        # and recreate collectors for testing purposes
        pass


# Global metrics collector instance
metrics_collector = MetricsCollector()


class MetricsTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str, **labels):
        self.operation_name = operation_name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            # Record the duration (this would be customized based on operation type)
            print(f"Operation {self.operation_name} took {duration:.3f}s")


# Convenience functions for common metrics recording
def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics."""
    metrics_collector.record_http_request(method, endpoint, status, duration)


def record_performance_regression(component: str, metric: str):
    """Record performance regression."""
    metrics_collector.record_performance_regression(component, metric)


def get_metrics_output() -> str:
    """Get current metrics in Prometheus format."""
    return metrics_collector.get_metrics()
