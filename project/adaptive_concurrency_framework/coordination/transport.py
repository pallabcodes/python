import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RaftMessage:
    type: str  # "request_vote", "append_entries", etc.
    sender_id: str
    term: int
    data: Dict[str, Any]

class AbstractTransport(ABC):
    """Strategy Pattern: Abstract base for consensus communication."""
    
    @abstractmethod
    async def send(self, target_id: str, message: RaftMessage) -> Optional[RaftMessage]:
        pass

    @abstractmethod
    async def listen(self, callback) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

class SocketTransport(AbstractTransport):
    """Concrete Strategy: Real TCP-based communication."""
    
    def __init__(self, node_id: str, host: str, port: int, peer_map: Dict[str, str]):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peer_map = peer_map # node_id -> "host:port"
        self.server = None
        self.callback = None

    async def listen(self, callback) -> None:
        self.callback = callback
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info(f"Node {self.node_id} listening on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()

    async def _handle_client(self, reader, writer):
        data = await reader.read(1024)
        # In real implementation: deserialize data, call callback, write response
        writer.close()

    async def send(self, target_id: str, message: RaftMessage) -> Optional[RaftMessage]:
        if target_id not in self.peer_map:
            return None
        # In real implementation: connect to target, send message, wait for response
        return None

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
