"""Adapter for adaptive concurrency framework."""

from typing import Any, Dict, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../adaptive_concurrency_framework"))

try:
    from adaptive_concurrency_framework.core.engine import AdaptiveConcurrencyEngine
    HAS_FRAMEWORK = True
except ImportError:
    HAS_FRAMEWORK = False
    AdaptiveConcurrencyEngine = None


class FrameworkAdapter:
    """Adapter for integrating with adaptive concurrency framework."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize framework adapter.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._engine: Optional[Any] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize concurrency framework engine."""
        if HAS_FRAMEWORK and AdaptiveConcurrencyEngine:
            try:
                self._engine = AdaptiveConcurrencyEngine()
                self._logger.info("Concurrency framework adapter initialized")
            except Exception as e:
                self._logger.error(f"Failed to initialize framework: {e}")
                self._engine = None
        else:
            self._logger.warning("Concurrency framework not available")

    def optimize(
        self,
        workload: Dict[str, Any],
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """Optimize workload using concurrency framework.

        Args:
            workload: Workload dictionary
            strategy: Optional strategy to use

        Returns:
            Optimization result dictionary
        """
        if not self._engine:
            return self._mock_optimization(workload, strategy)

        try:
            result = self._engine.optimize(workload)
            self._logger.info("Framework optimization completed")
            return result
        except Exception as e:
            self._logger.error(f"Framework optimization failed: {e}")
            return self._mock_optimization(workload, strategy)

    def _mock_optimization(
        self,
        workload: Dict[str, Any],
        strategy: Optional[str]
    ) -> Dict[str, Any]:
        """Mock optimization when framework unavailable.

        Args:
            workload: Workload dictionary
            strategy: Optional strategy

        Returns:
            Mock result dictionary
        """
        return {
            "status": "mock",
            "strategy": strategy or "unknown",
            "performance": {}
        }

