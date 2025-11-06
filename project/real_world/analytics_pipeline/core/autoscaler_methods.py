"""
AdaptiveAutoscaler method implementations.

This module contains the method implementations for the AdaptiveAutoscaler class
to keep the main class file focused and under the 200-line limit.
"""

from typing import Optional

from .orchestrator_core import PipelineStats
from .autoscaler_core import AdaptiveAutoscaler, ScalingDecision, AutoscalerStats


def evaluate_scaling(self: AdaptiveAutoscaler, pipeline_stats: PipelineStats) -> Optional[ScalingDecision]:
    """Evaluate whether scaling is needed based on current metrics.

    Args:
        pipeline_stats: Current pipeline statistics

    Returns:
        Scaling decision or None if no action needed
    """
    current_time = time.time()

    # Update statistics
    with self._stats_lock:
        self._stats.evaluations_performed += 1
        self._stats.last_evaluation_time = current_time

    # Check cooldown period
    if current_time - self._last_scaling_time < self.config.cooldown_period:
        return None

    # Extract relevant metrics
    metrics = self._extract_metrics(pipeline_stats)

    # Make scaling decision based on strategy
    if self.config.strategy == ScalingStrategy.QUEUE_DEPTH:
        decision = self._evaluate_queue_depth(metrics)
    elif self.config.strategy == ScalingStrategy.PROCESSING_LATENCY:
        decision = self._evaluate_latency(metrics)
    elif self.config.strategy == ScalingStrategy.THROUGHPUT:
        decision = self._evaluate_throughput(metrics)
    elif self.config.strategy == ScalingStrategy.COMPOSITE:
        decision = self._evaluate_composite(metrics)
    else:
        return None

    if decision and decision.should_scale:
        # Update statistics
        with self._stats_lock:
            self._stats.scaling_decisions += 1
            if decision.action == 'scale_up':
                self._stats.scale_up_events += 1
            elif decision.action == 'scale_down':
                self._stats.scale_down_events += 1

            self._stats.last_scaling_time = current_time
            self._last_scaling_time = current_time
            self._current_workers = decision.target_workers

        self._logger.info(
            f"Scaling decision: {decision.action} to {decision.target_workers} workers "
            f"(reason: {decision.reason})"
        )

    return decision


def get_stats(self: AdaptiveAutoscaler) -> AutoscalerStats:
    """Get autoscaler statistics."""
    with self._stats_lock:
        return AutoscalerStats(
            evaluations_performed=self._stats.evaluations_performed,
            scaling_decisions=self._stats.scaling_decisions,
            scale_up_events=self._stats.scale_up_events,
            scale_down_events=self._stats.scale_down_events,
            last_evaluation_time=self._stats.last_evaluation_time,
            last_scaling_time=self._stats.last_scaling_time
        )


def force_scale_to(self: AdaptiveAutoscaler, target_workers: int) -> bool:
    """Force scaling to specific number of workers.

    Args:
        target_workers: Target number of workers

    Returns:
        True if scaling was performed, False otherwise
    """
    target_workers = max(self.config.min_workers, min(self.config.max_workers, target_workers))

    if target_workers == self._current_workers:
        return False

    action = 'scale_up' if target_workers > self._current_workers else 'scale_down'

    self._current_workers = target_workers
    self._last_scaling_time = time.time()

    with self._stats_lock:
        self._stats.scaling_decisions += 1
        if action == 'scale_up':
            self._stats.scale_up_events += 1
        else:
            self._stats.scale_down_events += 1
        self._stats.last_scaling_time = self._last_scaling_time

    self._logger.info(f"Force scaled to {target_workers} workers")
    return True
