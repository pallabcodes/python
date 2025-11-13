"""Integrator for subprocess examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/subprocess_examples"))


class SubprocessIntegrator:
    """Integrate subprocess examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize subprocess integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._techniques: List[str] = [
            "process_execution",
            "process_communication",
            "process_control",
            "external_commands"
        ]
        self._logger.info("Subprocess integrator initialized")

    def get_available_techniques(self) -> List[str]:
        """Get list of available subprocess techniques.

        Returns:
            List of technique names
        """
        return self._techniques

    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create subprocess strategy from technique.

        Args:
            technique: Technique name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating subprocess strategy: {technique}")
        return {
            "type": "subprocess",
            "technique": technique,
            "config": config
        }

