"""
Producer-consumer queue implementation with graceful shutdown.

This module provides a production-grade producer-consumer pattern
implementation using Python's queue.Queue. It demonstrates proper
thread coordination, graceful shutdown using DONE sentinels, and
backpressure handling with bounded queues.
"""

import threading
import time
import logging
from queue import Queue, Full, Empty
from typing import Any, Optional, Callable, List, Dict
from dataclasses import dataclass
from enum import Enum


class ShutdownSignal:
    """Sentinel object for signaling graceful shutdown.

    This singleton is used as a sentinel value in queues to signal
    that producers have finished and consumers should shut down
    gracefully.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __str__(self) -> str:
        return "<ShutdownSignal>"

    def __repr__(self) -> str:
        return "ShutdownSignal()"


# Global shutdown sentinel instance
DONE = ShutdownSignal()


class ProducerConsumerQueue:
    """
    Thread-safe producer-consumer queue with graceful shutdown.

    This class implements the classic producer-consumer pattern using
    Python's queue.Queue. It supports multiple producers and consumers,
    graceful shutdown via DONE sentinels, and optional bounded queues
    for backpressure control.

    When to Use:
        - Decoupling producers and consumers
        - Implementing job queues
        - Handling variable production/consumption rates
        - Building event-driven systems
        - Managing resource consumption

    Real-World Examples:
        - Job queues: Producers submit jobs, workers consume
        - Log aggregation: Services produce logs, aggregator consumes
        - Event processing: Event sources produce, processors consume
        - Message queues: Publishers produce, subscribers consume
        - Task queues: Task generators produce, executors consume

    Gotchas:
        - DONE sentinels must be sent (one per consumer)
        - Queue.put() blocks when full (bounded queues)
        - Queue.get() blocks when empty
        - task_done() must be called for each get()
        - Shutdown must wait for producers before sending DONE
        - Timeout handling prevents indefinite blocking

    Performance Notes:
        - Bounded queues prevent memory exhaustion
        - Backpressure slows producers when consumers lag
        - Optimal producer/consumer ratio depends on workload
        - Queue size affects latency vs memory tradeoff

    Features:
    - Multiple producer and consumer threads
    - Graceful shutdown using DONE sentinels
    - Bounded queues for backpressure
    - Comprehensive monitoring and logging
    - Configurable timeouts and retry logic

    Attributes:
        _queue: Internal queue for message passing.
        _producers: List of active producer threads.
        _consumers: List of active consumer threads.
        _shutdown_event: Event for coordinating shutdown.
        _logger: Structured logger with correlation IDs.
    """

    def __init__(
        self,
        maxsize: int = 0,
        name: str = "ProducerConsumerQueue"
    ) -> None:
        """Initialize the producer-consumer queue.

        Args:
            maxsize: Maximum queue size (0 for unbounded).
            name: Queue name for logging and identification.

        Raises:
            ValueError: If maxsize is negative.
        """
        if maxsize < 0:
            raise ValueError("maxsize cannot be negative")

        self._queue: Queue[Any] = Queue(maxsize=maxsize)
        self._producers: List[ProducerThread] = []
        self._consumers: List[ConsumerThread] = []
        self._shutdown_event = threading.Event()
        self._name = name
        self._logger = logging.getLogger(__name__)

        self._logger.info(
            f"ProducerConsumerQueue '{name}' initialized",
            extra={
                "queue_name": name,
                "maxsize": maxsize,
                "bounded": maxsize > 0
            }
        )

    def add_producer(
        self,
        producer_func: Callable[[], Any],
        name: str = None,
        interval: float = 0.0
    ) -> None:
        """Add a producer to the queue.

        Args:
            producer_func: Function that generates items to produce.
            name: Optional name for the producer thread.
            interval: Time to wait between productions (seconds).
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot add producer to shut down queue")

        producer = ProducerThread(
            queue=self._queue,
            producer_func=producer_func,
            name=name or f"Producer-{len(self._producers) + 1}",
            interval=interval,
            shutdown_event=self._shutdown_event,
            logger=self._logger
        )

        self._producers.append(producer)
        self._logger.info(
            f"Added producer '{producer.name}' to queue '{self._name}'",
            extra={"producer_name": producer.name, "queue_name": self._name}
        )

    def add_consumer(
        self,
        consumer_func: Callable[[Any], None],
        name: str = None
    ) -> None:
        """Add a consumer to the queue.

        Args:
            consumer_func: Function that processes consumed items.
            name: Optional name for the consumer thread.
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot add consumer to shut down queue")

        consumer = ConsumerThread(
            queue=self._queue,
            consumer_func=consumer_func,
            name=name or f"Consumer-{len(self._consumers) + 1}",
            shutdown_event=self._shutdown_event,
            logger=self._logger
        )

        self._consumers.append(consumer)
        self._logger.info(
            f"Added consumer '{consumer.name}' to queue '{self._name}'",
            extra={"consumer_name": consumer.name, "queue_name": self._name}
        )

    def start(self) -> None:
        """Start all producer and consumer threads."""
        if not self._producers and not self._consumers:
            raise RuntimeError("No producers or consumers added to queue")

        self._logger.info(
            f"Starting ProducerConsumerQueue '{self._name}'",
            extra={
                "queue_name": self._name,
                "producer_count": len(self._producers),
                "consumer_count": len(self._consumers)
            }
        )

        # Start all threads
        for producer in self._producers:
            producer.start()

        for consumer in self._consumers:
            consumer.start()

    def shutdown(self, timeout: Optional[float] = None) -> None:
        """Shutdown the queue gracefully.

        Signals all producers to stop, waits for them to finish,
        then sends DONE sentinels to consumers.

        Args:
            timeout: Maximum time to wait for graceful shutdown.
        """
        self._logger.info(
            f"Initiating shutdown of ProducerConsumerQueue '{self._name}'",
            extra={"queue_name": self._name, "timeout": timeout}
        )

        # Signal shutdown to producers
        self._shutdown_event.set()

        # Wait for producers to finish
        producer_timeout = timeout / 2 if timeout else None
        for producer in self._producers:
            producer.join(timeout=producer_timeout)
            if producer.is_alive():
                self._logger.warning(
                    f"Producer '{producer.name}' did not shutdown within timeout",
                    extra={
                        "queue_name": self._name,
                        "producer_name": producer.name,
                        "timeout": producer_timeout
                    }
                )

        # Send DONE sentinels to consumers (one per consumer)
        for _ in self._consumers:
            try:
                self._queue.put(DONE, timeout=1.0)
            except Full:
                self._logger.warning(
                    "Queue full during shutdown, consumer may not receive DONE",
                    extra={"queue_name": self._name}
                )

        # Wait for consumers to finish
        consumer_timeout = timeout / 2 if timeout else None
        for consumer in self._consumers:
            consumer.join(timeout=consumer_timeout)
            if consumer.is_alive():
                self._logger.warning(
                    f"Consumer '{consumer.name}' did not shutdown within timeout",
                    extra={
                        "queue_name": self._name,
                        "consumer_name": consumer.name,
                        "timeout": consumer_timeout
                    }
                )

        self._logger.info(
            f"ProducerConsumerQueue '{self._name}' shutdown complete",
            extra={"queue_name": self._name}
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
        for producer in self._producers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                producer.join(timeout=remaining)
                if producer.is_alive():
                    return False  # Producer didn't complete within timeout
            else:
                producer.join()

        for consumer in self._consumers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                consumer.join(timeout=remaining)
                if consumer.is_alive():
                    return False  # Consumer didn't complete within timeout
            else:
                consumer.join()

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get current queue statistics.

        Returns:
            Dictionary with queue statistics.
        """
        return {
            "queue_name": self._name,
            "queue_size": self._queue.qsize(),
            "maxsize": self._queue.maxsize,
            "producer_count": len(self._producers),
            "consumer_count": len(self._consumers),
            "active_producers": sum(1 for p in self._producers if p.is_alive()),
            "active_consumers": sum(1 for c in self._consumers if c.is_alive()),
            "shutdown_signaled": self._shutdown_event.is_set()
        }


