"""
Core platform components for MLOps + Gen AI Platform.

Provides the main platform orchestrator and core abstractions.
"""

from .platform import MLOpsPlatform
from .config import PlatformConfig

__all__ = ["MLOpsPlatform", "PlatformConfig"]
