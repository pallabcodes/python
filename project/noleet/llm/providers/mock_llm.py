"""Mock LLM implementation for testing and fallbacks."""

import logging
from typing import Optional
from ..llm_base import LLMBase


class MockLLM(LLMBase):
    """Mock LLM for testing and fallback scenarios."""

    def __init__(
        self,
        model_name: str = "mock-llm",
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize mock LLM.

        Args:
            model_name: Mock model name
            logger: Optional logger instance
        """
        super().__init__(model_name, logger)
        self._responses = {
            "sentiment": "The text appears to be neutral in sentiment.",
            "difficulty": "The question appears to be of intermediate difficulty.",
            "topics": "The main topics appear to be: algorithms, data structures.",
            "recommendation": "Based on your interests, I recommend exploring dynamic programming projects.",
            "analysis": "The code appears to be well-structured and follows good practices."
        }

    def is_available(self) -> bool:
        """Mock LLM is always available."""
        return True

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate mock response based on prompt content.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (ignored)

        Returns:
            Mock response
        """
        prompt_lower = prompt.lower()

        # Try to match prompt to predefined responses
        for key, response in self._responses.items():
            if key in prompt_lower:
                self._logger.debug(f"Mock response for '{key}': {response[:50]}...")
                return response

        # Generic response
        response = f"Mock LLM response for prompt: {prompt[:100]}..."
        self._logger.debug(f"Generic mock response: {response[:50]}...")
        return response

