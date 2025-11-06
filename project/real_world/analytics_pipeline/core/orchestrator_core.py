"""
Core orchestrator functionality.

This module contains the main PipelineOrchestrator class and core
orchestration logic for managing pipeline lifecycle and coordination.
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..pipeline_core.message import DataMessage, ControlMessage
from ..pipeline_core.stage_base import PipelineStage


class PipelineState(Enum):
    """Pipeline execution states."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    RESUMING = "resuming"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


@dataclass
class PipelineStats:
    """Statistics for pipeline execution."""
    messages_processed: int = 0
    messages_failed: int = 0
    processing_time: float = 0.0
    stage_stats: Dict[str, Dict[str, Any]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def __post_init__(self):
        """Initialize mutable fields."""
        if self.stage_stats is None:
            self.stage_stats = {}

    @property
    def total_time(self) -> float:
        """Get total execution time."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

    @property
    def throughput(self) -> float:
        """Get messages per second."""
        total_time = self.total_time
        if total_time > 0:
            return self.messages_processed / total_time
        return 0.0


class PipelineOrchestrator:
    """Main orchestrator for the analytics pipeline.

    This class coordinates all aspects of the analytics pipeline:
    - Stage lifecycle management
    - Message routing between stages
    - Resource allocation and scaling
    - Fault tolerance and recovery
    - Monitoring and statistics
    """

    def __init__(
        self,
        name: str,
        stages: List[PipelineStage],
        message_router: Optional[Any] = None,
        autoscaler: Optional[Any] = None
    ):
        """Initialize the pipeline orchestrator.

        Args:
            name: Pipeline name for identification
            stages: List of pipeline stages to orchestrate
            message_router: Optional custom message router
            autoscaler: Optional autoscaling component
        """
        self.name = name
        self.stages = stages
        self.message_router = message_router or MessageRouter()
        self.autoscaler = autoscaler

        # State management
        self._state = PipelineState.INITIALIZING
        self._state_lock = threading.RLock()

        # Statistics and monitoring
        self._stats = PipelineStats()
        self._stats_lock = threading.Lock()

        # Control and coordination
        self._control_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        # Error handling
        self._error_handler: Optional[Callable[[Exception], None]] = None

        # Logging
        self._logger = logging.getLogger(f"{__name__}.{name}")

        # Circuit breakers for each stage (will be initialized)
        self._circuit_breakers: Dict[str, Any] = {}

        self._logger.info(f"Initialized pipeline orchestrator '{name}' with {len(stages)} stages")

    @property
    def state(self) -> PipelineState:
        """Get current pipeline state."""
# Import lifecycle and execution methods
from .orchestrator_lifecycle import (
    start, stop, _initialize_stages, _initialize_circuit_breakers,
    _cleanup_stages, _start_control_thread
)
from .orchestrator_execution import (
    submit_message, _submit_to_stage, _find_stage_by_name, _handle_error
)
