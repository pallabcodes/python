"""Ollama LLM provider implementation."""

import logging
from typing import Any, Optional
from .mock_llm import MockLLM


class OllamaLLM(MockLLM):
    """Ollama LLM implementation for local models."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        temperature: float = 0.1,
        timeout: int = 60,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize Ollama LLM.

        Args:
            base_url: Ollama server base URL
            model: Model name (llama2, mistral, etc.)
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            logger: Optional logger instance
        """
        super().__init__(model, logger)
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._timeout = timeout
        self._client: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if Ollama LLM is available."""
        try:
            self._get_client()
            # Test with a simple request
            response = self._client.list()
            return len(response.get("models", [])) > 0
        except Exception:
            return False

    def _get_client(self) -> Any:
        """Get or create Ollama client."""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self._base_url)
            except ImportError:
                self._logger.warning("Ollama package not installed")
                return None
        return self._client

    def _generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama API."""
        client = self._get_client()
        if not client:
            return self._get_mock_response(prompt)

        try:
            response = client.generate(
                model=self._model,
                prompt=prompt,
                options={
                    "temperature": self._temperature,
                    "timeout": self._timeout
                },
                **kwargs
            )

            return response.get("response", "")

        except Exception as e:
            self._logger.error(f"Ollama API error: {e}")
            return self._get_mock_response(prompt)

    def _get_mock_response(self, prompt: str) -> str:
        """Get mock response when Ollama is unavailable."""
        self._logger.warning("Using mock response - Ollama unavailable")
        return f"Mock response for: {prompt[:100]}..."

