"""
Threading + Multiprocessing Hybrid Patterns.

This module demonstrates how to combine threading's lightweight concurrency
with multiprocessing's true parallelism for complex workloads.

Key patterns:
- Threading for I/O-bound concurrent operations
- Multiprocessing for CPU-bound parallel processing
- Coordination between threads and processes
- Resource sharing and synchronization across boundaries
"""

import threading
import multiprocessing
import concurrent.futures
import time
import logging
import queue
import os
from typing import Any, Callable, List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from threading import Event, Semaphore
import signal
import sys

logger = logging.getLogger(__name__)


@dataclass
class HybridTaskResult:
    """Result of a hybrid thread/process task."""
    task_id: str
    result: Any
    execution_time: float
    worker_type: str  # 'thread' or 'process'
    worker_id: int


class ThreadingMultiprocessingHybrid:
    """
    Hybrid concurrency combining threading and multiprocessing.

    This class demonstrates how to:
    - Use threads for I/O-bound concurrent work
    - Use processes for CPU-bound parallel work
    - Coordinate between thread and process pools
    - Handle complex workflows spanning both models
    """

    def __init__(self,
                 max_threads: int = 8,
                 max_processes: Optional[int] = None,
                 thread_name_prefix: str = "hybrid-thread",
                 process_name_prefix: str = "hybrid-process"):
        self.max_threads = max_threads
        self.max_processes = max_processes or multiprocessing.cpu_count()
        self.thread_name_prefix = thread_name_prefix
        self.process_name_prefix = process_name_prefix

        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None
        self._running = False
        self._task_counter = 0
        self._lock = threading.Lock()

        # Coordination primitives
        self._shutdown_event = Event()
        self._thread_semaphore = Semaphore(max_threads)
        self._process_semaphore = Semaphore(self.max_processes)

        # Results coordination
        self._results_queue: Optional[queue.Queue] = None
        self._results_thread: Optional[threading.Thread] = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def start(self):
        """Start the hybrid executor."""
        if self._running:
            return

        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Create executors
        self._thread_executor = ThreadPoolExecutor(
            max_workers=self.max_threads,
            thread_name_prefix=self.thread_name_prefix
        )
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.max_processes
        )

        # Setup results coordination
        self._results_queue = queue.Queue()
        self._results_thread = threading.Thread(
            target=self._results_processor,
            name="results-processor",
            daemon=True
        )
        self._results_thread.start()

        self._running = True
        logger.info(f"Started ThreadingMultiprocessingHybrid "
                   f"(threads={self.max_threads}, processes={self.max_processes})")

    def stop(self):
        """Stop the hybrid executor."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        # Shutdown executors
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
            self._thread_executor = None

        if self._process_executor:
            self._process_executor.shutdown(wait=True)
            self._process_executor = None

        # Wait for results processor
        if self._results_thread and self._results_thread.is_alive():
            self._results_thread.join(timeout=5.0)

        logger.info("Stopped ThreadingMultiprocessingHybrid")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
        sys.exit(0)

    def _get_next_task_id(self) -> str:
        """Get next unique task ID."""
        with self._lock:
            self._task_counter += 1
            return f"hybrid_task_{self._task_counter}"

    def _results_processor(self):
        """Process results from the results queue."""
        while not self._shutdown_event.is_set():
            try:
                # Non-blocking queue check
                result = self._results_queue.get(timeout=0.1)
                logger.debug(f"Processed result: {result.task_id}")
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing result: {e}")

    def submit_thread_task(self, func: Callable, *args, **kwargs) -> str:
        """
        Submit a task to the thread pool.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task ID for tracking
        """
        if not self._running or not self._thread_executor:
            raise RuntimeError("Hybrid executor not started")

        task_id = self._get_next_task_id()

        def wrapped_task():
            start_time = time.time()
            try:
                with self._thread_semaphore:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    task_result = HybridTaskResult(
                        task_id=task_id,
                        result=result,
                        execution_time=execution_time,
                        worker_type='thread',
                        worker_id=threading.get_ident()
                    )

                    if self._results_queue:
                        self._results_queue.put(task_result)

                    return task_result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Thread task {task_id} failed: {e}")
                raise

        self._thread_executor.submit(wrapped_task)
        return task_id

    def submit_process_task(self, func: Callable, *args, **kwargs) -> str:
        """
        Submit a task to the process pool.

        Args:
            func: Function to execute (must be picklable)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task ID for tracking
        """
        if not self._running or not self._process_executor:
            raise RuntimeError("Hybrid executor not started")

        task_id = self._get_next_task_id()

        def wrapped_task():
            start_time = time.time()
            try:
                with self._process_semaphore:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    task_result = HybridTaskResult(
                        task_id=task_id,
                        result=result,
                        execution_time=execution_time,
                        worker_type='process',
                        worker_id=os.getpid()
                    )

                    return task_result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Process task {task_id} failed: {e}")
                raise

        self._process_executor.submit(wrapped_task)
        return task_id

    def submit_hybrid_workflow(
        self,
        thread_tasks: List[Tuple[Callable, Tuple, Dict]],
        process_tasks: List[Tuple[Callable, Tuple, Dict]]
    ) -> Dict[str, str]:
        """
        Submit a hybrid workflow with both thread and process tasks.

        Args:
            thread_tasks: List of (func, args, kwargs) tuples for threads
            process_tasks: List of (func, args, kwargs) tuples for processes

        Returns:
            Dict mapping task types to lists of task IDs
        """
        if not self._running:
            raise RuntimeError("Hybrid executor not started")

        thread_ids = []
        process_ids = []

        # Submit thread tasks
        for func, args, kwargs in thread_tasks:
            task_id = self.submit_thread_task(func, *args, **kwargs)
            thread_ids.append(task_id)

        # Submit process tasks
        for func, args, kwargs in process_tasks:
            task_id = self.submit_process_task(func, *args, **kwargs)
            process_ids.append(task_id)

        return {
            'thread_tasks': thread_ids,
            'process_tasks': process_ids
        }

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all submitted tasks to complete.

        Args:
            timeout: Maximum time to wait (None for indefinite)

        Returns:
            True if all tasks completed, False if timeout occurred
        """
        if not self._running:
            return True

        # Wait for thread executor
        if self._thread_executor:
            try:
                self._thread_executor.shutdown(wait=True, timeout=timeout)
            except Exception:
                pass

        # Wait for process executor
        if self._process_executor:
            try:
                self._process_executor.shutdown(wait=True, timeout=timeout)
            except Exception:
                pass

        return True

    def get_queue_size(self) -> Dict[str, int]:
        """
        Get the current queue sizes for monitoring.

        Returns:
            Dict with thread and process queue information
        """
        return {
            'results_queue_size': self._results_queue.qsize() if self._results_queue else 0,
            'thread_workers': self.max_threads,
            'process_workers': self.max_processes,
            'shutdown_pending': self._shutdown_event.is_set()
        }


