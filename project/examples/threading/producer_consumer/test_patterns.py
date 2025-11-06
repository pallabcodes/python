"""
Test patterns for producer-consumer queue implementations.

This module provides comprehensive tests for the ProducerConsumerQueue
class, including unit tests, integration tests, and stress tests to
ensure correctness and robustness.
"""

import time
import threading
import pytest
from typing import List, Any, Dict
from queue import Full, Empty

from producer_consumer import ProducerConsumerQueue, DONE


class TestProducerConsumerQueue:
    """Unit tests for ProducerConsumerQueue."""

    def test_initialization(self):
        """Test queue initialization."""
        # Unbounded queue
        queue = ProducerConsumerQueue()
        assert queue._queue.maxsize == 0

        # Bounded queue
        queue = ProducerConsumerQueue(maxsize=10)
        assert queue._queue.maxsize == 10

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
        results_lock = threading.Lock()

        def producer(start: int):
            for i in range(start, start + 2):
                yield f"producer-{i}"

        def consumer(item: str):
            with results_lock:
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

    def test_bounded_queue_backpressure(self):
        """Test backpressure with bounded queues."""
        queue = ProducerConsumerQueue(maxsize=2)
        produced = []
        consumed = []

        def fast_producer():
            for i in range(5):
                produced.append(i)
                yield i
                time.sleep(0.01)  # Very fast

        def slow_consumer(item):
            consumed.append(item)
            time.sleep(0.1)  # Slow consumption

        queue.add_producer(lambda: next(fast_producer().__iter__(), None))
        queue.add_consumer(slow_consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=10.0)

        assert len(produced) == 5
        assert len(consumed) == 5
        assert set(consumed) == set(produced)

    def test_graceful_shutdown(self):
        """Test graceful shutdown with DONE sentinels."""
        queue = ProducerConsumerQueue()
        consumed_items = []
        shutdown_received = False

        def continuous_producer():
            count = 0
            while True:
                yield f"item-{count}"
                count += 1
                if count >= 10:  # Prevent infinite loop
                    break

        def consumer(item):
            if item is DONE:
                nonlocal shutdown_received
                shutdown_received = True
            else:
                consumed_items.append(item)
                time.sleep(0.01)

        queue.add_producer(continuous_producer)
        queue.add_consumer(consumer)

        queue.start()

        # Let it run briefly, then shutdown
        time.sleep(0.1)
        queue.shutdown(timeout=2.0)

        # Verify shutdown was graceful
        assert len(consumed_items) > 0  # Some items were processed
        assert shutdown_received  # DONE sentinel was received

    def test_shutdown_after_producer_completion(self):
        """Test shutdown when producers complete naturally."""
        queue = ProducerConsumerQueue()
        results = []

        def finite_producer():
            for i in range(3):
                yield i

        def consumer(item):
            results.append(item)

        queue.add_producer(lambda: next(finite_producer().__iter__(), None))
        queue.add_consumer(consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=5.0)

        assert len(results) == 3
        assert set(results) == {0, 1, 2}

    def test_empty_queue_operations(self):
        """Test operations on empty queue."""
        queue = ProducerConsumerQueue()

        # Should not crash with no producers/consumers
        with pytest.raises(RuntimeError):
            queue.start()

    def test_stats_reporting(self):
        """Test queue statistics reporting."""
        queue = ProducerConsumerQueue(maxsize=5, name="TestQueue")

        stats = queue.get_stats()
        assert stats["queue_name"] == "TestQueue"
        assert stats["maxsize"] == 5
        assert stats["producer_count"] == 0
        assert stats["consumer_count"] == 0
        assert not stats["shutdown_signaled"]

    def test_context_manager(self):
        """Test context manager usage."""
        results = []

        def producer():
            for i in range(2):
                yield i

        def consumer(item):
            results.append(item)

        with ProducerConsumerQueue() as queue:
            queue.add_producer(lambda: next(producer().__iter__(), None))
            queue.add_consumer(consumer)
            queue.start()
            queue.wait_for_completion(timeout=5.0)

        assert len(results) == 2
        assert set(results) == {0, 1}


