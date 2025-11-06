"""
MessageRouter method implementations.

This module contains the method implementations for the MessageRouter class
to keep the main class file focused and under the 200-line limit.
"""

import re
from typing import Dict, List, Any, Optional, Callable, Union

from ..pipeline_core.message import DataMessage
from .router_core import MessageRouter, RoutingRule, RoutingStats, RoutingStrategy


def add_rule(
    self: MessageRouter,
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

    # Insert rule in priority order (highest first)
    insert_index = 0
    for i, existing_rule in enumerate(self._rules):
        if priority > existing_rule.priority:
            insert_index = i
            break
        insert_index = i + 1

    self._rules.insert(insert_index, rule)
    self._logger.info(f"Added routing rule for stage '{stage_name}' (priority {priority})")


def add_content_rule(
    self: MessageRouter,
    stage_name: str,
    field_path: str,
    value_pattern: Union[str, re.Pattern],
    priority: int = 0
) -> None:
    """Add a content-based routing rule.

    Args:
        stage_name: Name of stage to route to
        field_path: Dot-separated path to field in message data
        value_pattern: String pattern or compiled regex to match
        priority: Rule priority
    """
    def condition(message: DataMessage) -> bool:
        field_value = self._extract_field_value(message.data, field_path)
        if field_value is None:
            return False

        if isinstance(value_pattern, str):
            return str(field_value) == value_pattern
        else:
            return bool(value_pattern.search(str(field_value)))

    self.add_rule(
        stage_name=stage_name,
        condition=condition,
        priority=priority,
        description=f"Content rule: {field_path} matches {value_pattern}"
    )


def route_message(self: MessageRouter, message: DataMessage) -> Optional[str]:
    """Route a message to the appropriate stage.

    Args:
        message: Message to route

    Returns:
        Stage name to route to, or None if no route found
    """
    if self.strategy == RoutingStrategy.CONTENT_BASED:
        return self._route_by_rules(message)
    elif self.strategy == RoutingStrategy.METADATA_BASED:
        return self._route_by_metadata(message)
    elif self.strategy == RoutingStrategy.PRIORITY_BASED:
        return self._route_by_priority(message)
    elif self.strategy == RoutingStrategy.ROUND_ROBIN:
        return self._route_round_robin(message)
    elif self.strategy == RoutingStrategy.WEIGHTED:
        return self._route_weighted(message)
    else:
        return self._route_by_rules(message)  # Default fallback


def get_stats(self: MessageRouter) -> RoutingStats:
    """Get routing statistics."""
    with self._stats_lock:
        return RoutingStats(
            messages_routed=self._stats.messages_routed,
            routing_failures=self._stats.routing_failures,
            stage_distribution=self._stats.stage_distribution.copy()
        )


def clear_rules(self: MessageRouter) -> None:
    """Clear all routing rules."""
    self._rules.clear()
    self._logger.info("Cleared all routing rules")


def list_rules(self: MessageRouter) -> List[Dict[str, Any]]:
    """List all routing rules.

    Returns:
        List of rule information dictionaries
    """
    return [
        {
            'stage_name': rule.stage_name,
            'priority': rule.priority,
            'description': rule.description
        }
        for rule in self._rules
    ]
