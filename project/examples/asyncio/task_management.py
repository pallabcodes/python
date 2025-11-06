"""
Task management examples demonstrating asyncio task lifecycle.

This module covers:
- Creating and managing tasks
- Task cancellation and cleanup
- Task groups and structured concurrency
- Task introspection and monitoring
- Exception handling in tasks
- Task scheduling and prioritization
"""

import asyncio
import random
import time
from typing import Any, List, Optional


class TaskManagementExample:
    """
    Examples of asyncio task management.
    """

    async def basic_task_creation(self) -> None:
        """Demonstrate basic task creation and management."""
        print("=== Basic Task Creation ===")

        async def worker(task_id: str, duration: float) -> str:
            """Worker coroutine."""
            print(f"Task {task_id}: starting (duration: {duration}s)")
            await asyncio.sleep(duration)
            result = f"Task {task_id} completed"
            print(f"Task {task_id}: finished")
            return result

        # Create tasks
        task1 = asyncio.create_task(worker("A", 0.5))
        task2 = asyncio.create_task(worker("B", 0.3))
        task3 = asyncio.create_task(worker("C", 0.8))

        print("Tasks created and started")

        # Wait for tasks to complete
        results = await asyncio.gather(task1, task2, task3)

        print("All tasks completed:")
        for result in results:
            print(f"  {result}")

        print()

    async def task_introspection(self) -> None:
        """Demonstrate task introspection capabilities."""
        print("=== Task Introspection ===")

        async def monitored_task(task_id: str) -> None:
            """Task that reports its own information."""
            task = asyncio.current_task()
            print(f"Task {task_id}:")
            print(f"  Task object: {task}")
            print(f"  Task name: {task.get_name()}")
            print(f"  Is done: {task.done()}")
            print(f"  Is cancelled: {task.cancelled()}")

            await asyncio.sleep(0.5)

            # Check status again
            print(f"Task {task_id} after sleep:")
            print(f"  Is done: {task.done()}")
            print(f"  Loop: {task.get_loop()}")

        # Set task names
        task1 = asyncio.create_task(monitored_task("Monitor-1"))
        task1.set_name("Named-Monitor-Task-1")

        task2 = asyncio.create_task(monitored_task("Monitor-2"))
        task2.set_name("Named-Monitor-Task-2")

        await asyncio.gather(task1, task2)

        # Introspect completed tasks
        print("After completion:")
        print(f"  Task1 done: {task1.done()}")
        print(f"  Task2 done: {task2.done()}")
        print(f"  Task1 result: {task1.result()}")
        print(f"  Task2 result: {task2.result()}")

        print()

    async def task_cancellation(self) -> None:
        """Demonstrate task cancellation."""
        print("=== Task Cancellation ===")

        async def cancellable_task(task_id: str) -> str:
            """Task that can be cancelled."""
            try:
                print(f"Task {task_id}: starting work")
                for i in range(10):
                    print(f"Task {task_id}: step {i+1}/10")
                    await asyncio.sleep(0.2)

                    # Check for cancellation
                    if asyncio.current_task().cancelled():
                        print(f"Task {task_id}: detected cancellation")
                        break

                return f"Task {task_id} completed normally"

            except asyncio.CancelledError:
                print(f"Task {task_id}: CancelledError caught, cleaning up...")
                # Perform cleanup here
                await asyncio.sleep(0.1)  # Simulate cleanup
                print(f"Task {task_id}: cleanup completed")
                raise  # Re-raise the CancelledError

        # Create and start tasks
        task1 = asyncio.create_task(cancellable_task("Cancel-Me"))
        task2 = asyncio.create_task(cancellable_task("Complete-Normally"))

        # Let them run for a bit
        await asyncio.sleep(0.8)

        # Cancel the first task
        print("Cancelling task1...")
        task1.cancel()

        # Wait for both tasks
        try:
            result1 = await task1
            print(f"Task1 result: {result1}")
        except asyncio.CancelledError:
            print("Task1 was cancelled (expected)")

        result2 = await task2
        print(f"Task2 result: {result2}")

        print()

    async def timeout_with_cancellation(self) -> None:
        """Demonstrate timeout handling with cancellation."""
        print("=== Timeout with Cancellation ===")

        async def long_running_task(task_id: str, duration: float) -> str:
            """Task that takes a long time."""
            print(f"Task {task_id}: will run for {duration}s")
            await asyncio.sleep(duration)
            return f"Task {task_id} completed after {duration}s"

        # Test timeout with cancellation
        print("Testing timeout (2s) with 3s task:")
        try:
            result = await asyncio.wait_for(
                long_running_task("Timeout-Test", 3.0),
                timeout=2.0
            )
            print(f"Unexpected success: {result}")
        except asyncio.TimeoutError:
            print("Task timed out and was cancelled")

        # Test successful completion within timeout
        print("\nTesting successful completion within timeout:")
        try:
            result = await asyncio.wait_for(
                long_running_task("Success-Test", 1.0),
                timeout=2.0
            )
            print(f"Success: {result}")
        except asyncio.TimeoutError:
            print("Unexpected timeout")

        print()

    async def task_groups_structured_concurrency(self) -> None:
        """Demonstrate task groups and structured concurrency."""
        print("=== Task Groups (Structured Concurrency) ===")

        async def worker_in_group(group_name: str, task_id: str) -> str:
            """Worker that belongs to a task group."""
            print(f"Group {group_name} - Task {task_id}: starting")
            await asyncio.sleep(random.uniform(0.3, 0.8))
            result = f"Group {group_name} - Task {task_id} result"
            print(f"Group {group_name} - Task {task_id}: completed")
            return result

        async def run_task_group(group_name: str, num_tasks: int) -> List[str]:
            """Run a group of related tasks."""
            print(f"Starting task group '{group_name}' with {num_tasks} tasks")

            # Create task group (using asyncio.gather for structured concurrency)
            tasks = [
                worker_in_group(group_name, f"T{i+1}")
                for i in range(num_tasks)
            ]

            try:
                results = await asyncio.gather(*tasks)
                print(f"Task group '{group_name}' completed successfully")
                return results
            except Exception as e:
                print(f"Task group '{group_name}' failed: {e}")
                raise

        # Run multiple task groups
        group1 = asyncio.create_task(run_task_group("Group-A", 3))
        group2 = asyncio.create_task(run_task_group("Group-B", 2))
        group3 = asyncio.create_task(run_task_group("Group-C", 4))

        # Wait for all groups
        group_results = await asyncio.gather(group1, group2, group3, return_exceptions=True)

        print("All task groups completed:")
        for i, result in enumerate(group_results):
            if isinstance(result, Exception):
                print(f"  Group {chr(65+i)}: Failed - {result}")
            else:
                print(f"  Group {chr(65+i)}: {len(result)} tasks completed")

        print()

    async def exception_handling_in_tasks(self) -> None:
        """Demonstrate exception handling in task management."""
        print("=== Exception Handling in Tasks ===")

        async def task_that_may_fail(task_id: str, should_fail: bool) -> str:
            """Task that may raise an exception."""
            print(f"Task {task_id}: starting")
            await asyncio.sleep(0.2)

            if should_fail:
                raise ValueError(f"Task {task_id} failed as requested")

            return f"Task {task_id} succeeded"

        # Test exception handling with gather
        print("Testing exception handling with gather:")
        tasks = [
            task_that_may_fail("Success-1", False),
            task_that_may_fail("Fail-1", True),
            task_that_may_fail("Success-2", False),
            task_that_may_fail("Fail-2", True),
        ]

        # Method 1: Let exceptions propagate
        print("\nMethod 1: Let exceptions propagate")
        try:
            results = await asyncio.gather(*tasks)
            print(f"All succeeded: {results}")
        except Exception as e:
            print(f"Exception propagated: {e}")

        # Method 2: Handle exceptions individually
        print("\nMethod 2: Handle exceptions with return_exceptions")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i+1}: Failed - {result}")
            else:
                print(f"Task {i+1}: Succeeded - {result}")

        # Method 3: Handle exceptions in wait
        print("\nMethod 3: Handle exceptions with wait")
        tasks = [asyncio.create_task(task_that_may_fail(f"Wait-{i+1}", i % 2 == 1)) for i in range(4)]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        print("Completed tasks:")
        for task in done:
            try:
                result = task.result()
                print(f"  {task.get_name()}: {result}")
            except Exception as e:
                print(f"  {task.get_name()}: Failed - {e}")

        print()

    async def task_prioritization_simulation(self) -> None:
        """Demonstrate task prioritization simulation."""
        print("=== Task Prioritization Simulation ===")

        async def prioritized_task(task_id: str, priority: int) -> str:
            """Task with priority (higher number = higher priority)."""
            print(f"Task {task_id} (priority {priority}): waiting to start")

            # Simulate priority-based scheduling with different delays
            # Lower priority tasks wait longer
            delay = (10 - priority) * 0.1
            await asyncio.sleep(delay)

            print(f"Task {task_id} (priority {priority}): now executing")
            await asyncio.sleep(0.3)  # Actual work time
            result = f"Task {task_id} (priority {priority}) completed"
            print(f"Task {task_id} (priority {priority}): finished")
            return result

        # Create tasks with different priorities
        tasks = []
        priorities = [8, 3, 9, 1, 6, 2, 7]  # Various priorities

        for i, priority in enumerate(priorities):
            task = asyncio.create_task(prioritized_task(f"P{i+1}", priority))
            task.set_name(f"Priority-{priority}-Task-{i+1}")
            tasks.append(task)

        print("Starting tasks with priority-based scheduling simulation...")

        # Wait for all tasks (they'll complete in priority order due to delays)
        results = await asyncio.gather(*tasks)

        print("All tasks completed in priority order:")
        for result in results:
            print(f"  {result}")

        print()

    async def task_monitoring_and_metrics(self) -> None:
        """Demonstrate task monitoring and metrics collection."""
        print("=== Task Monitoring and Metrics ===")

        class TaskMonitor:
            """Monitor for tracking task metrics."""
            def __init__(self):
                self.task_metrics = {}

            def record_task_start(self, task_id: str) -> None:
                """Record task start."""
                self.task_metrics[task_id] = {
                    "start_time": time.time(),
                    "status": "running"
                }

            def record_task_completion(self, task_id: str, result: Any = None, exception: Exception = None) -> None:
                """Record task completion."""
                if task_id in self.task_metrics:
                    metrics = self.task_metrics[task_id]
                    metrics["end_time"] = time.time()
                    metrics["duration"] = metrics["end_time"] - metrics["start_time"]
                    metrics["status"] = "failed" if exception else "completed"
                    metrics["result"] = str(result) if result else None
                    metrics["exception"] = str(exception) if exception else None

        monitor = TaskMonitor()

        async def monitored_task(task_id: str, duration: float, should_fail: bool = False) -> str:
            """Task that reports to monitor."""
            monitor.record_task_start(task_id)

            try:
                print(f"Task {task_id}: executing for {duration}s")
                await asyncio.sleep(duration)

                if should_fail:
                    raise RuntimeError(f"Task {task_id} failed")

                result = f"Task {task_id} completed successfully"
                monitor.record_task_completion(task_id, result)
                return result

            except Exception as e:
                monitor.record_task_completion(task_id, exception=e)
                raise

        # Run monitored tasks
        tasks = [
            monitored_task("Fast-Success", 0.3, False),
            monitored_task("Slow-Success", 0.8, False),
            monitored_task("Fast-Fail", 0.2, True),
            monitored_task("Medium-Success", 0.5, False),
        ]

        # Use gather with exception handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Display results and metrics
        print("Task execution results:")
        for i, result in enumerate(results):
            task_id = f"Task-{i+1}"
            if isinstance(result, Exception):
                print(f"  {task_id}: ❌ Failed - {result}")
            else:
                print(f"  {task_id}: ✅ Succeeded - {result}")

        print("\nTask metrics:")
        for task_id, metrics in monitor.task_metrics.items():
            status = "✅" if metrics["status"] == "completed" else "❌"
            duration = metrics["duration"]
            print(".2f")

        # Calculate summary statistics
        completed_tasks = [m for m in monitor.task_metrics.values() if m["status"] == "completed"]
        failed_tasks = [m for m in monitor.task_metrics.values() if m["status"] == "failed"]

        if completed_tasks:
            avg_duration = sum(m["duration"] for m in completed_tasks) / len(completed_tasks)
            print(".2f")

        success_rate = len(completed_tasks) / len(monitor.task_metrics) * 100
        print(f"Success rate: {len(completed_tasks)}/{len(monitor.task_metrics)} ({success_rate:.1f}%)")
        print()

    async def task_cleanup_and_resources(self) -> None:
        """Demonstrate proper task cleanup and resource management."""
        print("=== Task Cleanup and Resource Management ===")

        class ResourceManager:
            """Mock resource manager for demonstration."""
            def __init__(self):
                self.allocated_resources = set()
                self.lock = asyncio.Lock()

            async def allocate_resource(self, resource_id: str) -> str:
                """Allocate a resource."""
                async with self.lock:
                    if resource_id in self.allocated_resources:
                        raise RuntimeError(f"Resource {resource_id} already allocated")
                    self.allocated_resources.add(resource_id)
                    print(f"🔓 Allocated resource: {resource_id}")
                    return resource_id

            async def release_resource(self, resource_id: str) -> None:
                """Release a resource."""
                async with self.lock:
                    if resource_id in self.allocated_resources:
                        self.allocated_resources.remove(resource_id)
                        print(f"🔒 Released resource: {resource_id}")

            def get_allocated_count(self) -> int:
                """Get count of allocated resources."""
                return len(self.allocated_resources)

        resource_manager = ResourceManager()

        async def resource_using_task(task_id: str) -> str:
            """Task that uses resources and ensures cleanup."""
            resource_id = None

            try:
                # Allocate resource
                resource_id = await resource_manager.allocate_resource(f"res_{task_id}")

                # Use resource
                await asyncio.sleep(random.uniform(0.2, 0.6))

                # Simulate potential failure
                if random.random() > 0.8:  # 20% chance
                    raise Exception(f"Task {task_id} encountered an error")

                result = f"Task {task_id} completed with resource {resource_id}"
                print(f"✅ {result}")
                return result

            except Exception as e:
                print(f"❌ Task {task_id} failed: {e}")
                raise
            finally:
                # Always cleanup resource
                if resource_id:
                    await resource_manager.release_resource(resource_id)

        # Run tasks with proper cleanup
        print("Running tasks with resource management:")
        tasks = [resource_using_task(f"T{i+1}") for i in range(5)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        print("\nTask results:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Task {i+1}: ❌ Failed")
            else:
                print(f"  Task {i+1}: ✅ Succeeded")

        print(f"\nFinal allocated resources: {resource_manager.get_allocated_count()}")
        print("All resources properly cleaned up!")

        print()


async def main() -> None:
    """Run all task management examples."""
    print("Asyncio Task Management Examples")
    print("=" * 33)

    example = TaskManagementExample()

    await example.basic_task_creation()
    await example.task_introspection()
    await example.task_cancellation()
    await example.timeout_with_cancellation()
    await example.task_groups_structured_concurrency()
    await example.exception_handling_in_tasks()
    await example.task_prioritization_simulation()
    await example.task_monitoring_and_metrics()
    await example.task_cleanup_and_resources()

    print("All task management examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
