"""
Core queue and sentinel classes for producer-consumer pattern.

This module provides the fundamental building blocks for thread-safe
communication between producers and consumers.
"""

import logging
from queue import Queue
from typing import Any


class ShutdownSignal:
    """Sentinel object for signaling graceful shutdown.

    This singleton is used as a sentinel value in queues to signal
    that producers have finished and consumers should shut down
    gracefully. It ensures clean termination of processing pipelines.

    Attributes:
        _instance: Singleton instance of the sentinel.
    """

    _instance = None

    def __new__(cls):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __str__(self) -> str:
        """String representation of the sentinel."""
        return "<ShutdownSignal>"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return "ShutdownSignal()"


# Global shutdown sentinel instance
DONE = ShutdownSignal()


class ThreadSafeQueue:
    """Wrapper around queue.Queue with additional monitoring.

    This class provides a thread-safe queue with statistics and
    monitoring capabilities. It wraps Python's standard Queue
    with additional metadata for observability.

    Attributes:
        _queue: The underlying Queue instance.
        _name: Optional name for identification.
        _created_at: Timestamp when queue was created.
    """

    def __init__(self, maxsize: int = 0, name: str = "ThreadSafeQueue") -> None:
        """Initialize the thread-safe queue.

        Args:
            maxsize: Maximum queue size (0 for unbounded).
            name: Queue name for identification.

        Raises:
            ValueError: If maxsize is negative.
        """
        if maxsize < 0:
            raise ValueError("maxsize cannot be negative")

        self._queue: Queue[Any] = Queue(maxsize=maxsize)
        self._name = name
        self._created_at = None  # Set when first used

        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Get queue name."""
        return self._name

    @property
    def maxsize(self) -> int:
        """Get maximum queue size."""
        return self._queue.maxsize

    def qsize(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()

    def put(self, item: Any, block: bool = True, timeout: float = None) -> None:
        """Put item in queue.

        Args:
            item: Item to put in queue.
            block: Whether to block if queue is full.
            timeout: Maximum time to wait.
        """
        if self._created_at is None:
            import time
            self._created_at = time.time()

        self._queue.put(item, block=block, timeout=timeout)

    def get(self, block: bool = True, timeout: float = None) -> Any:
        """Get item from queue.

        Args:
            block: Whether to block if queue is empty.
            timeout: Maximum time to wait.

        Returns:
            Item from queue.
        """
        return self._queue.get(block=block, timeout=timeout)

    def task_done(self) -> None:
        """Indicate that a formerly enqueued task is complete."""
        self._queue.task_done()

    def join(self) -> None:
        """Block until all items in the queue have been gotten and processed."""
        self._queue.join()

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dictionary with queue statistics.
        """
        import time
        current_time = time.time()

        return {
            "name": self._name,
            "size": self.qsize(),
            "maxsize": self.maxsize,
            "empty": self.empty(),
            "full": self.full(),
            "bounded": self.maxsize > 0,
            "age": current_time - (self._created_at or current_time)
        }

