"""
Module: Threaded Producer-Consumer Queue Pipeline
Target: Google L6/L7 Concurrency Standard

Key Concepts:
1. Thread-Safe Queue (`queue.Queue`): Bounded FIFO queue handling thread synchronization internally.
2. Producer Threads: Put work items into the queue (`queue.put()`). Blocks if queue maxsize is reached (Backpressure).
3. Consumer Threads: Pull items from queue (`queue.get()`), process work, and signal completion via `queue.task_done()`.
4. Graceful Shutdown: Using Sentinel objects (`None`) to signal worker threads to exit cleanly.
"""

import queue
import threading
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(threadName)s] %(message)s")
logger = logging.getLogger(__name__)

SENTINEL = None  # Poison pill to gracefully terminate worker threads

def producer(work_queue: queue.Queue, item_count: int) -> None:
    """Producer thread putting tasks into bounded queue."""
    logger.info(f"Producer starting. Will produce {item_count} items.")
    for i in range(1, item_count + 1):
        item = f"Task-{i}"
        # Blocks if queue.maxsize is reached (Thread Backpressure)
        work_queue.put(item)
        logger.info(f"Produced: {item} (Queue size: {work_queue.qsize()})")
        time.sleep(random.uniform(0.01, 0.05))

    logger.info("Producer finished. Putting sentinel pills for consumers.")


def consumer(work_queue: queue.Queue, result_queue: queue.Queue) -> None:
    """Consumer thread pulling tasks from queue and processing them."""
    while True:
        item = work_queue.get()
        if item is SENTINEL:
            logger.info("Received sentinel. Exiting consumer worker.")
            work_queue.task_done()
            break

        try:
            # Simulate work processing
            logger.info(f"Processing: {item}")
            time.sleep(random.uniform(0.05, 0.15))
            result = f"Result[{item}]"
            result_queue.put(result)
        finally:
            work_queue.task_done()


def run_producer_consumer_pipeline():
    # Bounded Queue enforces memory limits & backpressure
    work_queue = queue.Queue(maxsize=5)
    result_queue = queue.Queue()

    num_consumers = 3
    total_tasks = 10

    # Start Worker Consumer Threads
    consumers = []
    for i in range(num_consumers):
        t = threading.Thread(
            target=consumer,
            args=(work_queue, result_queue),
            name=f"ConsumerWorker-{i+1}"
        )
        t.start()
        consumers.append(t)

    # Start Producer Thread
    prod_thread = threading.Thread(
        target=producer,
        args=(work_queue, total_tasks),
        name="ProducerThread"
    )
    prod_thread.start()

    # Wait for producer to finish creating work
    prod_thread.join()

    # Send Poison Pills to stop consumers
    for _ in range(num_consumers):
        work_queue.put(SENTINEL)

    # Wait for all tasks to be fully marked task_done()
    work_queue.join()

    # Wait for consumer threads to finish cleanup
    for c in consumers:
        c.join()

    # Drain results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    logger.info(f"Pipeline Completed! Total Results Collected: {len(results)}")
    print(f"Results Sample: {results[:3]} ... {results[-1]}")


if __name__ == "__main__":
    run_producer_consumer_pipeline()
