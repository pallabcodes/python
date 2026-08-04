"""Integrator for threading examples enforcing Google-grade BaseIntegrator ABC contract."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/threading_examples"))

from .base_integrator import BaseIntegrator


class ThreadingIntegrator(BaseIntegrator):
    """Integrate multithreading techniques into intelligent orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize threading integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "thread_locks",
            "condition_variables",
            "thread_pools",
            "daemon_threads"
        ]
        self._logger.info("Threading integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available threading techniques.

        Returns:
            List of technique names
        """
        return list(self._techniques)

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

        Raises:
            ValueError: If target technique is not supported.
        """
        if technique not in self._techniques:
            raise ValueError(
                f"Unsupported threading technique '{technique}'. "
                f"Supported: {self._techniques}"
            )

        self._logger.info(f"Creating threading strategy: {technique}")
        return {
            "type": "threading",
            "technique": technique,
            "config": config
        }
