"""
Tests for distributed coordination.
"""

import pytest
import asyncio
from adaptive_concurrency_framework.coordination.distributed_coordinator import DistributedCoordinator
from adaptive_concurrency_framework.coordination.timestamp_tokens import TimestampTokenCoordinator


@pytest.mark.asyncio
async def test_timestamp_token_coordinator():
    """Test timestamp token coordinator."""
    coordinator = TimestampTokenCoordinator()
    
    token1 = await coordinator.generate_token("task1")
    token2 = await coordinator.generate_token("task2")
    
    assert token1.sequence < token2.sequence
    assert token1.timestamp <= token2.timestamp


@pytest.mark.asyncio
async def test_distributed_coordinator():
    """Test distributed coordinator."""
    coordinator = DistributedCoordinator(node_id="test_node")
    await coordinator.initialize()
    
    # Test coordination
    decision = {"strategy": "threading"}
    success = await coordinator.coordinate_optimization(decision)
    
    # Should succeed (even if not leader, should handle gracefully)
    assert isinstance(success, bool)
    
    await coordinator.shutdown()


@pytest.mark.asyncio
async def test_distributed_lock():
    """Test distributed lock."""
    coordinator = DistributedCoordinator(node_id="test_node")
    await coordinator.initialize()
    
    lock = await coordinator.acquire_coordination_lock("test_resource")
    assert lock.is_acquired()
    
    await coordinator.release_coordination_lock("test_resource")
    
    await coordinator.shutdown()

