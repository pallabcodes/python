"""
Core adaptive autoscaling functionality.

This module contains the main AdaptiveAutoscaler class and core
scaling logic for dynamic resource management.
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .orchestrator_core import PipelineStats


class ScalingStrategy(Enum):
    """Autoscaling strategies."""
    QUEUE_DEPTH = "queue_depth"
    PROCESSING_LATENCY = "processing_latency"
    THROUGHPUT = "throughput"
    COMPOSITE = "composite"


@dataclass
class ScalingConfig:
    """Configuration for autoscaling."""
    strategy: ScalingStrategy = ScalingStrategy.COMPOSITE
    min_workers: int = 2
    max_workers: int = 20
    scale_up_threshold: float = 0.8  # 80% utilization
    scale_down_threshold: float = 0.3  # 30% utilization
    cooldown_period: float = 300.0  # 5 minutes between scaling
    evaluation_interval: float = 60.0  # Evaluate every minute
    scale_factor: float = 1.5  # Scale by 1.5x

    def __post_init__(self):
        """Validate configuration."""
        if self.min_workers < 1:
            raise ValueError("min_workers must be at least 1")
        if self.max_workers < self.min_workers:
            raise ValueError("max_workers must be >= min_workers")
        if not (0 < self.scale_up_threshold <= 1):
            raise ValueError("scale_up_threshold must be between 0 and 1")
        if not (0 <= self.scale_down_threshold < self.scale_up_threshold):
            raise ValueError("scale_down_threshold must be < scale_up_threshold")


@dataclass
class ScalingDecision:
    """Decision made by autoscaler."""
    action: str  # 'scale_up', 'scale_down', 'no_action'
    target_workers: int
    reason: str
    metrics: Dict[str, Any]
    timestamp: float

    @property
    def should_scale(self) -> bool:
        """Check if scaling action is needed."""
        return self.action in ['scale_up', 'scale_down']


@dataclass
class AutoscalerStats:
    """Statistics for autoscaler performance."""
    evaluations_performed: int = 0
    scaling_decisions: int = 0
    scale_up_events: int = 0
    scale_down_events: int = 0
    last_evaluation_time: Optional[float] = None
    last_scaling_time: Optional[float] = None


class AdaptiveAutoscaler:
    """Adaptive autoscaler for pipeline resources.

    This class monitors pipeline performance metrics and makes intelligent
    decisions about resource allocation to maintain optimal throughput
    and latency while minimizing resource waste.
    """

    def __init__(
        self,
        config: Optional[ScalingConfig] = None,
        target_component: str = "processing_stages"
    ):
        """Initialize adaptive autoscaler.

        Args:
            config: Autoscaling configuration
            target_component: Component to scale (e.g., 'processing_stages')
        """
        self.config = config or ScalingConfig()
        self.target_component = target_component

        # Current state
        self._current_workers = self.config.min_workers
        self._last_scaling_time = 0.0

        # Statistics
        self._stats = AutoscalerStats()
        self._stats_lock = threading.Lock()

        # Logging
        self._logger = logging.getLogger(f"{__name__}.{target_component}")

        self._logger.info(
            f"Initialized autoscaler for '{target_component}' with "
            f"{self.config.min_workers}-{self.config.max_workers} workers"
        )

    @property
    def current_workers(self) -> int:
        """Get current number of workers."""
        return self._current_workers

    def evaluate_scaling(self, pipeline_stats: PipelineStats) -> Optional[ScalingDecision]:
        """Evaluate whether scaling is needed based on current metrics."""
        pass

# Import autoscaler methods
from .autoscaler_methods import (
    evaluate_scaling, get_stats, force_scale_to
)
