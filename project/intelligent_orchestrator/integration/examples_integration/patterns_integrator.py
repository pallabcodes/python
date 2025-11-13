"""Integrator for concurrency patterns examples."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../examples/patterns"))


class PatternsIntegrator:
    """Integrate concurrency patterns examples into orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize patterns integrator.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._patterns: List[str] = [
            "pipeline",
            "datastore_writer",
            "html_parser",
            "http_fetcher"
        ]
        self._logger.info("Patterns integrator initialized")

    def get_available_patterns(self) -> List[str]:
        """Get list of available concurrency patterns.

        Returns:
            List of pattern names
        """
        return self._patterns

    def create_strategy(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create strategy from pattern.

        Args:
            pattern: Pattern name
            config: Configuration dictionary

        Returns:
            Strategy dictionary
        """
        self._logger.info(f"Creating pattern-based strategy: {pattern}")
        return {
            "type": "pattern",
            "pattern": pattern,
            "config": config
        }

