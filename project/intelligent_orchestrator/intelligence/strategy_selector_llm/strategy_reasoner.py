"""LLM reasoning for strategy selection."""

from typing import Any, Dict, List, Optional
import logging

from ...llm_orchestration.agents.strategy_selector_agent import StrategySelectorAgent


class StrategyReasoner:
    """Reason about optimal strategies using LLM."""

    def __init__(
        self,
        llm_agent: Optional[StrategySelectorAgent] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize strategy reasoner.

        Args:
            llm_agent: LLM agent for reasoning
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._llm_agent = llm_agent or StrategySelectorAgent(logger=logger)
        self._logger.info("Strategy reasoner initialized")

    def reason(
        self,
        analysis: Dict[str, Any],
        strategies: List[str]
    ) -> Dict[str, Any]:
        """Reason about optimal strategy selection.

        Args:
            analysis: Workload analysis results
            strategies: Available strategies to choose from

        Returns:
            Reasoning result with selected strategy
        """
        try:
            input_data = {
                "analysis": analysis,
                "strategies": strategies
            }
            result = self._llm_agent.execute(input_data)
            reasoning = self._parse_result(result)
            self._logger.info("Strategy reasoning completed")
            return reasoning
        except Exception as e:
            self._logger.error(f"Reasoning failed: {e}")
            return self._default_reasoning(strategies)

    def _parse_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM agent result into reasoning format.

        Args:
            result: LLM agent result dictionary

        Returns:
            Structured reasoning dictionary
        """
        return {
            "selected_strategy": result.get("selected_strategy", "unknown"),
            "reasoning": result.get("reasoning", ""),
            "confidence": result.get("confidence", 0.5)
        }

    def _default_reasoning(self, strategies: List[str]) -> Dict[str, Any]:
        """Return default reasoning when LLM unavailable.

        Args:
            strategies: Available strategies

        Returns:
            Default reasoning dictionary
        """
        selected = strategies[0] if strategies else "unknown"
        return {
            "selected_strategy": selected,
            "reasoning": "Default selection - LLM unavailable",
            "confidence": 0.0
        }

