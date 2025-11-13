"""Natural language decision explanations."""

from typing import Any, Dict, Optional
import logging

from ...llm_orchestration.agents.explanation_agent import ExplanationAgent


class DecisionExplainer:
    """Generate natural language explanations of decisions."""

    def __init__(
        self,
        llm_agent: Optional[ExplanationAgent] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize decision explainer.

        Args:
            llm_agent: LLM agent for explanations
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._llm_agent = llm_agent or ExplanationAgent(logger=logger)
        self._logger.info("Decision explainer initialized")

    def explain(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanation for decision.

        Args:
            decision: Decision dictionary with strategy and context

        Returns:
            Explanation dictionary
        """
        try:
            input_data = {
                "decision": decision,
                "context": decision.get("context", {})
            }
            result = self._llm_agent.execute(input_data)
            explanation = self._format_explanation(result)
            self._logger.info("Decision explanation generated")
            return explanation
        except Exception as e:
            self._logger.error(f"Explanation generation failed: {e}")
            return self._default_explanation(decision)

    def _format_explanation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format LLM result into explanation.

        Args:
            result: LLM agent result

        Returns:
            Formatted explanation dictionary
        """
        return {
            "explanation": result.get("explanation", ""),
            "format": "natural_language",
            "decision": result.get("decision", {})
        }

    def _default_explanation(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Return default explanation when LLM unavailable.

        Args:
            decision: Decision dictionary

        Returns:
            Default explanation dictionary
        """
        return {
            "explanation": "Unable to generate explanation - LLM unavailable",
            "format": "natural_language",
            "decision": decision
        }

