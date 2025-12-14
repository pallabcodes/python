"""Base classes for LLM operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
import functools
import hashlib
import json
from datetime import datetime

# Import caching for performance optimization
try:
    from ..core.cache import get_llm_cache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False


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

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response with optional caching.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        # Check for cache control in kwargs
        use_cache = kwargs.pop('use_cache', True)
        cache_ttl = kwargs.pop('cache_ttl', 3600)  # 1 hour default

        if use_cache and CACHING_AVAILABLE:
            cache = get_llm_cache()
            cache_key = self._generate_cache_key(prompt, kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                self._logger.debug(f"LLM cache hit for key: {cache_key[:16]}...")
                return cached_result

            # Generate response
            result = self._generate_response(prompt, **kwargs)

            # Cache the result
            try:
                cache.set(cache_key, result, ttl=cache_ttl)
                self._logger.debug(f"Cached LLM response for key: {cache_key[:16]}...")
            except Exception as e:
                self._logger.warning(f"Failed to cache LLM response: {e}")

            return result
        else:
            return self._generate_response(prompt, **kwargs)

    @abstractmethod
    def _generate_response(self, prompt: str, **kwargs) -> str:
        """
        Internal method for generating text response.
        Must be implemented by subclasses.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        pass

    def _generate_cache_key(self, prompt: str, kwargs: Dict[str, Any]) -> str:
        """Generate a cache key for the LLM request."""
        # Create a deterministic key from prompt and parameters
        key_data = {
            'model': self._model_name,
            'prompt': prompt[:1000],  # Limit prompt length for key
            'kwargs': {k: v for k, v in kwargs.items() if k not in ['api_key', 'token']}  # Exclude sensitive data
        }

        # Create hash of the key data
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

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

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts with optional caching.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (one per text)
        """
        if CACHING_AVAILABLE:
            cache = get_llm_cache()
            uncached_texts = []
            cached_embeddings = []
            cache_keys = []

            # Check cache for each text
            for text in texts:
                cache_key = self._generate_embed_cache_key(text)
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    cached_embeddings.append((texts.index(text), cached_result))
                else:
                    uncached_texts.append(text)
                    cache_keys.append(cache_key)

            # Generate embeddings for uncached texts
            if uncached_texts:
                embeddings = self._embed_texts(uncached_texts)

                # Cache the results
                for key, embedding in zip(cache_keys, embeddings):
                    try:
                        cache.set(key, embedding, ttl=7200)  # 2 hours for embeddings
                    except Exception as e:
                        self._logger.warning(f"Failed to cache embedding: {e}")

                # Merge cached and new embeddings
                result = [None] * len(texts)
                for i, embedding in cached_embeddings:
                    result[i] = embedding

                uncached_idx = 0
                for i, item in enumerate(result):
                    if item is None:
                        result[i] = embeddings[uncached_idx]
                        uncached_idx += 1

                return result
            else:
                # All results were cached
                return [embedding for _, embedding in sorted(cached_embeddings, key=lambda x: x[0])]
        else:
            return self._embed_texts(texts)

    @abstractmethod
    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Internal method for generating embeddings.
        Must be implemented by subclasses.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (one per text)
        """
        pass

    def _generate_embed_cache_key(self, text: str) -> str:
        """Generate a cache key for text embedding."""
        key_data = {
            'model': self._model_name,
            'text': text[:500],  # Limit text length for key
            'operation': 'embed'
        }

        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

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

