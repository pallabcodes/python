"""
Advanced producer-consumer demonstrations.

This module contains advanced demonstrations including backpressure,
graceful shutdown, and error handling scenarios.
"""

import time
import logging
import random

from .queue_core import ProducerConsumerQueue
from .context import create_producer_consumer_context


def demo_backpressure_handling() -> None:
    """Demonstrate backpressure handling with bounded queues."""
    print("\n=== Backpressure Handling Demo ===")

    # Small bounded queue to create backpressure
    queue = ProducerConsumerQueue(maxsize=3, name="BackpressureDemo")

    # Fast producer that overwhelms the queue
    def fast_producer() -> dict:
        """Produce items faster than they can be consumed."""
        for i in range(20):
            item = {
                "id": i,
                "timestamp": time.time(),
                "data": f"Item {i}"
            }
            print(f"Producing fast: {item['id']}")
            yield item
            time.sleep(0.05)  # Very fast

    # Slow consumer that creates backpressure
    def slow_consumer(item: dict) -> None:
        """Consume items slowly to create backpressure."""
        print(f"Consuming slow: {item['id']}")
        time.sleep(0.3)  # Slow consumption - creates backpressure

    queue.add_producer(lambda: next(fast_producer().__iter__(), None), "FastProducer")
    queue.add_consumer(slow_consumer, "SlowConsumer")

    # Monitor queue during execution
    def monitor_queue(queue: ProducerConsumerQueue) -> None:
        """Monitor queue stats during execution."""
        for _ in range(10):
            stats = queue.get_stats()
            print(f"Queue size: {stats['queue_size']}/{stats['maxsize']}, "
                  f"Active: P={stats['active_producers']} C={stats['active_consumers']}")
            time.sleep(1.0)

    # Start monitoring in background
    import threading
    monitor_thread = threading.Thread(target=monitor_queue, args=(queue,))
    monitor_thread.daemon = True
    monitor_thread.start()

    # Run the demo
    with create_producer_consumer_context(queue):
        queue.wait_for_completion(timeout=120.0)

    print("Backpressure demo completed - notice how queue size fluctuated")


def demo_graceful_shutdown() -> None:
    """Demonstrate graceful shutdown with DONE sentinels."""
    print("\n=== Graceful Shutdown Demo ===")

    queue = ProducerConsumerQueue(name="ShutdownDemo")

    # Producer that generates items indefinitely until shutdown
    shutdown_producer = None  # Would be threading.Event()

    def continuous_producer() -> str:
        """Produce items continuously until shutdown."""
        count = 0
        while True:
            yield f"item-{count}"
            count += 1
            if count >= 10:  # Prevent infinite loop
                break

    # Consumer that processes items
    items_processed = []

    def consumer(item: str) -> None:
        """Process items and track them."""
        items_processed.append(item)
        print(f"Processed: {item}")
        time.sleep(0.05)

    queue.add_producer(lambda: next(continuous_producer().__iter__(), None), "ContinuousProducer")
    queue.add_consumer(consumer, "ProcessingConsumer")

    # Start the queue
    with create_producer_consumer_context(queue):
        # Let it run for a few seconds
        time.sleep(2.0)

        print(f"Items processed before shutdown: {len(items_processed)}")

        # Signal shutdown - this will stop the producer and send DONE sentinels
        # Wait a bit more for graceful shutdown
        time.sleep(1.0)

    final_count = len(items_processed)
    print(f"Final items processed: {final_count}")
    print("Graceful shutdown demo completed")


def demo_error_handling() -> None:
    """Demonstrate error handling in producer-consumer scenarios."""
    print("\n=== Error Handling Demo ===")

    queue = ProducerConsumerQueue(maxsize=5, name="ErrorDemo")

    # Producer that occasionally fails
    def unreliable_producer() -> dict:
        """Producer that sometimes fails."""
        for i in range(10):
            if random.random() < 0.2:  # 20% failure rate
                raise ValueError(f"Producer failed on item {i}")

            yield {"id": i, "data": f"Item {i}"}
            time.sleep(0.1)

    # Consumer that occasionally fails
    def unreliable_consumer(item: dict) -> None:
        """Consumer that sometimes fails."""
        if random.random() < 0.15:  # 15% failure rate
            raise RuntimeError(f"Consumer failed on item {item['id']}")

        print(f"Successfully processed: {item['id']}")
        time.sleep(0.05)

    queue.add_producer(lambda: next(unreliable_producer().__iter__(), None), "UnreliableProducer")
    queue.add_consumer(unreliable_consumer, "UnreliableConsumer")

    # Start and let errors occur
    with create_producer_consumer_context(queue):
        try:
            queue.wait_for_completion(timeout=30.0)
        except Exception as e:
            print(f"Demo completed with expected errors: {e}")

    print("Error handling demo completed - check logs for error details")


def run_advanced_demos() -> None:
    """Run all advanced producer-consumer demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Advanced Producer-Consumer Demonstrations")
    print("=" * 50)

    try:
        demo_backpressure_handling()
        demo_graceful_shutdown()
        demo_error_handling()

        print("\n" + "=" * 50)
        print("Advanced demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run advanced demonstrations when executed directly."""
    run_advanced_demos()

