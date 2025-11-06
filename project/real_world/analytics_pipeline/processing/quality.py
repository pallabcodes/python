"""
Quality stage for the analytics pipeline.

This module provides data quality validation and monitoring capabilities
including completeness checks, accuracy validation, and quality metrics.
"""

import time
import hashlib
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .stage_base import BaseProcessingStage


# Import quality methods
from .quality_methods import (
    _load_quality_rules, _create_condition_function, _check_type, _process_message,
    _check_required_fields, _update_quality_metrics, _get_all_field_paths,
    _add_quality_metadata, _log_quality_issue, get_quality_metrics,
    get_recent_issues, is_quality_acceptable, _extract_field
)


@dataclass
class QualityRule:
    """Configuration for a data quality rule."""

    name: str
    rule_type: str  # 'completeness', 'accuracy', 'consistency', 'timeliness', 'validity'
    field_path: str
    condition: Callable[[Any], bool]
    severity: str = 'warning'  # 'warning', 'error', 'critical'
    description: str = ''
    enabled: bool = True


@dataclass
class QualityMetrics:
    """Quality metrics for data validation."""

    total_messages: int = 0
    valid_messages: int = 0
    invalid_messages: int = 0
    quality_score: float = 100.0
    rule_violations: Dict[str, int] = field(default_factory=dict)
    field_completeness: Dict[str, float] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


@dataclass
class QualityIssue:
    """Represents a data quality issue."""

    rule_name: str
    severity: str
    field_path: str
    description: str
    message_value: Any
    timestamp: float


class QualityStage(BaseProcessingStage):
    """Stage for data quality validation and monitoring.

    This stage provides comprehensive data quality capabilities:
    - Completeness validation (required fields)
    - Accuracy checks (data type, range validation)
    - Consistency validation (cross-field rules)
    - Timeliness monitoring (data freshness)
    - Quality metrics and reporting
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
# Methods are implemented in quality_methods.py to keep file under 200 lines
