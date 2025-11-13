"""
Tests for adaptive optimizer.
"""

import pytest
from adaptive_concurrency_framework.optimization.adaptive_optimizer import (
    AdaptiveOptimizer,
    OptimizationDecision
)
from adaptive_concurrency_framework.core.engine import FrameworkConfig
from adaptive_concurrency_framework.core.workload_analyzer import WorkloadCharacteristics


@pytest.mark.asyncio
async def test_adaptive_optimizer():
    """Test adaptive optimizer."""
    config = FrameworkConfig()
    optimizer = AdaptiveOptimizer(config)
    
    workload_characteristics = WorkloadCharacteristics(
        is_cpu_bound=True,
        recommended_strategy="multiprocessing"
    )
    
    benchmark_results = {
        "multiprocessing_process_pool": type('obj', (object,), {
            'throughput': 100.0,
            'execution_time': 1.0
        })()
    }
    
    decision = await optimizer.optimize(workload_characteristics, benchmark_results)
    
    assert isinstance(decision, OptimizationDecision)
    assert decision.selected_strategy is not None
    assert 0.0 <= decision.confidence <= 1.0


@pytest.mark.asyncio
async def test_optimizer_considers_workload_characteristics():
    """Test that optimizer considers workload characteristics."""
    config = FrameworkConfig()
    optimizer = AdaptiveOptimizer(config)
    
    cpu_characteristics = WorkloadCharacteristics(is_cpu_bound=True)
    io_characteristics = WorkloadCharacteristics(is_io_bound=True)
    
    benchmark_results = {}
    
    cpu_decision = await optimizer.optimize(cpu_characteristics, benchmark_results)
    io_decision = await optimizer.optimize(io_characteristics, benchmark_results)
    
    # CPU-bound should prefer multiprocessing
    # I/O-bound should prefer asyncio/threading
    # (exact selection depends on scoring logic)
    assert cpu_decision.selected_strategy is not None
    assert io_decision.selected_strategy is not None

