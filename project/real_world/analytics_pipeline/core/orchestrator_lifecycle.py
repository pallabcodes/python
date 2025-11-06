"""
Orchestrator lifecycle management methods.

This module contains methods for managing the pipeline orchestrator's
lifecycle including start, stop, initialization, and cleanup operations.
"""

import time
import threading
import logging
from typing import Optional

from .orchestrator_core import PipelineOrchestrator, PipelineState


def start(self: PipelineOrchestrator) -> None:
    """Start the pipeline orchestrator."""
    with self._state_lock:
        if self._state != PipelineState.INITIALIZING:
            raise RuntimeError(f"Cannot start pipeline in state: {self._state}")

        self._state = PipelineState.RUNNING
        self._stats.start_time = time.time()

    try:
        # Initialize stages
        self._initialize_stages()

        # Initialize circuit breakers
        self._initialize_circuit_breakers()

        # Start control thread
        self._start_control_thread()

        self._logger.info(f"Pipeline '{self.name}' started successfully")

    except Exception as e:
        with self._state_lock:
            self._state = PipelineState.ERROR
        self._handle_error(e)
        raise


def stop(self: PipelineOrchestrator, timeout: float = 30.0) -> None:
    """Stop the pipeline orchestrator.

    Args:
        timeout: Maximum time to wait for graceful shutdown
    """
    with self._state_lock:
        if self._state in [PipelineState.SHUTDOWN, PipelineState.SHUTTING_DOWN]:
            return

        self._state = PipelineState.SHUTTING_DOWN

    self._logger.info(f"Stopping pipeline '{self.name}' with timeout {timeout}s")

    # Signal shutdown
    self._shutdown_event.set()

    # Wait for control thread
    if self._control_thread and self._control_thread.is_alive():
        self._control_thread.join(timeout=timeout)

    # Cleanup stages
    self._cleanup_stages()

    # Update final statistics
    with self._stats_lock:
        self._stats.end_time = time.time()

    with self._state_lock:
        self._state = PipelineState.SHUTDOWN

    self._logger.info(f"Pipeline '{self.name}' stopped successfully")


def _initialize_stages(self: PipelineOrchestrator) -> None:
    """Initialize all pipeline stages."""
    for stage in self.stages:
        try:
            stage.initialize()
            self._logger.debug(f"Initialized stage '{stage.name}'")
        except Exception as e:
            self._logger.error(f"Failed to initialize stage '{stage.name}': {e}")
            raise


def _initialize_circuit_breakers(self: PipelineOrchestrator) -> None:
    """Initialize circuit breakers for each stage."""
    # Import here to avoid circular imports
    from .circuit_breaker_core import CircuitBreaker

    for stage in self.stages:
        self._circuit_breakers[stage.name] = CircuitBreaker(
            name=f"{self.name}.{stage.name}",
            failure_threshold=5,
            recovery_timeout=60.0
        )


def _cleanup_stages(self: PipelineOrchestrator) -> None:
    """Cleanup all pipeline stages."""
    for stage in reversed(self.stages):
        try:
            stage.cleanup()
            self._logger.debug(f"Cleaned up stage '{stage.name}'")
        except Exception as e:
            self._logger.error(f"Error cleaning up stage '{stage.name}': {e}")


def _start_control_thread(self: PipelineOrchestrator) -> None:
    """Start the control thread for pipeline management."""
    self._control_thread = threading.Thread(
        target=self._control_loop,
        name=f"Pipeline-{self.name}-Control",
        daemon=True
    )
    self._control_thread.start()
