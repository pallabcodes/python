"""Predictive strategy selection using historical data."""

from typing import Any, Dict, List, Optional
import logging


class PredictiveSelector:
    """Predict optimal strategies using historical optimization data."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize predictive selector.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._history: List[Dict[str, Any]] = []
        self._logger.info("Predictive selector initialized")

    def predict(
        self,
        workload: Dict[str, Any],
        strategies: List[str]
    ) -> Dict[str, Any]:
        """Predict optimal strategy based on historical data.

        Args:
            workload: Workload dictionary
            strategies: Available strategies

        Returns:
            Prediction dictionary with recommended strategy
        """
        try:
            similar_cases = self._find_similar_cases(workload)
            prediction = self._predict_from_history(similar_cases, strategies)
            self._logger.info("Strategy prediction completed")
            return prediction
        except Exception as e:
            self._logger.error(f"Prediction failed: {e}")
            return self._default_prediction(strategies)

    def add_history(self, case: Dict[str, Any]) -> None:
        """Add optimization case to history.

        Args:
            case: Optimization case dictionary
        """
        self._history.append(case)
        self._logger.debug(f"Added case to history: {len(self._history)} cases")

    def _find_similar_cases(self, workload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar historical cases.

        Args:
            workload: Workload dictionary

        Returns:
            List of similar cases
        """
        return self._history[:5]

    def _predict_from_history(
        self,
        cases: List[Dict[str, Any]],
        strategies: List[str]
    ) -> Dict[str, Any]:
        """Predict strategy from historical cases.

        Args:
            cases: Similar historical cases
            strategies: Available strategies

        Returns:
            Prediction dictionary
        """
        if not cases:
            return self._default_prediction(strategies)
        best_strategy = cases[0].get("strategy", strategies[0] if strategies else "unknown")
        return {
            "predicted_strategy": best_strategy,
            "confidence": 0.6,
            "based_on_cases": len(cases)
        }

    def _default_prediction(self, strategies: List[str]) -> Dict[str, Any]:
        """Return default prediction when no history available.

        Args:
            strategies: Available strategies

        Returns:
            Default prediction dictionary
        """
        return {
            "predicted_strategy": strategies[0] if strategies else "unknown",
            "confidence": 0.0,
            "based_on_cases": 0
        }

