"""
Basic producer-consumer demonstrations.

This module contains fundamental demonstrations of producer-consumer
patterns including single and multiple producers/consumers.
"""

import time
import logging

from .queue_core import ProducerConsumerQueue


def demo_basic_producer_consumer() -> None:
    """Demonstrate basic producer-consumer pattern."""
    print("=== Basic Producer-Consumer Demo ===")

    # Create queue with 2 producers and 2 consumers
    queue = ProducerConsumerQueue(name="BasicDemo")

    # Producer function that generates numbers
    def number_producer() -> int:
        """Generate sequential numbers."""
        for i in range(10):
            print(f"Producing: {i}")
            yield i
        return None  # Signal completion

    # Consumer function that processes numbers
    def number_consumer(item: int) -> None:
        """Process a number."""
        print(f"Consuming: {item}")
        time.sleep(0.1)  # Simulate processing time

    # Add producers and consumers
    queue.add_producer(lambda: next(number_producer().__iter__(), None), "NumProducer")
    queue.add_consumer(number_consumer, "NumConsumer")

    # Start and wait for completion
    queue.start()
    queue.wait_for_completion(timeout=30.0)

    stats = queue.get_stats()
    print(f"Demo completed - processed {stats.get('queue_size', 0)} items")


def demo_multiple_producers_consumers() -> None:
    """Demonstrate multiple producers and consumers."""
    print("\n=== Multiple Producers/Consumers Demo ===")

    queue = ProducerConsumerQueue(maxsize=5, name="MultiDemo")  # Bounded queue

    # Different types of producers
    def fast_producer() -> str:
        """Fast producer generating letters."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            yield f"fast-{letter}"
            time.sleep(0.05)

    def slow_producer() -> str:
        """Slow producer generating numbers."""
        for i in range(10):
            yield f"slow-{i}"
            time.sleep(0.2)

    # Different types of consumers
    def uppercase_consumer(item: str) -> None:
        """Convert to uppercase."""
        result = item.upper()
        print(f"Upper: {result}")
        time.sleep(0.1)

    def lowercase_consumer(item: str) -> None:
        """Convert to lowercase."""
        result = item.lower()
        print(f"Lower: {result}")
        time.sleep(0.1)

    # Add multiple producers and consumers
    queue.add_producer(lambda: next(fast_producer().__iter__(), None), "FastProducer")
    queue.add_producer(lambda: next(slow_producer().__iter__(), None), "SlowProducer")
    queue.add_consumer(uppercase_consumer, "UpperConsumer")
    queue.add_consumer(lowercase_consumer, "LowerConsumer")

    # Use context manager for automatic cleanup
    from .context import create_producer_consumer_context
    with create_producer_consumer_context(queue):
        # Wait for completion
        queue.wait_for_completion(timeout=60.0)

    print("Multiple producers/consumers demo completed")


def run_basic_demos() -> None:
    """Run all basic producer-consumer demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Basic Producer-Consumer Demonstrations")
    print("=" * 50)

    try:
        demo_basic_producer_consumer()
        demo_multiple_producers_consumers()

        print("\n" + "=" * 50)
        print("Basic demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run basic demonstrations when executed directly."""
    run_basic_demos()

