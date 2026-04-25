"""
Refactored Consensus Module
Patterns: Strategy (Transport), Factory (Node Creation), State Machine (Raft)
"""

import asyncio
import time
import logging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .transport import AbstractTransport, RaftMessage

logger = logging.getLogger(__name__)

class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

@dataclass
class LogEntry:
    term: int
    index: int
    command: Any

class ConsensusCoordinator:
    """
    Raft Consensus implementation using Strategy Pattern for Transport.
    """
    
    def __init__(self, node_id: str, transport: AbstractTransport, peers: List[str]):
        self.node_id = node_id
        self.transport = transport
        self.peers = peers
        
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log: List[LogEntry] = []
        self.commit_index = 0
        
        self._lock = asyncio.Lock()
        self._election_timeout = 2.0 + (uuid.uuid4().int % 1000) / 500.0 # Random jitter
        self._last_heartbeat = time.time()
        self._active = False

    async def start(self):
        self._active = True
        asyncio.create_task(self.transport.listen(self._on_message))
        asyncio.create_task(self._election_timer())

    async def _on_message(self, message: RaftMessage) -> Optional[RaftMessage]:
        async with self._lock:
            if message.term > self.current_term:
                self.current_term = message.term
                self.state = NodeState.FOLLOWER
                self.voted_for = None
            
            if message.type == "request_vote":
                return await self._handle_vote_request(message)
            elif message.type == "append_entries":
                return await self._handle_append_entries(message)
        return None

    async def _election_timer(self):
        while self._active:
            await asyncio.sleep(0.1)
            async with self._lock:
                if self.state != NodeState.LEADER:
                    if time.time() - self._last_heartbeat > self._election_timeout:
                        await self._start_election()

    async def _start_election(self):
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self._last_heartbeat = time.time()
        logger.info(f"Node {self.node_id} starting election for term {self.current_term}")
        
        votes = 1
        for peer in self.peers:
            msg = RaftMessage("request_vote", self.node_id, self.current_term, {})
            resp = await self.transport.send(peer, msg)
            if resp and resp.data.get("vote_granted"):
                votes += 1
        
        if votes > (len(self.peers) + 1) / 2:
            await self._become_leader()

    async def _become_leader(self):
        self.state = NodeState.LEADER
        logger.info(f"Node {self.node_id} became LEADER for term {self.current_term}")
        asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.state == NodeState.LEADER and self._active:
            for peer in self.peers:
                msg = RaftMessage("append_entries", self.node_id, self.current_term, {})
                await self.transport.send(peer, msg)
            await asyncio.sleep(0.5)

    async def _handle_vote_request(self, msg: RaftMessage) -> RaftMessage:
        granted = False
        if msg.term >= self.current_term and (self.voted_for is None or self.voted_for == msg.sender_id):
            granted = True
            self.voted_for = msg.sender_id
            self._last_heartbeat = time.time()
        
        return RaftMessage("vote_response", self.node_id, self.current_term, {"vote_granted": granted})

    async def _handle_append_entries(self, msg: RaftMessage) -> RaftMessage:
        self._last_heartbeat = time.time()
        return RaftMessage("append_response", self.node_id, self.current_term, {"success": True})

class ConsensusFactory:
    """Factory Pattern: Creating nodes with the right configuration."""
    
    @staticmethod
    def create_socket_node(node_id: str, host: str, port: int, peer_map: Dict[str, str]) -> ConsensusCoordinator:
        from .transport import SocketTransport
        transport = SocketTransport(node_id, host, port, peer_map)
        peers = [pid for pid in peer_map.keys() if pid != node_id]
        return ConsensusCoordinator(node_id, transport, peers)
