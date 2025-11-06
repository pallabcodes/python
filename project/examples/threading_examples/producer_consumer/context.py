"""
Context manager and factory functions for ProducerConsumerQueue.

This module provides convenient ways to create and manage
ProducerConsumerQueue instances, including context managers
for automatic resource cleanup.
"""

from typing import Optional

from .queue_coordinator import ProducerConsumerQueue


class ProducerConsumerContext:
    """Context manager for ProducerConsumerQueue."""

    def __init__(self, queue: ProducerConsumerQueue):
        """Initialize context manager with queue."""
        self._queue = queue

    def __enter__(self):
        """Enter context and start the queue."""
        self._queue.start()
        return self._queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and shutdown the queue."""
        self._queue.shutdown(timeout=10.0)
        return False


def create_producer_consumer_context(
    maxsize: int = 0,
    name: str = "ProducerConsumerQueue"
) -> ProducerConsumerContext:
    """Create a context-managed producer-consumer queue.

    This factory function creates a ProducerConsumerQueue instance
    wrapped in a context manager that handles automatic startup
    and shutdown.

    Args:
        maxsize: Maximum queue size (0 for unbounded).
        name: Queue name for logging.

    Returns:
        Context manager that handles queue lifecycle.

    Example:
        >>> with create_producer_consumer_context() as queue:
        ...     queue.add_producer(producer_func)
        ...     queue.add_consumer(consumer_func)
        ...     queue.wait_for_completion()
    """
    queue = ProducerConsumerQueue(maxsize=maxsize, name=name)
    return ProducerConsumerContext(queue)


def create_simple_queue(
    producer_func,
    consumer_func,
    maxsize: int = 0,
    name: str = "SimpleQueue"
) -> ProducerConsumerQueue:
    """Create a simple producer-consumer queue with one producer and consumer.

    This factory function creates a basic queue setup with a single
    producer and consumer, useful for simple use cases.

    Args:
        producer_func: Function that generates items.
        consumer_func: Function that processes items.
        maxsize: Maximum queue size (0 for unbounded).
        name: Queue name for logging.

    Returns:
        Configured ProducerConsumerQueue instance.

    Example:
        >>> def producer():
        ...     for i in range(10):
        ...         yield i
        >>>
        >>> def consumer(item):
        ...     print(f"Processed: {item}")
        >>>
        >>> queue = create_simple_queue(producer, consumer)
        >>> with ProducerConsumerContext(queue) as q:
        ...     q.wait_for_completion()
    """
    queue = ProducerConsumerQueue(maxsize=maxsize, name=name)
    queue.add_producer(producer_func)
    queue.add_consumer(consumer_func)
    return queue


def create_work_pool(
    task_generator,
    worker_func,
    num_workers: int = 4,
    maxsize: int = 0,
    name: str = "WorkPool"
) -> ProducerConsumerQueue:
    """Create a work pool with one producer and multiple workers.

    This factory function creates a producer-consumer setup where
    one producer generates tasks and multiple worker consumers
    process them in parallel.

    Args:
        task_generator: Function that generates tasks.
        worker_func: Function that processes tasks.
        num_workers: Number of worker consumers.
        maxsize: Maximum queue size (0 for unbounded).
        name: Queue name for logging.

    Returns:
        Configured ProducerConsumerQueue instance.

    Example:
        >>> def generate_tasks():
        ...     for i in range(100):
        ...         yield f"task-{i}"
        >>>
        >>> def process_task(task):
        ...     print(f"Processing {task}")
        >>>
        >>> pool = create_work_pool(generate_tasks, process_task, num_workers=4)
        >>> with ProducerConsumerContext(pool) as p:
        ...     p.wait_for_completion()
    """
    queue = ProducerConsumerQueue(maxsize=maxsize, name=name)
    queue.add_producer(task_generator)

    for i in range(num_workers):
        queue.add_consumer(worker_func, name=f"Worker-{i+1}")

    return queue


def create_pipeline(
    stages: list,
    maxsize: int = 0,
    name: str = "Pipeline"
) -> ProducerConsumerQueue:
    """Create a multi-stage processing pipeline.

    This factory function creates a pipeline where each stage processes
    items and passes them to the next stage. Note: This is a simplified
    version - for complex pipelines, consider a dedicated pipeline
    framework.

    Args:
        stages: List of (producer_func, consumer_func) tuples for each stage.
        maxsize: Maximum queue size for each stage.
        name: Base name for the pipeline.

    Returns:
        Configured ProducerConsumerQueue (simplified - real pipelines need more).

    Note:
        This is a basic implementation. For production pipelines,
        consider using a dedicated pipeline framework with proper
        error handling and monitoring.
    """
    if not stages:
        raise ValueError("At least one stage is required")

    # For simplicity, create a single queue
    # Real pipeline would need multiple queues and coordination
    queue = ProducerConsumerQueue(maxsize=maxsize, name=name)

    # Add all stages to the same queue (simplified)
    for i, (producer_func, consumer_func) in enumerate(stages):
        queue.add_producer(producer_func, name=f"Stage{i+1}-Producer")
        queue.add_consumer(consumer_func, name=f"Stage{i+1}-Consumer")

    return queue

