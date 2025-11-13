"""Main LLM-powered workload analyzer."""

from typing import Any, Dict, Optional
import logging

from .code_analyzer import CodeAnalyzer
from .natural_language_analyzer import NaturalLanguageAnalyzer
from .embedding_matcher import EmbeddingMatcher


class WorkloadAnalyzerLLM:
    """Main analyzer combining code analysis, NLP, and embeddings."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize LLM-powered workload analyzer.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._code_analyzer = CodeAnalyzer(logger=logger)
        self._nlp_analyzer = NaturalLanguageAnalyzer(logger=logger)
        self._embedding_matcher = EmbeddingMatcher(logger=logger)
        self._logger.info("LLM-powered workload analyzer initialized")

    def analyze(self, workload: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive workload analysis using multiple methods.

        Args:
            workload: Workload dictionary with code and/or description

        Returns:
            Comprehensive analysis dictionary
        """
        try:
            code_analysis = self._analyze_code(workload)
            nlp_analysis = self._analyze_nlp(workload)
            similar = self._find_similar(workload)
            combined = self._combine_analyses(
                code_analysis,
                nlp_analysis,
                similar
            )
            self._logger.info("Comprehensive workload analysis completed")
            return combined
        except Exception as e:
            self._logger.error(f"Analysis failed: {e}")
            return self._default_analysis()

    def _analyze_code(self, workload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workload code.

        Args:
            workload: Workload dictionary

        Returns:
            Code analysis dictionary
        """
        code = workload.get("code", "")
        if code:
            return self._code_analyzer.analyze(code)
        return {}

    def _analyze_nlp(self, workload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workload using NLP.

        Args:
            workload: Workload dictionary

        Returns:
            NLP analysis dictionary
        """
        description = workload.get("description", "")
        if description:
            return self._nlp_analyzer.analyze(description)
        return {}

    def _find_similar(self, workload: Dict[str, Any]) -> list:
        """Find similar workloads.

        Args:
            workload: Workload dictionary

        Returns:
            List of similar workloads
        """
        return self._embedding_matcher.find_similar(workload)

    def _combine_analyses(
        self,
        code_analysis: Dict[str, Any],
        nlp_analysis: Dict[str, Any],
        similar: list
    ) -> Dict[str, Any]:
        """Combine multiple analyses into single result.

        Args:
            code_analysis: Code analysis results
            nlp_analysis: NLP analysis results
            similar: Similar workloads

        Returns:
            Combined analysis dictionary
        """
        return {
            "code_analysis": code_analysis,
            "nlp_analysis": nlp_analysis,
            "similar_workloads": similar,
            "bound_type": nlp_analysis.get("bound_type", "unknown"),
            "confidence": 0.7
        }

    def _default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when all methods fail.

        Returns:
            Default analysis dictionary
        """
        return {
            "code_analysis": {},
            "nlp_analysis": {},
            "similar_workloads": [],
            "bound_type": "unknown",
            "confidence": 0.0
        }

