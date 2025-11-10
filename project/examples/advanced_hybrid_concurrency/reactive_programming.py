"""
Reactive Programming Patterns for Hybrid Concurrency.

This module implements reactive programming patterns using streams,
observables, and backpressure handling for event-driven concurrency.

Features:
- Reactive streams with operators
- RxPY integration for observables
- Backpressure handling
- Async reactive streams
"""

import asyncio
import threading
import time
import logging
from typing import Any, Callable, List, Dict, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Optional RxPY import
try:
    import rx
    from rx import operators as ops
    from rx.subject import Subject
    RXPY_AVAILABLE = True
except ImportError:
    rx = None
    ops = None
    Subject = None
    RXPY_AVAILABLE = False


@dataclass
class StreamEvent:
    """Event in a reactive stream."""
    data: Any
    timestamp: float = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


class ReactiveStream:
    """Basic reactive stream implementation."""

    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self._subscribers: List[Callable] = []
        self._operators: List[Callable] = []
        self._running = False
        self._lock = threading.Lock()

    def subscribe(self, subscriber: Callable):
        """Subscribe to stream events."""
        with self._lock:
            self._subscribers.append(subscriber)

    def map(self, func: Callable) -> 'ReactiveStream':
        """Apply map operator."""
        self._operators.append(lambda x: func(x))
        return self

    def filter(self, predicate: Callable[[Any], bool]) -> 'ReactiveStream':
        """Apply filter operator."""
        self._operators.append(lambda x: x if predicate(x) else None)
        return self

    def emit(self, data: Any):
        """Emit data to stream."""
        event = StreamEvent(data)

        # Apply operators
        current = event
        for operator in self._operators:
            result = operator(current.data)
            if result is None:  # Filtered out
                return
            current = StreamEvent(result, current.timestamp, current.metadata)

        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                subscriber(current)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")


class RxPyObservable:
    """RxPY-based observable wrapper."""

    def __init__(self):
        if not RXPY_AVAILABLE:
            raise ImportError("RxPY not available")

        self.subject = Subject()

    def subscribe(self, observer):
        """Subscribe to observable."""
        return self.subject.subscribe(observer)

    def on_next(self, value):
        """Emit value."""
        self.subject.on_next(value)

    def on_error(self, error):
        """Emit error."""
        self.subject.on_error(error)

    def on_completed(self):
        """Complete observable."""
        self.subject.on_completed()

    def pipe(self, *operators):
        """Apply operators."""
        return self.subject.pipe(*operators)


class AsyncReactiveStream:
    """Async reactive stream with backpressure."""

    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self._subscribers: List[Callable] = []
        self._running = False

    async def emit(self, data: Any):
        """Emit data with backpressure."""
        await self._queue.put(data)
        await self._process_emissions()

    async def _process_emissions(self):
        """Process emissions to subscribers."""
        try:
            while not self._queue.empty():
                data = self._queue.get_nowait()

                # Notify all subscribers
                tasks = []
                for subscriber in self._subscribers:
                    task = asyncio.create_task(self._notify_subscriber(subscriber, data))
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)
                self._queue.task_done()

        except Exception as e:
            logger.error(f"Stream processing error: {e}")

    async def _notify_subscriber(self, subscriber: Callable, data: Any):
        """Notify subscriber asynchronously."""
        try:
            await subscriber(data)
        except Exception as e:
            logger.error(f"Subscriber error: {e}")

    def subscribe(self, subscriber: Callable):
        """Subscribe to stream."""
        self._subscribers.append(subscriber)


class BackpressureHandler:
    """Backpressure handling strategies."""

    @staticmethod
    def drop_oldest(queue: asyncio.Queue, max_size: int):
        """Drop oldest items when queue is full."""
        while queue.qsize() >= max_size:
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break

    @staticmethod
    def drop_newest(queue: asyncio.Queue, item: Any, max_size: int):
        """Drop new item when queue is full."""
        if queue.qsize() >= max_size:
            return False  # Don't add
        queue.put_nowait(item)
        return True

    @staticmethod
    async def block_until_space(queue: asyncio.Queue, item: Any, max_size: int):
        """Block until space is available."""
        while queue.qsize() >= max_size:
            await asyncio.sleep(0.01)
        await queue.put(item)


class StreamProcessor:
    """Stream processing with reactive patterns."""

    def __init__(self):
        self.streams: Dict[str, ReactiveStream] = {}

    def create_stream(self, name: str) -> ReactiveStream:
        """Create named stream."""
        stream = ReactiveStream()
        self.streams[name] = stream
        return stream

    def connect_streams(self, from_stream: str, to_stream: str):
        """Connect streams for pipeline processing."""
        source = self.streams.get(from_stream)
        target = self.streams.get(to_stream)

        if source and target:
            source.subscribe(lambda event: target.emit(event.data))

    async def process_pipeline(self, pipeline_config: Dict[str, Any]):
        """Process data through pipeline."""
        # Implementation for pipeline processing
        pass


async def demonstrate_reactive_patterns():
    """Demonstrate reactive programming patterns."""
    print("⚡ Reactive Programming Demonstration")
    print("=" * 40)

    # Basic reactive stream
    print("\n1. Basic Reactive Stream:")
    stream = ReactiveStream()

    def print_subscriber(event):
        print(f"Received: {event.data} at {event.timestamp:.2f}")

    stream.subscribe(print_subscriber)
    stream.map(lambda x: x * 2).filter(lambda x: x > 5)

    for i in range(10):
        stream.emit(i)
        await asyncio.sleep(0.1)

    # Async reactive stream
    print("\n2. Async Reactive Stream:")
    async_stream = AsyncReactiveStream()

    async def async_subscriber(data):
        await asyncio.sleep(0.05)
        print(f"Async received: {data}")

    async_stream.subscribe(async_subscriber)

    for i in range(5):
        await async_stream.emit(f"async_{i}")

    # RxPY demonstration (if available)
    if RXPY_AVAILABLE:
        print("\n3. RxPY Observable:")
        observable = RxPyObservable()

        observable.subscribe(
            on_next=lambda x: print(f"RxPY: {x}"),
            on_error=lambda e: print(f"RxPY Error: {e}"),
            on_completed=lambda: print("RxPY Completed")
        )

        # Apply operators
        observable.pipe(
            ops.map(lambda x: x * 10),
            ops.filter(lambda x: x > 20)
        )

        for i in range(10):
            observable.on_next(i)

        observable.on_completed()

    print("\n✅ Reactive programming demonstration complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demonstrate_reactive_patterns())
