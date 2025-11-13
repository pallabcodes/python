"""Public API for orchestrator."""

from typing import Any, Dict, Optional
import logging

from .orchestrator_engine import OrchestratorEngine
from .orchestrator_config import OrchestratorConfig


class OrchestratorAPI:
    """Public API interface for intelligent orchestrator."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize orchestrator API.

        Args:
            config: Orchestrator configuration
            logger: Optional logger instance
        """
        self._engine = OrchestratorEngine(config=config, logger=logger)
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info("Orchestrator API initialized")

    def optimize_workload(self, workload: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workload - main API method.

        Args:
            workload: Workload dictionary with code and/or description

        Returns:
            Optimization result dictionary
        """
        return self._engine.optimize(workload)

