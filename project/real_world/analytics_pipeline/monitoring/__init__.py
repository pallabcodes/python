"""
Monitoring and observability for the analytics pipeline.

This module provides comprehensive monitoring capabilities:
- Metrics: 50+ metrics collection (throughput, latency, errors)
- Health: Health checks for all components
- Alerting: Alert rules and notification management
- Dashboard: Real-time metrics visualization
"""

from .metrics import MetricsCollector
from .health import HealthChecker
from .alerting import AlertManager
from .dashboard import MetricsDashboard

__all__ = [
    'MetricsCollector',
    'HealthChecker',
    'AlertManager',
    'MetricsDashboard'
]
