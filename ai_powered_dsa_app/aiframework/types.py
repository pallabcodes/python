"""
Type definitions for AI Framework

Contains shared data types and request/response objects.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class GenerationRequest:
    """Request object for LLM generation."""
    prompt: str
    quality_requirement: str = "standard"  # basic, standard, high, premium
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class GenerationResponse:
    """Response object for LLM generation."""
    content: str
    provider_used: str
    tokens_used: int
    cost: float
    latency: float
    quality_score: float
    batch_efficiency: Optional[float] = None
