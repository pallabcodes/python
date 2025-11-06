"""
LLM Manager for unified language model management across providers.

Provides enterprise-grade LLM management with support for:
- Multiple providers (OpenAI, Anthropic, Hugging Face)
- Unified API interface
- Token usage tracking and cost management
- Model performance monitoring
- Fallback and retry mechanisms
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig


class TokenUsage(BaseModel):
    """Token usage tracking for LLM calls."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    model: str
    timestamp: datetime


class LLMResponse(BaseModel):
    """Standardized LLM response format."""

    content: str
    model: str
    usage: TokenUsage
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""

    provider: str  # openai, anthropic, huggingface, etc.
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class LLMManager:
    """
    Unified LLM management across multiple providers.

    Features:
    - Multi-provider support with automatic failover
    - Token usage tracking and cost management
    - Performance monitoring and metrics
    - Batch processing capabilities
    - Context management and conversation history
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize LLM manager.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.LLMManager")

        # Provider configurations
        self._providers: Dict[str, LLMConfig] = {}
        self._active_provider: Optional[str] = None

        # Usage tracking
        self._usage_history: List[TokenUsage] = []
        self._usage_file = self.config.data_dir / "llm_usage.json"

        # Client instances (lazy loaded)
        self._clients: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize LLM manager and validate configurations."""
        self.logger.info("Initializing LLM manager...")

        # Load usage history
        await self._load_usage_history()

        # Setup providers from config
        await self._setup_providers()

        # Test connections
        await self._validate_connections()

        self.logger.info(f"LLM manager initialized with {len(self._providers)} providers")

    async def _setup_providers(self) -> None:
        """Setup LLM providers from configuration."""
        # Primary provider from config
        if hasattr(self.config, 'llm') and self.config.llm.provider and self.config.llm.model_name:
            primary_config = LLMConfig(
                provider=self.config.llm.provider,
                model=self.config.llm.model_name,
                api_key=getattr(self.config.llm, 'api_key', None),
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            )
            self._providers[self.config.llm.provider] = primary_config
            self._active_provider = self.config.llm.provider
        else:
            # Setup default providers for demo
            self.logger.info("No LLM providers configured, setting up demo providers")
            demo_config = LLMConfig(
                provider="huggingface",
                model="microsoft/DialoGPT-small",
                temperature=0.7,
                max_tokens=50,  # Small for demo
            )
            self._providers["huggingface"] = demo_config
            self._active_provider = "huggingface"

        if not self._providers:
            self.logger.warning("No LLM providers configured")

    async def _validate_connections(self) -> None:
        """Validate connections to configured providers."""
        for provider_name, provider_config in self._providers.items():
            try:
                # Test connection with a simple prompt
                test_response = await self._call_provider(
                    provider_config,
                    "Hello, this is a test message. Please respond with 'OK'."
                )
                if test_response:
                    self.logger.info(f"Provider {provider_name} connection validated")
                else:
                    self.logger.warning(f"Provider {provider_name} test failed")
            except Exception as e:
                self.logger.error(f"Provider {provider_name} validation failed: {e}")

    async def _call_provider(
        self,
        provider_config: LLMConfig,
        prompt: str,
        **kwargs
    ) -> Optional[LLMResponse]:
        """
        Call a specific LLM provider.

        Args:
            provider_config: Provider configuration
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            LLM response or None if failed
        """
        provider = provider_config.provider

        try:
            if provider == "openai":
                return await self._call_openai(provider_config, prompt, **kwargs)
            elif provider == "anthropic":
                return await self._call_anthropic(provider_config, prompt, **kwargs)
            elif provider == "huggingface":
                return await self._call_huggingface(provider_config, prompt, **kwargs)
            else:
                self.logger.error(f"Unsupported provider: {provider}")
                return None

        except Exception as e:
            self.logger.error(f"Provider {provider} call failed: {e}")
            return None

    async def _call_openai(
        self,
        config: LLMConfig,
        prompt: str,
        **kwargs
    ) -> Optional[LLMResponse]:
        """Call OpenAI API."""
        try:
            import openai

            if not hasattr(self, '_openai_client') or not self._openai_client:
                self._openai_client = openai.AsyncOpenAI(api_key=config.api_key)

            messages = [{"role": "user", "content": prompt}]

            response = await self._openai_client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs
            )

            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                estimated_cost=self._calculate_openai_cost(
                    config.model, response.usage.prompt_tokens, response.usage.completion_tokens
                ),
                model=config.model,
                timestamp=datetime.now()
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=config.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason
            )

        except ImportError:
            self.logger.error("OpenAI package not installed")
            return None
        except Exception as e:
            self.logger.error(f"OpenAI call failed: {e}")
            return None

    async def _call_anthropic(
        self,
        config: LLMConfig,
        prompt: str,
        **kwargs
    ) -> Optional[LLMResponse]:
        """Call Anthropic API."""
        try:
            import anthropic

            if not hasattr(self, '_anthropic_client') or not self._anthropic_client:
                self._anthropic_client = anthropic.AsyncAnthropic(api_key=config.api_key)

            response = await self._anthropic_client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            # Estimate token usage (Anthropic doesn't provide exact counts)
            prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
            completion_tokens = len(response.content[0].text.split()) * 1.3

            usage = TokenUsage(
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                total_tokens=int(prompt_tokens + completion_tokens),
                estimated_cost=self._calculate_anthropic_cost(
                    config.model, int(prompt_tokens), int(completion_tokens)
                ),
                model=config.model,
                timestamp=datetime.now()
            )

            return LLMResponse(
                content=response.content[0].text,
                model=config.model,
                usage=usage,
                finish_reason=response.stop_reason
            )

        except ImportError:
            self.logger.error("Anthropic package not installed")
            return None
        except Exception as e:
            self.logger.error(f"Anthropic call failed: {e}")
            return None

    async def _call_huggingface(
        self,
        config: LLMConfig,
        prompt: str,
        **kwargs
    ) -> Optional[LLMResponse]:
        """Call Hugging Face model."""
        try:
            from transformers import pipeline

            # Use local model (would need model loading logic)
            model_key = f"huggingface_{config.model}"
            if model_key not in self._clients:
                # For demo, use a simple pipeline
                try:
                    self._clients[model_key] = pipeline(
                        "text-generation",
                        model=config.model,
                        device=-1  # CPU
                    )
                except Exception as e:
                    self.logger.error(f"Failed to load Hugging Face model {config.model}: {e}")
                    return None

            generator = self._clients[model_key]

            # Generate response
            outputs = generator(
                prompt,
                max_length=config.max_tokens,
                temperature=config.temperature,
                do_sample=True,
                pad_token_id=50256,  # Common pad token
                **kwargs
            )

            response_text = outputs[0]['generated_text'][len(prompt):].strip()

            # Estimate token usage
            prompt_tokens = len(prompt.split())
            completion_tokens = len(response_text.split())

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost=0.0,  # Local model, no API cost
                model=config.model,
                timestamp=datetime.now()
            )

            return LLMResponse(
                content=response_text,
                model=config.model,
                usage=usage
            )

        except ImportError:
            self.logger.error("Transformers package not installed")
            return None
        except Exception as e:
            self.logger.error(f"Hugging Face call failed: {e}")
            return None

    async def generate_text(
        self,
        prompt: str,
        provider: Optional[str] = None,
        fallback: bool = True,
        **kwargs
    ) -> Optional[LLMResponse]:
        """
        Generate text using configured LLM providers.

        Args:
            prompt: Input prompt
            provider: Specific provider to use (optional)
            fallback: Whether to fallback to other providers on failure
            **kwargs: Additional parameters

        Returns:
            LLM response or None if all providers failed
        """
        providers_to_try = []

        if provider and provider in self._providers:
            providers_to_try.append(provider)
        elif self._active_provider:
            providers_to_try.append(self._active_provider)

        if fallback:
            # Add all other providers as fallback
            for p in self._providers:
                if p not in providers_to_try:
                    providers_to_try.append(p)

        for provider_name in providers_to_try:
            provider_config = self._providers[provider_name]
            self.logger.debug(f"Trying provider: {provider_name}")

            response = await self._call_provider(provider_config, prompt, **kwargs)
            if response:
                # Track usage
                self._usage_history.append(response.usage)
                await self._save_usage_history()

                return response

        self.logger.error("All LLM providers failed")
        return None

    async def generate_batch(
        self,
        prompts: List[str],
        provider: Optional[str] = None,
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Optional[LLMResponse]]:
        """
        Generate text for multiple prompts concurrently.

        Args:
            prompts: List of input prompts
            provider: Provider to use
            max_concurrent: Maximum concurrent requests
            **kwargs: Additional parameters

        Returns:
            List of LLM responses
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(prompt: str) -> Optional[LLMResponse]:
            async with semaphore:
                return await self.generate_text(prompt, provider, **kwargs)

        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_responses = []
        for response in responses:
            if isinstance(response, Exception):
                self.logger.error(f"Batch generation error: {response}")
                valid_responses.append(None)
            else:
                valid_responses.append(response)

        return valid_responses

    def get_usage_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get usage statistics for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Usage statistics
        """
        cutoff_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - hours)

        recent_usage = [
            usage for usage in self._usage_history
            if usage.timestamp > cutoff_time
        ]

        if not recent_usage:
            return {"total_calls": 0, "total_tokens": 0, "total_cost": 0.0}

        total_tokens = sum(usage.total_tokens for usage in recent_usage)
        total_cost = sum(usage.estimated_cost for usage in recent_usage)

        return {
            "total_calls": len(recent_usage),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_tokens_per_call": total_tokens / len(recent_usage),
            "calls_by_model": self._group_usage_by_model(recent_usage),
            "cost_by_model": self._group_cost_by_model(recent_usage),
        }

    def _group_usage_by_model(self, usage_list: List[TokenUsage]) -> Dict[str, int]:
        """Group usage by model."""
        model_counts = {}
        for usage in usage_list:
            model_counts[usage.model] = model_counts.get(usage.model, 0) + 1
        return model_counts

    def _group_cost_by_model(self, usage_list: List[TokenUsage]) -> Dict[str, float]:
        """Group cost by model."""
        model_costs = {}
        for usage in usage_list:
            model_costs[usage.model] = model_costs.get(usage.model, 0.0) + usage.estimated_cost
        return model_costs

    def _calculate_openai_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate OpenAI API cost."""
        # Simplified pricing (would need to be updated)
        pricing = {
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
        }

        rates = pricing.get(model, {"prompt": 0.001, "completion": 0.002})
        return (prompt_tokens * rates["prompt"] + completion_tokens * rates["completion"]) / 1000

    def _calculate_anthropic_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate Anthropic API cost."""
        # Simplified pricing
        pricing = {
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
        }

        rates = pricing.get(model, {"prompt": 0.001, "completion": 0.005})
        return (prompt_tokens * rates["prompt"] + completion_tokens * rates["completion"]) / 1000

    async def _load_usage_history(self) -> None:
        """Load usage history from disk."""
        if self._usage_file.exists():
            try:
                with open(self._usage_file, "r") as f:
                    data = json.load(f)
                    self._usage_history = [TokenUsage(**item) for item in data]
                self.logger.info(f"Loaded {len(self._usage_history)} usage records")
            except Exception as e:
                self.logger.error(f"Failed to load usage history: {e}")

    async def _save_usage_history(self) -> None:
        """Save usage history to disk."""
        try:
            # Keep only recent history (last 10000 records)
            if len(self._usage_history) > 10000:
                self._usage_history = self._usage_history[-10000:]

            data = [usage.dict() for usage in self._usage_history]
            with open(self._usage_file, "w") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save usage history: {e}")

    async def shutdown(self) -> None:
        """Shutdown LLM manager."""
        self.logger.info("Shutting down LLM manager...")

        # Save final usage stats
        await self._save_usage_history()

        # Close any open clients
        self._clients.clear()

        self.logger.info("LLM manager shutdown complete")
