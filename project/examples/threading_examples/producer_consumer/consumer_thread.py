"""
Consumer thread implementation for producer-consumer pattern.

This module provides the ConsumerThread class that handles
item retrieval and processing from queues in a thread-safe manner.
"""

import threading
import time
import logging
from typing import Any, Callable

from .queue import ThreadSafeQueue, DONE


class ConsumerThread(threading.Thread):
    """Consumer thread that processes queued items.

    This thread continuously gets items from a queue and processes
    them using a consumer function. It handles DONE sentinels for
    graceful shutdown.

    Attributes:
        _queue: Queue to get items from.
        _consumer_func: Function that processes items.
        _shutdown_event: Event to signal shutdown.
        _logger: Logger for this consumer.
    """

    def __init__(
        self,
        queue: ThreadSafeQueue,
        consumer_func: Callable[[Any], None],
        name: str,
        shutdown_event: threading.Event,
        logger: logging.Logger
    ) -> None:
        """Initialize consumer thread.

        Args:
            queue: Queue to get items from.
            consumer_func: Function that processes items.
            name: Thread name for identification.
            shutdown_event: Event to monitor for shutdown.
            logger: Parent logger instance.
        """
        super().__init__(name=name, daemon=True)
        self._queue = queue
        self._consumer_func = consumer_func
        self._shutdown_event = shutdown_event
        self._logger = logger.getChild(f"consumer.{name}")

        self._items_processed = 0
        self._errors_encountered = 0
        self._shutdown_received = False

    def run(self) -> None:
        """Run the consumer loop."""
        self._logger.info(f"Consumer '{self.name}' started")

        try:
            while not self._shutdown_event.is_set():
                try:
                    # Get item from queue
                    item = self._queue.get(timeout=1.0)

                    if item is DONE:
                        # Received shutdown sentinel
                        self._shutdown_received = True
                        self._logger.debug(f"Consumer '{self.name}' received DONE sentinel")
                        break

                    # Process item
                    self._consumer_func(item)
                    self._queue.task_done()
                    self._items_processed += 1

                except Exception as e:
                    self._errors_encountered += 1
                    self._logger.error(
                        f"Consumer '{self.name}' error: {e}",
                        extra={
                            "consumer_name": self.name,
                            "error_type": type(e).__name__,
                            "items_processed": self._items_processed,
                            "errors_encountered": self._errors_encountered
                        },
                        exc_info=True
                    )
                    # Continue processing despite errors
                    time.sleep(0.1)

        finally:
            self._logger.info(
                f"Consumer '{self.name}' finished",
                extra={
                    "consumer_name": self.name,
                    "items_processed": self._items_processed,
                    "errors_encountered": self._errors_encountered,
                    "shutdown_received": self._shutdown_received
                }
            )

    @property
    def items_processed(self) -> int:
        """Get number of items processed."""
        return self._items_processed

    @property
    def errors_encountered(self) -> int:
        """Get number of errors encountered."""
        return self._errors_encountered

    @property
    def shutdown_received(self) -> bool:
        """Check if shutdown sentinel was received."""
        return self._shutdown_received

