"""Intelligent provider router for multi-API LLM orchestration."""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from .llm_base import LLMProvider
from .batch_processor import BatchProcessor, BatchConfig, BatchRequest, BatchResult, BatchStrategy


class QualityRequirement(Enum):
    """Quality requirements for LLM responses."""
    BASIC = 0.6      # Basic understanding, simple tasks
    STANDARD = 0.75  # Good quality, most use cases
    HIGH = 0.85      # High quality, important recommendations
    PREMIUM = 0.95   # Premium quality, critical decisions


class ProviderRouter:
    """Intelligent router for multiple LLM providers with fallback chains."""

    def __init__(
        self,
        providers: Dict[str, LLMProvider],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize provider router.

        Args:
            providers: Dictionary of provider instances
            logger: Optional logger
        """
        self._providers = providers
        self._logger = logger or logging.getLogger(__name__)

        # Quality routing preferences
        self._quality_routing = {
            QualityRequirement.BASIC: ["gemini", "together", "huggingface", "ollama"],
            QualityRequirement.STANDARD: ["gemini", "together", "openai", "ollama"],
            QualityRequirement.HIGH: ["gemini", "together", "openai", "anthropic"],
            QualityRequirement.PREMIUM: ["openai", "anthropic", "gemini", "together"]
        }

        # Performance tracking
        self._performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self._provider_status: Dict[str, Dict[str, Any]] = {}

        # Batching support (optional for beta)
        self._batch_processor: Optional[BatchProcessor] = None
        self._batching_enabled = False

        # Update initial status
        self._update_provider_status()

    def enable_beta_batching(
        self,
        max_batch_size: int = 3,
        max_wait_time: float = 15.0,
        strategy: BatchStrategy = BatchStrategy.HYBRID
    ):
        """
        Enable batching for beta testing to work around rate limits.

        Args:
            max_batch_size: Maximum requests per batch
            max_wait_time: Maximum seconds to wait for batch
            strategy: Batching strategy to use
        """
        batch_config = BatchConfig(
            strategy=strategy,
            max_batch_size=max_batch_size,
            max_wait_time=max_wait_time,
            enabled=True
        )

        async def process_batch(requests: List[BatchRequest]) -> List[BatchResult]:
            """Process a batch of requests."""
            results = []
            for request in requests:
                try:
                    # Use the normal routing for each request in the batch
                    response, provider = self.generate_with_fallback(
                        prompt=request.prompt,
                        quality_requirement=QualityRequirement(request.quality_requirement.upper()),
                        max_retries=2,  # Fewer retries in batch mode
                        batch_mode=True
                    )

                    results.append(BatchResult(
                        request_id=request.request_id,
                        response=response,
                        success=True,
                        processing_time=time.time() - request.timestamp
                    ))

                except Exception as e:
                    results.append(BatchResult(
                        request_id=request.request_id,
                        response="",
                        success=False,
                        processing_time=time.time() - request.timestamp,
                        error_message=str(e)
                    ))

            return results

        # Create the batch processor
        import asyncio
        if asyncio.iscoroutinefunction(process_batch):
            # Handle async function properly
            self._batch_processor = BatchProcessor(batch_config, process_batch, self._logger)
        else:
            # For sync usage, we'll need to adapt
            async def async_wrapper(requests):
                return await process_batch(requests)
            self._batch_processor = BatchProcessor(batch_config, async_wrapper, self._logger)

        self._batching_enabled = True
        self._logger.info(f"Enabled beta batching: {strategy.value}, size={max_batch_size}, wait={max_wait_time}s")

    def disable_batching(self):
        """Disable batching and return to normal operation."""
        self._batching_enabled = False
        if self._batch_processor:
            # Note: In real implementation, you'd want to flush pending requests
            self._batch_processor = None
        self._logger.info("Disabled batching, back to normal operation")

    async def generate_batch_async(
        self,
        request_id: str,
        prompt: str,
        quality_requirement: QualityRequirement = QualityRequirement.STANDARD
    ) -> str:
        """
        Generate response using batching (async version for beta).

        Args:
            request_id: Unique request identifier
            prompt: Input prompt
            quality_requirement: Required quality level

        Returns:
            Generated response
        """
        if not self._batching_enabled or not self._batch_processor:
            # Fall back to normal processing
            response, _ = self.generate_with_fallback(prompt, quality_requirement)
            return response

        # Submit to batch processor
        await self._batch_processor.submit_request(
            request_id=request_id,
            prompt=prompt,
            quality_requirement=quality_requirement.name.lower()
        )

        # In a real implementation, you'd have a way to retrieve results
        # For now, return a placeholder
        return f"Batched request {request_id} submitted for processing"

    def generate_with_fallback(
        self,
        prompt: str,
        quality_requirement: QualityRequirement = QualityRequirement.STANDARD,
        max_retries: int = 3,
        batch_mode: bool = False,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Generate response with intelligent provider selection and fallback.

        Args:
            prompt: Input prompt
            quality_requirement: Required quality level
            max_retries: Maximum retry attempts
            batch_mode: Whether this is part of a batch operation (affects rate limiting)
            **kwargs: Additional parameters

        Returns:
            Tuple of (response, provider_used)
        """
        provider_order = self._quality_routing[quality_requirement]

        # Skip rate limiting in batch mode (handled at batch level)
        if not batch_mode:
            self._enforce_rate_limit()

        for provider_name in provider_order:
            if provider_name not in self._providers:
                continue

            provider = self._providers[provider_name]

            # Check if provider is available and not rate limited
            if not self._is_provider_available(provider_name):
                self._logger.debug(f"Provider {provider_name} not available, skipping")
                continue

            # Attempt generation
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    response = provider.generate(prompt, **kwargs)
                    response_time = time.time() - start_time

                    # Track performance
                    self._track_performance(provider_name, True, response_time, len(prompt), len(response))

                    self._logger.info(f"Successfully generated response using {provider_name}")
                    return response, provider_name

                except Exception as e:
                    error_msg = str(e)
                    self._logger.warning(f"Attempt {attempt + 1} failed for {provider_name}: {error_msg}")

                    # Track failure
                    self._track_performance(provider_name, False, 0, len(prompt), 0, error_msg)

                    # If rate limited, mark as unavailable for a while
                    if "rate limit" in error_msg.lower() or "429" in error_msg:
                        self._mark_provider_rate_limited(provider_name, 60)  # 1 minute cooldown

                    # If it's the last attempt or a permanent error, try next provider
                    if attempt == max_retries - 1:
                        break

                    # Wait before retry (shorter in batch mode)
                    wait_time = min(2 ** attempt, 10) if not batch_mode else min(2 ** attempt, 2)
                    time.sleep(wait_time)

        # All providers failed
        self._logger.error("All providers failed, falling back to manual intervention")
        raise RuntimeError("All LLM providers failed. Manual intervention required.")

    def _is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is currently available."""
        if provider_name not in self._providers:
            return False

        provider = self._providers[provider_name]
        status = self._provider_status.get(provider_name, {})

        # Check basic availability
        if not provider.is_available():
            return False

        # Check rate limiting
        rate_limited_until = status.get("rate_limited_until", 0)
        if time.time() < rate_limited_until:
            return False

        # Check recent failure rate (if > 50% failures in last 10 attempts, mark unavailable)
        recent_performance = self._performance_history.get(provider_name, [])[-10:]
        if recent_performance:
            failure_rate = sum(1 for p in recent_performance if not p["success"]) / len(recent_performance)
            if failure_rate > 0.5:
                self._logger.warning(f"High failure rate for {provider_name}: {failure_rate:.1%}")
                return False

        return True

    def _track_performance(
        self,
        provider_name: str,
        success: bool,
        response_time: float,
        prompt_tokens: int,
        completion_tokens: int,
        error: Optional[str] = None
    ) -> None:
        """Track provider performance metrics."""
        if provider_name not in self._performance_history:
            self._performance_history[provider_name] = []

        performance_record = {
            "timestamp": time.time(),
            "success": success,
            "response_time": response_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "error": error
        }

        self._performance_history[provider_name].append(performance_record)

        # Keep only last 100 records per provider
        if len(self._performance_history[provider_name]) > 100:
            self._performance_history[provider_name] = self._performance_history[provider_name][-100:]

    def _mark_provider_rate_limited(self, provider_name: str, cooldown_seconds: int) -> None:
        """Mark provider as rate limited."""
        if provider_name not in self._provider_status:
            self._provider_status[provider_name] = {}

        self._provider_status[provider_name]["rate_limited_until"] = time.time() + cooldown_seconds
        self._logger.info(f"Marked {provider_name} as rate limited for {cooldown_seconds} seconds")

    def _update_provider_status(self) -> None:
        """Update status information for all providers."""
        for provider_name, provider in self._providers.items():
            try:
                info = provider.get_provider_info()
                self._provider_status[provider_name] = {
                    **info,
                    "last_updated": time.time(),
                    "available": provider.is_available()
                }
            except Exception as e:
                self._logger.error(f"Failed to update status for {provider_name}: {e}")
                self._provider_status[provider_name] = {
                    "available": False,
                    "error": str(e),
                    "last_updated": time.time()
                }

    def get_provider_recommendation(
        self,
        quality_requirement: QualityRequirement,
        prompt_complexity: float = 0.5
    ) -> str:
        """
        Get recommended provider for given requirements.

        Args:
            quality_requirement: Required quality level
            prompt_complexity: Prompt complexity (0.0-1.0)

        Returns:
            Recommended provider name
        """
        provider_order = self._quality_routing[quality_requirement]

        # Score providers based on multiple factors
        best_provider = None
        best_score = -1

        for provider_name in provider_order:
            if not self._is_provider_available(provider_name):
                continue

            score = self._calculate_provider_score(provider_name, quality_requirement, prompt_complexity)

            if score > best_score:
                best_score = score
                best_provider = provider_name

        return best_provider or "manual_intervention"

    def _calculate_provider_score(
        self,
        provider_name: str,
        quality_requirement: QualityRequirement,
        prompt_complexity: float
    ) -> float:
        """Calculate overall score for provider selection."""
        status = self._provider_status.get(provider_name, {})
        performance = self._performance_history.get(provider_name, [])

        score = 0.0

        # Quality alignment (40% weight)
        provider_quality = status.get("quality_score", 0.5)
        required_quality = quality_requirement.value
        quality_alignment = 1.0 - abs(provider_quality - required_quality)
        score += quality_alignment * 0.4

        # Performance reliability (30% weight)
        if performance:
            recent_performance = performance[-10:]  # Last 10 requests
            success_rate = sum(1 for p in recent_performance if p["success"]) / len(recent_performance)
            avg_response_time = sum(p["response_time"] for p in recent_performance if p["success"]) / max(1, sum(1 for p in recent_performance if p["success"]))

            # Favor high success rate and reasonable response time
            reliability_score = success_rate * (1.0 if avg_response_time < 10 else 0.5)
            score += reliability_score * 0.3
        else:
            # No performance history, assume neutral
            score += 0.5 * 0.3

        # Cost efficiency (20% weight)
        cost = status.get("cost_per_token", 0.0)
        if cost == 0:  # Free tier
            score += 1.0 * 0.2
        elif cost < 0.001:  # Very cheap
            score += 0.8 * 0.2
        elif cost < 0.01:  # Reasonable
            score += 0.5 * 0.2
        else:  # Expensive
            score += 0.2 * 0.2

        # Availability bonus (10% weight)
        if status.get("available", False):
            score += 1.0 * 0.1
        else:
            score += 0.0 * 0.1

        return score

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics."""
        stats = {
            "providers": {},
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "provider_usage": {}
        }

        total_response_time = 0.0

        for provider_name, performance in self._performance_history.items():
            provider_stats = {
                "total_requests": len(performance),
                "successful_requests": sum(1 for p in performance if p["success"]),
                "failed_requests": sum(1 for p in performance if not p["success"]),
                "average_response_time": 0.0,
                "success_rate": 0.0,
                "recent_failures": sum(1 for p in performance[-5:] if not p["success"])
            }

            if provider_stats["total_requests"] > 0:
                provider_stats["success_rate"] = provider_stats["successful_requests"] / provider_stats["total_requests"]

                successful_times = [p["response_time"] for p in performance if p["success"]]
                if successful_times:
                    provider_stats["average_response_time"] = sum(successful_times) / len(successful_times)

            stats["providers"][provider_name] = provider_stats
            stats["total_requests"] += provider_stats["total_requests"]
            stats["successful_requests"] += provider_stats["successful_requests"]
            stats["failed_requests"] += provider_stats["failed_requests"]
            total_response_time += provider_stats["average_response_time"] * provider_stats["successful_requests"]

        if stats["successful_requests"] > 0:
            stats["average_response_time"] = total_response_time / stats["successful_requests"]

        return stats

    def add_provider(self, name: str, provider: LLMProvider) -> None:
        """Add a new provider to the router."""
        self._providers[name] = provider
        self._performance_history[name] = []
        self._update_provider_status()
        self._logger.info(f"Added provider: {name}")

    def remove_provider(self, name: str) -> None:
        """Remove a provider from the router."""
        if name in self._providers:
            del self._providers[name]
            if name in self._performance_history:
                del self._performance_history[name]
            if name in self._provider_status:
                del self._provider_status[name]
            self._logger.info(f"Removed provider: {name}")

    def get_available_providers(self) -> List[str]:
        """Get list of currently available providers."""
        return [name for name in self._providers.keys() if self._is_provider_available(name)]

    def force_provider_refresh(self) -> None:
        """Force refresh of all provider statuses."""
        self._update_provider_status()
        self._logger.info("Refreshed all provider statuses")
