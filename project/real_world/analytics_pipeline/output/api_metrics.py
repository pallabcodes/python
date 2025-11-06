"""
Metrics API endpoints for the analytics pipeline.

This module contains the MetricsAPI class which provides REST API endpoints
for accessing pipeline metrics, monitoring data, and system health information.
"""

from typing import Optional
from datetime import datetime

from .api_core import APIResponse


class MetricsAPI:
    """API endpoints for pipeline metrics and monitoring."""

    def __init__(self, pipeline_orchestrator):
        """Initialize metrics API.

        Args:
            pipeline_orchestrator: Pipeline orchestrator instance
        """
        self.orchestrator = pipeline_orchestrator

    def get_pipeline_status(self) -> APIResponse:
        """Get overall pipeline status.

        Returns:
            API response with pipeline status
        """
        try:
            status = {
                'state': self.orchestrator.get_status(),
                'uptime': self.orchestrator.get_uptime(),
                'active_stages': len(self.orchestrator.get_active_stages()),
                'total_messages_processed': self.orchestrator.get_total_messages_processed(),
                'error_count': self.orchestrator.get_error_count(),
                'last_activity': self.orchestrator.get_last_activity_time()
            }

            return APIResponse(True, status, "Pipeline status retrieved successfully")

        except Exception as e:
            return APIResponse(False, None, "Failed to get pipeline status", str(e))

    def get_stage_metrics(self, stage_name: Optional[str] = None) -> APIResponse:
        """Get metrics for pipeline stages.

        Args:
            stage_name: Optional specific stage name

        Returns:
            API response with stage metrics
        """
        try:
            if stage_name:
                metrics = self.orchestrator.get_stage_metrics(stage_name)
                if not metrics:
                    return APIResponse(False, None, f"Stage '{stage_name}' not found")
            else:
                metrics = self.orchestrator.get_all_stage_metrics()

            return APIResponse(True, metrics, "Stage metrics retrieved successfully")

        except Exception as e:
            return APIResponse(False, None, "Failed to get stage metrics", str(e))

    def get_storage_metrics(self, backend_name: Optional[str] = None) -> APIResponse:
        """Get storage backend metrics.

        Args:
            backend_name: Optional specific backend name

        Returns:
            API response with storage metrics
        """
        try:
            if backend_name:
                metrics = self.orchestrator.get_storage_metrics(backend_name)
                if not metrics:
                    return APIResponse(False, None, f"Storage backend '{backend_name}' not found")
            else:
                metrics = self.orchestrator.get_all_storage_metrics()

            return APIResponse(True, metrics, "Storage metrics retrieved successfully")

        except Exception as e:
            return APIResponse(False, None, "Failed to get storage metrics", str(e))

    def get_system_health(self) -> APIResponse:
        """Get system health status.

        Returns:
            API response with health status
        """
        try:
            health = {
                'overall_status': 'healthy',  # TODO: Implement health checks
                'checks': {
                    'pipeline_running': self.orchestrator.is_running(),
                    'stages_healthy': True,  # TODO: Implement stage health checks
                    'storage_healthy': True,  # TODO: Implement storage health checks
                    'memory_usage': 'normal',  # TODO: Implement memory monitoring
                    'cpu_usage': 'normal'  # TODO: Implement CPU monitoring
                },
                'timestamp': datetime.now().isoformat()
            }

            return APIResponse(True, health, "System health retrieved successfully")

        except Exception as e:
            return APIResponse(False, None, "Failed to get system health", str(e))
