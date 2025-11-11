"""
Monitoring and Alerting layer with Actor Model.

Provides:
- Actor-based monitoring system
- Fault-tolerant alerting
"""

from .actor_system import ActorSystem

__all__ = [
    "ActorSystem"
]
