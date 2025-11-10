"""
Producer thread implementation for producer-consumer pattern.

This module provides the ProducerThread class that handles
item generation and queue insertion in a thread-safe manner.
"""

import threading
import time
import logging
from typing import Any, Callable

from .queue import ThreadSafeQueue


class ProducerThread(threading.Thread):
    """Producer thread that generates and queues items.

    This thread continuously calls a producer function to generate
    items and puts them in a queue. It handles graceful shutdown
    and error recovery.

    Attributes:
        _queue: Queue to put generated items in.
        _producer_func: Function that generates items.
        _interval: Time to wait between productions.
        _shutdown_event: Event to signal shutdown.
        _logger: Logger for this producer.
    """

    def __init__(
        self,
        queue: ThreadSafeQueue,
        producer_func: Callable[[], Any],
        name: str,
        interval: float,
        shutdown_event: threading.Event,
        logger: logging.Logger
    ) -> None:
        """Initialize producer thread.

        Args:
            queue: Queue to put items in.
            producer_func: Function that returns items to produce.
            name: Thread name for identification.
            interval: Seconds to wait between productions.
            shutdown_event: Event to monitor for shutdown.
            logger: Parent logger instance.
        """
        super().__init__(name=name, daemon=True)
        self._queue = queue
        self._producer_func = producer_func
        self._interval = interval
        self._shutdown_event = shutdown_event
        self._logger = logger.getChild(f"producer.{name}")

        self._items_produced = 0
        self._errors_encountered = 0

    def run(self) -> None:
        """Run the producer loop."""
        self._logger.info(f"Producer '{self.name}' started")

        try:
            while not self._shutdown_event.is_set():
                try:
                    # Generate item
                    item = self._producer_func()
                    if item is None:
                        # Producer signaled completion
                        self._logger.debug(f"Producer '{self.name}' completed normally")
                        break

                    # Put item in queue
                    self._queue.put(item, timeout=1.0)
                    self._items_produced += 1

                    # Wait between productions if specified
                    if self._interval > 0:
                        time.sleep(self._interval)

                except Exception as e:
                    self._errors_encountered += 1
                    self._logger.error(
                        f"Producer '{self.name}' error: {e}",
                        extra={
                            "producer_name": self.name,
                            "error_type": type(e).__name__,
                            "items_produced": self._items_produced,
                            "errors_encountered": self._errors_encountered
                        },
                        exc_info=True
                    )
                    # Continue processing despite errors
                    time.sleep(0.1)

        finally:
            self._logger.info(
                f"Producer '{self.name}' finished",
                extra={
                    "producer_name": self.name,
                    "items_produced": self._items_produced,
                    "errors_encountered": self._errors_encountered
                }
            )

    @property
    def items_produced(self) -> int:
        """Get number of items produced."""
        return self._items_produced

    @property
    def errors_encountered(self) -> int:
        """Get number of errors encountered."""
        return self._errors_encountered

