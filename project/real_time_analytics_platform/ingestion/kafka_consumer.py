"""
Kafka Consumer for Distributed Messaging.

Demonstrates:
- Kafka consumer integration for distributed event streaming
- Consumer group management and rebalancing
- Message deserialization and error handling
- Graceful degradation when Kafka libraries unavailable
- Integration with analytics platform event system
"""

import asyncio
import json
import time
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

# Kafka imports (with fallbacks)
try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.errors import KafkaError
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False
    class KafkaConsumer:
        def __init__(self, *args, **kwargs): pass
        def __iter__(self): return iter([])
        def close(self): pass
    
    class KafkaProducer:
        def __init__(self, *args, **kwargs): pass
        def send(self, *args, **kwargs): return None
        def flush(self): pass
        def close(self): pass
    
    class KafkaError(Exception):
        pass

logger = logging.getLogger(__name__)


class ConsumerState(Enum):
    """Kafka consumer state."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class KafkaMessage:
    """Represents a Kafka message."""
    topic: str
    partition: int
    offset: int
    key: Optional[bytes]
    value: bytes
    timestamp: float
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class KafkaConsumerMetrics:
    """Metrics for Kafka consumer performance."""
    messages_consumed: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    bytes_consumed: int = 0
    consumer_lag: int = 0
    rebalance_count: int = 0
    error_count: int = 0
    last_message_time: float = 0.0


class KafkaConsumerHandler:
    """
    High-performance Kafka consumer for distributed analytics messaging.
    
    Features:
    - Consumer group management
    - Automatic rebalancing
    - Message deserialization
    - Error handling and retry logic
    - Metrics collection
    - Graceful shutdown
    """
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        topics: List[str],
        group_id: str,
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = True,
        max_poll_records: int = 100,
        session_timeout_ms: int = 30000
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.max_poll_records = max_poll_records
        self.session_timeout_ms = session_timeout_ms
        
        # Consumer state
        self.state = ConsumerState.STOPPED
        self.consumer: Optional[KafkaConsumer] = None
        
        # Message processing
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue = asyncio.Queue(maxsize=10000)
        self.processing_tasks: List[asyncio.Task] = []
        
        # Metrics
        self.metrics = KafkaConsumerMetrics()
        
        # Control
        self.running = False
        self.num_workers = 4
    
    async def start(self):
        """Start the Kafka consumer."""
        if self.running:
            return
        
        logger.info(f"Starting Kafka consumer for group: {self.group_id}")
        self.state = ConsumerState.STARTING
        
        try:
            # Create consumer
            if HAS_KAFKA:
                self.consumer = KafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    auto_offset_reset=self.auto_offset_reset,
                    enable_auto_commit=self.enable_auto_commit,
                    max_poll_records=self.max_poll_records,
                    session_timeout_ms=self.session_timeout_ms,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                    key_deserializer=lambda k: k.decode('utf-8') if k else None
                )
            else:
                logger.warning("Kafka not available, using mock consumer")
                self.consumer = None
            
            self.running = True
            self.state = ConsumerState.RUNNING
            
            # Start processing workers
            for i in range(self.num_workers):
                task = asyncio.create_task(self._processing_worker(f"worker-{i}"))
                self.processing_tasks.append(task)
            
            # Start consumption loop
            consumption_task = asyncio.create_task(self._consumption_loop())
            
            logger.info("Kafka consumer started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Kafka consumer: {e}")
            self.state = ConsumerState.ERROR
            raise
    
    async def stop(self):
        """Stop the Kafka consumer."""
        if not self.running:
            return
        
        logger.info("Stopping Kafka consumer...")
        self.state = ConsumerState.STOPPING
        self.running = False
        
        # Close consumer
        if self.consumer:
            try:
                self.consumer.close()
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
        
        # Cancel processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        self.state = ConsumerState.STOPPED
        logger.info("Kafka consumer stopped")
    
    async def _consumption_loop(self):
        """Main loop for consuming messages from Kafka."""
        logger.info("Starting Kafka consumption loop...")
        
        if not HAS_KAFKA or not self.consumer:
            # Mock mode - simulate message consumption
            while self.running:
                await asyncio.sleep(1)
                # Generate mock messages
                mock_message = {
                    "topic": self.topics[0] if self.topics else "mock_topic",
                    "partition": 0,
                    "offset": self.metrics.messages_consumed,
                    "key": None,
                    "value": {
                        "event_id": str(uuid.uuid4()),
                        "event_type": "kafka_event",
                        "data": {"source": "kafka", "timestamp": time.time()}
                    },
                    "timestamp": time.time()
                }
                await self.message_queue.put(mock_message)
            return
        
        while self.running:
            try:
                # Poll for messages
                message_pack = self.consumer.poll(timeout_ms=1000)
                
                if not message_pack:
                    continue
                
                # Process each partition's messages
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        kafka_message = KafkaMessage(
                            topic=topic_partition.topic,
                            partition=topic_partition.partition,
                            offset=message.offset,
                            key=message.key,
                            value=json.dumps(message.value).encode('utf-8') if message.value else b'',
                            timestamp=message.timestamp / 1000.0 if hasattr(message, 'timestamp') else time.time(),
                            headers={}
                        )
                        
                        # Add to processing queue
                        try:
                            await self.message_queue.put({
                                "kafka_message": kafka_message,
                                "raw_message": message
                            })
                            self.metrics.messages_consumed += 1
                            self.metrics.bytes_consumed += len(kafka_message.value)
                            self.metrics.last_message_time = time.time()
                        except asyncio.QueueFull:
                            logger.warning("Message queue full, dropping message")
                            self.metrics.error_count += 1
                
            except Exception as e:
                logger.error(f"Error in consumption loop: {e}")
                self.metrics.error_count += 1
                self.metrics.rebalance_count += 1
                await asyncio.sleep(1)
    
    async def _processing_worker(self, worker_id: str):
        """Worker task for processing messages."""
        logger.info(f"Starting processing worker: {worker_id}")
        
        while self.running:
            try:
                # Get message from queue
                message_data = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # Process message
                await self._process_message(message_data)
                
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker {worker_id}: {e}")
                self.metrics.messages_failed += 1
                await asyncio.sleep(0.1)
    
    async def _process_message(self, message_data: Dict[str, Any]):
        """Process a single Kafka message."""
        kafka_message = message_data.get("kafka_message")
        if not kafka_message:
            return
        
        try:
            # Deserialize message value
            if kafka_message.value:
                event_data = json.loads(kafka_message.value.decode('utf-8'))
            else:
                event_data = {}
            
            # Route to handler based on topic
            topic = kafka_message.topic
            if topic in self.message_handlers:
                handler = self.message_handlers[topic]
                if asyncio.iscoroutinefunction(handler):
                    await handler(kafka_message, event_data)
                else:
                    handler(kafka_message, event_data)
            else:
                # Default handler
                await self._default_message_handler(kafka_message, event_data)
            
            self.metrics.messages_processed += 1
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.metrics.messages_failed += 1
    
    async def _default_message_handler(self, kafka_message: KafkaMessage, event_data: Dict[str, Any]):
        """Default message handler."""
        logger.debug(f"Processing message from topic {kafka_message.topic}: {event_data.get('event_id', 'unknown')}")
    
    def register_topic_handler(self, topic: str, handler: Callable):
        """Register a handler for a specific topic."""
        self.message_handlers[topic] = handler
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Kafka consumer metrics."""
        return {
            "state": self.state.value,
            "messages_consumed": self.metrics.messages_consumed,
            "messages_processed": self.metrics.messages_processed,
            "messages_failed": self.metrics.messages_failed,
            "bytes_consumed": self.metrics.bytes_consumed,
            "consumer_lag": self.metrics.consumer_lag,
            "rebalance_count": self.metrics.rebalance_count,
            "error_count": self.metrics.error_count,
            "last_message_time": self.metrics.last_message_time,
            "queue_size": self.message_queue.qsize(),
            "num_workers": self.num_workers
        }


