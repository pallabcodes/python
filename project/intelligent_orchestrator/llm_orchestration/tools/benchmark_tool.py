"""Tool for running benchmarks."""

from typing import Any, Dict, Optional
import logging

try:
    from langchain.tools import BaseTool as LangChainBaseTool
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    LangChainBaseTool = object

from ..base.tool_base import BaseTool


class BenchmarkTool(BaseTool):
    """Tool for running performance benchmarks."""

    def __init__(
        self,
        benchmark_runner: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize benchmark tool.

        Args:
            benchmark_runner: Benchmark runner instance
            logger: Optional logger instance
        """
        super().__init__(
            "benchmark",
            "Tool for running performance benchmarks",
            logger
        )
        self._benchmark_runner = benchmark_runner

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run benchmark.

        Args:
            input_data: Dictionary with benchmark configuration

        Returns:
            Benchmark result dictionary
        """
        if not self._benchmark_runner:
            return self._mock_execution(input_data)

        try:
            workload = input_data.get("workload")
            strategies = input_data.get("strategies", [])
            results = self._benchmark_runner.run(workload, strategies)
            self._log_execution(input_data, results)
            return results
        except Exception as e:
            self._logger.error(f"Tool execution failed: {e}")
            return self._mock_execution(input_data)

    def _mock_execution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution when benchmark runner unavailable.

        Args:
            input_data: Input data dictionary

        Returns:
            Mock result dictionary
        """
        return {
            "status": "mock",
            "strategies": input_data.get("strategies", []),
            "results": {}
        }


class LangChainBenchmarkTool(LangChainBaseTool):
    """LangChain-compatible wrapper for benchmark tool."""

    name = "benchmark"
    description = "Run performance benchmarks for strategies"

    def __init__(self, benchmark_tool: BenchmarkTool):
        """Initialize LangChain wrapper.

        Args:
            benchmark_tool: Underlying benchmark tool
        """
        super().__init__()
        self._benchmark_tool = benchmark_tool

    def _run(self, query: str) -> str:
        """Execute tool synchronously.

        Args:
            query: Query string with benchmark info

        Returns:
            Result string
        """
        input_data = {"query": query}
        result = self._benchmark_tool.execute(input_data)
        return str(result)

    async def _arun(self, query: str) -> str:
        """Execute tool asynchronously.

        Args:
            query: Query string with benchmark info

        Returns:
            Result string
        """
        return self._run(query)

