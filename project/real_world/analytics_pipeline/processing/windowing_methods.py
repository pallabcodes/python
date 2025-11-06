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
        self._emit_window_events = self._config.get('emit_window_events', True)

        # Window state
        self._active_windows: Dict[str, Dict[str, List[WindowData]]] = defaultdict(dict)
        self._completed_windows: Deque[WindowData] = deque(maxlen=1000)
        self._lock = threading.RLock()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            name=f"WindowCleanup-{name}",
            daemon=True
        )
        self._cleanup_thread.start()

        # Validation
        self._validate_config([])  # No required config keys

    def _load_window_configs(self) -> List[WindowConfig]:
        """Load window configurations from config.

        Returns:
            List of window configurations
        """
        windows_config = self._config.get('windows', [])
        windows = []

        for window_config in windows_config:
            try:
                window = WindowConfig(
                    name=window_config['name'],
                    window_type=window_config.get('type', 'sliding'),
                    size_seconds=window_config['size_seconds'],
                    slide_seconds=window_config.get('slide_seconds'),
                    session_timeout=window_config.get('session_timeout'),
                    group_by_fields=window_config.get('group_by', []),
                    emit_partial_results=window_config.get('emit_partial_results', False),
                    max_window_size=window_config.get('max_window_size', 10000)
                )
                windows.append(window)
            except Exception as e:
                self._logger.warning(f"Failed to load window config: {e}")

        return windows

    def _process_message(self, message: Any) -> Optional[Any]:
        """Process a message through windowing logic.

        Args:
            message: Input message to window

        Returns:
            Original message or window event message
        """
# Methods are implemented in windowing_methods.py to keep file under 200 lines
