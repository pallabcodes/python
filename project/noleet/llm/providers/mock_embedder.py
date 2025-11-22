"""Mock embedder implementation for testing."""

import logging
from typing import List, Optional
from ..llm_base import EmbedderBase


class MockEmbedder(EmbedderBase):
    """Mock embedder for testing and fallback scenarios."""

    def __init__(
        self,
        model_name: str = "mock-embedder",
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize mock embedder.

        Args:
            model_name: Mock model name
            logger: Optional logger instance
        """
        super().__init__(model_name, logger)
        self._dimension = 384  # Standard embedding dimension

    def is_available(self) -> bool:
        """Mock embedder is always available."""
        return True

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings.

        Args:
            texts: List of texts to embed

        Returns:
            List of mock embeddings
        """
        import random
        embeddings = []
        for text in texts:
            # Generate deterministic mock embedding based on text hash
            random.seed(hash(text))
            embedding = [random.random() for _ in range(self._dimension)]
            embeddings.append(embedding)

        self._logger.debug(f"Generated {len(embeddings)} mock embeddings")
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Generate mock query embedding.

        Args:
            query: Query text

        Returns:
            Mock embedding
        """
        embeddings = self.embed([query])
        return embeddings[0] if embeddings else []

    def similarity(
        self,
        query_embedding: List[float],
        doc_embeddings: List[List[float]]
    ) -> List[float]:
        """
        Generate mock similarity scores.

        Args:
            query_embedding: Query embedding (ignored)
            doc_embeddings: Document embeddings (ignored)

        Returns:
            Mock similarity scores between 0.1 and 0.9
        """
        import random
        return [0.1 + random.random() * 0.8 for _ in doc_embeddings]

