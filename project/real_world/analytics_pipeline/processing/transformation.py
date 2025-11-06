"""
Transformation stage for the analytics pipeline.

This module provides data transformation capabilities including validation,
cleansing, normalization, and data type conversion.
"""

from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass

from .stage_base import BaseProcessingStage


# Import transformation methods
from .transformation_processing import (
    _load_validation_rules, _load_transformation_rules, _create_transform_function,
    _create_condition_function, _process_message, _apply_field_mappings,
    _apply_type_conversions, _apply_transformation_rule, _sanitize_text_fields,
    _normalize_timestamp_fields, _validate_message
)
from .transformation_utils import (
    _convert_value, _normalize_timestamp, _format_date, _deep_copy_message,
    _extract_field, _set_field
)


@dataclass
class TransformationRule:
    """Configuration for a data transformation rule."""

    field_path: str
    transform_function: Callable[[Any], Any]
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    required: bool = False
    default_value: Any = None


class TransformationStage(BaseProcessingStage):
    """Stage for transforming and normalizing message data.

    This stage provides various transformation capabilities:
    - Data validation and cleansing
    - Type conversion and normalization
    - Field mapping and renaming
    - Data sanitization and filtering
    - Schema validation
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the transformation stage.

        Args:
            name: Stage name
            config: Configuration dictionary with transformation settings
        """
        super().__init__(name, config)

        # Transformation configuration
        self._field_mappings = self._config.get('field_mappings', {})
        self._type_conversions = self._config.get('type_conversions', {})
        self._validation_rules = self._load_validation_rules()
        self._transformation_rules = self._load_transformation_rules()
        self._sanitize_text = self._config.get('sanitize_text', True)
        self._normalize_timestamps = self._config.get('normalize_timestamps', True)

        # Validation
        self._validate_config([])  # No required config keys

    # Methods are implemented in transformation_methods.py to keep file under 200 lines
# Methods are implemented in transformation_methods.py to keep file under 200 lines
