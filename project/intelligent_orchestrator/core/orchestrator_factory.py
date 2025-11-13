"""Factory for creating orchestrator instances."""

from typing import Optional
import logging

from .orchestrator_api import OrchestratorAPI
from .orchestrator_config import OrchestratorConfig


class OrchestratorFactory:
    """Factory for creating orchestrator instances."""

    @staticmethod
    def create(
        config: Optional[OrchestratorConfig] = None,
        logger: Optional[logging.Logger] = None
    ) -> OrchestratorAPI:
        """Create orchestrator API instance.

        Args:
            config: Optional configuration
            logger: Optional logger instance

        Returns:
            OrchestratorAPI instance
        """
        return OrchestratorAPI(config=config, logger=logger)

