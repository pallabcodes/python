"""
Lifecycle management for ProducerConsumerQueue.

This module provides methods for starting, stopping, and monitoring
the lifecycle of producer-consumer queues.
"""

import threading
import time
import logging
from typing import Optional, Any, Dict

from .queue_core import ProducerConsumerQueue
from .producer_thread import ProducerThread
from .consumer_thread import ConsumerThread
from .queue import DONE


class QueueLifecycleManager:
    """Manages the lifecycle of ProducerConsumerQueue instances.

    This class handles starting, shutting down, and monitoring
    producer-consumer queues with proper error handling and logging.
    """

    def __init__(self, queue: ProducerConsumerQueue):
        """Initialize lifecycle manager.

        Args:
            queue: ProducerConsumerQueue to manage.
        """
        self._queue = queue
        self._logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start all producer and consumer threads."""
        if not self._queue.producers and not self._queue.consumers:
            raise RuntimeError("No producers or consumers added to queue")

        # Initialize shutdown event if not already done
        if not hasattr(self._queue, '_shutdown_event') or self._queue._shutdown_event is None:
            self._queue._shutdown_event = threading.Event()

        self._logger.info(
            f"Starting ProducerConsumerQueue '{self._queue.name}'",
            extra={
                "queue_name": self._queue.name,
                "producer_count": len(self._queue.producers),
                "consumer_count": len(self._queue.consumers)
            }
        )

        # Start all threads
        for producer in self._queue.producers:
            producer.start()

        for consumer in self._queue.consumers:
            consumer.start()

    def shutdown(self, timeout: Optional[float] = None) -> None:
        """Shutdown the queue gracefully.

        Signals all producers to stop, waits for them to finish,
        then sends DONE sentinels to consumers.

        Args:
            timeout: Maximum time to wait for graceful shutdown.
        """
        self._logger.info(
            f"Initiating shutdown of ProducerConsumerQueue '{self._queue.name}'",
            extra={"queue_name": self._queue.name, "timeout": timeout}
        )

        # Signal shutdown to producers
        self._queue._shutdown_event.set()

        # Wait for producers to finish
        producer_timeout = timeout / 2 if timeout else None
        for producer in self._queue.producers:
            producer.join(timeout=producer_timeout)

        # Send DONE sentinels to consumers (one per consumer)
        for _ in self._queue.consumers:
            try:
                self._queue.queue.put(DONE, timeout=1.0)
            except Exception:
                self._logger.warning(
                    "Queue full during shutdown, consumer may not receive DONE",
                    extra={"queue_name": self._queue.name}
                )

        # Wait for consumers to finish
        consumer_timeout = timeout / 2 if timeout else None
        for consumer in self._queue.consumers:
            consumer.join(timeout=consumer_timeout)

        self._logger.info(
            f"ProducerConsumerQueue '{self._queue.name}' shutdown complete",
            extra={"queue_name": self._queue.name}
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
        for producer in self._queue.producers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                producer.join(timeout=remaining)
            else:
                producer.join()

        for consumer in self._queue.consumers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                consumer.join(timeout=remaining)
            else:
                consumer.join()

        return True


# Monkey patch methods onto ProducerConsumerQueue
def _start_queue(self) -> None:
    """Start the queue (wrapper for lifecycle manager)."""
    manager = QueueLifecycleManager(self)
    manager.start()

def _shutdown_queue(self, timeout: Optional[float] = None) -> None:
    """Shutdown the queue (wrapper for lifecycle manager)."""
    manager = QueueLifecycleManager(self)
    manager.shutdown(timeout)

def _wait_for_completion_queue(self, timeout: Optional[float] = None) -> bool:
    """Wait for completion (wrapper for lifecycle manager)."""
    manager = QueueLifecycleManager(self)
    return manager.wait_for_completion(timeout)

def _get_stats_queue(self) -> Dict[str, Any]:
    """Get queue statistics."""
    from .queue_manager import get_queue_stats
    return get_queue_stats(self)

# Add methods to the class
ProducerConsumerQueue.start = _start_queue
ProducerConsumerQueue.shutdown = _shutdown_queue
ProducerConsumerQueue.wait_for_completion = _wait_for_completion_queue
ProducerConsumerQueue.get_stats = _get_stats_queue

