"""
Queue interfaces for pipeline message passing.

This module defines the queue interfaces used for message passing
between pipeline stages, providing a clean abstraction over
different queue implementations.
"""

import time
import logging
from typing import Any, Optional, Protocol
from abc import ABC, abstractmethod

from .message import Message


class MessageQueue(Protocol):
    """Protocol for message queue operations.

    This protocol defines the interface that all message queues
    must implement for use in pipelines.
    """

    @abstractmethod
    def put(self, message: Message, timeout: Optional[float] = None) -> None:
        """Put a message in the queue."""
        ...

    @abstractmethod
    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Get a message from the queue."""
        ...

    @abstractmethod
    def empty(self) -> bool:
        """Check if queue is empty."""
        ...

    @abstractmethod
    def qsize(self) -> int:
        """Get queue size."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the queue."""
        ...


class InMemoryMessageQueue:
    """In-memory message queue implementation.

    A thread-safe queue implementation using Python's queue.Queue
    for message passing between pipeline stages.

    Attributes:
        _queue: Underlying queue implementation.
        _name: Queue name for identification.
        _closed: Whether the queue has been closed.
    """

    def __init__(self, maxsize: int = 0, name: str = "MessageQueue"):
        """Initialize the message queue.

        Args:
            maxsize: Maximum queue size (0 for unbounded).
            name: Queue name for identification.
        """
        try:
            from queue import Queue
            self._queue = Queue(maxsize=maxsize)
        except ImportError:
            # Fallback for environments without queue
            self._queue = None
            self._items = []
            self._maxsize = maxsize

        self._name = name
        self._closed = False
        self._logger = logging.getLogger(__name__)

    def put(self, message: Message, timeout: Optional[float] = None) -> None:
        """Put a message in the queue.

        Args:
            message: Message to put in queue.
            timeout: Maximum time to wait if queue is full.

        Raises:
            RuntimeError: If queue is closed.
        """
        if self._closed:
            raise RuntimeError(f"Cannot put message in closed queue '{self._name}'")

        if self._queue is not None:
            # Use standard queue
            self._queue.put(message, timeout=timeout)
        else:
            # Fallback implementation
            if self._maxsize > 0 and len(self._items) >= self._maxsize:
                # Simulate blocking behavior
                start_time = time.time()
                while len(self._items) >= self._maxsize:
                    if timeout and (time.time() - start_time) > timeout:
                        raise RuntimeError("Queue full timeout")
                    time.sleep(0.01)
            self._items.append(message)

        self._logger.debug(
            f"Message {message.id} put in queue '{self._name}'",
            extra={"message_id": message.id, "queue_name": self._name}
        )

    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Get a message from the queue.

        Args:
            timeout: Maximum time to wait for a message.

        Returns:
            Message from queue or None if timeout.
        """
        if self._closed:
            return None

        try:
            if self._queue is not None:
                # Use standard queue
                return self._queue.get(timeout=timeout)
            else:
                # Fallback implementation
                start_time = time.time()
                while not self._items:
                    if timeout and (time.time() - start_time) > timeout:
                        return None
                    time.sleep(0.01)
                return self._items.pop(0)
        except Exception:
            # Handle queue timeout or other exceptions
            return None

    def empty(self) -> bool:
        """Check if queue is empty."""
        if self._queue is not None:
            return self._queue.empty()
        return len(self._items) == 0

    def qsize(self) -> int:
        """Get queue size."""
        if self._queue is not None:
            return self._queue.qsize()
        return len(self._items)

    def close(self) -> None:
        """Close the queue."""
        self._closed = True
        self._logger.debug(f"Queue '{self._name}' closed")


def create_message_queue(
    queue_type: str = "memory",
    maxsize: int = 0,
    name: str = "MessageQueue",
    **kwargs
) -> MessageQueue:
    """Factory function to create message queues.

    Args:
        queue_type: Type of queue to create ("memory" supported).
        maxsize: Maximum queue size.
        name: Queue name.
        **kwargs: Additional queue-specific parameters.

    Returns:
        Configured message queue instance.

    Raises:
        ValueError: If queue_type is not supported.
    """
    if queue_type == "memory":
        return InMemoryMessageQueue(maxsize=maxsize, name=name)
    else:
        raise ValueError(f"Unsupported queue type: {queue_type}")

