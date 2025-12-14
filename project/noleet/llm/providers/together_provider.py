"""Together AI API provider for NoLeet."""

import logging
import time
from typing import Dict, Any, Optional, List
import requests
from ..llm_base import LLMProvider


class TogetherProvider(LLMProvider):
    """Together AI API provider with free tier support."""

    PROVIDER_NAME = "together"
    BASE_URL = "https://api.together.xyz/v1"

    MODELS = {
        "meta-llama/Llama-2-70b-chat-hf": {
            "context_window": 4096,
            "max_output": 2048,
            "rate_limit": 1,  # Very limited free tier
            "quality_score": 0.88,
            "cost_per_token": 0  # Free tier
        },
        "codellama/CodeLlama-34b-Instruct-hf": {
            "context_window": 16384,
            "max_output": 2048,
            "rate_limit": 1,
            "quality_score": 0.82,
            "cost_per_token": 0
        },
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {
            "context_window": 32768,
            "max_output": 4096,
            "rate_limit": 1,
            "quality_score": 0.90,
            "cost_per_token": 0
        },
        "Qwen/Qwen1.5-72B-Chat": {
            "context_window": 32768,
            "max_output": 4096,
            "rate_limit": 1,
            "quality_score": 0.86,
            "cost_per_token": 0
        }
    }

    def __init__(
        self,
        api_key: str,
        model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Together AI provider.

        Args:
            api_key: Together AI API key
            model: Model name
            logger: Optional logger
        """
        super().__init__(logger)
        self._api_key = api_key
        self._model_name = model
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        self._last_request_time = 0
        self._request_count = 0
        self._reset_time = time.time()

        self._logger.info(f"Initialized Together AI provider with model {model}")

    def is_available(self) -> bool:
        """Check if Together AI is available."""
        try:
            # Simple health check
            response = self._session.get(f"{self.BASE_URL}/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using Together AI.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        self._enforce_rate_limit()

        try:
            payload = {
                "model": self._model_name,
                "prompt": prompt,
                "max_tokens": kwargs.get('max_tokens', self.MODELS[self._model_name]["max_output"]),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.9),
                "top_k": kwargs.get('top_k', 50),
                "repetition_penalty": kwargs.get('repetition_penalty', 1.1),
                "stop": kwargs.get('stop', [])
            }

            response = self._session.post(
                f"{self.BASE_URL}/completions",
                json=payload,
                timeout=60
            )

            self._update_rate_tracking()

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["text"].strip()
                else:
                    raise ValueError("No completion choices in response")
            else:
                raise ValueError(f"API error: {response.status_code} - {response.text}")

        except Exception as e:
            self._logger.error(f"Together AI generation failed: {e}")
            raise

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting (very conservative for free tier)."""
        model_config = self.MODELS[self._model_name]
        rate_limit = model_config["rate_limit"]  # Usually 1 RPM

        current_time = time.time()

        # Reset counter if minute has passed
        if current_time - self._reset_time >= 60:
            self._request_count = 0
            self._reset_time = current_time

        # Check if we need to wait
        if self._request_count >= rate_limit:
            wait_time = 60 - (current_time - self._reset_time)
            if wait_time > 0:
                self._logger.info(f"Together AI rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self._request_count = 0
                self._reset_time = time.time()

        # Minimum delay between requests (2 seconds for safety)
        time_since_last = current_time - self._last_request_time
        if time_since_last < 2.0:
            time.sleep(2.0 - time_since_last)

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
