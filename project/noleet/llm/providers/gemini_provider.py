"""Google Gemini API provider for NoLeet."""

import logging
import time
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from ..llm_base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini API provider with free tier support."""

    PROVIDER_NAME = "gemini"
    MODELS = {
        "gemini-1.5-flash": {
            "context_window": 1048576,  # 1M tokens
            "max_output": 8192,
            "rate_limit": 60,  # requests per minute (free tier)
            "quality_score": 0.85,
            "cost_per_token": 0  # Free tier
        },
        "gemini-1.5-pro": {
            "context_window": 2097152,  # 2M tokens
            "max_output": 8192,
            "rate_limit": 60,
            "quality_score": 0.92,
            "cost_per_token": 0
        }
    }

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            model: Model name
            logger: Optional logger
        """
        super().__init__(logger)
        self._api_key = api_key
        self._model_name = model
        self._client = None
        self._last_request_time = 0
        self._request_count = 0
        self._reset_time = time.time()

        # Configure Gemini
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(model)

        self._logger.info(f"Initialized Gemini provider with model {model}")

    def is_available(self) -> bool:
        """Check if Gemini is available."""
        try:
            # Simple availability check
            return self._client is not None and self._api_key is not None
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using Gemini.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        self._enforce_rate_limit()

        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 0.9),
                top_k=kwargs.get('top_k', 40),
                max_output_tokens=self.MODELS[self._model_name]["max_output"],
                candidate_count=1
            )

            response = self._client.generate_content(
                prompt,
                generation_config=generation_config
            )

            self._update_rate_tracking()

            if response and response.text:
                return response.text.strip()
            else:
                raise ValueError("Empty response from Gemini")

        except Exception as e:
            self._logger.error(f"Gemini generation failed: {e}")
            raise

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting."""
        model_config = self.MODELS[self._model_name]
        rate_limit = model_config["rate_limit"]

        current_time = time.time()

        # Reset counter if minute has passed
        if current_time - self._reset_time >= 60:
            self._request_count = 0
            self._reset_time = current_time

        # Check if we need to wait
        if self._request_count >= rate_limit:
            wait_time = 60 - (current_time - self._reset_time)
            if wait_time > 0:
                self._logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self._request_count = 0
                self._reset_time = time.time()

        # Enforce minimum delay between requests (1 per second for safety)
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)

    def _update_rate_tracking(self) -> None:
        """Update rate tracking after successful request."""
        self._request_count += 1
        self._last_request_time = time.time()

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": self.PROVIDER_NAME,
            "model": self._model_name,
            "context_window": self.MODELS[self._model_name]["context_window"],
            "quality_score": self.MODELS[self._model_name]["quality_score"],
            "rate_limit": self.MODELS[self._model_name]["rate_limit"],
            "cost_per_token": self.MODELS[self._model_name]["cost_per_token"],
            "free_tier": True,
            "current_usage": {
                "requests_this_minute": self._request_count,
                "time_until_reset": max(0, 60 - (time.time() - self._reset_time))
            }
        }

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for request."""
        # Free tier - always 0
        return 0.0

    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        return list(self.MODELS.keys())
