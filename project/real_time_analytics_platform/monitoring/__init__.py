"""
Monitoring and Alerting layer with Actor Model.

Provides:
- Actor-based monitoring system
- Fault-tolerant alerting
- Dashboard API for live metrics
"""

from .actor_system import ActorSystem
from .dashboard_api import DashboardAPI

__all__ = [
    "ActorSystem",
    "DashboardAPI"
]
