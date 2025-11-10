"""
Basic asyncio examples demonstrating coroutines, event loops, tasks, and futures.

This module covers:
- Defining and calling coroutines with async/await
- Event loop management and execution
- Task creation and concurrent execution
- Future objects and result handling
- Synchronization with asyncio.sleep
- Exception handling in async code
"""

import asyncio
import time
from typing import Any, Coroutine


class BasicAsyncioExample:
    """
    Basic asyncio examples for coroutines, tasks, and event loops.
    """

    @staticmethod
    async def simple_coroutine(name: str, delay: float = 1.0) -> str:
        """
        A simple coroutine that simulates async work.

        Args:
            name: Coroutine identifier
            delay: Delay in seconds

        Returns:
            Result message
        """
        print(f"Coroutine {name} starting...")
        await asyncio.sleep(delay)
        print(f"Coroutine {name} completed after {delay}s")
        return f"Result from {name}"

    @staticmethod
    async def cpu_bound_simulation(iterations: int) -> int:
        """
        Simulate CPU-bound work using asyncio.sleep for context switching.

        Args:
            iterations: Number of iterations

        Returns:
            Computed result
        """
        result = 0
        for i in range(iterations):
            result += i ** 2
            # Yield control to allow other coroutines to run
            if i % 1000 == 0:
                await asyncio.sleep(0)  # Allow other tasks to run
        return result

    async def basic_coroutine_execution(self) -> None:
        """Demonstrate basic coroutine definition and execution."""
        print("=== Basic Coroutine Execution ===")

        # Call coroutines sequentially
        print("Sequential execution:")
        start_time = time.time()

        result1 = await self.simple_coroutine("A", 0.5)
        result2 = await self.simple_coroutine("B", 0.3)
        result3 = await self.simple_coroutine("C", 0.2)

        sequential_time = time.time() - start_time
        print(".2f")
        print(f"Results: {result1}, {result2}, {result3}")
        print()

    async def concurrent_execution(self) -> None:
        """Demonstrate concurrent execution of coroutines."""
        print("=== Concurrent Execution ===")

        print("Concurrent execution:")
        start_time = time.time()

        # Create tasks for concurrent execution
        task1 = asyncio.create_task(self.simple_coroutine("A", 0.5))
        task2 = asyncio.create_task(self.simple_coroutine("B", 0.3))
        task3 = asyncio.create_task(self.simple_coroutine("C", 0.2))

        # Wait for all tasks to complete
        results = await asyncio.gather(task1, task2, task3)

        concurrent_time = time.time() - start_time
        print(".2f")
        print(f"Results: {results}")
        print()

    async def task_vs_coroutine(self) -> None:
        """Compare direct coroutine calls vs task creation."""
        print("=== Task vs Coroutine Comparison ===")

        async def worker(task_id: str) -> str:
            """Worker coroutine."""
            await asyncio.sleep(0.5)
            return f"Task {task_id} result"

        # Method 1: Direct await (sequential)
        print("Direct await (sequential):")
        start_time = time.time()
        result1 = await worker("1")
        result2 = await worker("2")
        sequential_time = time.time() - start_time
        print(".2f")

        # Method 2: Create tasks (concurrent)
        print("Task creation (concurrent):")
        start_time = time.time()
        task1 = asyncio.create_task(worker("1"))
        task2 = asyncio.create_task(worker("2"))
        results = await asyncio.gather(task1, task2)
        concurrent_time = time.time() - start_time
        print(".2f")
        print()

    async def future_operations(self) -> None:
        """Demonstrate Future objects and their operations."""
        print("=== Future Operations ===")

        async def async_operation(name: str, delay: float) -> str:
            """Async operation that returns a Future."""
            await asyncio.sleep(delay)
            return f"Future result: {name}"

        # Create futures from coroutines
        future1 = asyncio.ensure_future(async_operation("A", 0.3))
        future2 = asyncio.ensure_future(async_operation("B", 0.5))
        future3 = asyncio.ensure_future(async_operation("C", 0.2))

        print("Futures created, checking status...")
        print(f"Future1 done: {future1.done()}")
        print(f"Future2 done: {future2.done()}")
        print(f"Future3 done: {future3.done()}")

        # Wait for futures with timeout
        done, pending = await asyncio.wait(
            [future1, future2, future3],
            timeout=1.0,
            return_when=asyncio.ALL_COMPLETED
        )

        print(f"Completed: {len(done)}, Pending: {len(pending)}")

        # Get results
        for future in done:
            try:
                result = future.result()
                print(f"Future result: {result}")
            except Exception as e:
                print(f"Future exception: {e}")

        print()

    async def exception_handling(self) -> None:
        """Demonstrate exception handling in async code."""
        print("=== Exception Handling ===")

        async def failing_coroutine(name: str, should_fail: bool = False) -> str:
            """Coroutine that may raise an exception."""
            await asyncio.sleep(0.2)
            if should_fail:
                raise ValueError(f"Simulated failure in {name}")
            return f"Success from {name}"

        # Handle exceptions in individual tasks
        print("Individual exception handling:")
        try:
            result1 = await failing_coroutine("Task1", False)
            print(f"Task1: {result1}")
        except Exception as e:
            print(f"Task1 failed: {e}")

        try:
            result2 = await failing_coroutine("Task2", True)
            print(f"Task2: {result2}")
        except Exception as e:
            print(f"Task2 failed: {e}")

        # Handle exceptions in gather
        print("\nException handling with gather:")
        tasks = [
            failing_coroutine("A", False),
            failing_coroutine("B", True),
            failing_coroutine("C", False)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {chr(65+i)} failed: {result}")
            else:
                print(f"Task {chr(65+i)} succeeded: {result}")

        print()

    async def event_loop_info(self) -> None:
        """Demonstrate event loop information and management."""
        print("=== Event Loop Information ===")

        loop = asyncio.get_running_loop()

        print(f"Event loop: {loop}")
        print(f"Loop is running: {loop.is_running()}")
        print(f"Loop is closed: {loop.is_closed()}")

        # Get loop time
        start_time = loop.time()
        await asyncio.sleep(0.1)
        end_time = loop.time()

        print(".3f")

        # Schedule callback
        def callback():
            print("Callback executed in event loop")

        loop.call_soon(callback)

        # Schedule delayed callback
        def delayed_callback():
            print("Delayed callback executed")

        loop.call_later(0.2, delayed_callback)

        await asyncio.sleep(0.3)
        print()

    async def nested_coroutines(self) -> None:
        """Demonstrate nested coroutine calls."""
        print("=== Nested Coroutines ===")

        async def inner_operation(name: str) -> str:
            """Inner coroutine operation."""
            await asyncio.sleep(0.1)
            return f"Inner result: {name}"

        async def middle_operation(name: str) -> str:
            """Middle coroutine that calls inner operations."""
            result1 = await inner_operation(f"{name}-1")
            result2 = await inner_operation(f"{name}-2")
            await asyncio.sleep(0.1)
            return f"Middle result: {name} [{result1}, {result2}]"

        async def outer_operation() -> str:
            """Outer coroutine that orchestrates everything."""
            # Concurrent execution of middle operations
            tasks = [
                middle_operation("GroupA"),
                middle_operation("GroupB")
            ]

            results = await asyncio.gather(*tasks)
            return f"Outer result: {', '.join(results)}"

        result = await outer_operation()
        print(f"Final result: {result}")
        print()

    async def performance_comparison(self) -> None:
        """Compare performance of sequential vs concurrent execution."""
        print("=== Performance Comparison ===")

        async def compute_task(task_id: str, iterations: int) -> tuple[str, float]:
            """A compute-intensive task."""
            start = time.time()
            result = await self.cpu_bound_simulation(iterations)
            duration = time.time() - start
            return f"Task {task_id}", duration

        # Sequential execution
        print("Sequential execution:")
        start_time = time.time()
        results_seq = []
        for i in range(3):
            result = await compute_task(f"Seq-{i+1}", 50000)
            results_seq.append(result)
        sequential_time = time.time() - start_time

        print(".2f")
        for name, duration in results_seq:
            print(".3f")

        # Concurrent execution
        print("\nConcurrent execution:")
        start_time = time.time()
        tasks = [compute_task(f"Conc-{i+1}", 50000) for i in range(3)]
        results_conc = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        print(".2f")
        for name, duration in results_conc:
            print(".3f")

        speedup = sequential_time / concurrent_time
        print(".2f")
        print()


async def main() -> None:
    """Run all basic asyncio examples."""
    print("Asyncio Basic Examples")
    print("=" * 25)

    example = BasicAsyncioExample()

    await example.basic_coroutine_execution()
    await example.concurrent_execution()
    await example.task_vs_coroutine()
    await example.future_operations()
    await example.exception_handling()
    await example.event_loop_info()
    await example.nested_coroutines()
    await example.performance_comparison()

    print("All basic examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
