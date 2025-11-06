"""
Metrics dashboard for the analytics pipeline.

This module contains the MetricsDashboard class which handles metric collection,
alerting, and dashboard data management.
"""

import time
from typing import Dict, Any, Optional, List
from collections import deque

from .dashboard_core import DashboardConfig, MetricSnapshot, Alert

# Import alert and data methods
from .dashboard_alerts import _setup_default_alerts, add_alert, _check_alerts
from .dashboard_data import (
    get_current_metrics, get_metrics_history, get_active_alerts,
    get_alert_history, get_dashboard_data
)


class MetricsDashboard:
    """Dashboard for displaying real-time pipeline metrics."""

    def __init__(self, orchestrator, config: Optional[DashboardConfig] = None):
        """Initialize metrics dashboard.

        Args:
            orchestrator: Pipeline orchestrator instance
            config: Dashboard configuration
        """
        self.orchestrator = orchestrator
        self.config = config or DashboardConfig()

        # Metrics history
        self.metrics_history: deque = deque(maxlen=self.config.max_metrics_history)

        # Alerts
        self.alerts: List[Alert] = []
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_history: deque = deque(maxlen=1000)

        # Initialize default alerts
        self._setup_default_alerts()

        # Dashboard state
        self.last_update = 0.0
        self.is_running = False

    def start(self) -> None:
        """Start the dashboard."""
        self.is_running = True
        self._update_metrics()

    def stop(self) -> None:
        """Stop the dashboard."""
        self.is_running = False

    def update(self) -> None:
        """Update dashboard metrics and check alerts."""
        if not self.is_running:
            return

        current_time = time.time()
        if current_time - self.last_update >= self.config.refresh_interval:
            self._update_metrics()
            self.last_update = current_time

    def _update_metrics(self) -> None:
        """Update metrics from orchestrator."""
        try:
            # Get current metrics
            pipeline_status = self.orchestrator.get_status()
            stage_metrics = self.orchestrator.get_all_stage_metrics()
            storage_metrics = self.orchestrator.get_all_storage_metrics()

            # Aggregate metrics
            metrics = {
                'timestamp': time.time(),
                'pipeline_running': pipeline_status == 'running',
                'pipeline_status': pipeline_status,
                'uptime': self.orchestrator.get_uptime(),
                'total_messages_processed': self.orchestrator.get_total_messages_processed(),
                'error_count': self.orchestrator.get_error_count(),
                'active_stages': len(self.orchestrator.get_active_stages()),
                'stage_metrics': stage_metrics,
                'storage_metrics': storage_metrics
            }

            # Calculate derived metrics
            metrics.update(self._calculate_derived_metrics(metrics))

            # Store in history
            snapshot = MetricSnapshot(time.time(), metrics)
            self.metrics_history.append(snapshot)

            # Check alerts
            self._check_alerts(metrics)

        except Exception as e:
            print(f"Error updating dashboard metrics: {e}")

    def _calculate_derived_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics from raw metrics.

        Args:
            metrics: Raw metrics dictionary

        Returns:
            Dictionary of derived metrics
        """
        derived = {}

        # Message throughput
        if len(self.metrics_history) >= 2:
            prev_snapshot = self.metrics_history[-2]
            time_diff = metrics['timestamp'] - prev_snapshot.timestamp
            msg_diff = (metrics['total_messages_processed'] -
                       prev_snapshot.metrics['total_messages_processed'])

            if time_diff > 0:
                derived['messages_per_second'] = msg_diff / time_diff

        # Error rate
        total_msgs = metrics.get('total_messages_processed', 0)
        errors = metrics.get('error_count', 0)
        if total_msgs > 0:
            derived['error_rate'] = errors / total_msgs

        # Stage health
        stage_metrics = metrics.get('stage_metrics', {})
        healthy_stages = sum(1 for stage_data in stage_metrics.values()
                           if stage_data.get('healthy', True))
        derived['healthy_stages'] = healthy_stages
        derived['total_stages'] = len(stage_metrics)

        # Storage usage (simplified)
        storage_metrics = metrics.get('storage_metrics', {})
        total_connections = sum(storage.get('active_connections', 0)
                              for storage in storage_metrics.values())
        derived['total_storage_connections'] = total_connections

        return derived
