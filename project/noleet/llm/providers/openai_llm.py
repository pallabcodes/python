"""OpenAI LLM provider implementation."""

import logging
from typing import Any, Optional
from .mock_llm import MockLLM


class OpenAILLM(MockLLM):
    """OpenAI LLM implementation using ChatGPT."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "gpt-4",
        temperature: float = 0.1,
        max_tokens: int = 1000,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            logger: Optional logger instance
        """
        super().__init__(model, logger)
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._client: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if OpenAI LLM is available."""
        if not self._api_key:
            return False

        try:
            self._get_client()
            return self._client is not None
        except Exception:
            return False

    def _get_client(self) -> Any:
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key,
                    timeout=self._timeout
                )
            except ImportError:
                self._logger.warning("OpenAI package not installed")
                return None
        return self._client

    def _generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        client = self._get_client()
        if not client:
            return self._get_mock_response(prompt)

        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content
            return content if content else ""

        except Exception as e:
            self._logger.error(f"OpenAI API error: {e}")
            return self._get_mock_response(prompt)

    def _get_mock_response(self, prompt: str) -> str:
        """Get mock response when API is unavailable."""
        self._logger.warning("Using mock response - OpenAI API unavailable")
        return f"Mock response for: {prompt[:100]}..."

