"""Abstract base class for LangChain tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseTool(ABC):
    """Abstract base class for LangChain tools."""

    def __init__(
        self,
        tool_name: str,
        tool_description: str,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize base tool.

        Args:
            tool_name: Name identifier for the tool
            tool_description: Description of tool functionality
            logger: Optional logger instance
        """
        self._tool_name = tool_name
        self._tool_description = tool_description
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(
            f"Initializing tool {tool_name}",
            extra={"tool_name": tool_name}
        )

    @property
    def tool_name(self) -> str:
        """Get tool name."""
        return self._tool_name

    @property
    def tool_description(self) -> str:
        """Get tool description."""
        return self._tool_description

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool logic.

        Args:
            input_data: Input data dictionary

        Returns:
            Result dictionary with tool output
        """
        pass

    def _log_execution(
        self,
        input_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Log tool execution.

        Args:
            input_data: Input data
            result: Execution result
        """
        self._logger.info(
            f"Tool {self._tool_name} executed",
            extra={
                "tool_name": self._tool_name,
                "input_keys": list(input_data.keys()),
                "result_keys": list(result.keys())
            }
        )

