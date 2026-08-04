"""Integrator for multiprocessing examples enforcing Google-grade BaseIntegrator ABC contract."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/multiprocessing_examples"))

from .base_integrator import BaseIntegrator


class MultiprocessingIntegrator(BaseIntegrator):
    """Integrate multiprocessing techniques into intelligent orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize multiprocessing integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "process_pools",
            "shared_memory",
            "process_communication",
            "parallel_processing"
        ]
        self._logger.info("Multiprocessing integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available multiprocessing techniques.

        Returns:
            List of technique names
        """
        return list(self._techniques)

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create multiprocessing strategy from technique.

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
                f"Unsupported multiprocessing technique '{technique}'. "
                f"Supported: {self._techniques}"
            )

        self._logger.info(f"Creating multiprocessing strategy: {technique}")
        return {
            "type": "multiprocessing",
            "technique": technique,
            "config": config
        }
