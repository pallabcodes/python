"""
Core pipeline components for the analytics pipeline.

This module contains the foundational components that enable the analytics
pipeline to operate with production-grade reliability and performance.
"""

from .orchestrator_core import PipelineOrchestrator
from .router_core import MessageRouter
from .autoscaler_core import AdaptiveAutoscaler
from .circuit_breaker_core import CircuitBreaker

__all__ = [
    'PipelineOrchestrator',
    'MessageRouter',
    'AdaptiveAutoscaler',
    'CircuitBreaker'
]
