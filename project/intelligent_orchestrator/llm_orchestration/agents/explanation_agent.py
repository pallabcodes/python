"""Agent for generating natural language explanations."""

from typing import Any, Dict, Optional
import logging

try:
    from langchain.agents import AgentExecutor, initialize_agent, AgentType
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from ..base.agent_base import BaseAgent


class ExplanationAgent(BaseAgent):
    """Agent for generating natural language explanations of decisions."""

    def __init__(
        self,
        llm_model: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize explanation agent.

        Args:
            llm_model: LLM model name (default: gpt-4)
            logger: Optional logger instance
        """
        super().__init__("explanation", logger)
        self._llm_model = llm_model or "gpt-4"
        self._agent_executor: Optional[Any] = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize LangChain agent executor."""
        if not HAS_LANGCHAIN:
            self._logger.warning("LangChain not available, using mock agent")
            return

        try:
            llm = ChatOpenAI(model=self._llm_model, temperature=0.7)
            tools = []
            self._agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            self._logger.info("Explanation agent initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize agent: {e}")
            self._agent_executor = None

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanation using LLM.

        Args:
            input_data: Dictionary with decision and context

        Returns:
            Explanation dictionary
        """
        if not self._agent_executor:
            return self._mock_explanation(input_data)

        try:
            prompt = self._build_explanation_prompt(input_data)
            result = self._agent_executor.run(prompt)
            explanation = self._format_explanation(result, input_data)
            self._log_execution(input_data, explanation)
            return explanation
        except Exception as e:
            self._logger.error(f"Agent execution failed: {e}")
            return self._mock_explanation(input_data)

    def _build_explanation_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build explanation prompt from input data.

        Args:
            input_data: Input data dictionary

        Returns:
            Formatted prompt string
        """
        decision = input_data.get("decision", {})
        context = input_data.get("context", {})
        return f"""Explain this optimization decision in natural language:

Decision:
{decision}

Context:
{context}

Provide a clear, understandable explanation.
"""

    def _format_explanation(
        self,
        result: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format agent result into explanation dictionary.

        Args:
            result: Raw agent result string
            input_data: Original input data

        Returns:
            Formatted explanation dictionary
        """
        return {
            "explanation": result,
            "decision": input_data.get("decision", {}),
            "format": "natural_language"
        }

    def _mock_explanation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock explanation when LLM is unavailable.

        Args:
            input_data: Input data dictionary

        Returns:
            Mock explanation result
        """
        return {
            "explanation": "Mock explanation - LLM unavailable",
            "decision": input_data.get("decision", {}),
            "format": "natural_language"
        }

    def shutdown(self) -> None:
        """Shutdown agent and cleanup resources."""
        self._agent_executor = None
        self._logger.info("Explanation agent shut down")

