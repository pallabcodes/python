"""
Storage dataclasses and metrics for the analytics pipeline.

This module contains the dataclasses and metrics structures for storage backends,
separated for better modularity and to keep file sizes under limits.
"""

from dataclasses import dataclass
from typing import Any, Optional, List


@dataclass
class StorageMetrics:
    """Metrics for storage operations."""

    operations_total: int = 0
    operations_successful: int = 0
    operations_failed: int = 0
    bytes_written: int = 0
    bytes_read: int = 0
    last_operation_time: float = 0.0
    average_operation_time: float = 0.0
    connection_pool_size: int = 0
    active_connections: int = 0


@dataclass
class StorageConfig:
    """Configuration for storage backends."""

    backend_type: str
    connection_string: str
    max_connections: int = 10
    connection_timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    enable_metrics: bool = True
    enable_compression: bool = False
    batch_size: int = 100
    flush_interval: int = 60  # seconds


@dataclass
class QueryFilter:
    """Filter criteria for queries."""

    field: str
    operator: str  # 'eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'contains', 'regex'
    value: Any
    case_sensitive: bool = True


@dataclass
class QueryOptions:
    """Options for query operations."""

    limit: Optional[int] = None
    offset: int = 0
    sort_by: Optional[str] = None
    sort_order: str = 'asc'  # 'asc', 'desc'
    fields: Optional[List[str]] = None  # Fields to include in results