"""Integrator for asyncio examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/asyncio_examples"))


class AsyncioIntegrator:
    """Integrate asyncio examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize asyncio integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "async_io",
            "event_loops",
            "async_tasks",
            "async_patterns",
            "concurrent_async"
        ]
        self._logger.info("Asyncio integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available asyncio techniques.

        Returns:
            List of technique names
        """
        return self._techniques

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create asyncio strategy from technique.

        Args:
            technique: Technique name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating asyncio strategy: {technique}")
        return {
            "type": "asyncio",
            "technique": technique,
            "config": config
        }

