"""
Adaptive optimization demonstration.

This demo showcases the adaptive optimizer's ability to select
optimal concurrency strategies based on workload analysis and benchmarking.
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


def sample_workload(n: int) -> int:
    """Sample workload for optimization."""
    result = 0
    for i in range(n):
        result += i * i
    return result


async def main():
    """Run adaptive optimization demo."""
    logger.info("=" * 70)
    logger.info("Adaptive Optimization Demo")
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
    
    # Optimize workload
    logger.info("\nOptimizing workload...")
    result = await engine.optimize_strategy(sample_workload)
    
    logger.info(f"\nOptimization Result:")
    logger.info(f"  Selected Strategy: {result.selected_strategy}")
    logger.info(f"  Confidence: {result.confidence:.2f}")
    logger.info(f"  Expected Improvement: {result.expected_improvement:.2f}%")
    logger.info(f"  Reasoning: {result.reasoning}")
    
    if result.alternatives:
        logger.info(f"\n  Alternatives:")
        for alt in result.alternatives[:3]:
            logger.info(f"    - {alt['strategy']}: {alt['score']:.2f}")
    
    logger.info("\n" + "=" * 70)
    logger.info("Demo complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

