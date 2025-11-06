"""
Production MLOps + Gen AI Platform

A comprehensive platform that combines MLOps infrastructure with Generative AI capabilities,
built on enterprise-grade analytics pipeline foundation.

Features:
- MLOps: Model training, registry, monitoring, feature store
- Gen AI: LLM fine-tuning, RAG, AI agents, multi-modal processing
- Production: FastAPI serving, monitoring, deployment automation

Author: AI Assistant
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

from .core import MLOpsPlatform

__all__ = ["MLOpsPlatform"]
