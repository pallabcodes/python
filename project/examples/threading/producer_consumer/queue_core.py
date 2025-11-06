"""
Core ProducerConsumerQueue class implementation.

This module provides the core ProducerConsumerQueue class with
basic initialization and thread management functionality.
"""

import logging
from typing import Any, Callable, List

from .producer_thread import ProducerThread
from .consumer_thread import ConsumerThread
from .queue import ThreadSafeQueue


class ProducerConsumerQueue:
    """Thread-safe producer-consumer queue with graceful shutdown.

    This class implements the classic producer-consumer pattern using
    Python's queue.Queue. It supports multiple producers and consumers,
    graceful shutdown via DONE sentinels, and optional bounded queues
    for backpressure control.
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
        self._shutdown_event = None  # Will be set when starting
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
        if self._shutdown_event and self._shutdown_event.is_set():
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
        if self._shutdown_event and self._shutdown_event.is_set():
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

    @property
    def shutdown_event(self):
        """Get shutdown event (for internal use)."""
        return self._shutdown_event

