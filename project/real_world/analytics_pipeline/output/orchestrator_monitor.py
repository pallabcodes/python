"""
Pipeline monitoring components for the analytics pipeline.

This module contains the PipelineMonitor class which handles
monitoring, metrics collection, and status reporting for the analytics pipeline.
"""

import time
from typing import Dict, Any, Optional, List

from .orchestrator_init import PipelineInitializer


class PipelineMonitor:
    """Handles monitoring and metrics collection for the pipeline."""

    def __init__(self, initializer: PipelineInitializer):
        """Initialize the pipeline monitor.

        Args:
            initializer: Pipeline initializer with component references
        """
        self.initializer = initializer
        self.start_time: Optional[float] = None
        self.total_messages_processed = 0
        self.error_count = 0

    def start_monitoring(self) -> None:
        """Start monitoring."""
        self.start_time = time.time()

    def update_metrics(self, messages_processed: int = 0, errors: int = 0) -> None:
        """Update pipeline metrics.

        Args:
            messages_processed: Number of messages processed since last update
            errors: Number of errors since last update
        """
        self.total_messages_processed += messages_processed
        self.error_count += errors

        # Update dashboard if available
        if self.initializer.dashboard:
            self.initializer.dashboard.update()

    def get_status(self) -> str:
        """Get current pipeline status.

        Returns:
            Status string
        """
        if not hasattr(self.initializer, 'running') or not self.initializer.running:
            return 'stopped'

        # Check if orchestrator is active
        if self.initializer.core_orchestrator.get_status() == 'running':
            return 'running'

        return 'error'

    def get_uptime(self) -> float:
        """Get pipeline uptime in seconds.

        Returns:
            Uptime in seconds
        """
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_total_messages_processed(self) -> int:
        """Get total messages processed.

        Returns:
            Total message count
        """
        return self.total_messages_processed

    def get_error_count(self) -> int:
        """Get total error count.

        Returns:
            Total error count
        """
        return self.error_count

    def get_active_stages(self) -> List[str]:
        """Get list of active stage names.

        Returns:
            List of active stage names
        """
        return list(self.initializer.processing_stages.keys())

    def get_last_activity_time(self) -> Optional[float]:
        """Get timestamp of last activity.

        Returns:
            Last activity timestamp
        """
        return self.initializer.core_orchestrator.get_stats().get('last_activity')

    def get_stage_metrics(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Stage metrics dictionary or None
        """
        if stage_name in self.initializer.processing_stages:
            return self.initializer.processing_stages[stage_name].get_stats()
        return None

    def get_all_stage_metrics(self) -> Dict[str, Any]:
        """Get metrics for all stages.

        Returns:
            Dictionary of stage metrics
        """
        return {
            name: stage.get_stats()
            for name, stage in self.initializer.processing_stages.items()
        }

    def get_storage_metrics(self, backend_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific storage backend.

        Args:
            backend_name: Name of the storage backend

        Returns:
            Storage metrics dictionary or None
        """
        if backend_name in self.initializer.storage_backends:
            backend = self.initializer.storage_backends[backend_name]
            return backend.get_metrics()
        return None

    def get_all_storage_metrics(self) -> Dict[str, Any]:
        """Get metrics for all storage backends.

        Returns:
            Dictionary of storage metrics
        """
        return {
            name: backend.get_metrics()
            for name, backend in self.initializer.storage_backends.items()
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data.

        Returns:
            Dashboard data dictionary
        """
        if not self.initializer.dashboard:
            return {}

        return self.initializer.dashboard.get_dashboard_data()
