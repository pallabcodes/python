"""NLP-based workload analysis using LLM."""

from typing import Any, Dict, Optional
import logging

from ...llm_orchestration.agents.workload_analyzer_agent import WorkloadAnalyzerAgent


class NaturalLanguageAnalyzer:
    """Analyze workloads using natural language processing."""

    def __init__(
        self,
        llm_agent: Optional[WorkloadAnalyzerAgent] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize natural language analyzer.

        Args:
            llm_agent: LLM agent for analysis
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._llm_agent = llm_agent or WorkloadAnalyzerAgent(logger=logger)
        self._logger.info("Natural language analyzer initialized")

    def analyze(self, description: str) -> Dict[str, Any]:
        """Analyze workload from natural language description.

        Args:
            description: Natural language workload description

        Returns:
            Analysis dictionary
        """
        try:
            input_data = {"description": description}
            result = self._llm_agent.execute(input_data)
            analysis = self._parse_llm_result(result)
            self._logger.info("Natural language analysis completed")
            return analysis
        except Exception as e:
            self._logger.error(f"Analysis failed: {e}")
            return self._default_analysis()

    def _parse_llm_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM agent result into structured format.

        Args:
            result: LLM agent result dictionary

        Returns:
            Structured analysis dictionary
        """
        analysis_text = result.get("analysis", "")
        bound_type = result.get("bound_type", "unknown")
        recommended = result.get("recommended_pattern", "unknown")
        return {
            "analysis": analysis_text,
            "bound_type": bound_type,
            "recommended_pattern": recommended,
            "confidence": 0.7
        }

    def _default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when LLM unavailable.

        Returns:
            Default analysis dictionary
        """
        return {
            "analysis": "Unable to analyze - LLM unavailable",
            "bound_type": "unknown",
            "recommended_pattern": "unknown",
            "confidence": 0.0
        }

