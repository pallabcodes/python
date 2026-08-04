"""Integrator for concurrent.futures examples enforcing BaseIntegrator ABC contract."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/concurrent_futures_examples"))

from .base_integrator import BaseIntegrator


class ConcurrentFuturesIntegrator(BaseIntegrator):
    """Integrate concurrent.futures executor techniques into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize concurrent.futures integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "thread_pool_executor",
            "process_pool_executor",
            "as_completed",
            "future_callbacks"
        ]
        self._logger.info("ConcurrentFutures integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available concurrent.futures techniques.

        Returns:
            List of technique names
        """
        return list(self._techniques)

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

        Raises:
            ValueError: If target technique is not supported.
        """
        if technique not in self._techniques:
            raise ValueError(
                f"Unsupported concurrent.futures technique '{technique}'. "
                f"Supported: {self._techniques}"
            )

        self._logger.info(f"Creating concurrent.futures strategy: {technique}")
        return {
            "type": "concurrent_futures",
            "technique": technique,
            "config": config
        }
