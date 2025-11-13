"""Integrator for hybrid concurrency examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/hybrid_concurrency"))


class HybridIntegrator:
    """Integrate hybrid concurrency examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize hybrid integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "asyncio_threading",
            "asyncio_multiprocessing",
            "threading_multiprocessing",
            "custom_executor"
        ]
        self._logger.info("Hybrid integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available hybrid techniques.

        Returns:
            List of technique names
        """
        return self._techniques

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create hybrid strategy from technique.

        Args:
            technique: Technique name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating hybrid strategy: {technique}")
        return {
            "type": "hybrid",
            "technique": technique,
            "config": config
        }

