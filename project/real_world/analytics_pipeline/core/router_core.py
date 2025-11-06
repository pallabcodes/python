"""
Core message routing functionality.

This module contains the main MessageRouter class and core
routing logic for distributing messages to appropriate stages.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

from ..pipeline_core.message import DataMessage


class RoutingStrategy(Enum):
    """Message routing strategies."""
    CONTENT_BASED = "content_based"
    METADATA_BASED = "metadata_based"
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"


@dataclass
class RoutingRule:
    """Rule for routing messages to stages."""
    stage_name: str
    condition: Callable[[DataMessage], bool]
    priority: int = 0
    description: str = ""

    def matches(self, message: DataMessage) -> bool:
        """Check if rule matches the message.

        Args:
            message: Message to evaluate

        Returns:
            True if rule matches, False otherwise
        """
        try:
            return self.condition(message)
        except Exception:
            # If condition evaluation fails, rule doesn't match
            return False


@dataclass
class RoutingStats:
    """Statistics for message routing."""
    messages_routed: int = 0
    routing_failures: int = 0
    stage_distribution: Dict[str, int] = None

    def __post_init__(self):
        """Initialize mutable fields."""
        if self.stage_distribution is None:
            self.stage_distribution = {}


class MessageRouter:
    """Dynamic message router for the analytics pipeline.

    This class provides intelligent routing of messages to appropriate
    pipeline stages based on configurable rules and strategies.
    """

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.CONTENT_BASED):
        """Initialize message router.

        Args:
            strategy: Default routing strategy
        """
        self.strategy = strategy
        self._rules: List[RoutingRule] = []
        self._logger = logging.getLogger(__name__)

        # Statistics
        self._stats = RoutingStats()
        self._stats_lock = threading.Lock()

        # Round-robin state
        self._round_robin_index = 0

        # Weighted routing state
        self._weighted_weights: Dict[str, float] = {}

    def add_rule(
        self,
        stage_name: str,
        condition: Callable[[DataMessage], bool],
        priority: int = 0,
        description: str = ""
    ) -> None:
        """Add a routing rule.

        Args:
            stage_name: Name of stage to route to
            condition: Function that returns True if message should be routed to stage
            priority: Rule priority (higher values evaluated first)
            description: Human-readable description of the rule
        """
        rule = RoutingRule(
            stage_name=stage_name,
            condition=condition,
            priority=priority,
            description=description
        )
# Import routing methods
from .router_methods import (
    add_rule, add_content_rule, route_message, get_stats,
    clear_rules, list_rules
)
