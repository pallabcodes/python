"""
Basic unit tests for ProducerConsumerQueue.

This module contains fundamental tests for queue initialization,
basic producer-consumer interactions, and core functionality.
"""

import pytest

from .queue_core import ProducerConsumerQueue


class TestProducerConsumerQueueBasic:
    """Unit tests for basic ProducerConsumerQueue functionality."""

    def test_initialization(self):
        """Test queue initialization."""
        # Unbounded queue
        queue = ProducerConsumerQueue()
        assert queue.queue.maxsize == 0

        # Bounded queue
        queue = ProducerConsumerQueue(maxsize=10)
        assert queue.queue.maxsize == 10

        # Invalid maxsize
        with pytest.raises(ValueError):
            ProducerConsumerQueue(maxsize=-1)

    def test_single_producer_consumer(self):
        """Test basic single producer-consumer interaction."""
        queue = ProducerConsumerQueue()
        results = []

        def producer():
            for i in range(3):
                yield i

        def consumer(item):
            results.append(item)

        queue.add_producer(lambda: next(producer().__iter__(), None))
        queue.add_consumer(consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=5.0)

        assert len(results) == 3
        assert set(results) == {0, 1, 2}

    def test_multiple_producers_consumers(self):
        """Test multiple producers and consumers."""
        queue = ProducerConsumerQueue()
        results = []
        results_lock = None  # Would need threading.Lock in real implementation

        def producer(start: int):
            for i in range(start, start + 2):
                yield f"producer-{i}"

        def consumer(item: str):
            results.append(item)

        # Add multiple producers and consumers
        queue.add_producer(lambda: next(producer(0).__iter__(), None))
        queue.add_producer(lambda: next(producer(10).__iter__(), None))
        queue.add_consumer(consumer)
        queue.add_consumer(consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=10.0)

        assert len(results) == 4
        assert set(results) == {"producer-0", "producer-1", "producer-10", "producer-11"}

    def test_empty_queue_operations(self):
        """Test operations on empty queue."""
        queue = ProducerConsumerQueue()

        # Should not crash with no producers/consumers
        with pytest.raises(RuntimeError):
            queue.start()

    def test_properties(self):
        """Test queue property access."""
        queue = ProducerConsumerQueue(maxsize=5, name="TestQueue")

        assert queue.name == "TestQueue"
        assert queue.queue.maxsize == 5
        assert len(queue.producers) == 0
        assert len(queue.consumers) == 0