class TestStressScenarios:
    """Stress tests for producer-consumer queue."""

    def test_high_throughput(self):
        """Test high-throughput scenario."""
        queue = ProducerConsumerQueue(maxsize=100)
        produced_count = 0
        consumed_count = 0

        def high_volume_producer():
            nonlocal produced_count
            for i in range(1000):
                produced_count += 1
                yield i

        def high_volume_consumer(item):
            nonlocal consumed_count
            consumed_count += 1

        # Add multiple producers and consumers
        for _ in range(3):
            queue.add_producer(lambda: next(high_volume_producer().__iter__(), None))

        for _ in range(3):
            queue.add_consumer(high_volume_consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=30.0)

        assert produced_count == 3000  # 3 producers * 1000 items
        assert consumed_count == 3000

    def test_long_running_operations(self):
        """Test long-running producer-consumer operations."""
        queue = ProducerConsumerQueue()
        start_time = time.time()
        results = []

        def slow_producer():
            for i in range(5):
                yield i
                time.sleep(0.1)  # Slow production

        def slow_consumer(item):
            results.append(item)
            time.sleep(0.2)  # Slow consumption

        queue.add_producer(lambda: next(slow_producer().__iter__(), None))
        queue.add_consumer(slow_consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=20.0)

        elapsed = time.time() - start_time
        assert elapsed < 15.0  # Should complete within reasonable time
        assert len(results) == 5

    def test_error_recovery(self):
        """Test error recovery and continued operation."""
        queue = ProducerConsumerQueue()
        successful_items = []
        failed_items = []

        def error_prone_producer():
            for i in range(10):
                if i % 3 == 0:
                    raise ValueError(f"Producer error on {i}")
                yield i

        def robust_consumer(item):
            try:
                if item % 2 == 0:
                    raise RuntimeError(f"Consumer error on {item}")
                successful_items.append(item)
            except Exception:
                failed_items.append(item)

        # Note: This test demonstrates that individual errors don't crash
        # the entire system, but the current implementation may need
        # error handling improvements for production use.

        queue.add_producer(lambda: next(error_prone_producer().__iter__(), None))
        queue.add_consumer(robust_consumer)

        queue.start()
        # Allow some time for operations, but expect errors
        time.sleep(1.0)
        queue.shutdown(timeout=5.0)

        # Verify some items were processed despite errors
        total_processed = len(successful_items) + len(failed_items)
        assert total_processed > 0


class TestThreadSafety:
    """Tests for thread safety aspects."""

    def test_concurrent_access_safety(self):
        """Test that concurrent operations don't corrupt state."""
        queue = ProducerConsumerQueue()
        counter = {"value": 0}
        lock = threading.Lock()

        def counting_producer():
            for i in range(100):
                yield i

        def counting_consumer(item):
            with lock:
                counter["value"] += 1

        # Add multiple producers and consumers
        for _ in range(5):
            queue.add_producer(lambda: next(counting_producer().__iter__(), None))

        for _ in range(5):
            queue.add_consumer(counting_consumer)

        queue.start()
        assert queue.wait_for_completion(timeout=20.0)

        assert counter["value"] == 500  # 5 producers * 100 items

    def test_shutdown_thread_safety(self):
        """Test thread-safe shutdown operations."""
        queue = ProducerConsumerQueue()

        def infinite_producer():
            count = 0
            while True:
                yield count
                count += 1
                time.sleep(0.01)

        def consumer(item):
            time.sleep(0.01)

        queue.add_producer(infinite_producer)
        queue.add_consumer(consumer)

        # Start and immediately shutdown
        queue.start()
        time.sleep(0.1)  # Let it start
        queue.shutdown(timeout=2.0)

        # Verify shutdown completed
        stats = queue.get_stats()
        assert stats["shutdown_signaled"]
        assert not any(p.is_alive() for p in queue._producers)
        assert not any(c.is_alive() for c in queue._consumers)


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])

