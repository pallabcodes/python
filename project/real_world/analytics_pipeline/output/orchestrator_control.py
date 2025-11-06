"""
Pipeline control operations for the analytics pipeline.

This module contains control and execution operations for the PipelineRunner class,
separated for better modularity and to keep file sizes under limits.
"""

import time
import signal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .orchestrator import PipelineRunner


def _run_main_loop(self: 'PipelineRunner') -> None:
    """Run the main processing loop."""
    print(f"Pipeline '{self.config.name}' running...")

    while self.running:
        try:
            # Process messages from sources
            for source_name, source in self.initializer.sources.items():
                try:
                    messages = source.get_messages()
                    if messages:
                        for message in messages:
                            # Route message through processing stages
                            self.initializer.core_orchestrator.process_message(message)

                            # Update metrics
                            self.monitor.update_metrics(messages_processed=1)

                except Exception as e:
                    print(f"Error processing source {source_name}: {e}")
                    self.monitor.update_metrics(errors=1)

            # Small delay to prevent tight loop
            time.sleep(0.1)

        except Exception as e:
            print(f"Error in main loop: {e}")
            self.monitor.update_metrics(errors=1)
            time.sleep(1)


def _monitoring_loop(self: 'PipelineRunner') -> None:
    """Run the monitoring loop in a separate thread."""
    while self.running:
        try:
            # Update dashboard
            if self.initializer.dashboard:
                self.initializer.dashboard.update()

            # Log status periodically
            if int(time.time()) % 60 == 0:  # Every minute
                status = self.monitor.get_status()
                metrics = self.monitor.get_total_messages_processed()
                print(f"Status: {status}, Messages: {metrics}")

            time.sleep(5)  # Update every 5 seconds

        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(5)


def _update_metrics(self: 'PipelineRunner') -> None:
    """Update pipeline metrics."""
    # This is now handled by PipelineMonitor
    pass


def _signal_handler(self: 'PipelineRunner', signum, frame) -> None:
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}, shutting down...")
    self.stop()

class PipelineOrchestrator:
    """High-level pipeline orchestrator interface."""

    def __init__(self, config=None):
        """Initialize pipeline orchestrator.

        Args:
            config: Pipeline configuration
        """
        from .orchestrator_core import PipelineConfig
        self.config = config or PipelineConfig()
        self.runner = None

    def configure(self, config):
        """Configure the pipeline.

        Args:
            config: Pipeline configuration
        """
        from .orchestrator_core import PipelineConfig
        self.config = config

    def start(self):
        """Start the pipeline."""
        from .orchestrator import PipelineRunner
        if self.runner is None:
            self.runner = PipelineRunner(self.config)
        self.runner.start()

    def stop(self):
        """Stop the pipeline."""
        if self.runner:
            self.runner.stop()

    def get_status(self):
        """Get pipeline status."""
        if self.runner:
            return self.runner.get_status()
        return 'not_initialized'

    def get_metrics(self):
        """Get pipeline metrics."""
        if not self.runner:
            return {}

        return {
            'status': self.runner.get_status(),
            'uptime': self.runner.get_uptime(),
            'messages_processed': self.runner.get_total_messages_processed(),
            'errors': self.runner.get_error_count(),
            'active_stages': len(self.runner.get_active_stages()),
            'stage_metrics': self.runner.get_all_stage_metrics(),
            'storage_metrics': self.runner.get_all_storage_metrics()
        }

    def export_data(self, backend_name, collection, format_type, output_path, **kwargs):
        """Export data from pipeline storage."""
        if not self.runner:
            raise RuntimeError("Pipeline not started")

        return self.runner.export_data(backend_name, collection, format_type, output_path, **kwargs)

    # Delegate other methods to runner
    def __getattr__(self, name):
        if self.runner and hasattr(self.runner, name):
            return getattr(self.runner, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
