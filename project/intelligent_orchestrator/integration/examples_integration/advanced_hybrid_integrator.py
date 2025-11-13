"""Integrator for advanced hybrid concurrency examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/advanced_hybrid_concurrency"))


class AdvancedHybridIntegrator:
    """Integrate advanced hybrid concurrency examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize advanced hybrid integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "distributed_concurrency",
            "actor_model",
            "reactive_programming",
            "advanced_synchronization",
            "performance_profiling"
        ]
        self._logger.info("Advanced hybrid integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available advanced hybrid techniques.

        Returns:
            List of technique names
        """
        return self._techniques

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create advanced hybrid strategy from technique.

        Args:
            technique: Technique name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating advanced hybrid strategy: {technique}")
        return {
            "type": "advanced_hybrid",
            "technique": technique,
            "config": config
        }

