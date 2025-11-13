"""Abstract base class for LangGraph workflows."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseWorkflow(ABC):
    """Abstract base class for LangGraph workflows."""

    def __init__(
        self,
        workflow_name: str,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize base workflow.

        Args:
            workflow_name: Name identifier for the workflow
            logger: Optional logger instance
        """
        self._workflow_name = workflow_name
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(
            f"Initializing workflow {workflow_name}",
            extra={"workflow_name": workflow_name}
        )

    @property
    def workflow_name(self) -> str:
        """Get workflow name."""
        return self._workflow_name

    @abstractmethod
    def build(self) -> Any:
        """Build the workflow graph.

        Returns:
            LangGraph workflow graph
        """
        pass

    @abstractmethod
    def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with initial state.

        Args:
            initial_state: Initial workflow state

        Returns:
            Final workflow state
        """
        pass

    def _log_execution(
        self,
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any]
    ) -> None:
        """Log workflow execution.

        Args:
            initial_state: Initial state
            final_state: Final state
        """
        self._logger.info(
            f"Workflow {self._workflow_name} executed",
            extra={
                "workflow_name": self._workflow_name,
                "initial_keys": list(initial_state.keys()),
                "final_keys": list(final_state.keys())
            }
        )

