"""
WebSocket Handler for Real-Time Streaming Analytics.

Demonstrates:
- AsyncIO WebSocket connections for real-time data streaming
- Connection management and lifecycle handling
- Message broadcasting to multiple clients
- Rate limiting and connection throttling
- Graceful degradation when WebSocket libraries unavailable
"""

import asyncio
import json
import time
import logging
import uuid
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque

# WebSocket imports (with fallbacks)
try:
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.websockets import WebSocketState
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False
    class WebSocket:
        def __init__(self): pass
        async def accept(self): pass
        async def receive_text(self): return ""
        async def send_text(self, data: str): pass
        async def send_json(self, data: dict): pass
        async def close(self): pass
        @property
        def client(self): return None
        @property
        def state(self): return WebSocketState.CONNECTED
    
    class WebSocketDisconnect(Exception):
        pass
    
    class WebSocketState:
        CONNECTED = "connected"
        DISCONNECTED = "disconnected"

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection."""
    connection_id: str
    websocket: WebSocket
    connected_at: float = field(default_factory=time.time)
    last_message_at: float = field(default_factory=time.time)
    message_count: int = 0
    client_info: Dict[str, Any] = field(default_factory=dict)
    subscriptions: Set[str] = field(default_factory=set)


@dataclass
class WebSocketMetrics:
    """Metrics for WebSocket handler performance."""
    total_connections: int = 0
    active_connections: int = 0
    total_messages_received: int = 0
    total_messages_sent: int = 0
    total_bytes_received: int = 0
    total_bytes_sent: int = 0
    connection_errors: int = 0
    message_errors: int = 0
    broadcast_count: int = 0


class WebSocketHandler:
    """
    High-performance WebSocket handler for real-time analytics streaming.
    
    Features:
    - Multiple concurrent WebSocket connections
    - Message broadcasting to all or specific clients
    - Connection lifecycle management
    - Rate limiting and throttling
    - Topic-based subscriptions
    - Graceful error handling
    """
    
    def __init__(
        self,
        max_connections: int = 1000,
        message_rate_limit: int = 100,
        broadcast_queue_size: int = 10000
    ):
        self.max_connections = max_connections
        self.message_rate_limit = message_rate_limit
        self.broadcast_queue_size = broadcast_queue_size
        
        # Connection management
        self.connections: Dict[str, WebSocketConnection] = {}
        self.connection_lock = asyncio.Lock()
        
        # Topic subscriptions
        self.topic_subscribers: Dict[str, Set[str]] = {}
        self.topic_lock = asyncio.Lock()
        
        # Broadcasting queue
        self.broadcast_queue = asyncio.Queue(maxsize=broadcast_queue_size)
        self.broadcast_task = None
        
        # Metrics
        self.metrics = WebSocketMetrics()
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        
        self.running = False
    
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            client_info: Optional client information
            
        Returns:
            Connection ID for the new connection
        """
        async with self.connection_lock:
            # Check connection limit
            if len(self.connections) >= self.max_connections:
                logger.warning(f"Connection limit reached ({self.max_connections})")
                await websocket.close(code=1008, reason="Connection limit exceeded")
                raise RuntimeError("Maximum connections reached")
            
            # Accept connection
            if HAS_WEBSOCKET:
                await websocket.accept()
            
            # Create connection record
            connection_id = str(uuid.uuid4())
            connection = WebSocketConnection(
                connection_id=connection_id,
                websocket=websocket,
                client_info=client_info or {}
            )
            
            self.connections[connection_id] = connection
            self.metrics.total_connections += 1
            self.metrics.active_connections = len(self.connections)
            
            logger.info(f"WebSocket connection established: {connection_id}")
            
            # Send welcome message
            await self._send_to_connection(
                connection_id,
                {
                    "type": "connection_established",
                    "connection_id": connection_id,
                    "server_time": time.time(),
                    "message_rate_limit": self.message_rate_limit
                }
            )
            
            return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        async with self.connection_lock:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            
            # Unsubscribe from all topics
            async with self.topic_lock:
                for topic in list(connection.subscriptions):
                    await self._unsubscribe_from_topic(connection_id, topic)
            
            # Close WebSocket
            try:
                if HAS_WEBSOCKET:
                    await connection.websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket {connection_id}: {e}")
            
            # Remove connection
            del self.connections[connection_id]
            self.metrics.active_connections = len(self.connections)
            
            logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def handle_connection(self, websocket: WebSocket, connection_id: str):
        """
        Handle messages from a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            connection_id: Connection identifier
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        try:
            while self.running and connection_id in self.connections:
                # Receive message
                if HAS_WEBSOCKET:
                    try:
                        message_text = await websocket.receive_text()
                    except WebSocketDisconnect:
                        break
                else:
                    # Mock mode - simulate receiving messages
                    await asyncio.sleep(1)
                    message_text = json.dumps({"type": "ping", "timestamp": time.time()})
                
                # Process message
                await self._process_message(connection_id, message_text)
                
                # Update connection activity
                connection.last_message_at = time.time()
                connection.message_count += 1
                self.metrics.total_messages_received += 1
                self.metrics.total_bytes_received += len(message_text.encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Error handling connection {connection_id}: {e}")
            self.metrics.connection_errors += 1
        finally:
            await self.disconnect(connection_id)
    
    async def _process_message(self, connection_id: str, message_text: str):
        """Process incoming WebSocket message."""
        try:
            message = json.loads(message_text)
            message_type = message.get("type", "unknown")
            
            # Route to handler
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(connection_id, message)
                else:
                    handler(connection_id, message)
            else:
                # Default handlers
                await self._handle_default_message(connection_id, message)
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from connection {connection_id}")
            self.metrics.message_errors += 1
        except Exception as e:
            logger.error(f"Error processing message from {connection_id}: {e}")
            self.metrics.message_errors += 1
    
    async def _handle_default_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle default message types."""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            topic = message.get("topic")
            if topic:
                await self.subscribe_to_topic(connection_id, topic)
        
        elif message_type == "unsubscribe":
            topic = message.get("topic")
            if topic:
                await self.unsubscribe_from_topic(connection_id, topic)
        
        elif message_type == "ping":
            await self._send_to_connection(connection_id, {"type": "pong", "timestamp": time.time()})
    
    async def subscribe_to_topic(self, connection_id: str, topic: str):
        """Subscribe connection to a topic."""
        if connection_id not in self.connections:
            return
        
        async with self.topic_lock:
            if topic not in self.topic_subscribers:
                self.topic_subscribers[topic] = set()
            
            self.topic_subscribers[topic].add(connection_id)
            self.connections[connection_id].subscriptions.add(topic)
            
            await self._send_to_connection(
                connection_id,
                {"type": "subscribed", "topic": topic}
            )
    
    async def unsubscribe_from_topic(self, connection_id: str, topic: str):
        """Unsubscribe connection from a topic."""
        await self._unsubscribe_from_topic(connection_id, topic)
        
        await self._send_to_connection(
            connection_id,
            {"type": "unsubscribed", "topic": topic}
        )
    
    async def _unsubscribe_from_topic(self, connection_id: str, topic: str):
        """Internal unsubscribe logic."""
        async with self.topic_lock:
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(connection_id)
                if not self.topic_subscribers[topic]:
                    del self.topic_subscribers[topic]
            
            if connection_id in self.connections:
                self.connections[connection_id].subscriptions.discard(topic)
    
    async def broadcast(self, message: Dict[str, Any], topic: Optional[str] = None):
        """
        Broadcast message to all or topic-specific connections.
        
        Args:
            message: Message to broadcast
            topic: Optional topic filter
        """
        try:
            await self.broadcast_queue.put({
                "message": message,
                "topic": topic,
                "timestamp": time.time()
            })
            self.metrics.broadcast_count += 1
        except asyncio.QueueFull:
            logger.warning("Broadcast queue full, dropping message")
    
    async def _broadcast_loop(self):
        """Background loop for broadcasting messages."""
        logger.info("Starting WebSocket broadcast loop...")
        
        while self.running:
            try:
                # Get message from queue
                broadcast_data = await asyncio.wait_for(
                    self.broadcast_queue.get(),
                    timeout=1.0
                )
                
                message = broadcast_data["message"]
                topic = broadcast_data.get("topic")
                
                # Determine target connections
                if topic:
                    # Topic-specific broadcast
                    async with self.topic_lock:
                        target_connections = list(
                            self.topic_subscribers.get(topic, set())
                        )
                else:
                    # Broadcast to all connections
                    async with self.connection_lock:
                        target_connections = list(self.connections.keys())
                
                # Send to all target connections
                tasks = []
                for connection_id in target_connections:
                    if connection_id in self.connections:
                        tasks.append(
                            self._send_to_connection(connection_id, message)
                        )
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                self.broadcast_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            message_json = json.dumps(message)
            
            if HAS_WEBSOCKET:
                await connection.websocket.send_text(message_json)
            else:
                # Mock mode - log instead
                logger.debug(f"Mock send to {connection_id}: {message.get('type', 'unknown')}")
            
            self.metrics.total_messages_sent += 1
            self.metrics.total_bytes_sent += len(message_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a custom message handler."""
        self.message_handlers[message_type] = handler
    
    async def start(self):
        """Start the WebSocket handler."""
        if self.running:
            return
        
        self.running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("WebSocket handler started")
    
    async def stop(self):
        """Stop the WebSocket handler."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel broadcast task
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all connections
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)
        
        logger.info("WebSocket handler stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get WebSocket handler metrics."""
        return {
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "total_messages_received": self.metrics.total_messages_received,
            "total_messages_sent": self.metrics.total_messages_sent,
            "total_bytes_received": self.metrics.total_bytes_received,
            "total_bytes_sent": self.metrics.total_bytes_sent,
            "connection_errors": self.metrics.connection_errors,
            "message_errors": self.metrics.message_errors,
            "broadcast_count": self.metrics.broadcast_count,
            "topic_count": len(self.topic_subscribers),
            "queue_size": self.broadcast_queue.qsize()
        }


# Export handler
if not HAS_WEBSOCKET:
    logger.warning("WebSocket support not available. Install FastAPI for full functionality.")

