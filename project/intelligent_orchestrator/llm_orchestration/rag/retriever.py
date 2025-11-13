"""RAG retriever for similar optimization cases."""

from typing import Any, Dict, List, Optional
import logging

from .knowledge_base import KnowledgeBase


class RAGRetriever:
    """RAG retriever for finding similar optimization cases."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize RAG retriever.

        Args:
            knowledge_base: Knowledge base instance
            logger: Optional logger instance
        """
        self._knowledge_base = knowledge_base
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info("RAG retriever initialized")

    def retrieve(
        self,
        query: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve similar cases from knowledge base.

        Args:
            query: Query dictionary with workload info
            limit: Maximum number of results

        Returns:
            List of retrieved cases with relevance scores
        """
        try:
            cases = self._knowledge_base.search_similar(query, limit)
            enriched = self._enrich_cases(cases, query)
            self._logger.info(f"Retrieved {len(enriched)} cases")
            return enriched
        except Exception as e:
            self._logger.error(f"Retrieval failed: {e}")
            return []

    def _enrich_cases(
        self,
        cases: List[Dict[str, Any]],
        query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enrich cases with relevance information.

        Args:
            cases: List of cases
            query: Original query

        Returns:
            Enriched cases with relevance scores
        """
        enriched = []
        for case in cases:
            enriched_case = {
                **case,
                "relevance_score": self._calculate_relevance(case, query)
            }
            enriched.append(enriched_case)
        return sorted(enriched, key=lambda x: x["relevance_score"], reverse=True)

    def _calculate_relevance(
        self,
        case: Dict[str, Any],
        query: Dict[str, Any]
    ) -> float:
        """Calculate relevance score between case and query.

        Args:
            case: Case dictionary
            query: Query dictionary

        Returns:
            Relevance score (0.0 to 1.0)
        """
        return 0.5

