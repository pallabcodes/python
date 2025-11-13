"""
Core ProducerConsumerQueue class for coordinating producers and consumers.

This module provides the main ProducerConsumerQueue class that manages
the lifecycle of producer and consumer threads.
"""

import threading
import time
import logging
from queue import Full
from typing import Any, Callable, List, Optional

from .producer_thread import ProducerThread
from .consumer_thread import ConsumerThread
from .queue import ThreadSafeQueue, DONE


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
        self._queue = ThreadSafeQueue(maxsize=maxsize, name=name)
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
            if producer.is_alive():
                self._logger.warning(
                    f"Producer '{producer.name}' did not shutdown within timeout",
                    extra={
                        "queue_name": self._name,
                        "producer_name": producer.name,
                        "timeout": producer_timeout
                    }
                )

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
            if consumer.is_alive():
                self._logger.warning(
                    f"Consumer '{consumer.name}' did not shutdown within timeout",
                    extra={
                        "queue_name": self._name,
                        "consumer_name": consumer.name,
                        "timeout": consumer_timeout
                    }
                )

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
                if producer.is_alive():
                    return False  # Producer didn't complete within timeout
            else:
                producer.join()

        for consumer in self._consumers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                consumer.join(timeout=remaining)
                if consumer.is_alive():
                    return False  # Consumer didn't complete within timeout
            else:
                consumer.join()

        return True

    # Properties for accessing internal state
    @property
    def producers(self) -> List[ProducerThread]:
        """Get list of producer threads."""
        return self._producers[:]

    @property
    def consumers(self) -> List[ConsumerThread]:
        """Get list of consumer threads."""
        return self._consumers[:]

    @property
    def queue(self) -> ThreadSafeQueue:
        """Get the underlying queue."""
        return self._queue

    @property
    def name(self) -> str:
        """Get queue name."""
        return self._name

