"""
Tests for workload analyzer.
"""

import pytest
import asyncio
from adaptive_concurrency_framework.core.workload_analyzer import (
    WorkloadAnalyzer,
    WorkloadCharacteristics
)
from adaptive_concurrency_framework.core.engine import FrameworkConfig


def cpu_bound_task(n: int = 1000) -> int:
    """CPU-bound task."""
    result = 0
    for i in range(n):
        result += i * i
    return result


def io_bound_task() -> str:
    """I/O-bound task."""
    import time
    time.sleep(0.01)
    return "done"


@pytest.mark.asyncio
async def test_workload_analyzer_cpu_bound():
    """Test workload analyzer with CPU-bound task."""
    config = FrameworkConfig()
    analyzer = WorkloadAnalyzer(config)
    
    characteristics = await analyzer.analyze(cpu_bound_task)
    
    assert isinstance(characteristics, WorkloadCharacteristics)
    assert "threading" in characteristics.profiling_metrics or "multiprocessing" in characteristics.profiling_metrics


@pytest.mark.asyncio
async def test_workload_analyzer_io_bound():
    """Test workload analyzer with I/O-bound task."""
    config = FrameworkConfig()
    analyzer = WorkloadAnalyzer(config)
    
    characteristics = await analyzer.analyze(io_bound_task)
    
    assert isinstance(characteristics, WorkloadCharacteristics)
    assert "threading" in characteristics.profiling_metrics or "asyncio" in characteristics.profiling_metrics


@pytest.mark.asyncio
async def test_workload_analyzer_determines_characteristics():
    """Test that workload analyzer determines characteristics."""
    config = FrameworkConfig()
    analyzer = WorkloadAnalyzer(config)
    
    characteristics = await analyzer.analyze(cpu_bound_task)
    
    # Should determine at least one characteristic
    assert (
        characteristics.is_cpu_bound or
        characteristics.is_io_bound or
        characteristics.is_mixed
    )

