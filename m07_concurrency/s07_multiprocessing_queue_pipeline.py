"""
Module: Multi-Core Process Parallelism with Multiprocessing Queue
Target: Google L6/L7 Systems Standard

Key Concepts:
1. `multiprocessing.Queue`: Process-safe IPC Queue backed by OS pipes & shared memory lock primitives.
2. True Hardware Parallelism: Each consumer runs in a SEPARATE Python process with its own CPython interpreter & GIL.
3. IPC Work Distribution: Producer process feeds tasks into the queue; N parallel worker processes execute CPU-bound work in parallel.
4. Result Aggregation: Process workers push output back into a dedicated response IPC queue.
"""

import multiprocessing as mp
import os
import time
import math
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PID:%(process)d] %(message)s")
logger = logging.getLogger(__name__)

SENTINEL = None

def cpu_heavy_task(n: int) -> int:
    """Simulate CPU-intensive calculation (bypassing GIL when run across processes)."""
    val = 0
    for i in range(1, n * 1000):
        val += math.isqrt(i)
    return val

def process_worker(task_queue: mp.Queue, result_queue: mp.Queue) -> None:
    """Worker loop running in a dedicated OS Process."""
    logger.info(f"Worker process started (PID: {os.getpid()}).")
    while True:
        task = task_queue.get()
        if task is SENTINEL:
            logger.info("Received process sentinel. Terminating worker.")
            break

        task_id, num = task
        logger.info(f"Executing CPU task {task_id} with param {num}")

        # Heavy CPU computation running in TRUE parallel across CPU cores
        res = cpu_heavy_task(num)

        result_queue.put((task_id, res, os.getpid()))

def run_multiprocessing_queue_pipeline():
    task_queue = mp.Queue(maxsize=10)
    result_queue = mp.Queue()

    num_workers = mp.cpu_count()
    logger.info(f"Launching {num_workers} Parallel Worker Processes...")

    processes = []
    for _ in range(num_workers):
        p = mp.Process(target=process_worker, args=(task_queue, result_queue))
        p.start()
        processes.append(p)

    total_tasks = 12
    start_time = time.perf_counter()

    # Feed tasks to workers
    for i in range(1, total_tasks + 1):
        task_queue.put((i, 5000 + (i * 500)))

    # Push poison pills to shut down worker processes
    for _ in range(num_workers):
        task_queue.put(SENTINEL)

    # Collect results from parallel workers
    results = []
    for _ in range(total_tasks):
        res = result_queue.get()
        results.append(res)
        logger.info(f"Collected Result from Task {res[0]} computed by PID {res[2]}")

    for p in processes:
        p.join()

    elapsed = time.perf_counter() - start_time
    logger.info(f"Parallel Multiprocessing Queue Pipeline completed in {elapsed:.3f}s")
    print(f"Aggregated {len(results)} Parallel Process Results across {num_workers} CPU Cores.")


if __name__ == "__main__":
    run_multiprocessing_queue_pipeline()
