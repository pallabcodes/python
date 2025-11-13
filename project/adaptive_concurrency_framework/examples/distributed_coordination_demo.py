"""
Distributed coordination demonstration.

This demo showcases distributed coordination using consensus algorithms,
distributed locking, and CRDT state sharing.
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from adaptive_concurrency_framework.coordination.distributed_coordinator import DistributedCoordinator
from adaptive_concurrency_framework.coordination.timestamp_tokens import TimestampTokenCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run distributed coordination demo."""
    logger.info("=" * 70)
    logger.info("Distributed Coordination Demo")
    logger.info("=" * 70)
    
    # Test timestamp tokens
    logger.info("\n1. Testing Timestamp Tokens...")
    token_coordinator = TimestampTokenCoordinator()
    
    token1 = await token_coordinator.generate_token("task1", {"type": "optimization"})
    token2 = await token_coordinator.generate_token("task2", {"type": "benchmark"})
    
    logger.info(f"   Token 1: sequence={token1.sequence}, timestamp={token1.timestamp}")
    logger.info(f"   Token 2: sequence={token2.sequence}, timestamp={token2.timestamp}")
    
    comparison = await token_coordinator.compare_tokens(token1, token2)
    logger.info(f"   Comparison: token1 {'<' if comparison < 0 else '>' if comparison > 0 else '=='} token2")
    
    # Test distributed coordinator
    logger.info("\n2. Testing Distributed Coordinator...")
    coordinator = DistributedCoordinator(node_id="demo_node")
    await coordinator.initialize()
    
    # Coordinate an optimization decision
    decision = {"strategy": "threading", "confidence": 0.85}
    success = await coordinator.coordinate_optimization(decision)
    logger.info(f"   Coordination success: {success}")
    
    # Get shared state
    shared_state = await coordinator.get_shared_optimization_state()
    logger.info(f"   Shared state: {shared_state}")
    
    # Test distributed lock
    logger.info("\n3. Testing Distributed Lock...")
    lock = await coordinator.acquire_coordination_lock("optimization_resource")
    logger.info(f"   Lock acquired: {lock.is_acquired()}")
    
    await coordinator.release_coordination_lock("optimization_resource")
    logger.info(f"   Lock released")
    
    await coordinator.shutdown()
    
    logger.info("\n" + "=" * 70)
    logger.info("Demo complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

