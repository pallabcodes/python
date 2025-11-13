"""
Distributed coordinator for multi-instance optimization coordination.

Combines:
- Consensus algorithms (Raft-like)
- Distributed locking
- CRDT state sharing
- Actor model (Pykka-inspired)
- Reactive streams
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .consensus import ConsensusCoordinator
from .distributed_locking import DistributedLock
from .crdt_state import CRDTState, ObservableAtomicConsistencyProtocol

logger = logging.getLogger(__name__)


class DistributedCoordinator:
    """
    Distributed coordinator for multi-instance optimization.
    
    Combines multiple coordination mechanisms:
    - Consensus for decision coordination
    - Distributed locks for resource access
    - CRDT state for shared optimization insights
    - Actor model for message passing
    - Reactive streams for event handling
    """
    
    def __init__(self, node_id: Optional[str] = None):
        """Initialize distributed coordinator."""
        self.node_id = node_id
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._consensus = ConsensusCoordinator(node_id)
        self._crdt_state = CRDTState(node_id or "default")
        self._oacp = ObservableAtomicConsistencyProtocol(node_id or "default")
        
        self._locks: Dict[str, DistributedLock] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize distributed coordinator."""
        if self._initialized:
            return
        
        await self._consensus.initialize()
        self._initialized = True
        self._logger.info("Distributed coordinator initialized")
    
    async def shutdown(self) -> None:
        """Shutdown distributed coordinator."""
        await self._consensus.shutdown()
        
        # Release all locks
        for lock in self._locks.values():
            if lock.is_acquired():
                await lock.release()
        
        self._initialized = False
        self._logger.info("Distributed coordinator shut down")
    
    async def coordinate_optimization(self, optimization_decision: Any) -> bool:
        """
        Coordinate an optimization decision across instances.
        
        Args:
            optimization_decision: The optimization decision to coordinate
            
        Returns:
            True if decision coordinated successfully
        """
        if not self._initialized:
            await self.initialize()
        
        # Use consensus to propose decision
        if self._consensus.is_leader():
            success = await self._consensus.propose_decision(optimization_decision)
            
            if success:
                # Share decision via CRDT state
                await self._oacp.set_state("latest_optimization", optimization_decision)
                self._logger.info(f"Coordinated optimization decision: {optimization_decision}")
            
            return success
        else:
            self._logger.debug("Not leader, cannot coordinate optimization")
            return False
    
    async def get_shared_optimization_state(self) -> Dict[str, Any]:
        """Get shared optimization state from CRDT."""
        return await self._oacp.get_state()
    
    async def acquire_coordination_lock(self, resource_name: str) -> DistributedLock:
        """
        Acquire a distributed lock for coordination.
        
        Args:
            resource_name: Name of the resource to lock
            
        Returns:
            DistributedLock instance
        """
        if resource_name not in self._locks:
            self._locks[resource_name] = DistributedLock(resource_name, owner_id=self.node_id)
        
        lock = self._locks[resource_name]
        await lock.acquire()
        
        return lock
    
    async def release_coordination_lock(self, resource_name: str) -> None:
        """Release a distributed lock."""
        if resource_name in self._locks:
            await self._locks[resource_name].release()

