"""
Aggregation stage for the analytics pipeline.

This module provides real-time data aggregation capabilities including
counting, summing, averaging, and complex analytics over sliding windows.
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .stage_base import BaseProcessingStage


@dataclass
class AggregationWindow:
    """Configuration for an aggregation window."""

    name: str
    window_type: str  # 'sliding', 'tumbling', 'hopping'
    window_size: int  # Size in seconds
    slide_interval: Optional[int] = None  # For hopping windows
    aggregation_functions: List[str] = field(default_factory=list)
    group_by_fields: List[str] = field(default_factory=list)
    filter_condition: Optional[Callable] = None


@dataclass
class AggregationResult:
    """Result of an aggregation operation."""

    window_name: str
    group_key: str
    timestamp: float
    metrics: Dict[str, Any]
    count: int
    window_start: float
    window_end: float


class AggregationStage(BaseProcessingStage):
    """Stage for aggregating and analyzing message data in real-time.

    This stage provides various aggregation capabilities:
    - Count, sum, average, min, max aggregations
    - Sliding and tumbling windows
    - Grouped aggregations
    - Real-time analytics and KPIs
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the aggregation stage.

        Args:
            name: Stage name
            config: Configuration dictionary with aggregation settings
        """
        super().__init__(name, config)

        # Aggregation configuration
        self._windows = self._load_aggregation_windows()
        self._max_window_size = self._config.get('max_window_size', 3600)  # 1 hour
        self._cleanup_interval = self._config.get('cleanup_interval', 300)  # 5 minutes
        self._enable_persistence = self._config.get('enable_persistence', False)

        # Aggregation state
        self._window_data: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._current_aggregates: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self._lock = threading.RLock()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            name=f"AggregationCleanup-{name}",
            daemon=True
        )
        self._cleanup_thread.start()

        # Validation
        self._validate_config([])  # No required config keys

    def _load_aggregation_windows(self) -> List[AggregationWindow]:
        """Load aggregation windows from configuration.

        Returns:
            List of configured aggregation windows
        """
        windows_config = self._config.get('windows', [])
        windows = []

        for window_config in windows_config:
            try:
                window = AggregationWindow(
                    name=window_config['name'],
                    window_type=window_config.get('type', 'sliding'),
                    window_size=window_config['size'],
                    slide_interval=window_config.get('slide_interval'),
                    aggregation_functions=window_config.get('functions', ['count']),
                    group_by_fields=window_config.get('group_by', []),
                    filter_condition=self._create_filter_function(window_config.get('filter'))
                )
                windows.append(window)
            except Exception as e:
                self._logger.warning(f"Failed to load aggregation window: {e}")

        return windows

    def _create_filter_function(self, filter_config: Optional[Dict[str, Any]]) -> Optional[Callable]:
        """Create a filter function from configuration.

        Args:
            filter_config: Filter configuration dictionary

        Returns:
            Filter function or None
        """
        if not filter_config:
# Methods are implemented in aggregation_methods.py to keep file under 200 lines
