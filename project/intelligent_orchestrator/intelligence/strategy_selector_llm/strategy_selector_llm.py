"""Main LLM-powered strategy selector."""

from typing import Any, Dict, List, Optional
import logging

from .strategy_reasoner import StrategyReasoner
from .tradeoff_analyzer import TradeoffAnalyzer
from .predictive_selector import PredictiveSelector


class StrategySelectorLLM:
    """Main selector combining reasoning, trade-offs, and predictions."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize LLM-powered strategy selector.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._reasoner = StrategyReasoner(logger=logger)
        self._tradeoff_analyzer = TradeoffAnalyzer(logger=logger)
        self._predictive_selector = PredictiveSelector(logger=logger)
        self._logger.info("LLM-powered strategy selector initialized")

    def select(
        self,
        analysis: Dict[str, Any],
        strategies: List[str]
    ) -> Dict[str, Any]:
        """Select optimal strategy using multiple methods.

        Args:
            analysis: Workload analysis results
            strategies: Available strategies

        Returns:
            Selection result dictionary
        """
        try:
            reasoning = self._reasoner.reason(analysis, strategies)
            tradeoffs = self._tradeoff_analyzer.analyze(strategies, analysis)
            prediction = self._predictive_selector.predict(analysis, strategies)
            selection = self._combine_selections(reasoning, tradeoffs, prediction)
            self._logger.info("Strategy selection completed")
            return selection
        except Exception as e:
            self._logger.error(f"Selection failed: {e}")
            return self._default_selection(strategies)

    def _combine_selections(
        self,
        reasoning: Dict[str, Any],
        tradeoffs: List[Dict[str, Any]],
        prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine multiple selection methods.

        Args:
            reasoning: LLM reasoning result
            tradeoffs: Trade-off analyses
            prediction: Predictive selection result

        Returns:
            Combined selection dictionary
        """
        selected = reasoning.get("selected_strategy", "unknown")
        return {
            "selected_strategy": selected,
            "reasoning": reasoning.get("reasoning", ""),
            "tradeoffs": tradeoffs,
            "prediction": prediction,
            "confidence": reasoning.get("confidence", 0.5)
        }

    def _default_selection(self, strategies: List[str]) -> Dict[str, Any]:
        """Return default selection when all methods fail.

        Args:
            strategies: Available strategies

        Returns:
            Default selection dictionary
        """
        return {
            "selected_strategy": strategies[0] if strategies else "unknown",
            "reasoning": "Default selection - all methods failed",
            "tradeoffs": [],
            "prediction": {},
            "confidence": 0.0
        }

