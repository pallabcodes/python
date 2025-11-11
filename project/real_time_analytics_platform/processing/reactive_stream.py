"""
Reactive Streams implementation for event processing pipelines.

Demonstrates:
- Reactive programming patterns
- Backpressure handling
- Event filtering and transformation
- Asynchronous stream processing
- Error handling and recovery
"""

import asyncio
import time
import logging
from typing import Any, Callable, List, Optional, Dict, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class StreamState(Enum):
    """States for reactive stream lifecycle."""
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamEvent:
    """Event wrapper for reactive streams."""
    data: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sequence_id: Optional[int] = None


@dataclass
class StreamMetrics:
    """Metrics for stream processing."""
    events_processed: int = 0
    events_filtered: int = 0
    processing_errors: int = 0
    backpressure_events: int = 0
    avg_processing_time: float = 0.0
    max_queue_size: int = 0


class ReactiveStream:
    """
    Reactive stream for asynchronous event processing.

    Features:
    - Map/Filter operations
    - Backpressure handling
    - Error recovery
    - Performance monitoring
    - Async iteration support
    """

    def __init__(self, name: str = "reactive_stream", buffer_size: int = 1000):
        self.name = name
        self.buffer_size = buffer_size
        self.state = StreamState.CREATED

        # Processing pipeline
        self._operations: List[Callable] = []
        self._subscribers: List[Callable] = []

        # Async queues for backpressure
        self._input_queue = asyncio.Queue(maxsize=buffer_size)
        self._processing_queue = asyncio.Queue(maxsize=buffer_size)

        # Control and monitoring
        self._processing_task: Optional[asyncio.Task] = None
        self._metrics = StreamMetrics()
        self._error_handler: Optional[Callable] = None

        # Synchronization
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

    async def emit(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Emit data into the stream.

        Returns True if successfully queued, False if backpressure triggered.
        """
        if self.state != StreamState.ACTIVE:
            return False

        try:
            event = StreamEvent(
                data=data,
                metadata=metadata or {},
                sequence_id=self._metrics.events_processed
            )

            await asyncio.wait_for(
                self._input_queue.put(event),
                timeout=1.0  # 1 second timeout for backpressure
            )

            self._metrics.max_queue_size = max(
                self._metrics.max_queue_size,
                self._input_queue.qsize()
            )

            return True

        except asyncio.TimeoutError:
            self._metrics.backpressure_events += 1
            logger.warning(f"Stream {self.name}: Backpressure triggered, queue full")
            return False

    def map(self, func: Callable[[Any], Any]) -> 'ReactiveStream':
        """Add a map operation to the pipeline."""
        self._operations.append(("map", func))
        return self

    def filter(self, predicate: Callable[[Any], bool]) -> 'ReactiveStream':
        """Add a filter operation to the pipeline."""
        self._operations.append(("filter", predicate))
        return self

    def flat_map(self, func: Callable[[Any], List[Any]]) -> 'ReactiveStream':
        """Add a flat_map operation to flatten nested structures."""
        self._operations.append(("flat_map", func))
        return self

    def buffer(self, size: int, timeout: float = 1.0) -> 'ReactiveStream':
        """Add buffering operation for batch processing."""
        self._operations.append(("buffer", (size, timeout)))
        return self

    def window(self, window_size: int, slide: int = 1) -> 'ReactiveStream':
        """Add windowing operation for sliding/tumbling windows."""
        self._operations.append(("window", (window_size, slide)))
        return self

    def distinct(self, key_func: Optional[Callable[[Any], Any]] = None) -> 'ReactiveStream':
        """Add distinct operation to remove duplicates."""
        seen = set()
        def distinct_filter(item):
            key = key_func(item) if key_func else item
            if key in seen:
                return False
            seen.add(key)
            return True
        self._operations.append(("filter", distinct_filter))
        return self

    def throttle(self, interval: float) -> 'ReactiveStream':
        """Throttle events to maximum rate."""
        last_emit = [0.0]  # Mutable closure
        def throttle_filter(item):
            current_time = time.time()
            if current_time - last_emit[0] >= interval:
                last_emit[0] = current_time
                return True
            return False
        self._operations.append(("filter", throttle_filter))
        return self

    def subscribe(self, subscriber: Callable[[Any], Union[None, Awaitable[None]]]):
        """Subscribe to stream events."""
        self._subscribers.append(subscriber)
        return self

    def on_error(self, error_handler: Callable[[Exception, Any], None]):
        """Set error handler for processing errors."""
        self._error_handler = error_handler
        return self

    async def start(self):
        """Start the reactive stream processing."""
        async with self._lock:
            if self.state != StreamState.CREATED:
                return

            self.state = StreamState.ACTIVE
            self._processing_task = asyncio.create_task(self._processing_loop())

            logger.info(f"Started reactive stream: {self.name}")

    async def stop(self):
        """Stop the reactive stream processing."""
        async with self._lock:
            if self.state != StreamState.ACTIVE:
                return

            self.state = StreamState.COMPLETED
            self._shutdown_event.set()

            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass

            logger.info(f"Stopped reactive stream: {self.name}")

    async def pause(self):
        """Pause stream processing."""
        async with self._lock:
            if self.state == StreamState.ACTIVE:
                self.state = StreamState.PAUSED
                logger.info(f"Paused reactive stream: {self.name}")

    async def resume(self):
        """Resume stream processing."""
        async with self._lock:
            if self.state == StreamState.PAUSED:
                self.state = StreamState.ACTIVE
                logger.info(f"Resumed reactive stream: {self.name}")

    async def _processing_loop(self):
        """Main processing loop for the reactive stream."""
        logger.info(f"Starting processing loop for stream: {self.name}")

        try:
            while not self._shutdown_event.is_set():
                try:
                    # Get next event with timeout
                    event = await asyncio.wait_for(
                        self._input_queue.get(),
                        timeout=0.1
                    )

                    # Process the event through pipeline
                    await self._process_event(event)

                    # Mark as processed
                    self._input_queue.task_done()

                except asyncio.TimeoutError:
                    # No events available, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    if self._error_handler:
                        self._error_handler(e, None)
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"Processing loop cancelled for stream: {self.name}")
        except Exception as e:
            logger.error(f"Fatal error in processing loop: {e}")
            self.state = StreamState.ERROR

    async def _process_event(self, event: StreamEvent):
        """Process a single event through the pipeline."""
        start_time = time.time()
        current_data = event.data

        try:
            # Apply each operation in sequence
            for op_type, op_func in self._operations:
                if op_type == "map":
                    current_data = op_func(current_data)
                    if asyncio.iscoroutine(current_data):
                        current_data = await current_data

                elif op_type == "filter":
                    should_pass = op_func(current_data)
                    if asyncio.iscoroutine(should_pass):
                        should_pass = await should_pass

                    if not should_pass:
                        self._metrics.events_filtered += 1
                        return  # Filtered out

                elif op_type == "flat_map":
                    mapped = op_func(current_data)
                    if asyncio.iscoroutine(mapped):
                        mapped = await mapped

                    if isinstance(mapped, (list, tuple)):
                        # Process each item in flattened result
                        for item in mapped:
                            await self._emit_to_subscribers(item)
                        return
                    else:
                        current_data = mapped

                elif op_type == "buffer":
                    # Buffer operation would be more complex in full implementation
                    # For demo, just pass through
                    pass

                elif op_type == "window":
                    # Windowing operation would be complex, skip for demo
                    pass

            # Event passed all operations, emit to subscribers
            await self._emit_to_subscribers(current_data)

            # Update metrics
            processing_time = time.time() - start_time
            self._metrics.events_processed += 1
            self._metrics.avg_processing_time = (
                (self._metrics.avg_processing_time * (self._metrics.events_processed - 1)) +
                processing_time
            ) / self._metrics.events_processed

        except Exception as e:
            self._metrics.processing_errors += 1
            logger.error(f"Error processing event: {e}")
            if self._error_handler:
                self._error_handler(e, event.data)

    async def _emit_to_subscribers(self, data: Any):
        """Emit processed data to all subscribers."""
        tasks = []

        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    tasks.append(subscriber(data))
                else:
                    # Run sync subscriber in thread pool
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, subscriber, data))
            except Exception as e:
                logger.error(f"Error emitting to subscriber: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_metrics(self) -> Dict[str, Any]:
        """Get stream processing metrics."""
        return {
            "stream_name": self.name,
            "state": self.state.value,
            "events_processed": self._metrics.events_processed,
            "events_filtered": self._metrics.events_filtered,
            "processing_errors": self._metrics.processing_errors,
            "backpressure_events": self._metrics.backpressure_events,
            "avg_processing_time": self._metrics.avg_processing_time,
            "max_queue_size": self._metrics.max_queue_size,
            "current_queue_size": self._input_queue.qsize(),
            "total_operations": len(self._operations),
            "subscriber_count": len(self._subscribers)
        }

    # Async iterator support
    def __aiter__(self):
        return self

    async def __anext__(self):
        """Async iterator implementation."""
        while True:
            try:
                event = await asyncio.wait_for(
                    self._input_queue.get(),
                    timeout=1.0
                )
                return event.data
            except asyncio.TimeoutError:
                if self.state == StreamState.COMPLETED:
                    raise StopAsyncIteration
                continue

    @asynccontextmanager
    async def subscribe_context(self, subscriber: Callable):
        """Context manager for temporary subscriptions."""
        self.subscribe(subscriber)
        try:
            yield
        finally:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)


# Utility functions for common stream operations
def create_validation_stream() -> ReactiveStream:
    """Create a stream for data validation."""
    return (ReactiveStream("validation_stream")
            .filter(lambda x: isinstance(x, dict))
            .filter(lambda x: "event_id" in x)
            .filter(lambda x: "data" in x))


def create_analytics_stream() -> ReactiveStream:
    """Create a stream for analytics processing."""
    return (ReactiveStream("analytics_stream")
            .filter(lambda x: x.get("priority", 1) >= 2)  # High priority only
            .throttle(0.1)  # Max 10 events per second
            .map(lambda x: {**x, "processed_at": time.time()}))


def create_monitoring_stream() -> ReactiveStream:
    """Create a stream for system monitoring."""
    return (ReactiveStream("monitoring_stream")
            .buffer(10, 1.0)  # Buffer 10 events or 1 second
            .map(lambda batch: {
                "batch_size": len(batch),
                "avg_priority": sum(x.get("priority", 1) for x in batch) / len(batch),
                "timestamp": time.time()
            }))
