"""Tool for metrics collection."""

from typing import Any, Dict, Optional
import logging

try:
    from langchain.tools import BaseTool as LangChainBaseTool
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    LangChainBaseTool = object

from ..base.tool_base import BaseTool


class MetricsTool(BaseTool):
    """Tool for collecting and analyzing metrics."""

    def __init__(
        self,
        metrics_collector: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize metrics tool.

        Args:
            metrics_collector: Metrics collector instance
            logger: Optional logger instance
        """
        super().__init__(
            "metrics",
            "Tool for collecting and analyzing performance metrics",
            logger
        )
        self._metrics_collector = metrics_collector

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics.

        Args:
            input_data: Dictionary with metrics query

        Returns:
            Metrics result dictionary
        """
        if not self._metrics_collector:
            return self._mock_execution(input_data)

        try:
            query = input_data.get("query", {})
            metrics = self._metrics_collector.collect(query)
            self._log_execution(input_data, metrics)
            return metrics
        except Exception as e:
            self._logger.error(f"Tool execution failed: {e}")
            return self._mock_execution(input_data)

    def _mock_execution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution when metrics collector unavailable.

        Args:
            input_data: Input data dictionary

        Returns:
            Mock result dictionary
        """
        return {
            "status": "mock",
            "metrics": {},
            "timestamp": "mock"
        }


class LangChainMetricsTool(LangChainBaseTool):
    """LangChain-compatible wrapper for metrics tool."""

    name = "metrics"
    description = "Collect and analyze performance metrics"

    def __init__(self, metrics_tool: MetricsTool):
        """Initialize LangChain wrapper.

        Args:
            metrics_tool: Underlying metrics tool
        """
        super().__init__()
        self._metrics_tool = metrics_tool

    def _run(self, query: str) -> str:
        """Execute tool synchronously.

        Args:
            query: Query string with metrics info

        Returns:
            Result string
        """
        input_data = {"query": query}
        result = self._metrics_tool.execute(input_data)
        return str(result)

    async def _arun(self, query: str) -> str:
        """Execute tool asynchronously.

        Args:
            query: Query string with metrics info

        Returns:
            Result string
        """
        return self._run(query)

