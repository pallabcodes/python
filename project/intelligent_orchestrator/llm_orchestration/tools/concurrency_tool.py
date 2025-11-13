"""Tool for concurrency framework integration."""

from typing import Any, Dict, Optional
import logging

try:
    from langchain.tools import BaseTool as LangChainBaseTool
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    LangChainBaseTool = object

from ..base.tool_base import BaseTool


class ConcurrencyTool(BaseTool):
    """Tool for interacting with adaptive concurrency framework."""

    def __init__(
        self,
        framework_adapter: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize concurrency tool.

        Args:
            framework_adapter: Adapter for concurrency framework
            logger: Optional logger instance
        """
        super().__init__(
            "concurrency_framework",
            "Tool for executing concurrency optimizations",
            logger
        )
        self._framework_adapter = framework_adapter

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute concurrency optimization.

        Args:
            input_data: Dictionary with workload and strategy

        Returns:
            Optimization result dictionary
        """
        if not self._framework_adapter:
            return self._mock_execution(input_data)

        try:
            workload = input_data.get("workload")
            strategy = input_data.get("strategy")
            result = self._framework_adapter.optimize(workload, strategy)
            self._log_execution(input_data, result)
            return result
        except Exception as e:
            self._logger.error(f"Tool execution failed: {e}")
            return self._mock_execution(input_data)

    def _mock_execution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution when framework adapter unavailable.

        Args:
            input_data: Input data dictionary

        Returns:
            Mock result dictionary
        """
        return {
            "status": "mock",
            "strategy": input_data.get("strategy", "unknown"),
            "performance": {}
        }


class LangChainConcurrencyTool(LangChainBaseTool):
    """LangChain-compatible wrapper for concurrency tool."""

    name = "concurrency_framework"
    description = "Execute concurrency optimizations using adaptive framework"

    def __init__(self, concurrency_tool: ConcurrencyTool):
        """Initialize LangChain wrapper.

        Args:
            concurrency_tool: Underlying concurrency tool
        """
        super().__init__()
        self._concurrency_tool = concurrency_tool

    def _run(self, query: str) -> str:
        """Execute tool synchronously.

        Args:
            query: Query string with workload info

        Returns:
            Result string
        """
        input_data = {"query": query}
        result = self._concurrency_tool.execute(input_data)
        return str(result)

    async def _arun(self, query: str) -> str:
        """Execute tool asynchronously.

        Args:
            query: Query string with workload info

        Returns:
            Result string
        """
        return self._run(query)

