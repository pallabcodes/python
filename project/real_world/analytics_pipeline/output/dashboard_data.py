"""
Dashboard data access for the analytics pipeline.

This module contains data retrieval functionality for the MetricsDashboard class,
separated for better modularity and to keep file sizes under limits.
"""

import time
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .dashboard_metrics import MetricsDashboard
    from .dashboard_core import MetricSnapshot


def get_current_metrics(self: 'MetricsDashboard') -> Optional[Dict[str, Any]]:
    """Get current metrics snapshot.

    Returns:
        Current metrics dictionary or None
    """
    if not self.metrics_history:
        return None

    return self.metrics_history[-1].metrics.copy()


def get_metrics_history(self: 'MetricsDashboard', hours: int = 1) -> List[Dict[str, Any]]:
    """Get metrics history for specified time period.

    Args:
        hours: Number of hours of history to return

    Returns:
        List of metric snapshots
    """
    cutoff_time = time.time() - (hours * 3600)

    return [
        snapshot.to_dict() for snapshot in self.metrics_history
        if snapshot.timestamp >= cutoff_time
    ]


def get_active_alerts(self: 'MetricsDashboard') -> List[Dict[str, Any]]:
    """Get currently active alerts.

    Returns:
        List of active alert dictionaries
    """
    return self.active_alerts.copy()


def get_alert_history(self: 'MetricsDashboard', limit: int = 50) -> List[Dict[str, Any]]:
    """Get alert history.

    Args:
        limit: Maximum number of alerts to return

    Returns:
        List of recent alerts
    """
    return list(self.alert_history)[-limit:]


def get_dashboard_data(self: 'MetricsDashboard') -> Dict[str, Any]:
    """Get complete dashboard data.

    Returns:
        Dictionary containing all dashboard data
    """
    return {
        'config': {
            'title': self.config.title,
            'refresh_interval': self.config.refresh_interval
        },
        'current_metrics': self.get_current_metrics(),
        'metrics_history': self.get_metrics_history(hours=1),
        'active_alerts': self.get_active_alerts(),
        'alert_history': self.get_alert_history(limit=20),
        'custom_widgets': self.config.custom_widgets,
        'last_update': self.last_update
    }
