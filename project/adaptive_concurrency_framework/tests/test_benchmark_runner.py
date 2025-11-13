"""
Tests for benchmark runner.
"""

import pytest
import asyncio
from adaptive_concurrency_framework.benchmarking.benchmark_runner import BenchmarkRunner
from adaptive_concurrency_framework.core.engine import FrameworkConfig


def sample_task(n: int = 100) -> int:
    """Sample task for benchmarking."""
    result = 0
    for i in range(n):
        result += i
    return result


@pytest.mark.asyncio
async def test_benchmark_runner():
    """Test benchmark runner."""
    config = FrameworkConfig()
    runner = BenchmarkRunner(config)
    
    results = await runner.run_comprehensive_benchmark(sample_task)
    
    assert isinstance(results, dict)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_benchmark_results_have_metrics():
    """Test that benchmark results contain metrics."""
    config = FrameworkConfig()
    runner = BenchmarkRunner(config)
    
    results = await runner.run_comprehensive_benchmark(sample_task)
    
    for strategy_name, result in results.items():
        assert hasattr(result, 'strategy_name')
        assert hasattr(result, 'execution_time')
        assert hasattr(result, 'throughput')

