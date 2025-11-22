"""SentenceTransformers embedder implementation."""

import logging
from typing import List, Optional, Any
from ..llm_base import EmbedderBase


class SentenceTransformersEmbedder(EmbedderBase):
    """SentenceTransformers embeddings implementation."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize SentenceTransformers embedder.

        Args:
            model_name: Model name (e.g., 'all-MiniLM-L6-v2')
            device: Device to run on ('cpu', 'cuda')
            logger: Optional logger instance
        """
        super().__init__(model_name, logger)
        self._model_name = model_name
        self._device = device
        self._model: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if SentenceTransformers embedder is available."""
        try:
            self._get_model()
            return self._model is not None
        except Exception:
            return False

    def _get_model(self) -> Any:
        """Get or create SentenceTransformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name, device=self._device)
            except ImportError:
                self._logger.warning("sentence-transformers package not installed")
                return None
        return self._model

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        model = self._get_model()
        if not model:
            return self._get_mock_embeddings(len(texts))

        try:
            embeddings = model.encode(texts, convert_to_list=True)
            self._logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            self._logger.error(f"SentenceTransformers embedding error: {e}")
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

    def _get_mock_embeddings(self, count: int, dim: int = 384) -> List[List[float]]:
        """Generate mock embeddings for fallback."""
        import random
        return [[random.random() for _ in range(dim)] for _ in range(count)]

