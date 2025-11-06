"""
Producer-consumer queue implementation with graceful shutdown.

This module provides a production-grade producer-consumer pattern
implementation using Python's queue.Queue. It demonstrates proper
thread coordination, graceful shutdown using DONE sentinels, and
backpressure handling with bounded queues.
"""

import threading
import time
import logging
from queue import Queue, Full, Empty
from typing import Any, Optional, Callable, List, Dict
from dataclasses import dataclass
from enum import Enum


class ShutdownSignal:
    """Sentinel object for signaling graceful shutdown.

    This singleton is used as a sentinel value in queues to signal
    that producers have finished and consumers should shut down
    gracefully.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __str__(self) -> str:
        return "<ShutdownSignal>"

    def __repr__(self) -> str:
        return "ShutdownSignal()"


# Global shutdown sentinel instance
DONE = ShutdownSignal()


class ProducerConsumerQueue:
    """Thread-safe producer-consumer queue with graceful shutdown.

    This class implements the classic producer-consumer pattern using
    Python's queue.Queue. It supports multiple producers and consumers,
    graceful shutdown via DONE sentinels, and optional bounded queues
    for backpressure control.

    Features:
    - Multiple producer and consumer threads
    - Graceful shutdown using DONE sentinels
    - Bounded queues for backpressure
    - Comprehensive monitoring and logging
    - Configurable timeouts and retry logic

    Attributes:
        _queue: Internal queue for message passing.
        _producers: List of active producer threads.
        _consumers: List of active consumer threads.
        _shutdown_event: Event for coordinating shutdown.
        _logger: Structured logger with correlation IDs.
    """

    def __init__(
        self,
        maxsize: int = 0,
        name: str = "ProducerConsumerQueue"
    ) -> None:
        """Initialize the producer-consumer queue.

        Args:
            maxsize: Maximum queue size (0 for unbounded).
            name: Queue name for logging and identification.

        Raises:
            ValueError: If maxsize is negative.
        """
        if maxsize < 0:
            raise ValueError("maxsize cannot be negative")

        self._queue: Queue[Any] = Queue(maxsize=maxsize)
        self._producers: List[ProducerThread] = []
        self._consumers: List[ConsumerThread] = []
        self._shutdown_event = threading.Event()
        self._name = name
        self._logger = logging.getLogger(__name__)

        self._logger.info(
            f"ProducerConsumerQueue '{name}' initialized",
            extra={
                "queue_name": name,
                "maxsize": maxsize,
                "bounded": maxsize > 0
            }
        )

    def add_producer(
        self,
        producer_func: Callable[[], Any],
        name: str = None,
        interval: float = 0.0
    ) -> None:
        """Add a producer to the queue.

        Args:
            producer_func: Function that generates items to produce.
            name: Optional name for the producer thread.
            interval: Time to wait between productions (seconds).
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot add producer to shut down queue")

        producer = ProducerThread(
            queue=self._queue,
            producer_func=producer_func,
            name=name or f"Producer-{len(self._producers) + 1}",
            interval=interval,
            shutdown_event=self._shutdown_event,
            logger=self._logger
        )

        self._producers.append(producer)
        self._logger.info(
            f"Added producer '{producer.name}' to queue '{self._name}'",
            extra={"producer_name": producer.name, "queue_name": self._name}
        )

    def add_consumer(
        self,
        consumer_func: Callable[[Any], None],
        name: str = None
    ) -> None:
        """Add a consumer to the queue.

        Args:
            consumer_func: Function that processes consumed items.
            name: Optional name for the consumer thread.
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot add consumer to shut down queue")

        consumer = ConsumerThread(
            queue=self._queue,
            consumer_func=consumer_func,
            name=name or f"Consumer-{len(self._consumers) + 1}",
            shutdown_event=self._shutdown_event,
            logger=self._logger
        )

        self._consumers.append(consumer)
        self._logger.info(
            f"Added consumer '{consumer.name}' to queue '{self._name}'",
            extra={"consumer_name": consumer.name, "queue_name": self._name}
        )

    def start(self) -> None:
        """Start all producer and consumer threads."""
        if not self._producers and not self._consumers:
            raise RuntimeError("No producers or consumers added to queue")

        self._logger.info(
            f"Starting ProducerConsumerQueue '{self._name}'",
            extra={
                "queue_name": self._name,
                "producer_count": len(self._producers),
                "consumer_count": len(self._consumers)
            }
        )

        # Start all threads
        for producer in self._producers:
            producer.start()

        for consumer in self._consumers:
            consumer.start()

    def shutdown(self, timeout: Optional[float] = None) -> None:
        """Shutdown the queue gracefully.

        Signals all producers to stop, waits for them to finish,
        then sends DONE sentinels to consumers.

        Args:
            timeout: Maximum time to wait for graceful shutdown.
        """
        self._logger.info(
            f"Initiating shutdown of ProducerConsumerQueue '{self._name}'",
            extra={"queue_name": self._name, "timeout": timeout}
        )

        # Signal shutdown to producers
        self._shutdown_event.set()

        # Wait for producers to finish
        producer_timeout = timeout / 2 if timeout else None
        for producer in self._producers:
            producer.join(timeout=producer_timeout)

        # Send DONE sentinels to consumers (one per consumer)
        for _ in self._consumers:
            try:
                self._queue.put(DONE, timeout=1.0)
            except Full:
                self._logger.warning(
                    "Queue full during shutdown, consumer may not receive DONE",
                    extra={"queue_name": self._name}
                )

        # Wait for consumers to finish
        consumer_timeout = timeout / 2 if timeout else None
        for consumer in self._consumers:
            consumer.join(timeout=consumer_timeout)

        self._logger.info(
            f"ProducerConsumerQueue '{self._name}' shutdown complete",
            extra={"queue_name": self._name}
        )

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all producers and consumers to complete.

        Args:
            timeout: Maximum time to wait.

        Returns:
            True if all threads completed within timeout, False otherwise.
        """
        start_time = time.time()

        # Wait for all threads to complete
        for producer in self._producers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                producer.join(timeout=remaining)
            else:
                producer.join()

        for consumer in self._consumers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                consumer.join(timeout=remaining)
            else:
                consumer.join()

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get current queue statistics.

        Returns:
            Dictionary with queue statistics.
        """
        return {
            "queue_name": self._name,
            "queue_size": self._queue.qsize(),
            "maxsize": self._queue.maxsize,
            "producer_count": len(self._producers),
            "consumer_count": len(self._consumers),
            "active_producers": sum(1 for p in self._producers if p.is_alive()),
            "active_consumers": sum(1 for c in self._consumers if c.is_alive()),
            "shutdown_signaled": self._shutdown_event.is_set()
        }


class ProducerThread(threading.Thread):
    """Producer thread that generates and queues items."""

    def __init__(
        self,
        queue: Queue[Any],
        producer_func: Callable[[], Any],
        name: str,
        interval: float,
        shutdown_event: threading.Event,
        logger: logging.Logger
    ) -> None:
        """Initialize producer thread."""
        super().__init__(name=name, daemon=True)
        self._queue = queue
        self._producer_func = producer_func
        self._interval = interval
        self._shutdown_event = shutdown_event
        self._logger = logger

    def run(self) -> None:
        """Run the producer loop."""
        self._logger.info(
            f"Producer '{self.name}' started",
            extra={"producer_name": self.name}
        )

        items_produced = 0
        try:
            while not self._shutdown_event.is_set():
                try:
                    item = self._producer_func()
                    if item is None:
                        # Producer function signaled completion
                        break

                    self._queue.put(item, timeout=1.0)
                    items_produced += 1

                    if self._interval > 0:
                        time.sleep(self._interval)

                except Full:
                    # Queue is full, wait a bit before retrying
                    self._logger.debug(
                        f"Producer '{self.name}' queue full, waiting",
                        extra={"producer_name": self.name}
                    )
                    time.sleep(0.1)

                except Exception as e:
                    self._logger.error(
                        f"Producer '{self.name}' error: {e}",
                        extra={"producer_name": self.name, "error": str(e)},
                        exc_info=True
                    )
                    break

        finally:
            self._logger.info(
                f"Producer '{self.name}' finished, produced {items_produced} items",
                extra={
                    "producer_name": self.name,
                    "items_produced": items_produced
                }
            )


class ConsumerThread(threading.Thread):
    """Consumer thread that processes queued items."""

    def __init__(
        self,
        queue: Queue[Any],
        consumer_func: Callable[[Any], None],
        name: str,
        shutdown_event: threading.Event,
        logger: logging.Logger
    ) -> None:
        """Initialize consumer thread."""
        super().__init__(name=name, daemon=True)
        self._queue = queue
        self._consumer_func = consumer_func
        self._shutdown_event = shutdown_event
        self._logger = logger

    def run(self) -> None:
        """Run the consumer loop."""
        self._logger.info(
            f"Consumer '{self.name}' started",
            extra={"consumer_name": self.name}
        )

        items_processed = 0
        try:
            while not self._shutdown_event.is_set():
                try:
                    item = self._queue.get(timeout=1.0)

                    if item is DONE:
                        # Received shutdown sentinel
                        self._logger.debug(
                            f"Consumer '{self.name}' received DONE sentinel",
                            extra={"consumer_name": self.name}
                        )
                        break

                    self._consumer_func(item)
                    self._queue.task_done()
                    items_processed += 1

                except Empty:
                    # Queue is empty, continue waiting
                    continue

                except Exception as e:
                    self._logger.error(
                        f"Consumer '{self.name}' error: {e}",
                        extra={"consumer_name": self.name, "error": str(e)},
                        exc_info=True
                    )
                    break

        finally:
            self._logger.info(
                f"Consumer '{self.name}' finished, processed {items_processed} items",
                extra={
                    "consumer_name": self.name,
                    "items_processed": items_processed
                }
            )


# Context manager support
class ProducerConsumerContext:
    """Context manager for ProducerConsumerQueue."""

    def __init__(self, queue: ProducerConsumerQueue):
        self._queue = queue

    def __enter__(self):
        self._queue.start()
        return self._queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._queue.shutdown(timeout=10.0)
        return False


def create_producer_consumer_context(
    maxsize: int = 0,
    name: str = "ProducerConsumerQueue"
) -> ProducerConsumerContext:
    """Create a context-managed producer-consumer queue.

    Args:
        maxsize: Maximum queue size (0 for unbounded).
        name: Queue name for logging.

    Returns:
        Context manager that handles queue lifecycle.
    """
    queue = ProducerConsumerQueue(maxsize=maxsize, name=name)
    return ProducerConsumerContext(queue)

