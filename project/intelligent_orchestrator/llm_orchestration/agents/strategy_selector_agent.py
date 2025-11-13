"""Agent for selecting optimal concurrency strategies."""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.agents import AgentExecutor, initialize_agent, AgentType
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from ..base.agent_base import BaseAgent


class StrategySelectorAgent(BaseAgent):
    """Agent for selecting optimal concurrency strategies using LLM."""

    def __init__(
        self,
        llm_model: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize strategy selector agent.

        Args:
            llm_model: LLM model name (default: gpt-4)
            logger: Optional logger instance
        """
        super().__init__("strategy_selector", logger)
        self._llm_model = llm_model or "gpt-4"
        self._agent_executor: Optional[Any] = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize LangChain agent executor."""
        if not HAS_LANGCHAIN:
            self._logger.warning("LangChain not available, using mock agent")
            return

        try:
            llm = ChatOpenAI(model=self._llm_model, temperature=0)
            tools = self._create_tools()
            self._agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            self._logger.info("Strategy selector agent initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize agent: {e}")
            self._agent_executor = None

    def _create_tools(self) -> list:
        """Create tools for strategy selection.

        Returns:
            List of LangChain tools
        """
        return []

    def execute(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select optimal strategy using LLM reasoning.

        Args:
            input_data: Dictionary with workload analysis and options

        Returns:
            Selected strategy dictionary
        """
        if not self._agent_executor:
            return self._mock_selection(input_data)

        try:
            prompt = self._build_selection_prompt(input_data)
            result = self._agent_executor.run(prompt)
            selection = self._parse_result(result, input_data)
            self._log_execution(input_data, selection)
            return selection
        except Exception as e:
            self._logger.error(f"Agent execution failed: {e}")
            return self._mock_selection(input_data)

    def _build_selection_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build selection prompt from input data.

        Args:
            input_data: Input data dictionary

        Returns:
            Formatted prompt string
        """
        analysis = input_data.get("analysis", {})
        strategies = input_data.get("strategies", [])
        return f"""Select the optimal concurrency strategy based on:

Workload Analysis:
{analysis}

Available Strategies:
{strategies}

Consider trade-offs and select the best strategy.
"""

    def _parse_result(
        self,
        result: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse agent result into structured format.

        Args:
            result: Raw agent result string
            input_data: Original input data

        Returns:
            Structured selection dictionary
        """
        strategies = input_data.get("strategies", [])
        selected = strategies[0] if strategies else "unknown"
        return {
            "selected_strategy": selected,
            "reasoning": result,
            "confidence": 0.5
        }

    def _mock_selection(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock selection when LLM is unavailable.

        Args:
            input_data: Input data dictionary

        Returns:
            Mock selection result
        """
        strategies = input_data.get("strategies", [])
        selected = strategies[0] if strategies else "unknown"
        return {
            "selected_strategy": selected,
            "reasoning": "Mock selection - LLM unavailable",
            "confidence": 0.0
        }

    def shutdown(self) -> None:
        """Shutdown agent and cleanup resources."""
        self._agent_executor = None
        self._logger.info("Strategy selector agent shut down")

