"""Embedding generation for workloads."""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.embeddings import OpenAIEmbeddings
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    OpenAIEmbeddings = None


class WorkloadEmbedder:
    """Generate embeddings for workload descriptions."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize workload embedder.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._embeddings: Optional[Any] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize embeddings model."""
        if not HAS_LANGCHAIN:
            self._logger.warning("LangChain not available, using mock embeddings")
            return

        try:
            self._embeddings = OpenAIEmbeddings()
            self._logger.info("Workload embedder initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize embedder: {e}")
            self._embeddings = None

    def embed(self, workload: Dict[str, Any]) -> List[float]:
        """Generate embedding for workload.

        Args:
            workload: Workload dictionary

        Returns:
            Embedding vector
        """
        if not self._embeddings:
            return self._mock_embedding(workload)

        try:
            text = self._extract_text(workload)
            embedding = self._embeddings.embed_query(text)
            self._logger.debug(f"Generated embedding of length {len(embedding)}")
            return embedding
        except Exception as e:
            self._logger.error(f"Embedding generation failed: {e}")
            return self._mock_embedding(workload)

    def embed_batch(self, workloads: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for multiple workloads.

        Args:
            workloads: List of workload dictionaries

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for workload in workloads:
            embedding = self.embed(workload)
            embeddings.append(embedding)
        return embeddings

    def _extract_text(self, workload: Dict[str, Any]) -> str:
        """Extract text representation from workload.

        Args:
            workload: Workload dictionary

        Returns:
            Text representation
        """
        code = workload.get("code", "")
        description = workload.get("description", "")
        return f"{code}\n{description}"

    def _mock_embedding(self, workload: Dict[str, Any]) -> List[float]:
        """Generate mock embedding when embeddings unavailable.

        Args:
            workload: Workload dictionary

        Returns:
            Mock embedding vector
        """
        return [0.0] * 1536

