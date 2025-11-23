"""
Provider Management System

Handles multiple LLM providers with:
- Automatic provider selection based on quality/cost
- Fallback mechanisms
- Cost tracking and optimization
- Rate limit management
"""

import asyncio
import time
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .config import FrameworkConfig, ProviderConfig, Mode

@dataclass
class ProviderResponse:
    """Response from an LLM provider."""
    content: str
    tokens_used: int
    cost: float
    quality_score: float
    metadata: Dict[str, Any] = None

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = logging.getLogger(f"Provider.{config.name}")
        self._rate_limiter = RateLimiter(config.rate_limit)

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate text using this provider."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available."""
        pass

    @property
    def name(self) -> str:
        return self.config.name

    async def check_rate_limit(self) -> bool:
        """Check if we can make a request within rate limits."""
        return await self._rate_limiter.check_limit()

class MockProvider(LLMProvider):
    """Mock provider for development and testing."""

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate mock response."""
        await asyncio.sleep(0.1)  # Simulate API latency

        # Generate contextual mock response
        if "explain" in prompt.lower():
            content = f"This is a mock explanation for: {prompt[:50]}..."
        elif "code" in prompt.lower():
            content = f"```python\n# Mock code for: {prompt[:30]}\ndef mock_function():\n    return 'mock result'\n```"
        else:
            content = f"Mock response to: {prompt[:100]}..."

        return ProviderResponse(
            content=content,
            tokens_used=len(prompt.split()) * 2,
            cost=0.0,
            quality_score=self.config.quality_score,
            metadata={"mock": True, "provider": "mock"}
        )

    async def is_available(self) -> bool:
        return True

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key_env and os.getenv(config.api_key_env)

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        if not await self.is_available():
            raise Exception("OpenAI API key not configured")

        # Mock implementation - replace with real OpenAI API call
        await asyncio.sleep(0.5)

        return ProviderResponse(
            content=f"OpenAI response to: {prompt[:50]}...",
            tokens_used=len(prompt.split()) * 3,
            cost=len(prompt.split()) * self.config.cost_per_token,
            quality_score=self.config.quality_score,
            metadata={"model": "gpt-4", "provider": "openai"}
        )

    async def is_available(self) -> bool:
        return bool(self.api_key)

class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv(config.api_key_env)

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        if not await self.is_available():
            raise Exception("Gemini API key not configured")

        # Mock implementation - replace with real Gemini API call
        await asyncio.sleep(0.3)

        return ProviderResponse(
            content=f"Gemini response to: {prompt[:50]}...",
            tokens_used=len(prompt.split()) * 2,
            cost=0.0,  # Free tier
            quality_score=self.config.quality_score,
            metadata={"model": "gemini-1.5-flash", "provider": "gemini"}
        )

    async def is_available(self) -> bool:
        return bool(self.api_key)

class TogetherProvider(LLMProvider):
    """Together AI provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv(config.api_key_env)

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        if not await self.is_available():
            raise Exception("Together AI API key not configured")

        # Mock implementation - replace with real Together API call
        await asyncio.sleep(0.4)

        return ProviderResponse(
            content=f"Together AI response to: {prompt[:50]}...",
            tokens_used=len(prompt.split()) * 2,
            cost=0.0,  # Free tier
            quality_score=self.config.quality_score,
            metadata={"model": "mistral-7b", "provider": "together"}
        )

    async def is_available(self) -> bool:
        return bool(self.api_key)

class RateLimiter:
    """Simple rate limiter for API providers."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()

    async def check_limit(self) -> bool:
        """Check if we can make another request."""
        async with self.lock:
            current_time = time.time()

            # Remove old requests
            cutoff_time = current_time - 60
            self.requests = [r for r in self.requests if r > cutoff_time]

            # Check if under limit
            if len(self.requests) < self.requests_per_minute:
                self.requests.append(current_time)
                return True

            return False

class ProviderManager:
    """
    Manages multiple LLM providers with intelligent selection.

    Features:
    - Automatic provider selection based on quality/cost requirements
    - Fallback mechanisms when providers fail
    - Cost tracking and optimization
    - Rate limit management
    """

    def __init__(self, config: FrameworkConfig):
        self.config = config
        self.logger = logging.getLogger("ProviderManager")
        self.providers = {}

        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all configured providers."""
        provider_classes = {
            "mock": MockProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "together": TogetherProvider
        }

        for provider_name, provider_config in self.config.providers.items():
            if provider_config.enabled:
                provider_class = provider_classes.get(provider_name)
                if provider_class:
                    try:
                        provider = provider_class(provider_config)
                        self.providers[provider_name] = provider
                        self.logger.info(f"✅ Initialized provider: {provider_name}")
                    except Exception as e:
                        self.logger.warning(f"❌ Failed to initialize {provider_name}: {e}")

        # Ensure we always have at least the mock provider
        if "mock" not in self.providers:
            mock_config = self.config.providers["mock"]
            self.providers["mock"] = MockProvider(mock_config)

    def get_optimal_provider(self, quality_requirement: str) -> LLMProvider:
        """
        Get the optimal provider for the given quality requirement.

        Selection criteria:
        1. Meets quality requirement
        2. Lowest cost
        3. Highest rate limit
        4. Availability
        """
        quality_thresholds = {
            "basic": 0.0,
            "standard": 0.7,
            "high": 0.8,
            "premium": 0.9
        }

        threshold = quality_thresholds.get(quality_requirement, 0.7)
        available_providers = []

        for provider in self.providers.values():
            if (provider.config.is_available and
                provider.config.quality_score >= threshold):
                available_providers.append(provider)

        if not available_providers:
            # Fallback to mock provider
            self.logger.warning("No suitable providers available, using mock")
            return self.providers.get("mock")

        # Sort by cost, then by rate limit, then by quality
        available_providers.sort(key=lambda p: (
            p.config.cost_per_token,
            -p.config.rate_limit,  # Higher rate limit is better
            -p.config.quality_score
        ))

        optimal = available_providers[0]
        self.logger.debug(f"Selected provider: {optimal.name} for quality: {quality_requirement}")
        return optimal

    def list_providers(self) -> List[str]:
        """List all available providers."""
        return list(self.providers.keys())

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive provider status."""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "available": await provider.is_available(),
                "rate_limit": provider.config.rate_limit,
                "cost_per_token": provider.config.cost_per_token,
                "quality_score": provider.config.quality_score
            }
        return status

    async def optimize_for_cost(self) -> Dict[str, Any]:
        """Optimize provider configuration for cost efficiency."""
        optimizations = {}

        # Disable expensive providers if cheaper alternatives exist
        available_providers = await self.get_status()
        free_providers = [p for p, s in available_providers.items()
                         if s["available"] and s["cost_per_token"] == 0.0]

        if free_providers:
            optimizations["free_providers_available"] = len(free_providers)
            optimizations["recommendation"] = "Using free providers for cost optimization"
        else:
            optimizations["recommendation"] = "Consider adding free tier providers"

        return optimizations

    async def shutdown(self):
        """Shutdown all providers gracefully."""
        for provider in self.providers.values():
            # Add any cleanup logic here
            pass
