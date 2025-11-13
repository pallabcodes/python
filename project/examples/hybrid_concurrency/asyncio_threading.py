"""
AsyncIO + Threading Hybrid Patterns.

This module demonstrates how to combine asyncio's excellent I/O handling
with threading's ability to handle CPU-bound work without blocking
the event loop.

Key patterns:
- Offloading CPU work to thread pools from async code
- Concurrent I/O with CPU processing
- Managing thread pool lifecycle in async context
- Error handling across async/thread boundaries
"""

import asyncio
import concurrent.futures
import threading
import time
import logging
from typing import Any, Callable, List, Dict, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a hybrid async/thread task."""
    task_id: str
    result: Any
    execution_time: float
    thread_id: int
    is_cpu_bound: bool


class AsyncioThreadingHybrid:
    """
    Hybrid concurrency combining asyncio and threading.

    This class demonstrates how to:
    - Use asyncio for I/O-bound operations
    - Offload CPU-bound work to thread pools
    - Maintain concurrency while avoiding GIL limitations
    - Handle errors across async/thread boundaries

    When to Use:
        - Mixing I/O and CPU-bound work
        - Offloading CPU work from event loop
        - Maintaining async responsiveness
        - Hybrid async/threading patterns

    Real-World Examples:
        - Web servers: Async I/O + CPU processing
        - Data pipelines: Async I/O + CPU transforms
        - APIs: Async requests + CPU processing
        - File processing: Async I/O + CPU parsing

    Gotchas:
        - GIL limits CPU parallelism
        - Thread pool overhead
        - Error propagation across boundaries
        - Resource cleanup required
        - Thread safety considerations

    Performance Notes:
        - Optimal for I/O-bound with CPU work
        - GIL limits true CPU parallelism
        - Thread pool overhead
        - Balance async vs thread execution
    """

    def __init__(self, max_workers: int = 4, thread_name_prefix: str = "hybrid-worker"):
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._running = False
        self._task_counter = 0
        self._lock = threading.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the hybrid executor."""
        if self._executor is not None:
            return

        loop = asyncio.get_event_loop()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix=self.thread_name_prefix
        )
        self._running = True
        logger.info(f"Started AsyncioThreadingHybrid with {self.max_workers} workers")

    async def stop(self):
        """Stop the hybrid executor."""
        if self._executor is None:
            return

        self._running = False
        self._executor.shutdown(wait=True)
        self._executor = None
        logger.info("Stopped AsyncioThreadingHybrid")

    def _get_next_task_id(self) -> str:
        """Get next unique task ID."""
        with self._lock:
            self._task_counter += 1
            return f"task_{self._task_counter}"

    async def run_io_task(self, coro: Callable) -> TaskResult:
        """
        Run an I/O-bound task using asyncio.

        Args:
            coro: Async coroutine function

        Returns:
            TaskResult with execution details
        """
        if not self._running:
            raise RuntimeError("Hybrid executor not started")

        task_id = self._get_next_task_id()
        start_time = time.time()

        try:
            result = await coro()
            execution_time = time.time() - start_time

            return TaskResult(
                task_id=task_id,
                result=result,
                execution_time=execution_time,
                thread_id=threading.get_ident(),
                is_cpu_bound=False
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"IO task {task_id} failed: {e}")
            raise

    async def run_cpu_task(self, func: Callable, *args, **kwargs) -> TaskResult:
        """
        Run a CPU-bound task using thread pool.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            TaskResult with execution details
        """
        if not self._running or self._executor is None:
            raise RuntimeError("Hybrid executor not started")

        task_id = self._get_next_task_id()
        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor, func, *args, **kwargs
            )
            execution_time = time.time() - start_time

            return TaskResult(
                task_id=task_id,
                result=result,
                execution_time=execution_time,
                thread_id=threading.get_ident(),
                is_cpu_bound=True
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"CPU task {task_id} failed: {e}")
            raise

    async def run_mixed_tasks(
        self,
        io_tasks: List[Callable],
        cpu_tasks: List[tuple]
    ) -> Dict[str, TaskResult]:
        """
        Run mixed I/O and CPU tasks concurrently.

        Args:
            io_tasks: List of async coroutines
            cpu_tasks: List of (func, args, kwargs) tuples

        Returns:
            Dict mapping task IDs to results
        """
        if not self._running:
            raise RuntimeError("Hybrid executor not started")

        # Create all tasks
        all_tasks = []

        # Add I/O tasks
        for coro in io_tasks:
            task = self.run_io_task(coro)
            all_tasks.append(task)

        # Add CPU tasks
        for func, args, kwargs in cpu_tasks:
            task = self.run_cpu_task(func, *args, **kwargs)
            all_tasks.append(task)

        # Run all concurrently
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Process results
        task_results = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                continue
            task_results[result.task_id] = result

        return task_results

    async def run_pipeline(
        self,
        io_stage: Callable,
        cpu_stage: Callable,
        data_items: List[Any]
    ) -> List[Any]:
        """
        Run a pipeline: I/O stage -> CPU stage -> collect results.

        Args:
            io_stage: Async function for I/O processing
            cpu_stage: Sync function for CPU processing
            data_items: Input data

        Returns:
            List of processed results
        """
        async def process_item(item):
            # Stage 1: I/O processing
            io_result = await self.run_io_task(lambda: io_stage(item))
            processed_item = io_result.result

            # Stage 2: CPU processing
            cpu_result = await self.run_cpu_task(cpu_stage, processed_item)

            return cpu_result.result

        # Process all items concurrently
        tasks = [process_item(item) for item in data_items]
        results = await asyncio.gather(*tasks)

        return results

    async def asyncio_threading_real_world_example(self) -> None:
        """
        Real-World Scenario: AsyncIO + Threading - Web API with Data Processing.

        REAL-WORLD SCENARIO:
        ====================
        You're building a web API that handles requests:
        - Receive HTTP requests (I/O-bound)
        - Process data with CPU-intensive operations
        - Problem: Blocking CPU work freezes async event loop
        
        THE PROBLEM WITHOUT HYBRID:
        ============================
        - CPU work blocks event loop → no concurrent requests
        - Use pure asyncio → CPU work blocks everything
        - Use pure threading → inefficient I/O handling
        - System unresponsive → poor user experience
        
        THE SOLUTION:
        =============
        AsyncIO + Threading enables:
        - AsyncIO handles I/O (requests) efficiently
        - Thread pool handles CPU work without blocking
        - Event loop stays responsive → concurrent requests
        - Optimal for I/O-heavy + moderate CPU workloads
        - Best of both worlds → responsive + efficient
        
        WHEN TO USE ASYNCIO + THREADING:
        =================================
        ✅ Web APIs with CPU processing
        ✅ I/O-heavy + moderate CPU workloads
        ✅ Need async responsiveness
        ✅ CPU work doesn't need true parallelism
        ✅ GIL acceptable for CPU work
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Web API with Data Processing")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Web API handling requests")
        print("  - Receive HTTP requests (I/O-bound)")
        print("  - Process data with CPU-intensive operations")
        print("  - Problem: Blocking CPU work freezes async event loop")
        print()
        print("THE PROBLEM:")
        print("  Without hybrid:")
        print("    ❌ CPU work blocks event loop → no concurrent requests")
        print("    ❌ Use pure asyncio → CPU work blocks everything")
        print("    ❌ Use pure threading → inefficient I/O handling")
        print("    ❌ System unresponsive → poor user experience")
        print()
        print("THE SOLUTION:")
        print("  With AsyncIO + Threading:")
        print("    ✅ AsyncIO handles I/O (requests) efficiently")
        print("    ✅ Thread pool handles CPU work without blocking")
        print("    ✅ Event loop stays responsive → concurrent requests")
        print("    ✅ Optimal for I/O-heavy + moderate CPU workloads")
        print()
        print("=" * 70)
        print()

        async def handle_api_request(request_id: str) -> dict:
            """Simulate handling an API request."""
            # I/O: Fetch data (async)
            await asyncio.sleep(0.05)  # Simulate network I/O
            data = f"data_for_{request_id}"

            # CPU: Process data (sync, offloaded to thread pool)
            def process_data(data: str) -> dict:
                # Simulate CPU-intensive processing
                result = 0
                for i in range(50000):
                    result += hash(data + str(i))
                return {"request_id": request_id, "processed": result, "data": data}

            cpu_result = await self.run_cpu_task(process_data, data)
            return cpu_result.result

        print("Simulating web API with 5 concurrent requests...")
        print()

        request_ids = [f"req_{i}" for i in range(5)]
        start_time = time.time()

        # Handle requests concurrently
        tasks = [handle_api_request(rid) for rid in request_ids]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        print("Results:")
        for result in results:
            print(f"  ✅ {result['request_id']}: Processed successfully")
        print(f"\nTotal time: {elapsed:.3f}s")
        print(f"Average per request: {elapsed/len(results):.3f}s")
        print("  ✅ AsyncIO + Threading enabled concurrent request handling!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE ASYNCIO + THREADING:")
        print("   ✅ Web APIs with CPU processing")
        print("   ✅ I/O-heavy + moderate CPU workloads")
        print("   ✅ Need async responsiveness")
        print("   ✅ CPU work doesn't need true parallelism")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Event loop stays responsive")
        print("   - Concurrent I/O handling")
        print("   - CPU work doesn't block")
        print("   - Optimal for mixed workloads")
        print("=" * 70)
        print()


# Example usage functions
async def simulate_io_operation(data: str, delay: float = 0.1) -> str:
    """Simulate I/O operation."""
    await asyncio.sleep(delay)
    return f"IO_processed_{data}"

def simulate_cpu_operation(data: str) -> str:
    """Simulate CPU-bound operation."""
    # Simulate CPU work
    result = 0
    for i in range(100000):
        result += hash(data + str(i))
    return f"CPU_processed_{data}_{result}"

async def demonstrate_asyncio_threading_hybrid():
    """Demonstrate AsyncIO + Threading hybrid patterns."""

    print("🔄 AsyncIO + Threading Hybrid Demonstration")
    print("=" * 50)

    async with AsyncioThreadingHybrid(max_workers=4) as hybrid:

        print("\n1. Basic I/O and CPU task execution:")
        print("-" * 40)

        # Run I/O task
        io_result = await hybrid.run_io_task(
            lambda: simulate_io_operation("data1", 0.2)
        )
        print(f"IO task: {io_result.result} ({io_result.execution_time:.3f}s, "
              f"thread={io_result.thread_id}, is_cpu={io_result.is_cpu_bound})")

        # Run CPU task
        cpu_result = await hybrid.run_cpu_task(simulate_cpu_operation, "data2")
        print(f"CPU task: {cpu_result.result} ({cpu_result.execution_time:.3f}s, "
              f"thread={cpu_result.thread_id}, is_cpu={cpu_result.is_cpu_bound})")

        print("\n2. Mixed concurrent execution:")
        print("-" * 35)

        # Run mixed tasks
        io_tasks = [
            lambda: simulate_io_operation(f"io_data_{i}", 0.1)
            for i in range(3)
        ]
        cpu_tasks = [
            (simulate_cpu_operation, [f"cpu_data_{i}"], {})
            for i in range(3)
        ]

        start_time = time.time()
        results = await hybrid.run_mixed_tasks(io_tasks, cpu_tasks)
        total_time = time.time() - start_time

        print(f"Completed {len(results)} tasks in {total_time:.3f}s")
        for task_id, result in results.items():
            print(f"  {task_id}: {result.result} ({result.execution_time:.3f}s)")

        print("\n3. Pipeline processing:")
        print("-" * 25)

        # Pipeline: I/O -> CPU -> Result
        data_items = [f"item_{i}" for i in range(5)]

        pipeline_results = await hybrid.run_pipeline(
            lambda x: simulate_io_operation(x, 0.05),
            simulate_cpu_operation,
            data_items
        )

        print(f"Pipeline processed {len(pipeline_results)} items:")
        for i, result in enumerate(pipeline_results):
            print(f"  {data_items[i]} -> {result}")

    print("\n✅ AsyncIO + Threading hybrid demonstration complete!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run demonstration
    asyncio.run(demonstrate_asyncio_threading_hybrid())