class ProducerThread(threading.Thread):
    """
    Producer thread that generates and queues items.

    When to Use:
        - Generating items for consumers
        - Producing data at variable rates
        - Implementing producer side of pattern
        - Creating work items for workers

    Real-World Examples:
        - Log producers: Generate log entries
        - Event producers: Generate events
        - Task producers: Generate tasks
        - Data producers: Generate data items

    Gotchas:
        - Must check shutdown_event periodically
        - Queue.put() blocks when full
        - Handle Full exceptions for bounded queues
        - Producer function returning None signals completion
        - Interval controls production rate

    Performance Notes:
        - Production rate controlled by interval
        - Queue blocking provides backpressure
        - Optimal interval depends on workload
    """

    def __init__(
        self,
        queue: Queue[Any],
        producer_func: Callable[[], Any],
        name: str,
        interval: float,
        shutdown_event: threading.Event,
        logger: logging.Logger
    ) -> None:
        """Initialize producer thread."""
        super().__init__(name=name, daemon=True)
        self._queue = queue
        self._producer_func = producer_func
        self._interval = interval
        self._shutdown_event = shutdown_event
        self._logger = logger

    def run(self) -> None:
        """Run the producer loop."""
        self._logger.info(
            f"Producer '{self.name}' started",
            extra={"producer_name": self.name}
        )

        items_produced = 0
        try:
            while not self._shutdown_event.is_set():
                try:
                    item = self._producer_func()
                    if item is None:
                        # Producer function signaled completion
                        break

                    self._queue.put(item, timeout=1.0)
                    items_produced += 1

                    if self._interval > 0:
                        time.sleep(self._interval)

                except Full:
                    # Queue is full, wait a bit before retrying
                    self._logger.debug(
                        f"Producer '{self.name}' queue full, waiting",
                        extra={"producer_name": self.name}
                    )
                    time.sleep(0.1)

                except Exception as e:
                    self._logger.error(
                        f"Producer '{self.name}' error: {e}",
                        extra={"producer_name": self.name, "error": str(e)},
                        exc_info=True
                    )
                    break

        finally:
            self._logger.info(
                f"Producer '{self.name}' finished, produced {items_produced} items",
                extra={
                    "producer_name": self.name,
                    "items_produced": items_produced
                }
            )


