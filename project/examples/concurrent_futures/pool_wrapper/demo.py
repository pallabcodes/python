"""
Demonstrations of TypedThreadPoolExecutor features.

This module provides practical examples of using the enhanced
executor wrapper for various concurrent programming scenarios.
"""

import time
import random
import logging
from typing import List, Dict, Any

from .typed_executor import TypedThreadPoolExecutor
from .task_result import TaskBatchResult


def demo_basic_task_submission() -> None:
    """Demonstrate basic task submission and result retrieval."""
    print("=== Basic Task Submission Demo ===")

    def calculate_square(n: int) -> int:
        """Calculate square of a number."""
        time.sleep(0.1)  # Simulate work
        return n * n

    with TypedThreadPoolExecutor(max_workers=4) as executor:
        # Submit multiple tasks
        task_ids = []
        for i in range(5):
            task_id = executor.submit_task(calculate_square, i)
            task_ids.append(task_id)
            print(f"Submitted task {task_id} for {i}^2")

        # Get results
        results = []
        for task_id in task_ids:
            result = executor.get_task_result(task_id)
            results.append(result)
            print(f"Task {task_id}: {result.result} (took {result.duration:.2f}s)")

        successful = sum(1 for r in results if r.success)
        print(f"Completed: {successful}/{len(results)} tasks successfully")


def demo_batch_processing() -> None:
    """Demonstrate batch task submission and processing."""
    print("\n=== Batch Processing Demo ===")

    def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with simulated work."""
        time.sleep(random.uniform(0.1, 0.3))
        return {
            "id": data["id"],
            "processed": True,
            "result": data["value"] * 2,
            "worker": "batch_processor"
        }

    # Create batch of tasks
    tasks = [
        (process_data, ({"id": i, "value": i * 10},), {})
        for i in range(10)
    ]

    with TypedThreadPoolExecutor(max_workers=3) as executor:
        # Submit batch
        print("Submitting batch of 10 tasks...")
        task_ids = executor.submit_batch(tasks)

        # Get batch results
        batch_result = executor.get_batch_results(task_ids, timeout=10.0)

        print(f"Batch completed: {batch_result.successful_tasks}/{batch_result.total_tasks} successful")
        print(".2f")
        print(f"Total duration: {batch_result.total_duration:.2f}s")

        if batch_result.error_details:
            print(f"Errors: {len(batch_result.error_details)}")


def demo_timeout_and_cancellation() -> None:
    """Demonstrate timeout and cancellation handling."""
    print("\n=== Timeout and Cancellation Demo ===")

    def slow_task(task_id: str, duration: float) -> str:
        """Task that takes specified time."""
        time.sleep(duration)
        return f"Task {task_id} completed"

    def fast_task(task_id: str) -> str:
        """Fast task for comparison."""
        time.sleep(0.1)
        return f"Task {task_id} completed quickly"

    with TypedThreadPoolExecutor(max_workers=2) as executor:
        # Submit mix of fast and slow tasks
        slow_task_id = executor.submit_task(slow_task, "slow", 2.0)
        fast_task_id = executor.submit_task(fast_task, "fast")

        print("Submitted slow task (2s) and fast task (0.1s)")

        # Try to get fast task result with short timeout
        try:
            fast_result = executor.get_task_result(fast_task_id, timeout=0.5)
            print(f"Fast task completed: {fast_result.success}")
        except Exception as e:
            print(f"Fast task retrieval failed: {e}")

        # Cancel the slow task
        cancelled = executor.cancel_task(slow_task_id)
        print(f"Slow task cancelled: {cancelled}")

        # Try to get cancelled task result
        try:
            cancelled_result = executor.get_task_result(slow_task_id, timeout=1.0)
            print(f"Cancelled task result: success={cancelled_result.success}, "
                  f"cancelled={cancelled_result.cancelled}")
        except Exception as e:
            print(f"Cancelled task retrieval failed: {e}")


def demo_error_handling() -> None:
    """Demonstrate comprehensive error handling."""
    print("\n=== Error Handling Demo ===")

    def reliable_task(task_id: str) -> str:
        """Always succeeds."""
        return f"Task {task_id} succeeded"

    def unreliable_task(task_id: str) -> str:
        """Sometimes fails."""
        if random.random() < 0.7:  # 70% failure rate
            raise ValueError(f"Task {task_id} failed randomly")
        return f"Task {task_id} succeeded"

    with TypedThreadPoolExecutor(max_workers=3) as executor:
        # Submit mix of reliable and unreliable tasks
        task_ids = []
        for i in range(10):
            if i % 3 == 0:
                task_id = executor.submit_task(unreliable_task, f"unreliable-{i}")
            else:
                task_id = executor.submit_task(reliable_task, f"reliable-{i}")
            task_ids.append(task_id)

        print("Submitted 10 tasks (some unreliable)")

        # Collect all results
        results = []
        for task_id in task_ids:
            result = executor.get_task_result(task_id)
            results.append(result)

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"Results: {len(successful)} successful, {len(failed)} failed")

        if failed:
            print("Sample errors:")
            for failure in failed[:3]:  # Show first 3 errors
                print(f"  Task {failure.task_id}: {type(failure.error).__name__}")


def demo_performance_monitoring() -> None:
    """Demonstrate performance monitoring and statistics."""
    print("\n=== Performance Monitoring Demo ===")

    def cpu_bound_task(n: int) -> int:
        """CPU-bound task for performance testing."""
        result = 0
        for i in range(n * 1000):
            result += i * i
        return result

    with TypedThreadPoolExecutor(max_workers=4, name="PerfMonitor") as executor:
        # Submit multiple CPU-bound tasks
        task_ids = []
        for i in range(8):
            task_id = executor.submit_task(cpu_bound_task, 1000 + i * 100)
            task_ids.append(task_id)

        print("Submitted 8 CPU-bound tasks")

        # Monitor progress
        completed = 0
        while completed < len(task_ids):
            stats = executor.get_stats()
            print(f"Active tasks: {stats['active_tasks']}, "
                  f"Completed: {completed}/{len(task_ids)}")

            # Get completed results
            for task_id in task_ids[:]:  # Copy list to modify during iteration
                try:
                    result = executor.get_task_result(task_id, timeout=0.1)
                    completed += 1
                    task_ids.remove(task_id)
                    print(f"Task {result.task_id} completed in {result.duration:.2f}s")
                except Exception:
                    pass  # Task not ready yet

            time.sleep(0.5)

        print("All tasks completed")


def run_all_demos() -> None:
    """Run all executor demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running TypedThreadPoolExecutor Demonstrations")
    print("=" * 50)

    try:
        demo_basic_task_submission()
        demo_batch_processing()
        demo_timeout_and_cancellation()
        demo_error_handling()
        demo_performance_monitoring()

        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run demonstrations when executed directly."""
    run_all_demos()

