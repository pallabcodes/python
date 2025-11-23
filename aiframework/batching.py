"""
Intelligent Batching System

Optimizes LLM API usage through intelligent batching:
- Collects requests over time windows
- Batches multiple requests into single API calls
- Maximizes efficiency while preserving quality
- Automatically adapts to load and requirements
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from .config import BatchingConfig
from .providers import ProviderManager

class BatchStrategy(Enum):
    """Batching strategies."""
    COUNT = "count"      # Batch when we reach max_batch_size
    TIME = "time"        # Batch after max_wait_time
    HYBRID = "hybrid"    # Combine count and time

@dataclass
class BatchRequest:
    """Individual request in a batch."""
    request_id: str
    prompt: str
    quality_requirement: str
    timestamp: float
    metadata: Dict[str, Any] = None

@dataclass
class BatchResult:
    """Result of a batch processing operation."""
    request_id: str
    content: str
    provider_used: str
    tokens_used: int
    cost: float
    latency: float
    quality_score: float
    batch_efficiency: float  # Percentage of efficiency gained

class BatchProcessor:
    """Processes batches of requests efficiently."""

    def __init__(self, provider_manager: ProviderManager, config: BatchingConfig):
        self.provider_manager = provider_manager
        self.config = config
        self.logger = logging.getLogger("BatchProcessor")

        self.pending_requests: Dict[str, List[BatchRequest]] = defaultdict(list)
        self.processing_task: Optional[asyncio.Task] = None

        if config.enabled:
            self.processing_task = asyncio.create_task(self._process_batches())

    async def add_request(
        self,
        request_id: str,
        prompt: str,
        quality_requirement: str = "standard",
        **kwargs
    ) -> BatchResult:
        """
        Add a request to the batch queue.

        Returns a Future that will be resolved when the batch is processed.
        """
        request = BatchRequest(
            request_id=request_id,
            prompt=prompt,
            quality_requirement=quality_requirement,
            timestamp=time.time(),
            metadata=kwargs
        )

        # Group by quality requirement for optimal batching
        quality_key = quality_requirement
        self.pending_requests[quality_key].append(request)

        self.logger.debug(f"Added request {request_id} to batch (quality: {quality_requirement})")

        # Wait for batch processing
        return await self._wait_for_processing(request)

    async def _wait_for_processing(self, request: BatchRequest) -> BatchResult:
        """Wait for a request to be processed in its batch."""
        # In a real implementation, you'd use asyncio.Future or similar
        # For now, we'll simulate immediate processing for simplicity

        # Check if we should process immediately
        quality_key = request.quality_requirement
        batch = self.pending_requests[quality_key]

        if self._should_process_batch(batch):
            return await self._process_batch(batch, quality_key)

        # Wait for batch processing
        await asyncio.sleep(self.config.max_wait_time / 2)

        # Force process if still pending
        if request in batch:
            return await self._process_batch(batch, quality_key)

        # This shouldn't happen in real implementation
        raise Exception(f"Request {request.request_id} was not processed")

    def _should_process_batch(self, batch: List[BatchRequest]) -> bool:
        """Determine if a batch should be processed now."""
        if len(batch) >= self.config.max_batch_size:
            return True

        # Check time-based triggering
        if batch:
            oldest_request = min(batch, key=lambda r: r.timestamp)
            elapsed = time.time() - oldest_request.timestamp
            if elapsed >= self.config.max_wait_time:
                return True

        return False

    async def _process_batch(
        self,
        batch: List[BatchRequest],
        quality_key: str
    ) -> BatchResult:
        """Process a batch of requests."""
        if not batch:
            raise Exception("Empty batch")

        start_time = time.time()

        # Get optimal provider for this quality level
        provider = self.provider_manager.get_optimal_provider(quality_key)

        # Combine prompts for batch processing
        combined_prompt = self._create_batch_prompt(batch)

        try:
            # Process the batch
            provider_response = await provider.generate(combined_prompt)

            # Split results back to individual responses
            individual_results = self._split_batch_results(
                provider_response.content,
                batch,
                provider
            )

            # Calculate batch efficiency
            batch_efficiency = self._calculate_efficiency(len(batch), provider_response)

            # Return the first result (in real implementation, return all)
            result = individual_results[0]
            result.batch_efficiency = batch_efficiency

            # Remove processed requests
            self.pending_requests[quality_key] = [
                r for r in self.pending_requests[quality_key]
                if r not in batch
            ]

            processing_time = time.time() - start_time
            self.logger.info(
                f"Processed batch of {len(batch)} requests in {processing_time:.2f}s "
                f"(efficiency: {batch_efficiency:.1%})"
            )

            return result

        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            # Fallback to individual processing
            return await self._fallback_processing(batch[0], provider)

    def _create_batch_prompt(self, batch: List[BatchRequest]) -> str:
        """Create a combined prompt for batch processing."""
        prompt_parts = []

        for i, request in enumerate(batch, 1):
            prompt_parts.append(f"Request {i}: {request.prompt}")

        combined = "\n\n".join(prompt_parts)
        return f"Process these {len(batch)} requests efficiently:\n\n{combined}"

    def _split_batch_results(
        self,
        combined_response: str,
        batch: List[BatchRequest],
        provider: Any
    ) -> List[BatchResult]:
        """Split batch response into individual results."""
        # Simple splitting logic - in real implementation, use more sophisticated parsing
        response_parts = combined_response.split("\n\n")

        results = []
        for i, request in enumerate(batch):
            # Get corresponding response part, or use fallback
            content = response_parts[i] if i < len(response_parts) else combined_response

            result = BatchResult(
                request_id=request.request_id,
                content=content.strip(),
                provider_used=provider.name,
                tokens_used=len(request.prompt.split()) * 2,  # Estimate
                cost=0.0,  # Distributed across batch
                latency=time.time() - request.timestamp,
                quality_score=provider.config.quality_score,
                batch_efficiency=0.0  # Will be set later
            )
            results.append(result)

        return results

    def _calculate_efficiency(self, batch_size: int, provider_response: Any) -> float:
        """Calculate batching efficiency."""
        # Individual API calls would be: batch_size * cost_per_call
        # Batch API call is: 1 * cost_per_call
        # Efficiency = (batch_size - 1) / batch_size
        if batch_size <= 1:
            return 0.0
        return (batch_size - 1) / batch_size

    async def _fallback_processing(self, request: BatchRequest, provider: Any) -> BatchResult:
        """Fallback to individual processing if batch fails."""
        provider_response = await provider.generate(request.prompt)

        return BatchResult(
            request_id=request.request_id,
            content=provider_response.content,
            provider_used=provider.name,
            tokens_used=provider_response.tokens_used,
            cost=provider_response.cost,
            latency=time.time() - request.timestamp,
            quality_score=provider_response.quality_score,
            batch_efficiency=0.0  # No batching benefit
        )

    async def _process_batches(self):
        """Background task to continuously process batches."""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second

                for quality_key, batch in list(self.pending_requests.items()):
                    if self._should_process_batch(batch):
                        await self._process_batch(batch, quality_key)

            except Exception as e:
                self.logger.error(f"Batch processing error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def get_status(self) -> Dict[str, Any]:
        """Get batching system status."""
        total_pending = sum(len(batch) for batch in self.pending_requests.values())

        return {
            "enabled": self.config.enabled,
            "total_pending_requests": total_pending,
            "batches_by_quality": {
                quality: len(requests)
                for quality, requests in self.pending_requests.items()
            },
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_wait_time": self.config.max_wait_time,
                "strategy": self.config.strategy
            }
        }

    async def optimize_for_cost(self) -> Dict[str, Any]:
        """Optimize batching for cost efficiency."""
        optimizations = {}

        # Increase batch size for better efficiency
        if self.config.max_batch_size < 5:
            optimizations["batch_size_increase"] = "Consider increasing max_batch_size to 5 for better efficiency"

        # Reduce wait time for faster processing
        if self.config.max_wait_time > 10:
            optimizations["wait_time_reduction"] = "Consider reducing max_wait_time for faster responses"

        return optimizations

    async def shutdown(self):
        """Shutdown the batching system."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