# Module-level functions for multiprocessing compatibility
def cpu_intensive_task(data: str, intensity: int = 100000) -> Dict[str, Any]:
    """CPU-intensive task that benefits from multiprocessing."""
    import math

    result = 0
    for i in range(intensity):
        x = hash(data + str(i)) % 10000
        result += math.sin(x) * math.cos(x) * math.log(abs(x) + 1)

    return {
        'input': data,
        'result': result,
        'intensity': intensity,
        'process_id': os.getpid()
    }

def io_simulation_task(data: str, delay: float = 0.1) -> Dict[str, Any]:
    """I/O simulation task that benefits from threading."""
    import time
    start = time.time()
    time.sleep(delay)  # Simulate I/O delay
    end = time.time()

    return {
        'input': data,
        'delay': delay,
        'actual_delay': end - start,
        'thread_id': threading.get_ident()
    }


def demonstrate_threading_multiprocessing_hybrid():
    """Demonstrate Threading + Multiprocessing hybrid patterns."""

    print("🔄 Threading + Multiprocessing Hybrid Demonstration")
    print("=" * 58)

    with ThreadingMultiprocessingHybrid(max_threads=4, max_processes=2) as hybrid:

        print("\n1. Basic thread and process task submission:")
        print("-" * 48)

        # Submit individual tasks
        thread_task_id = hybrid.submit_thread_task(
            io_simulation_task, "thread_data", 0.2
        )
        process_task_id = hybrid.submit_process_task(
            cpu_intensive_task, "process_data", 50000
        )

        print(f"Submitted thread task: {thread_task_id}")
        print(f"Submitted process task: {process_task_id}")

        print("\n2. Hybrid workflow submission:")
        print("-" * 33)

        # Submit hybrid workflow
        thread_tasks = [
            (io_simulation_task, ("io_1", 0.1), {}),
            (io_simulation_task, ("io_2", 0.1), {}),
            (io_simulation_task, ("io_3", 0.1), {}),
        ]
        process_tasks = [
            (cpu_intensive_task, ("cpu_1", 30000), {}),
            (cpu_intensive_task, ("cpu_2", 30000), {}),
        ]

        start_time = time.time()
        workflow_ids = hybrid.submit_hybrid_workflow(thread_tasks, process_tasks)
        print(f"Submitted {len(workflow_ids['thread_tasks'])} thread tasks")
        print(f"Submitted {len(workflow_ids['process_tasks'])} process tasks")

        # Wait for completion
        hybrid.wait_for_completion(timeout=30.0)
        total_time = time.time() - start_time

        print(f"Executed workflow in {total_time:.3f}s")
        print("\n3. Queue monitoring:")
        print("-" * 20)
        queue_info = hybrid.get_queue_size()
        print(f"Results queue size: {queue_info['results_queue_size']}")
        print(f"Thread workers: {queue_info['thread_workers']}")
        print(f"Process workers: {queue_info['process_workers']}")

        # Wait a bit more for results processing
        time.sleep(1.0)

        final_queue_info = hybrid.get_queue_size()
        print(f"Final results queue size: {final_queue_info['results_queue_size']}")

    print("\n✅ Threading + Multiprocessing hybrid demonstration complete!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run demonstration
    demonstrate_threading_multiprocessing_hybrid()
