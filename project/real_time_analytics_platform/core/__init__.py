"""
Core components for the Real-Time Analytics Platform.

This module provides the foundational components that integrate
all our concurrency patterns into a cohesive analytics platform.
"""

from .platform import AnalyticsPlatform
from .config import PlatformConfig
from .event_system import EventSystem

__all__ = [
    "AnalyticsPlatform",
    "PlatformConfig",
    "EventSystem"
]


