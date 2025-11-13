"""Agent for adaptive learning from optimization results."""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.agents import AgentExecutor, initialize_agent, AgentType
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from ..base.agent_base import BaseAgent


class LearningAgent(BaseAgent):
    """Agent for learning patterns from optimization results."""

    def __init__(
        self,
        llm_model: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize learning agent.

        Args:
            llm_model: LLM model name (default: gpt-4)
            logger: Optional logger instance
        """
        super().__init__("learning", logger)
        self._llm_model = llm_model or "gpt-4"
        self._agent_executor: Optional[Any] = None
        self._learning_history: List[Dict[str, Any]] = []
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize LangChain agent executor."""
        if not HAS_LANGCHAIN:
            self._logger.warning("LangChain not available, using mock agent")
            return

        try:
            llm = ChatOpenAI(model=self._llm_model, temperature=0)
            tools = []
            self._agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            self._logger.info("Learning agent initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize agent: {e}")
            self._agent_executor = None

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from optimization results using LLM.

        Args:
            input_data: Dictionary with optimization results

        Returns:
            Learning insights dictionary
        """
        self._learning_history.append(input_data)
        if not self._agent_executor:
            return self._mock_learning(input_data)

        try:
            prompt = self._build_learning_prompt(input_data)
            result = self._agent_executor.run(prompt)
            insights = self._extract_insights(result, input_data)
            self._log_execution(input_data, insights)
            return insights
        except Exception as e:
            self._logger.error(f"Agent execution failed: {e}")
            return self._mock_learning(input_data)

    def _build_learning_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build learning prompt from input data.

        Args:
            input_data: Input data dictionary

        Returns:
            Formatted prompt string
        """
        results = input_data.get("results", {})
        history_summary = self._summarize_history()
        return f"""Analyze these optimization results and extract patterns:

Current Results:
{results}

Historical Context:
{history_summary}

Identify patterns and insights for future optimizations.
"""

    def _summarize_history(self) -> str:
        """Summarize learning history.

        Returns:
            Summary string
        """
        if not self._learning_history:
            return "No previous history"
        return f"{len(self._learning_history)} previous optimizations"

    def _extract_insights(
        self,
        result: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract insights from agent result.

        Args:
            result: Raw agent result string
            input_data: Original input data

        Returns:
            Insights dictionary
        """
        return {
            "insights": result,
            "patterns": [],
            "recommendations": []
        }

    def _mock_learning(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock learning when LLM is unavailable.

        Args:
            input_data: Input data dictionary

        Returns:
            Mock learning result
        """
        return {
            "insights": "Mock learning - LLM unavailable",
            "patterns": [],
            "recommendations": []
        }

    def shutdown(self) -> None:
        """Shutdown agent and cleanup resources."""
        self._agent_executor = None
        self._learning_history.clear()
        self._logger.info("Learning agent shut down")