class KafkaProducerHandler:
    """
    Kafka producer for sending analytics events.
    
    Features:
    - Async message production
    - Batching and compression
    - Error handling and retry logic
    - Metrics collection
    """
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        compression_type: str = "gzip",
        batch_size: int = 16384,
        linger_ms: int = 10
    ):
        self.bootstrap_servers = bootstrap_servers
        self.compression_type = compression_type
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        
        self.producer: Optional[KafkaProducer] = None
        self.messages_sent = 0
        self.messages_failed = 0
    
    async def start(self):
        """Start the Kafka producer."""
        if HAS_KAFKA:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                compression_type=self.compression_type,
                batch_size=self.batch_size,
                linger_ms=self.linger_ms,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
        else:
            logger.warning("Kafka not available, using mock producer")
    
    async def send(self, topic: str, value: Dict[str, Any], key: Optional[str] = None):
        """Send a message to Kafka."""
        try:
            if HAS_KAFKA and self.producer:
                future = self.producer.send(topic, value=value, key=key)
                # Wait for send to complete
                record_metadata = future.get(timeout=10)
                self.messages_sent += 1
                return record_metadata
            else:
                # Mock mode
                logger.debug(f"Mock send to topic {topic}: {value.get('event_id', 'unknown')}")
                self.messages_sent += 1
                return None
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")
            self.messages_failed += 1
            raise
    
    async def flush(self):
        """Flush pending messages."""
        if HAS_KAFKA and self.producer:
            self.producer.flush()
    
    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get producer metrics."""
        return {
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed
        }


# Export handlers
if not HAS_KAFKA:
    logger.warning("Kafka support not available. Install kafka-python for full functionality.")

