"""
Stress tests for ProducerConsumerQueue.

This module contains stress tests for high-throughput scenarios,
long-running operations, and error recovery.
"""

import time
import threading

from .queue_core import ProducerConsumerQueue


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
        assert not any(p.is_alive() for p in queue.producers)
        assert not any(c.is_alive() for c in queue.consumers)

