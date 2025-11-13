"""Integrator for concurrent.futures examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/concurrent_futures"))


class ConcurrentFuturesIntegrator:
    """Integrate concurrent.futures examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize concurrent.futures integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "thread_pool_executor",
            "process_pool_executor",
            "future_management",
            "parallel_map"
        ]
        self._logger.info("Concurrent.futures integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available concurrent.futures techniques.

        Returns:
            List of technique names
        """
        return self._techniques

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create concurrent.futures strategy from technique.

        Args:
            technique: Technique name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating concurrent.futures strategy: {technique}")
        return {
            "type": "concurrent_futures",
            "technique": technique,
            "config": config
        }

