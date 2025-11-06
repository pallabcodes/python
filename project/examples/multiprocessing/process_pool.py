"""
Process pool examples demonstrating concurrent.futures.ProcessPoolExecutor and multiprocessing.Pool.

This module covers:
- ProcessPoolExecutor for high-level process management
- multiprocessing.Pool for lower-level control
- Map/reduce operations
- Asynchronous task submission
- Pool configuration and resource management
"""

import concurrent.futures
import multiprocessing
import os
import time
from typing import Any, List, Optional


class ProcessPoolExample:
    """
    Examples using process pools for parallel computation.
    """

    @staticmethod
    def cpu_bound_task(x: int) -> int:
        """
        CPU-bound task that benefits from parallelization.

        Args:
            x: Input value

        Returns:
            Computed result
        """
        # Simulate CPU-intensive work
        result = 0
        for i in range(x):
            result += i * i
        return result

    @staticmethod
    def io_bound_task(filename: str) -> dict:
        """
        IO-bound task (simulated).

        Args:
            filename: File to process

        Returns:
            Processing result
        """
        # Simulate IO operation
        time.sleep(0.1)
        return {
            "filename": filename,
            "size": len(filename) * 100,
            "processed_at": time.time()
        }

    def process_pool_executor_basic(self) -> None:
        """Demonstrate basic ProcessPoolExecutor usage."""
        print("=== ProcessPoolExecutor Basic Usage ===")

        # Create input data
        numbers = [100000, 200000, 150000, 300000]

        # Sequential execution
        print("Sequential execution:")
        start_time = time.time()
        sequential_results = [self.cpu_bound_task(x) for x in numbers]
        sequential_time = time.time() - start_time
        print(".2f")

        # Parallel execution with ProcessPoolExecutor
        print("Parallel execution with ProcessPoolExecutor:")
        start_time = time.time()

        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit all tasks
            futures = [executor.submit(self.cpu_bound_task, x) for x in numbers]

            # Collect results as they complete
            parallel_results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                parallel_results.append(result)

        parallel_time = time.time() - start_time
        print(".2f")
        print(".1f")
        print()

    def process_pool_executor_map(self) -> None:
        """Demonstrate ProcessPoolExecutor.map() method."""
        print("=== ProcessPoolExecutor.map() Usage ===")

        # Create input data
        numbers = list(range(10, 15))

        print(f"Input numbers: {numbers}")

        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            # Use map for ordered results
            results = list(executor.map(self.cpu_bound_task, numbers))

        print(f"Results: {results}")

        # Verify order is preserved
        for i, (input_val, result) in enumerate(zip(numbers, results)):
            expected = sum(j * j for j in range(input_val))
            print(f"  {input_val} -> {result} (expected: {expected}) {'✓' if result == expected else '✗'}")

        print()

    def process_pool_executor_async(self) -> None:
        """Demonstrate asynchronous task submission and callbacks."""
        print("=== Asynchronous Task Submission ===")

        def task_done_callback(future: concurrent.futures.Future) -> None:
            """Callback executed when task completes."""
            try:
                result = future.result()
                print(f"Task completed with result: {result}")
            except Exception as exc:
                print(f"Task failed with exception: {exc}")

        with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
            # Submit tasks asynchronously
            futures = []
            for i in range(5):
                future = executor.submit(self.cpu_bound_task, 50000 + i * 10000)
                future.add_done_callback(task_done_callback)
                futures.append(future)

            # Wait for all tasks to complete
            print("Waiting for all tasks to complete...")
            for future in concurrent.futures.as_completed(futures):
                # Results already handled by callback
                pass

        print("All asynchronous tasks completed!\n")

    def multiprocessing_pool_basic(self) -> None:
        """Demonstrate basic multiprocessing.Pool usage."""
        print("=== multiprocessing.Pool Basic Usage ===")

        # Create input data
        numbers = [50000, 100000, 75000, 125000]

        # Using Pool with map
        with multiprocessing.Pool(processes=4) as pool:
            print("Using Pool.map():")
            start_time = time.time()
            results = pool.map(self.cpu_bound_task, numbers)
            pool_time = time.time() - start_time

        print(".2f")
        print(f"Results: {results}")
        print()

    def multiprocessing_pool_advanced(self) -> None:
        """Demonstrate advanced multiprocessing.Pool features."""
        print("=== Advanced multiprocessing.Pool Features ===")

        # Create input data
        numbers = [30000, 60000, 90000, 120000]
        files = [f"file_{i}.txt" for i in range(4)]

        with multiprocessing.Pool(processes=4) as pool:
            # Using apply_async for individual tasks
            print("Using apply_async():")
            results = []
            for num in numbers:
                result = pool.apply_async(self.cpu_bound_task, args=(num,))
                results.append(result)

            # Collect results
            async_results = [r.get() for r in results]
            print(f"apply_async results: {async_results}")

            # Using map_async
            print("Using map_async():")
            map_result = pool.map_async(self.cpu_bound_task, numbers)
            map_results = map_result.get()
            print(f"map_async results: {map_results}")

            # Using starmap for multiple arguments
            print("Using starmap():")
            # Create tasks with multiple arguments
            tasks = [(num, 2) for num in numbers[:2]]  # (number, multiplier)

            def multiply_task(x: int, multiplier: int) -> int:
                return self.cpu_bound_task(x) * multiplier

            starmap_results = pool.starmap(multiply_task, tasks)
            print(f"starmap results: {starmap_results}")

        print()

    def pool_resource_management(self) -> None:
        """Demonstrate pool resource management and configuration."""
        print("=== Pool Resource Management ===")

        print(f"CPU count: {multiprocessing.cpu_count()}")

        # Different pool configurations
        configurations = [
            ("Default pool", None),
            ("Limited workers", 2),
            ("Maximum workers", min(multiprocessing.cpu_count(), 8))
        ]

        numbers = [25000, 50000, 75000]

        for config_name, max_workers in configurations:
            print(f"{config_name} (max_workers={max_workers}):")

            with multiprocessing.Pool(processes=max_workers) as pool:
                start_time = time.time()
                results = pool.map(self.cpu_bound_task, numbers)
                elapsed = time.time() - start_time

                print(".2f")
                print(f"  Workers used: {pool._processes}")

        print()

    def error_handling_in_pools(self) -> None:
        """Demonstrate error handling in process pools."""
        print("=== Error Handling in Process Pools ===")

        def task_that_may_fail(x: int) -> int:
            """Task that may raise an exception."""
            if x == 50000:
                raise ValueError(f"Task failed for input {x}")
            return self.cpu_bound_task(x)

        numbers = [25000, 50000, 75000]

        print("Testing error handling with ProcessPoolExecutor:")
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(task_that_may_fail, x) for x in numbers]

            for i, future in enumerate(futures):
                try:
                    result = future.result()
                    print(f"Task {i+1} succeeded: {result}")
                except Exception as exc:
                    print(f"Task {i+1} failed: {exc}")

        print("\nTesting error handling with multiprocessing.Pool:")
        with multiprocessing.Pool(processes=3) as pool:
            try:
                results = pool.map(task_that_may_fail, numbers)
                print(f"All tasks succeeded: {results}")
            except Exception as exc:
                print(f"One or more tasks failed: {exc}")

        print()


def main() -> None:
    """Run all process pool examples."""
    print("Multiprocessing Process Pool Examples")
    print("=" * 45)

    example = ProcessPoolExample()

    example.process_pool_executor_basic()
    example.process_pool_executor_map()
    example.process_pool_executor_async()
    example.multiprocessing_pool_basic()
    example.multiprocessing_pool_advanced()
    example.pool_resource_management()
    example.error_handling_in_pools()

    print("All process pool examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()
