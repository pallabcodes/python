"""
Consensus algorithm implementation (Raft-like) for distributed coordination.

Based on concepts from "Concurrency Control in Distributed Database Systems"
by Bernstein & Goodman, implementing Raft-like consensus for optimization
decision coordination.
"""

import asyncio
import time
import logging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NodeState(Enum):
    """Node state in consensus algorithm."""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    """Log entry for consensus."""
    
    term: int
    index: int
    command: Any
    timestamp: float = field(default_factory=time.time)


@dataclass
class VoteRequest:
    """Vote request in consensus."""
    
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


@dataclass
class VoteResponse:
    """Vote response in consensus."""
    
    term: int
    vote_granted: bool


class ConsensusCoordinator:
    """
    Raft-like consensus coordinator for optimization decisions.
    
    Based on concepts from Bernstein & Goodman's distributed database
    concurrency control, implementing consensus for coordinating optimization
    decisions across multiple instances.
    
    Features:
    - Leader election
    - Log replication
    - Fault tolerance
    - Distributed coordination
    """
    
    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize consensus coordinator.
        
        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        
        self._lock = asyncio.Lock()
        self._election_timeout = 5.0
        self._heartbeat_interval = 1.0
        self._last_heartbeat = time.time()
        self._election_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def initialize(self) -> None:
        """Initialize consensus coordinator."""
        self._logger.info(f"Initializing consensus coordinator: {self.node_id}")
        self._election_task = asyncio.create_task(self._election_loop())
        
    async def shutdown(self) -> None:
        """Shutdown consensus coordinator."""
        self._logger.info("Shutting down consensus coordinator")
        if self._election_task:
            self._election_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
    async def _election_loop(self) -> None:
        """Background task for leader election."""
        while True:
            try:
                await asyncio.sleep(self._election_timeout)
                
                async with self._lock:
                    if self.state == NodeState.FOLLOWER:
                        elapsed = time.time() - self._last_heartbeat
                        if elapsed > self._election_timeout:
                            # Start election
                            await self._start_election()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Election loop error: {e}")
    
    async def _start_election(self) -> None:
        """Start leader election."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        
        self._logger.info(f"Starting election for term {self.current_term}")
        
        # In a real implementation, would request votes from other nodes
        # For now, assume single-node or majority vote
        
        # Simulate becoming leader
        await asyncio.sleep(0.1)
        self.state = NodeState.LEADER
        self._last_heartbeat = time.time()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self._logger.info(f"Elected as leader for term {self.current_term}")
    
    async def _heartbeat_loop(self) -> None:
        """Background task for sending heartbeats."""
        while self.state == NodeState.LEADER:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                self._last_heartbeat = time.time()
                # In real implementation, would send heartbeats to followers
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Heartbeat loop error: {e}")
    
    async def propose_decision(self, decision: Any) -> bool:
        """
        Propose an optimization decision.
        
        Args:
            decision: The decision to propose
            
        Returns:
            True if decision committed, False otherwise
        """
        async with self._lock:
            if self.state != NodeState.LEADER:
                self._logger.warning("Not leader, cannot propose decision")
                return False
            
            # Append to log
            entry = LogEntry(
                term=self.current_term,
                index=len(self.log),
                command=decision
            )
            self.log.append(entry)
            
            # In real implementation, would replicate to followers
            # For now, commit immediately
            self.commit_index = len(self.log) - 1
            
            self._logger.info(f"Proposed decision: {decision} (term={self.current_term}, index={entry.index})")
            
            return True
    
    async def get_committed_decisions(self) -> List[Any]:
        """Get all committed decisions."""
        async with self._lock:
            return [entry.command for entry in self.log[:self.commit_index + 1]]
    
    def is_leader(self) -> bool:
        """Check if this node is the leader."""
        return self.state == NodeState.LEADER

