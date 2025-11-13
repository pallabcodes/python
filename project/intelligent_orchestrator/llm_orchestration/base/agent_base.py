"""Abstract base class for LLM agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseAgent(ABC):
    """Abstract base class for LLM-powered agents."""

    def __init__(self, agent_name: str, logger: Optional[logging.Logger] = None):
        """Initialize base agent.

        Args:
            agent_name: Name identifier for the agent
            logger: Optional logger instance
        """
        self._agent_name = agent_name
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(
            f"Initializing agent {agent_name}",
            extra={"agent_name": agent_name}
        )

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self._agent_name

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic.

        Args:
            input_data: Input data dictionary

        Returns:
            Result dictionary with agent output
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown agent and cleanup resources."""
        pass

    def _log_execution(
        self,
        input_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Log agent execution.

        Args:
            input_data: Input data
            result: Execution result
        """
        self._logger.info(
            f"Agent {self._agent_name} executed",
            extra={
                "agent_name": self._agent_name,
                "input_keys": list(input_data.keys()),
                "result_keys": list(result.keys())
            }
        )

