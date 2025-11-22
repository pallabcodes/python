"""Text embedder for semantic search operations."""

import logging
from typing import List, Optional
from .llm_factory import LLMFactory
from .llm_config import LLMConfig
from .llm_base import EmbedderBase


class TextEmbedder:
    """High-level text embedder interface."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        factory: Optional[LLMFactory] = None,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize text embedder.

        Args:
            config: LLM configuration
            factory: LLM factory instance
            logger: Optional logger instance
        """
        self._config = config or LLMConfig()
        self._factory = factory or LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)
        self._embedder: Optional[EmbedderBase] = None

    def _get_embedder(self) -> EmbedderBase:
        """Get or create embedder instance."""
        if self._embedder is None or not self._embedder.is_available():
            self._embedder = self._factory.create_embedder()
        return self._embedder

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embedder = self._get_embedder()
        return embedder.embed(texts)

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query.

        Args:
            query: Query text

        Returns:
            Query embedding
        """
        embedder = self._get_embedder()
        return embedder.embed_query(query)

    def find_similar(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[tuple[str, float]]:
        """
        Find most similar documents to query.

        Args:
            query: Query text
            documents: List of document texts
            top_k: Number of top results to return

        Returns:
            List of (document, similarity_score) tuples
        """
        embedder = self._get_embedder()

        query_embedding = embedder.embed_query(query)
        doc_embeddings = embedder.embed(documents)
        similarities = embedder.similarity(query_embedding, doc_embeddings)

        # Sort by similarity (descending)
        results = list(zip(documents, similarities))
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def is_available(self) -> bool:
        """Check if embedder is available."""
        try:
            embedder = self._get_embedder()
            return embedder.is_available()
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        """Get current embedder model name."""
        embedder = self._get_embedder()
        return embedder.model_name

    @property
    def provider(self) -> str:
        """Get current embedder provider."""
        return self._config.embedding_provider

