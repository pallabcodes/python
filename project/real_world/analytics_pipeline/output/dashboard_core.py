"""
Dashboard core classes for the analytics pipeline.

This module contains the core dataclasses and base structures for the
dashboard functionality, separated for better modularity.
"""

import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field


@dataclass
class DashboardConfig:
    """Configuration for dashboard interface."""

    title: str = "Analytics Pipeline Dashboard"
    refresh_interval: int = 30  # seconds
    max_metrics_history: int = 1000
    enable_alerts: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    custom_widgets: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""

    timestamp: float
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'metrics': self.metrics
        }


@dataclass
class Alert:
    """Alert configuration and state."""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    message: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    enabled: bool = True
    last_triggered: Optional[float] = None
    trigger_count: int = 0

    def check_and_trigger(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check condition and return alert if triggered.

        Args:
            metrics: Current metrics

        Returns:
            Alert data if triggered, None otherwise
        """
        if not self.enabled:
            return None

        try:
            if self.condition(metrics):
                self.last_triggered = time.time()
                self.trigger_count += 1

                return {
                    'name': self.name,
                    'message': self.message,
                    'severity': self.severity,
                    'timestamp': self.last_triggered,
                    'trigger_count': self.trigger_count,
                    'metrics': metrics
                }
        except Exception as e:
            # Log error but don't crash
            print(f"Error checking alert '{self.name}': {e}")

        return None