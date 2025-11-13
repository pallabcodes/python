"""Knowledge base for optimization cases."""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.vectorstores import VectorStore
    from langchain.embeddings import OpenAIEmbeddings
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    VectorStore = None
    OpenAIEmbeddings = None


class KnowledgeBase:
    """Knowledge base for storing optimization cases."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize knowledge base.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._vector_store: Optional[Any] = None
        self._embeddings: Optional[Any] = None
        self._cases: List[Dict[str, Any]] = []
        self._initialize()

    def _initialize(self) -> None:
        """Initialize vector store and embeddings."""
        if not HAS_LANGCHAIN:
            self._logger.warning("LangChain not available, using mock store")
            return

        try:
            self._embeddings = OpenAIEmbeddings()
            self._vector_store = None
            self._logger.info("Knowledge base initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize knowledge base: {e}")

    def add_case(self, case: Dict[str, Any]) -> None:
        """Add optimization case to knowledge base.

        Args:
            case: Case dictionary with workload, strategy, results
        """
        self._cases.append(case)
        self._logger.info(f"Added case to knowledge base: {len(self._cases)} cases")

    def search_similar(
        self,
        query: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar optimization cases.

        Args:
            query: Query dictionary with workload characteristics
            limit: Maximum number of results

        Returns:
            List of similar cases
        """
        if not self._cases:
            return []

        query_text = self._extract_query_text(query)
        similar = self._find_similar_cases(query_text, limit)
        self._logger.info(f"Found {len(similar)} similar cases")
        return similar

    def _extract_query_text(self, query: Dict[str, Any]) -> str:
        """Extract text representation of query.

        Args:
            query: Query dictionary

        Returns:
            Text representation
        """
        workload = query.get("workload", {})
        return str(workload)

    def _find_similar_cases(
        self,
        query_text: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Find similar cases using simple matching.

        Args:
            query_text: Query text
            limit: Maximum results

        Returns:
            List of similar cases
        """
        return self._cases[:limit]