class ConsumerThread(threading.Thread):
    """
    Consumer thread that processes queued items.

    When to Use:
        - Processing items from queue
        - Consuming work items
        - Implementing consumer side of pattern
        - Processing data at variable rates

    Real-World Examples:
        - Log consumers: Process log entries
        - Event consumers: Process events
        - Task consumers: Process tasks
        - Data consumers: Process data items

    Gotchas:
        - Must check for DONE sentinel
        - Queue.get() blocks when empty
        - task_done() must be called after processing
        - Handle Empty exceptions
        - Consumer function errors stop consumer

    Performance Notes:
        - Processing rate depends on consumer function
        - Queue blocking provides backpressure
        - Multiple consumers improve throughput
        - Balance consumer count vs overhead
    """

    def __init__(
        self,
        queue: Queue[Any],
        consumer_func: Callable[[Any], None],
        name: str,
        shutdown_event: threading.Event,
        logger: logging.Logger
    ) -> None:
        """Initialize consumer thread."""
        super().__init__(name=name, daemon=True)
        self._queue = queue
        self._consumer_func = consumer_func
        self._shutdown_event = shutdown_event
        self._logger = logger

    def run(self) -> None:
        """Run the consumer loop."""
        self._logger.info(
            f"Consumer '{self.name}' started",
            extra={"consumer_name": self.name}
        )

        items_processed = 0
        try:
            while not self._shutdown_event.is_set():
                try:
                    item = self._queue.get(timeout=1.0)

                    if item is DONE:
                        # Received shutdown sentinel
                        self._logger.debug(
                            f"Consumer '{self.name}' received DONE sentinel",
                            extra={"consumer_name": self.name}
                        )
                        break

                    self._consumer_func(item)
                    self._queue.task_done()
                    items_processed += 1

                except Empty:
                    # Queue is empty, continue waiting
                    continue

                except Exception as e:
                    self._logger.error(
                        f"Consumer '{self.name}' error: {e}",
                        extra={"consumer_name": self.name, "error": str(e)},
                        exc_info=True
                    )
                    break

        finally:
            self._logger.info(
                f"Consumer '{self.name}' finished, processed {items_processed} items",
                extra={
                    "consumer_name": self.name,
                    "items_processed": items_processed
                }
            )

    def producer_consumer_real_world_example(self) -> None:
        """
        Real-World Scenario: Producer-Consumer Queue - Log Processing System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a log processing system:
        - Multiple services produce log entries
        - Workers process and analyze logs
        - Problem: Decouple log production from processing
        
        THE PROBLEM WITHOUT QUEUE:
        ===========================
        - Producers wait for consumers → blocking
        - Tight coupling → inflexible
        - No buffering → lost logs
        - Rate mismatch → inefficient
        - System fragile → poor scalability
        
        THE SOLUTION:
        =============
        Producer-Consumer Queue enables:
        - Decouple producers from consumers
        - Buffer logs in queue → handle rate mismatch
        - Multiple workers → parallel processing
        - Backpressure → prevent overload
        - Scalable architecture → production-ready
        
        WHEN TO USE PRODUCER-CONSUMER QUEUE:
        ====================================
        ✅ Log processing systems
        ✅ Decoupling producers/consumers
        ✅ Handling variable rates
        ✅ Event-driven systems
        ✅ Task processing pipelines
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Log Processing System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Log processing system")
        print("  - Multiple services produce log entries")
        print("  - Workers process and analyze logs")
        print("  - Problem: Decouple log production from processing")
        print()
        print("THE PROBLEM:")
        print("  Without queue:")
        print("    ❌ Producers wait for consumers → blocking")
        print("    ❌ Tight coupling → inflexible")
        print("    ❌ No buffering → lost logs")
        print("    ❌ Rate mismatch → inefficient")
        print()
        print("THE SOLUTION:")
        print("  With producer-consumer queue:")
        print("    ✅ Decouple producers from consumers")
        print("    ✅ Buffer logs in queue → handle rate mismatch")
        print("    ✅ Multiple workers → parallel processing")
        print("    ✅ Backpressure → prevent overload")
        print()
        print("=" * 70)
        print()

        queue = ProducerConsumerQueue(maxsize=10, name="LogProcessingQueue")

        log_count = {"value": 0}
        log_lock = threading.Lock()

        def log_producer_func() -> None:
            """Simulate a service producing logs."""
            service_id = 1
            num_logs = 5
            for i in range(num_logs):
                if queue._shutdown_event.is_set():
                    break
                log_entry = {
                    "service_id": service_id,
                    "log_id": i+1,
                    "message": f"Log entry {i+1} from service {service_id}",
                    "timestamp": time.time()
                }
                try:
                    queue._queue.put(log_entry, timeout=1.0)
                    print(f"  Service {service_id}: Produced log {i+1}")
                except:
                    break
                time.sleep(0.05)

        def log_consumer_func(log_entry: Any) -> None:
            """Simulate a worker processing logs."""
            if log_entry is DONE:
                return
            
            # Process log
            time.sleep(0.1)  # Simulate processing
            with log_lock:
                log_count["value"] += 1
            print(f"  Worker: Processed log from service {log_entry['service_id']}")

        print("Starting log processing system...")
        print("  - 2 services producing logs")
        print("  - 3 workers processing logs")
        print()

        # Add producers
        queue.add_producer(log_producer_func, name="service_1")
        queue.add_producer(log_producer_func, name="service_2")

        # Add consumers
        for i in range(3):
            queue.add_consumer(log_consumer_func, name=f"worker_{i+1}")

        # Start queue
        queue.start()

        # Wait a bit for processing
        time.sleep(2.0)

        # Shutdown queue
        queue.shutdown(timeout=5.0)

        print()
        print("  ✅ Producer-Consumer queue enabled decoupled log processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PRODUCER-CONSUMER QUEUE:")
        print("   ✅ Log processing systems")
        print("   ✅ Decoupling producers/consumers")
        print("   ✅ Handling variable rates")
        print("   ✅ Event-driven systems")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Decouples producers from consumers")
        print("   - Handles rate mismatches")
        print("   - Enables parallel processing")
        print("   - Scalable architecture")
        print("=" * 70)
        print()


# Context manager support
class ProducerConsumerContext:
    """
    Context manager for ProducerConsumerQueue.

    When to Use:
        - Automatic queue lifecycle management
        - Ensuring proper shutdown
        - Resource cleanup
        - Simplifying queue usage

    Real-World Examples:
        - With statements: Automatic cleanup
        - Resource management: Ensure shutdown
        - Testing: Clean up test queues
        - Temporary queues: Auto-cleanup

    Gotchas:
        - Automatically starts queue on enter
        - Automatically shuts down on exit
        - Shutdown timeout is fixed (10s)
        - Exceptions trigger shutdown

    Performance Notes:
        - Context manager overhead is minimal
        - Ensures proper cleanup
        - Prevents resource leaks
    """

    def __init__(self, queue: ProducerConsumerQueue):
        self._queue = queue

    def __enter__(self):
        self._queue.start()
        return self._queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._queue.shutdown(timeout=10.0)
        return False


def create_producer_consumer_context(
    maxsize: int = 0,
    name: str = "ProducerConsumerQueue"
) -> ProducerConsumerContext:
    """Create a context-managed producer-consumer queue.

    Args:
        maxsize: Maximum queue size (0 for unbounded).
        name: Queue name for logging.

    Returns:
        Context manager that handles queue lifecycle.
    """
    queue = ProducerConsumerQueue(maxsize=maxsize, name=name)
    return ProducerConsumerContext(queue)

