"""
Metrics collector for platform monitoring.

Provides Prometheus-compatible metrics collection and export
for all platform components and operations.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

from ..core.config import PlatformConfig


class MetricsCollector:
    """
    Prometheus-compatible metrics collector.

    Features:
    - Counter, Gauge, and Histogram metrics
    - Platform health metrics
    - Performance monitoring
    - Custom business metrics
    - Prometheus export format
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize metrics collector.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.MetricsCollector")

        # Metrics storage
        self._metrics: Dict[str, Dict[str, Any]] = {}

        # Collection settings
        self._collection_interval = self.config.monitoring.metrics_interval
        self._collection_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize metrics collector."""
        self.logger.info("Initializing metrics collector...")

        # Initialize core metrics
        await self._init_core_metrics()

        # Start collection task
        self._collection_task = asyncio.create_task(self._collect_metrics())

        self.logger.info(f"Metrics collector initialized with {self._collection_interval}s interval")

    async def _init_core_metrics(self) -> None:
        """Initialize core platform metrics."""
        # Platform health metrics
        self._create_gauge("platform_uptime_seconds", "Platform uptime in seconds")
        self._create_gauge("platform_components_total", "Total number of platform components")
        self._create_gauge("platform_components_active", "Number of active platform components")

        # MLOps metrics
        self._create_counter("mlops_experiments_total", "Total number of experiments created")
        self._create_counter("mlops_models_registered_total", "Total number of models registered")
        self._create_counter("mlops_inference_requests_total", "Total number of inference requests")

        # Gen AI metrics
        self._create_counter("genai_llm_requests_total", "Total number of LLM requests")
        self._create_counter("genai_tokens_generated_total", "Total number of tokens generated")
        self._create_gauge("genai_active_agents", "Number of active AI agents")

        # Performance metrics
        self._create_histogram("api_request_duration_seconds", "API request duration", buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
        self._create_histogram("model_inference_duration_seconds", "Model inference duration", buckets=[0.01, 0.1, 0.5, 1.0, 2.0])

        # Error metrics
        self._create_counter("errors_total", "Total number of errors", labels=["type", "component"])

    def _create_counter(self, name: str, description: str, labels: Optional[list] = None) -> None:
        """Create a counter metric."""
        self._metrics[name] = {
            "type": "counter",
            "description": description,
            "value": 0,
            "labels": labels or []
        }

    def _create_gauge(self, name: str, description: str, labels: Optional[list] = None) -> None:
        """Create a gauge metric."""
        self._metrics[name] = {
            "type": "gauge",
            "description": description,
            "value": 0.0,
            "labels": labels or []
        }

    def _create_histogram(self, name: str, description: str, buckets: Optional[list] = None, labels: Optional[list] = None) -> None:
        """Create a histogram metric."""
        self._metrics[name] = {
            "type": "histogram",
            "description": description,
            "buckets": buckets or [],
            "counts": [0] * len(buckets or []),
            "sum": 0.0,
            "labels": labels or []
        }

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        if name in self._metrics and self._metrics[name]["type"] == "counter":
            self._metrics[name]["value"] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        if name in self._metrics and self._metrics[name]["type"] == "gauge":
            self._metrics[name]["value"] = value

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value in a histogram metric."""
        if name in self._metrics and self._metrics[name]["type"] == "histogram":
            hist = self._metrics[name]
            hist["sum"] += value

            # Update bucket counts
            for i, bucket in enumerate(hist["buckets"]):
                if value <= bucket:
                    hist["counts"][i] += 1

    async def _collect_metrics(self) -> None:
        """Background metrics collection task."""
        while True:
            try:
                await self._collect_platform_metrics()
                await asyncio.sleep(self._collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self._collection_interval)

    async def _collect_platform_metrics(self) -> None:
        """Collect platform-specific metrics."""
        try:
            # This would integrate with the platform to collect real metrics
            # For now, update some demo metrics

            # Simulate platform uptime (would come from platform)
            import random
            uptime = random.randint(100, 1000)
            self.set_gauge("platform_uptime_seconds", uptime)

            # Simulate component counts
            self.set_gauge("platform_components_total", 9)
            self.set_gauge("platform_components_active", random.randint(7, 9))

            # Simulate request metrics
            if random.random() > 0.7:  # 30% chance
                self.observe_histogram("api_request_duration_seconds", random.uniform(0.1, 2.0))

        except Exception as e:
            self.logger.error(f"Platform metrics collection failed: {e}")

    def get_metrics_prometheus(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        for name, metric in self._metrics.items():
            # Help comment
            lines.append(f"# HELP {name} {metric['description']}")
            lines.append(f"# TYPE {name} {metric['type']}")

            if metric["type"] == "histogram":
                # Histogram format
                for i, bucket in enumerate(metric["buckets"]):
                    lines.append(f'{name}_bucket{{le="{bucket}"}} {metric["counts"][i]}')
                lines.append(f'{name}_count {sum(metric["counts"])}')
                lines.append(f'{name}_sum {metric["sum"]}')

            elif metric["type"] in ["counter", "gauge"]:
                lines.append(f"{name} {metric['value']}")

            lines.append("")  # Empty line between metrics

        return "\n".join(lines)

    def get_metrics_json(self) -> Dict[str, Any]:
        """
        Get metrics as JSON.

        Returns:
            Metrics dictionary
        """
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        for name, metric in self._metrics.items():
            if metric["type"] == "counter":
                metric["value"] = 0
            elif metric["type"] == "gauge":
                metric["value"] = 0.0
            elif metric["type"] == "histogram":
                metric["counts"] = [0] * len(metric["buckets"])
                metric["sum"] = 0.0

        self.logger.info("Metrics reset")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "healthy": True,
            "metrics_collected": len(self._metrics),
            "collection_interval": self._collection_interval,
            "collection_task_running": not self._collection_task.done() if self._collection_task else False
        }

    async def shutdown(self) -> None:
        """Shutdown metrics collector."""
        self.logger.info("Shutting down metrics collector...")

        # Cancel collection task
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Metrics collector shutdown complete")
