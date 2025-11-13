"""
Real-time data ingestion layer using AsyncIO.

Provides:
- REST API ingestion with rate limiting and circuit breakers
- WebSocket handler for real-time streaming
- Kafka consumer for distributed messaging
"""

from .api_server import APIServer
from .websocket_handler import WebSocketHandler
from .kafka_consumer import KafkaConsumerHandler, KafkaProducerHandler

__all__ = [
    "APIServer",
    "WebSocketHandler",
    "KafkaConsumerHandler",
    "KafkaProducerHandler"
]
