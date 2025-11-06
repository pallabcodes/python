"""
Dashboard alert management for the analytics pipeline.

This module contains alert-related functionality for the MetricsDashboard class,
separated for better modularity and to keep file sizes under limits.
"""

import time
from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .dashboard_metrics import MetricsDashboard
    from .dashboard_core import Alert


def _setup_default_alerts(self: 'MetricsDashboard') -> None:
    """Set up default alerts for common issues."""
    # Pipeline stopped alert
    self.add_alert(Alert(
        name='pipeline_stopped',
        condition=lambda m: not m.get('pipeline_running', True),
        message='Pipeline has stopped running',
        severity='critical'
    ))

    # High error rate alert
    self.add_alert(Alert(
        name='high_error_rate',
        condition=lambda m: m.get('error_rate', 0) > self.config.alert_thresholds.get('error_rate', 0.1),
        message='Error rate is above threshold',
        severity='warning'
    ))

    # Low throughput alert
    self.add_alert(Alert(
        name='low_throughput',
        condition=lambda m: m.get('messages_per_second', 0) < self.config.alert_thresholds.get('min_throughput', 1.0),
        message='Message throughput is below minimum threshold',
        severity='warning'
    ))

    # Storage full alert
    self.add_alert(Alert(
        name='storage_full',
        condition=lambda m: m.get('storage_usage_percent', 0) > self.config.alert_thresholds.get('storage_threshold', 90.0),
        message='Storage usage is above threshold',
        severity='error'
    ))


def add_alert(self: 'MetricsDashboard', alert: 'Alert') -> None:
    """Add a custom alert.

    Args:
        alert: Alert configuration
    """
    self.alerts.append(alert)


def _check_alerts(self: 'MetricsDashboard', metrics: Dict[str, Any]) -> None:
    """Check all alerts against current metrics.

    Args:
        metrics: Current metrics
    """
    if not self.config.enable_alerts:
        return

    for alert in self.alerts:
        alert_data = alert.check_and_trigger(metrics)
        if alert_data:
            self.active_alerts.append(alert_data)
            self.alert_history.append(alert_data)

            # Keep only recent active alerts (last 100)
            self.active_alerts = self.active_alerts[-100:]

            # Log alert
            print(f"ALERT [{alert_data['severity'].upper()}]: {alert_data['message']}")
