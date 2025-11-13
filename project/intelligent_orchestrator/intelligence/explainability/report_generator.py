"""LLM-generated optimization reports."""

from typing import Any, Dict, Optional
import logging

from ...llm_orchestration.agents.explanation_agent import ExplanationAgent


class ReportGenerator:
    """Generate comprehensive optimization reports using LLM."""

    def __init__(
        self,
        llm_agent: Optional[ExplanationAgent] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize report generator.

        Args:
            llm_agent: LLM agent for report generation
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._llm_agent = llm_agent or ExplanationAgent(logger=logger)
        self._logger.info("Report generator initialized")

    def generate(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization report.

        Args:
            optimization_data: Complete optimization data

        Returns:
            Report dictionary
        """
        try:
            input_data = {
                "decision": optimization_data,
                "context": optimization_data
            }
            result = self._llm_agent.execute(input_data)
            report = self._format_report(result, optimization_data)
            self._logger.info("Optimization report generated")
            return report
        except Exception as e:
            self._logger.error(f"Report generation failed: {e}")
            return self._default_report(optimization_data)

    def _format_report(
        self,
        result: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format LLM result into report.

        Args:
            result: LLM agent result
            data: Optimization data

        Returns:
            Formatted report dictionary
        """
        return {
            "summary": result.get("explanation", ""),
            "details": data,
            "format": "comprehensive_report"
        }

    def _default_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return default report when LLM unavailable.

        Args:
            data: Optimization data

        Returns:
            Default report dictionary
        """
        return {
            "summary": "Report generation unavailable",
            "details": data,
            "format": "comprehensive_report"
        }

