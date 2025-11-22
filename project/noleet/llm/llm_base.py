"""Base classes for LLM operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging


class LLMBase(ABC):
    """Abstract base class for LLM operations."""

    def __init__(self, model_name: str, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize LLM base.

        Args:
            model_name: Name of the LLM model
            logger: Optional logger instance
        """
        self._model_name = model_name
        self._logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM is available for use."""
        pass

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name


class LLMProvider(LLMBase):
    """Base class for LLM API providers with provider-specific features."""

    def __init__(
        self,
        model_name: str,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize LLM provider."""
        super().__init__(model_name, logger)

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information.

        Returns:
            Dictionary with provider details
        """
        return {
            "provider": self.__class__.__name__.replace("Provider", "").lower(),
            "model": self._model_name,
            "available": self.is_available(),
            "type": "llm_provider"
        }

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for a request.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        # Default implementation - override in subclasses
        return 0.0


class EmbedderBase(ABC):
    """Abstract base class for text embedding operations."""

    def __init__(self, model_name: str, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize embedder base.

        Args:
            model_name: Name of the embedding model
            logger: Optional logger instance
        """
        self._model_name = model_name
        self._logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (one per text)
        """
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if embedder is available for use."""
        pass

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name

    @abstractmethod
    def similarity(self, query_embedding: List[float], doc_embeddings: List[List[float]]) -> List[float]:
        """
        Calculate similarity scores between query and documents.

        Args:
            query_embedding: Query embedding
            doc_embeddings: Document embeddings

        Returns:
            Similarity scores (higher is more similar)
        """
        pass

