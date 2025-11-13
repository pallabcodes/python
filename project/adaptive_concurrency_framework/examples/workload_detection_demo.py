"""
Workload detection demonstration.

This demo showcases the workload analyzer's ability to detect
workload characteristics using ALL concurrency techniques.
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from adaptive_concurrency_framework.core.engine import AdaptiveConcurrencyEngine, FrameworkConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cpu_bound_task(n: int) -> int:
    """CPU-bound task: compute factorial."""
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


def io_bound_task() -> str:
    """I/O-bound task: simulate network I/O."""
    import time
    time.sleep(0.1)  # Simulate network delay
    return "I/O task completed"


async def async_io_task() -> str:
    """Async I/O-bound task."""
    await asyncio.sleep(0.1)
    return "Async I/O task completed"


async def main():
    """Run workload detection demo."""
    logger.info("=" * 70)
    logger.info("Workload Detection Demo")
    logger.info("=" * 70)
    
    # Create framework
    config = FrameworkConfig(
        enable_benchmarking=True,
        enable_optimization=True,
        enable_distributed_coordination=False,
        enable_ml_selector=False
    )
    
    engine = AdaptiveConcurrencyEngine(config)
    await engine.initialize()
    
    # Test CPU-bound workload
    logger.info("\n1. Analyzing CPU-bound workload...")
    cpu_characteristics = await engine.analyze_workload(cpu_bound_task)
    logger.info(f"   CPU-bound: {cpu_characteristics.is_cpu_bound}")
    logger.info(f"   I/O-bound: {cpu_characteristics.is_io_bound}")
    logger.info(f"   Recommended strategy: {cpu_characteristics.recommended_strategy}")
    
    # Test I/O-bound workload
    logger.info("\n2. Analyzing I/O-bound workload...")
    io_characteristics = await engine.analyze_workload(io_bound_task)
    logger.info(f"   CPU-bound: {io_characteristics.is_cpu_bound}")
    logger.info(f"   I/O-bound: {io_characteristics.is_io_bound}")
    logger.info(f"   Recommended strategy: {io_characteristics.recommended_strategy}")
    
    # Test async workload
    logger.info("\n3. Analyzing async I/O workload...")
    async_characteristics = await engine.analyze_workload(async_io_task)
    logger.info(f"   CPU-bound: {async_characteristics.is_cpu_bound}")
    logger.info(f"   I/O-bound: {async_characteristics.is_io_bound}")
    logger.info(f"   Recommended strategy: {async_characteristics.recommended_strategy}")
    
    logger.info("\n" + "=" * 70)
    logger.info("Demo complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

