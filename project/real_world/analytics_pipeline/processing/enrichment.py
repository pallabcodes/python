"""
Enrichment stage for the analytics pipeline.

This module provides data enrichment capabilities, adding metadata, context,
and additional information to messages as they flow through the pipeline.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from .stage_base import BaseProcessingStage


# Import enrichment methods
from .enrichment_core import (
    _load_enrichment_rules, _create_condition_function, _create_enrich_function,
    _process_message
)
from .enrichment_ops import (
    _add_timestamp_enrichment, _add_hash_enrichment, _add_processing_enrichment,
    _deep_copy_message, _extract_field
)


@dataclass
class EnrichmentRule:
    """Configuration for a single enrichment rule."""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    enrich_function: Callable[[Dict[str, Any]], Dict[str, Any]]
    enabled: bool = True
    priority: int = 0


class EnrichmentStage(BaseProcessingStage):
    """Stage for enriching messages with additional metadata and context.

    This stage can add various types of enrichment:
    - Timestamps and processing metadata
    - Message hashing for deduplication
    - Source-specific context
    - Business rule-based enrichment
    - Geolocation data (if available)
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the enrichment stage.

        Args:
            name: Stage name
            config: Configuration dictionary with enrichment settings
        """
        super().__init__(name, config)

        # Enrichment configuration
        self._add_timestamps = self._config.get('add_timestamps', True)
        self._add_message_hash = self._config.get('add_message_hash', True)
        self._add_processing_metadata = self._config.get('add_processing_metadata', True)
        self._custom_rules = self._load_enrichment_rules()

        # Validation
        self._validate_config([])  # No required config keys

    # Methods are implemented in enrichment_methods.py to keep file under 200 lines
