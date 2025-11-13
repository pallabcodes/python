"""Integrator for threading examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/threading_examples"))


class ThreadingIntegrator:
    """Integrate threading examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize threading integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "thread_pools",
            "producer_consumer",
            "synchronization",
            "thread_safe_structures"
        ]
        self._logger.info("Threading integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available threading techniques.

        Returns:
            List of technique names
        """
        return self._techniques

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create threading strategy from technique.

        Args:
            technique: Technique name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating threading strategy: {technique}")
        return {
            "type": "threading",
            "technique": technique,
            "config": config
        }

