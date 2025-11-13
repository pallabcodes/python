"""Interactive Q&A system about strategies."""

from typing import Any, Dict, Optional
import logging

from ...llm_orchestration.agents.explanation_agent import ExplanationAgent


class QASystem:
    """Interactive question-answering system about optimization strategies."""

    def __init__(
        self,
        llm_agent: Optional[ExplanationAgent] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize Q&A system.

        Args:
            llm_agent: LLM agent for answering questions
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._llm_agent = llm_agent or ExplanationAgent(logger=logger)
        self._logger.info("Q&A system initialized")

    def answer(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Answer question about optimization strategy.

        Args:
            question: Question string
            context: Context dictionary with optimization data

        Returns:
            Answer dictionary
        """
        try:
            input_data = {
                "decision": {"question": question},
                "context": context
            }
            result = self._llm_agent.execute(input_data)
            answer = self._format_answer(result, question)
            self._logger.info("Question answered")
            return answer
        except Exception as e:
            self._logger.error(f"Q&A failed: {e}")
            return self._default_answer(question)

    def _format_answer(
        self,
        result: Dict[str, Any],
        question: str
    ) -> Dict[str, Any]:
        """Format LLM result into answer.

        Args:
            result: LLM agent result
            question: Original question

        Returns:
            Formatted answer dictionary
        """
        return {
            "question": question,
            "answer": result.get("explanation", ""),
            "format": "qa"
        }

    def _default_answer(self, question: str) -> Dict[str, Any]:
        """Return default answer when LLM unavailable.

        Args:
            question: Question string

        Returns:
            Default answer dictionary
        """
        return {
            "question": question,
            "answer": "Unable to answer - LLM unavailable",
            "format": "qa"
        }