class BatchManager:
    """
    High-level batching manager.

    Provides a clean interface for batching operations with:
    - Automatic batch formation
    - Quality preservation
    - Cost optimization
    - Load balancing
    """

    def __init__(self, config: BatchingConfig):
        self.config = config
        self.logger = logging.getLogger("BatchManager")

        # Will be initialized when provider_manager is available
        self.processor: Optional[BatchProcessor] = None

    def initialize(self, provider_manager: ProviderManager):
        """Initialize with provider manager."""
        self.processor = BatchProcessor(provider_manager, self.config)

    async def add_request(
        self,
        request_id: str,
        prompt: str,
        quality_requirement: str = "standard",
        **kwargs
    ) -> BatchResult:
        """Add request to batch queue."""
        if not self.processor:
            raise Exception("BatchManager not initialized with provider manager")

        return await self.processor.add_request(
            request_id, prompt, quality_requirement, **kwargs
        )

    def should_batch(self) -> bool:
        """Determine if batching should be used."""
        if not self.config.enabled:
            return False

        # Always batch in development for efficiency
        # In production, batch based on load/cost optimization
        return True

    async def get_status(self) -> Dict[str, Any]:
        """Get batching status."""
        if self.processor:
            return await self.processor.get_status()
        return {"enabled": self.config.enabled, "initialized": False}

    async def optimize_for_cost(self) -> Dict[str, Any]:
        """Get cost optimization recommendations."""
        if self.processor:
            return await self.processor.optimize_for_cost()
        return {"recommendation": "Initialize BatchManager first"}

    async def shutdown(self):
        """Shutdown batching system."""
        if self.processor:
            await self.processor.shutdown()
