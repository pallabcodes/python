"""
AI Framework Core - The main entry point for AI engineers

Provides a unified interface for LLM operations across development and production.
Automatically handles provider selection, batching, and cost optimization.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .config import FrameworkConfig, Mode, BatchingConfig
from .providers import ProviderManager, ProviderResponse
from .batching import BatchManager
from .intervention import InterventionManager
from .monitoring import MetricsCollector
from .types import GenerationRequest, GenerationResponse

class AIFramework:
    """
    Main AI Framework class - your go-to tool for LLM operations.

    Features:
    - Automatic provider selection based on quality/cost requirements
    - Intelligent batching for development and production
    - Manual intervention for quality control
    - Comprehensive monitoring and cost tracking
    - Seamless development ↔ production transition

    Usage:
        # Development mode (free, unlimited)
        ai = AIFramework(mode="development")
        response = await ai.generate("Explain quantum computing")

        # Production mode (optimized for cost/performance)
        ai = AIFramework(mode="production")
        response = await ai.generate("Explain quantum computing")
    """

    def __init__(
        self,
        mode: Union[str, Mode] = "development",
        config: Optional[FrameworkConfig] = None,
        enable_batching: bool = True,
        enable_intervention: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize the AI Framework.

        Args:
            mode: "development" or "production"
            config: Custom configuration (optional)
            enable_batching: Enable request batching for efficiency
            enable_intervention: Enable manual intervention workflows
            log_level: Logging level
        """
        self.mode = Mode(mode) if isinstance(mode, str) else mode
        self.config = config or FrameworkConfig(mode=self.mode)

        # Setup logging
        self._setup_logging(log_level)

        # Initialize components
        self.providers = ProviderManager(self.config)
        self.metrics = MetricsCollector(self.config.monitoring)

        # Initialize optional components
        self.batching = BatchManager(self.config.batching) if enable_batching else None
        if self.batching:
            self.batching.initialize(self.providers)
        self.intervention = InterventionManager(self.config.intervention) if enable_intervention else None

        self.logger.info(f"🤖 AI Framework initialized in {self.mode.value} mode")
        self.logger.info(f"📊 Available providers: {len(self.providers.list_providers())}")

    def _setup_logging(self, log_level: str):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("AIFramework")

    async def generate(
        self,
        prompt: Union[str, GenerationRequest],
        **kwargs
    ) -> GenerationResponse:
        """
        Generate text using the optimal provider for your needs.

        Automatically handles:
        - Provider selection based on quality requirements
        - Batching for efficiency (when enabled)
        - Cost optimization
        - Quality monitoring
        - Manual intervention triggers

        Args:
            prompt: Text prompt or GenerationRequest object
            **kwargs: Additional parameters (quality_requirement, max_tokens, etc.)

        Returns:
            GenerationResponse with content and metadata
        """
        start_time = time.time()

        # Parse request
        request = self._parse_request(prompt, kwargs)

        self.logger.debug(f"🔄 Processing request: quality={request.quality_requirement}")

        # Check if manual intervention is needed
        if self.intervention and await self._should_intervene(request):
            return await self._handle_intervention(request)

        # Use batching if enabled and appropriate
        if self.batching and self._should_batch(request):
            return await self._batch_generate(request)

        # Direct generation
        return await self._direct_generate(request, start_time)

    async def _direct_generate(
        self,
        request: GenerationRequest,
        start_time: float
    ) -> GenerationResponse:
        """Handle direct (non-batched) generation."""
        # Get optimal provider
        provider = self.providers.get_optimal_provider(request.quality_requirement)

        # Generate response
        provider_response = await provider.generate(request.prompt, **request.__dict__)

        # Create response object
        response = GenerationResponse(
            content=provider_response.content,
            provider_used=provider.name,
            tokens_used=provider_response.tokens_used,
            cost=provider_response.cost,
            latency=time.time() - start_time,
            quality_score=provider_response.quality_score
        )

        # Record metrics
        await self.metrics.record_request(response)

        return response

    async def _batch_generate(self, request: GenerationRequest) -> GenerationResponse:
        """Handle batched generation for efficiency."""
        batch_result = await self.batching.add_request(
            request_id=f"req_{int(time.time())}",
            prompt=request.prompt,
            quality_requirement=request.quality_requirement
        )

        # Convert batch result to standard response
        return GenerationResponse(
            content=batch_result.content,
            provider_used=batch_result.provider_used,
            tokens_used=batch_result.tokens_used,
            cost=batch_result.cost,
            latency=batch_result.latency,
            quality_score=batch_result.quality_score,
            batch_efficiency=batch_result.batch_efficiency
        )

    async def _should_intervene(self, request: GenerationRequest) -> bool:
        """Determine if manual intervention is needed."""
        if not self.intervention:
            return False

        # Complex requests might need human review
        if len(request.prompt) > 2000:
            return True

        # High-quality requirements might trigger intervention
        if request.quality_requirement == "premium":
            return True

        return False

    async def _handle_intervention(self, request: GenerationRequest) -> GenerationResponse:
        """Handle manual intervention workflow."""
        intervention_result = await self.intervention.process_request(request)

        return GenerationResponse(
            content=intervention_result.content,
            provider_used="manual_intervention",
            tokens_used=0,  # No API cost
            cost=0.0,
            latency=intervention_result.processing_time,
            quality_score=intervention_result.quality_score
        )

    def _should_batch(self, request: GenerationRequest) -> bool:
        """Determine if request should be batched."""
        if not self.batching:
            return False

        # Development mode: always batch for efficiency
        if self.mode == Mode.DEVELOPMENT:
            return True

        # Production mode: batch based on load
        return self.batching.should_batch()

    def _parse_request(
        self,
        prompt: Union[str, GenerationRequest],
        kwargs: Dict[str, Any]
    ) -> GenerationRequest:
        """Parse input into GenerationRequest object."""
        if isinstance(prompt, GenerationRequest):
            return prompt

        return GenerationRequest(
            prompt=prompt,
            quality_requirement=kwargs.get("quality_requirement", "standard"),
            max_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature"),
            context=kwargs.get("context")
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive framework status."""
        return {
            "mode": self.mode.value,
            "providers": await self.providers.get_status(),
            "batching": await self.batching.get_status() if self.batching else None,
            "intervention": await self.intervention.get_status() if self.intervention else None,
            "metrics": await self.metrics.get_summary(),
            "config": self.config.to_dict()
        }

    async def optimize_for_cost(self) -> Dict[str, Any]:
        """Optimize configuration for cost efficiency."""
        optimizations = {}

        # Provider optimization
        provider_opt = await self.providers.optimize_for_cost()
        optimizations.update(provider_opt)

        # Batching optimization
        if self.batching:
            batch_opt = await self.batching.optimize_for_cost()
            optimizations.update(batch_opt)

        return optimizations

    async def shutdown(self):
        """Gracefully shutdown the framework."""
        self.logger.info("🛑 Shutting down AI Framework...")

        if self.batching:
            await self.batching.shutdown()

        if self.intervention:
            await self.intervention.shutdown()

        await self.providers.shutdown()
        await self.metrics.shutdown()

        self.logger.info("✅ AI Framework shutdown complete")

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()
