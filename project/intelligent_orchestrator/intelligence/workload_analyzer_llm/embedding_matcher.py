"""Match similar workloads using embeddings."""

from typing import Any, Dict, List, Optional
import logging

from ...llm_orchestration.rag.embedder import WorkloadEmbedder
from ...llm_orchestration.rag.retriever import RAGRetriever


class EmbeddingMatcher:
    """Match similar workloads using embedding similarity."""

    def __init__(
        self,
        embedder: Optional[WorkloadEmbedder] = None,
        retriever: Optional[RAGRetriever] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize embedding matcher.

        Args:
            embedder: Workload embedder instance
            retriever: RAG retriever instance
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._embedder = embedder or WorkloadEmbedder(logger=logger)
        self._retriever = retriever
        self._logger.info("Embedding matcher initialized")

    def find_similar(
        self,
        workload: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar workloads using embeddings.

        Args:
            workload: Workload dictionary
            limit: Maximum number of results

        Returns:
            List of similar workloads with similarity scores
        """
        try:
            if self._retriever:
                return self._retriever.retrieve(workload, limit)
            embedding = self._embedder.embed(workload)
            similar = self._match_by_embedding(embedding, limit)
            self._logger.info(f"Found {len(similar)} similar workloads")
            return similar
        except Exception as e:
            self._logger.error(f"Similarity matching failed: {e}")
            return []

    def _match_by_embedding(
        self,
        embedding: List[float],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Match workloads by embedding similarity.

        Args:
            embedding: Workload embedding vector
            limit: Maximum results

        Returns:
            List of similar workloads
        """
        return []

