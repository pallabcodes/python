"""OpenAI embedder implementation."""

import logging
from typing import List, Optional, Any
from ..llm_base import EmbedderBase


class OpenAIEmbedder(EmbedderBase):
    """OpenAI embeddings implementation."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "text-embedding-ada-002",
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize OpenAI embedder.

        Args:
            api_key: OpenAI API key
            model: Embedding model name
            logger: Optional logger instance
        """
        super().__init__(model, logger)
        self._api_key = api_key
        self._model = model
        self._client: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if OpenAI embedder is available."""
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
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                self._logger.warning("OpenAI package not installed")
                return None
        return self._client

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        client = self._get_client()
        if not client:
            return self._get_mock_embeddings(len(texts))

        try:
            response = client.embeddings.create(
                input=texts,
                model=self._model
            )

            embeddings = [data.embedding for data in response.data]
            self._logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            self._logger.error(f"OpenAI embedding error: {e}")
            return self._get_mock_embeddings(len(texts))

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for query.

        Args:
            query: Query text

        Returns:
            Query embedding
        """
        embeddings = self.embed([query])
        return embeddings[0] if embeddings else []

    def similarity(
        self,
        query_embedding: List[float],
        doc_embeddings: List[List[float]]
    ) -> List[float]:
        """
        Calculate cosine similarity scores.

        Args:
            query_embedding: Query embedding
            doc_embeddings: Document embeddings

        Returns:
            Similarity scores
        """
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            query_array = np.array(query_embedding).reshape(1, -1)
            doc_array = np.array(doc_embeddings)

            similarities = cosine_similarity(query_array, doc_array)[0]
            return similarities.tolist()

        except ImportError:
            self._logger.warning("NumPy or scikit-learn not available, using mock similarities")
            return [0.5] * len(doc_embeddings)

    def _get_mock_embeddings(self, count: int, dim: int = 1536) -> List[List[float]]:
        """Generate mock embeddings for fallback."""
        import random
        return [[random.random() for _ in range(dim)] for _ in range(count)]

