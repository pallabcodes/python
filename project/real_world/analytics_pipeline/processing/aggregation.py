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


# Import aggregation methods
from .aggregation_methods import (
    _load_aggregation_windows, _create_filter_function, _process_message,
    _update_window_aggregation, _clean_window_data, _calculate_aggregates,
    _extract_numeric_value, _extract_value_for_uniqueness, _create_group_key,
    _get_current_aggregation_results, _create_aggregation_message,
    get_aggregation_results, _cleanup_worker, _perform_cleanup, _extract_field
)


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
# Methods are implemented in aggregation_methods.py to keep file under 200 lines
