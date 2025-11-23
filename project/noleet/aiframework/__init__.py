"""
AI Framework - Reusable Multi-Provider LLM System

A production-ready framework for AI engineers that provides:
- Multi-provider LLM routing (Free APIs + Premium)
- Intelligent batching for development and production
- Manual intervention workflows for quality control
- Cost optimization and monitoring
- Development-first approach with mock providers

Usage:
    from aiframework import AIFramework

    # Development mode (mock providers)
    ai = AIFramework(mode="development")

    # Production mode (real APIs)
    ai = AIFramework(mode="production")

    # Use across your projects
    response = await ai.generate("Your prompt here")
"""

__version__ = "1.0.0"
__author__ = "AI Engineer Framework"

from .core import AIFramework
from .providers import ProviderManager
from .batching import BatchManager
from .intervention import InterventionManager

__all__ = [
    "AIFramework",
    "ProviderManager",
    "BatchManager",
    "InterventionManager"
]
