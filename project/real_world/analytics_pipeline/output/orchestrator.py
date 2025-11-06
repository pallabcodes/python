"""
Pipeline orchestrator for the analytics pipeline.

This module provides the main pipeline orchestrator that coordinates data sources,
processing stages, storage backends, and output components.
"""

import time
import threading
import signal
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.orchestrator_core import PipelineOrchestrator as CoreOrchestrator
from ..sources.source_factory import create_demo_sources
from ..processing.stage_base import BaseProcessingStage
from ..storage.backend_factory import StorageBackendFactory
from .export_parquet import ExportManager
from .dashboard import MetricsDashboard, DashboardConfig
from .orchestrator_core import PipelineConfig
from .orchestrator_control import PipelineOrchestrator
from .orchestrator_init import PipelineInitializer
from .orchestrator_monitor import PipelineMonitor
from .orchestrator_control import (
    _run_main_loop, _monitoring_loop, _update_metrics, _signal_handler
)



class PipelineRunner:
    """Main pipeline runner that coordinates all components."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline runner.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.initializer = PipelineInitializer(config)
        self.monitor = PipelineMonitor(self.initializer)

        # Control
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.shutdown_event = threading.Event()


        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self) -> None:
        """Initialize all pipeline components."""
        self.initializer.initialize_components()

    def start(self) -> None:
        """Start the pipeline."""
        if self.running:
            print("Pipeline is already running")
            return

        try:
            self.initialize()
            self.running = True
            self.monitor.start_monitoring()

            # Start core orchestrator
            self.initializer.core_orchestrator.start()

            # Start dashboard if enabled
            if self.initializer.dashboard:
                self.initializer.dashboard.start()

            # Start monitoring thread
            self.executor.submit(self._monitoring_loop)

            print(f"Pipeline '{self.config.name}' started successfully")

            if self.config.auto_start:
                # Keep running until stopped
                self._run_main_loop()

        except Exception as e:
            print(f"Failed to start pipeline: {e}")
            self.running = False
            raise

    def stop(self) -> None:
        """Stop the pipeline."""
        if not self.running:
            return

        print(f"Stopping pipeline '{self.config.name}'...")
        self.running = False
        self.shutdown_event.set()

        # Stop orchestrator
        self.core_orchestrator.stop()

        # Stop dashboard
        if self.dashboard:
            self.dashboard.stop()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        print("Pipeline stopped successfully")

    def get_status(self) -> str:
        """Get pipeline status."""
        return self.monitor.get_status()

    def get_uptime(self) -> float:
        """Get pipeline uptime in seconds."""
        return self.monitor.get_uptime()

    def get_total_messages_processed(self) -> int:
        """Get total messages processed."""
        return self.monitor.get_total_messages_processed()

    def get_error_count(self) -> int:
        """Get total error count."""
        return self.monitor.get_error_count()

    def get_active_stages(self) -> List[str]:
        """Get list of active stage names."""
        return self.monitor.get_active_stages()

    def get_last_activity_time(self) -> Optional[float]:
        """Get timestamp of last activity."""
        return self.monitor.get_last_activity_time()

    def get_stage_metrics(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific stage."""
        return self.monitor.get_stage_metrics(stage_name)

    def get_all_stage_metrics(self) -> Dict[str, Any]:
        """Get metrics for all stages."""
        return self.monitor.get_all_stage_metrics()

    def get_storage_metrics(self, backend_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific storage backend."""
        return self.monitor.get_storage_metrics(backend_name)

    def get_all_storage_metrics(self) -> Dict[str, Any]:
        """Get metrics for all storage backends."""
        return self.monitor.get_all_storage_metrics()

    def export_data(self, backend_name: str, collection: str, format_type: str,
                   output_path: str, **kwargs) -> Any:
        """Export data from storage backend."""
        if backend_name not in self.initializer.storage_backends:
            raise ValueError(f"Storage backend '{backend_name}' not found")

        backend = self.initializer.storage_backends[backend_name]
        return self.initializer.export_manager.export_from_storage(
            backend, collection, format_type, output_path, **kwargs
        )

    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """Get dashboard data if available."""
        return self.monitor.get_dashboard_data()

    def is_running(self) -> bool:
        """Check if pipeline is running."""
        return self.running


