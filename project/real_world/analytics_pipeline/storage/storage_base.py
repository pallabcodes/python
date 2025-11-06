"""
Base storage backend for the analytics pipeline.

This module defines the base classes and interfaces for all storage backends
in the analytics pipeline, providing common functionality for data persistence,
querying, and management.
"""

from typing import Dict, Any, Optional, List, Callable, Union, Iterator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..pipeline_core.message import DataMessage


# Import storage classes and methods
from .storage_metrics import (
    StorageMetrics, StorageConfig, QueryFilter, QueryOptions
)
from .storage_operations import (
    StorageBackend
)

