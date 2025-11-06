"""
Enrichment stage methods.

This module contains method implementations for the EnrichmentStage class
to keep the main class file focused and under the 200-line limit.
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from .enrichment import EnrichmentRule


def _load_enrichment_rules(self) -> List[EnrichmentRule]:
    """Load custom enrichment rules from configuration.

    Returns:
        List of configured enrichment rules
    """
    rules_config = self._config.get('rules', [])
    rules = []

    for rule_config in rules_config:
        try:
            rule = EnrichmentRule(
                name=rule_config.get('name', 'unnamed_rule'),
                condition=_create_condition_function(self, rule_config),
                enrich_function=_create_enrich_function(self, rule_config),
                enabled=rule_config.get('enabled', True),
                priority=rule_config.get('priority', 0)
            )
            rules.append(rule)
        except Exception as e:
            self._logger.warning(f"Failed to load enrichment rule: {e}")

    # Sort by priority
    rules.sort(key=lambda r: r.priority, reverse=True)
    return rules


def _create_condition_function(self, rule_config: Dict[str, Any]) -> Callable:
    """Create a condition function from rule configuration.

    Args:
        rule_config: Rule configuration dictionary

    Returns:
        Condition function that returns True if rule should apply
    """
    # Simple field existence condition
    if 'condition_field' in rule_config:
        field = rule_config['condition_field']
        return lambda msg: field in msg.get('data', {})

    # Default: always apply
    return lambda msg: True


def _create_enrich_function(self, rule_config: Dict[str, Any]) -> Callable:
    """Create an enrichment function from rule configuration.

    Args:
        rule_config: Rule configuration dictionary

    Returns:
        Function that returns enrichment data
    """
    enrichments = rule_config.get('enrichments', {})

    def enrich_func(message: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in enrichments.items():
            if isinstance(value, str) and value.startswith('$'):
                # Dynamic value from message
                field_path = value[1:]  # Remove $
                result[key] = _extract_field(self, message, field_path)
            else:
                # Static value
                result[key] = value
        return result

    return enrich_func


def _process_message(self, message: Any) -> Optional[Any]:
    """Process and enrich a message.

    Args:
        message: Input message to enrich

    Returns:
        Enriched message
    """
    if not isinstance(message, dict) or 'data' not in message:
        self._logger.warning("Invalid message format for enrichment")
        return message

    # Create enriched copy
    enriched_message = _deep_copy_message(self, message)

    # Add standard enrichments
    if self._add_timestamps:
        enriched_message = _add_timestamp_enrichment(self, enriched_message)

    if self._add_message_hash:
        enriched_message = _add_hash_enrichment(self, enriched_message)

    if self._add_processing_metadata:
        enriched_message = _add_processing_enrichment(self, enriched_message)

    # Apply custom enrichment rules
    for rule in self._custom_rules:
        if rule.enabled and rule.condition(enriched_message):
            try:
                enrichment_data = rule.enrich_function(enriched_message)
                enriched_message.setdefault('metadata', {}).update(enrichment_data)
            except Exception as e:
                self._logger.error(f"Error applying enrichment rule '{rule.name}': {e}")

    return enriched_message


