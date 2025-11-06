"""
Windowing stage for the analytics pipeline.

This module provides advanced windowing capabilities for real-time analytics
including sliding windows, tumbling windows, and session windows.
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable, Deque
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .stage_base import BaseProcessingStage


# Import windowing methods
from .windowing_methods import (
    _load_window_configs, _process_message, _process_window_message,
    _process_sliding_window, _process_tumbling_window, _process_hopping_window,
    _process_session_window, _create_window_event, _create_group_key,
    _extract_group_key_from_window_id, _cleanup_group_windows,
    get_window_stats, _cleanup_worker, _perform_cleanup, _extract_field
)


@dataclass
class WindowConfig:
    """Configuration for a time window."""

    name: str
    window_type: str  # 'sliding', 'tumbling', 'session', 'hopping'
    size_seconds: int
    slide_seconds: Optional[int] = None  # For hopping windows
    session_timeout: Optional[int] = None  # For session windows
    group_by_fields: List[str] = field(default_factory=list)
    emit_partial_results: bool = False
    max_window_size: int = 10000  # Maximum events per window


@dataclass
class WindowData:
    """Data structure for a time window."""

    window_id: str
    start_time: float
    end_time: float
    events: Deque[Dict[str, Any]] = field(default_factory=lambda: deque())
    last_event_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class WindowingStage(BaseProcessingStage):
    """Stage for advanced windowing operations on streaming data.

    This stage provides various windowing strategies:
    - Sliding windows: Continuous overlapping windows
    - Tumbling windows: Non-overlapping fixed-size windows
    - Hopping windows: Overlapping windows with configurable slide
    - Session windows: Dynamic windows based on activity gaps
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the windowing stage.

        Args:
            name: Stage name
            config: Configuration dictionary with windowing settings
        """
        super().__init__(name, config)

        # Windowing configuration
        self._windows = self._load_window_configs()
        self._max_windows_per_group = self._config.get('max_windows_per_group', 10)
        self._cleanup_interval = self._config.get('cleanup_interval', 60)  # 1 minute
# Methods are implemented in windowing_methods.py to keep file under 200 lines
