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

    Tasks are the primary way to schedule coroutines for concurrent execution.
    This class demonstrates task lifecycle, cancellation, monitoring, and cleanup.

    When to Use:
        - Scheduling coroutines for concurrent execution
        - Managing long-running operations
        - Implementing cancellation and timeout patterns
        - Monitoring task execution and performance
        - Building structured concurrency patterns

    Real-World Examples:
        - Background workers: Long-running background tasks
        - Request handling: Handle multiple requests concurrently
        - Data processing: Process data in parallel
        - Scheduled jobs: Run periodic tasks
        - Resource management: Manage resources with tasks

    Gotchas:
        - Tasks start immediately when created
        - Cancellation raises CancelledError in the task
        - Tasks must handle CancelledError for cleanup
        - Exceptions in tasks are stored, not raised immediately
        - Always await tasks or they may not complete

    Performance Notes:
        - Task creation overhead is minimal
        - Cancellation is cooperative (tasks must check)
        - Too many tasks can exhaust resources
        - Use semaphores to limit concurrent tasks
        - Monitor task completion to prevent leaks
    """

    async def basic_task_creation(self) -> None:
        """
        Demonstrate basic task creation and management.

        Shows how to create tasks and wait for their completion.
        Tasks enable concurrent execution of coroutines.

        When to Use:
            - Running coroutines concurrently
            - Creating background tasks
            - Parallelizing independent operations
            - Learning task basics

        Real-World Examples:
            - API calls: Make multiple API calls concurrently
            - File processing: Process multiple files in parallel
            - Database queries: Execute multiple queries concurrently
            - Background jobs: Run background processing tasks

        Gotchas:
            - create_task() schedules coroutine immediately
            - Tasks run concurrently, not sequentially
            - Must await tasks to get results
            - gather() waits for all tasks to complete
            - Tasks are Futures; can check done() status

        Performance Notes:
            - Tasks enable true concurrency for I/O-bound work
            - Overhead minimal compared to I/O wait times
            - Can create thousands of tasks efficiently
            - Memory usage increases with number of tasks
        """
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
        """
        Demonstrate task introspection capabilities.

        Shows how to inspect task state, name, and status.
        Useful for debugging, monitoring, and logging.

        When to Use:
            - Debugging task execution issues
            - Monitoring task status
            - Logging task information
            - Building task management systems
            - Understanding task lifecycle

        Real-World Examples:
            - Debugging: Inspect why tasks aren't completing
            - Monitoring: Track task status in dashboards
            - Logging: Include task names in logs
            - Profiling: Measure task execution times
            - Error tracking: Identify which tasks failed

        Gotchas:
            - current_task() returns current task or None
            - Task names help with debugging
            - done() checks if task completed
            - cancelled() checks if task was cancelled
            - result() raises exception if task failed

        Performance Notes:
            - Introspection overhead is minimal
            - Useful for debugging and monitoring
            - Set meaningful task names for easier debugging
        """
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
        """
        Demonstrate task cancellation.

        Shows how to cancel tasks and handle cancellation gracefully.
        Cancellation is cooperative; tasks must check for cancellation.

        When to Use:
            - Stopping long-running operations
            - Implementing timeouts
            - Graceful shutdown of tasks
            - Cancelling operations on user request
            - Resource cleanup on cancellation

        Real-World Examples:
            - Request cancellation: Cancel HTTP requests
            - Timeout handling: Cancel operations that take too long
            - User cancellation: Cancel operations on user request
            - Shutdown: Cancel tasks during application shutdown
            - Resource limits: Cancel tasks when resources exhausted

        Gotchas:
            - cancel() marks task for cancellation
            - Cancellation raises CancelledError in task
            - Tasks must handle CancelledError for cleanup
            - Cleanup code should be in except/finally blocks
            - Re-raise CancelledError after cleanup

        Performance Notes:
            - Cancellation is cooperative (not preemptive)
            - Tasks should check cancellation periodically
            - Cleanup should be fast to avoid delays
            - Cancelled tasks free resources immediately
        """
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
        """
        Demonstrate timeout handling with cancellation.

        Shows how to use wait_for() to implement timeouts.
        Timeouts automatically cancel tasks that exceed the limit.

        When to Use:
            - Preventing operations from running too long
            - Implementing request timeouts
            - Protecting against hung operations
            - Ensuring responsiveness
            - Resource protection

        Real-World Examples:
            - API timeouts: Timeout HTTP requests
            - Database timeouts: Timeout slow queries
            - User operations: Timeout user-initiated operations
            - Background jobs: Timeout background processing
            - Health checks: Timeout health check operations

        Gotchas:
            - wait_for() cancels task on timeout
            - TimeoutError raised if timeout exceeded
            - Task receives CancelledError (not TimeoutError)
            - Task cleanup happens automatically
            - Use return_exceptions=True to handle timeouts gracefully

        Performance Notes:
            - Timeouts prevent resource exhaustion
            - Cancellation overhead is minimal
            - Set appropriate timeout values
            - Consider retry logic for transient failures
        """
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
        """
        Demonstrate task groups and structured concurrency.

        Shows how to organize related tasks into groups for better
        management and error handling. Python 3.11+ has TaskGroup.

        When to Use:
            - Organizing related tasks
            - Implementing structured concurrency
            - Group error handling
            - Coordinating task lifecycles
            - Building hierarchical task structures

        Real-World Examples:
            - Request processing: Group tasks for a single request
            - Batch operations: Group tasks for a batch
            - Pipeline stages: Group tasks for a pipeline stage
            - Service operations: Group tasks for a service call
            - Transaction operations: Group tasks for a transaction

        Gotchas:
            - Tasks in group should be related
            - Group failure can cancel all tasks
            - Use return_exceptions for partial success
            - Consider TaskGroup (Python 3.11+) for better structure
            - Group cleanup happens automatically

        Performance Notes:
            - Grouping helps with organization
            - Error handling is cleaner with groups
            - Groups can be nested for hierarchy
            - Consider cancellation propagation
        """
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
        """
        Demonstrate exception handling in task management.

        Shows different patterns for handling exceptions in concurrent tasks.
        Critical for building robust concurrent systems.

        When to Use:
            - Handling errors in concurrent operations
            - Implementing fault-tolerant systems
            - Graceful error recovery
            - Partial success patterns
            - Error aggregation

        Real-World Examples:
            - API clients: Some requests fail, others succeed
            - Data processing: Process valid data, skip invalid
            - Batch operations: Continue on partial failures
            - Distributed systems: Handle node failures
            - Microservices: Handle service failures gracefully

        Gotchas:
            - gather() without return_exceptions stops on first error
            - return_exceptions=True returns exceptions as results
            - Always check isinstance(result, Exception)
            - wait() returns sets of done/pending tasks
            - Exceptions stored in task, not raised immediately

        Performance Notes:
            - Exception handling overhead is minimal
            - return_exceptions allows partial success
            - Consider retry logic for transient failures
            - Log errors appropriately
        """
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
        """
        Demonstrate task monitoring and metrics collection.

        Shows how to track task execution metrics for monitoring,
        debugging, and performance analysis.

        When to Use:
            - Monitoring task performance
            - Debugging slow tasks
            - Performance analysis
            - Building dashboards
            - Alerting on failures

        Real-World Examples:
            - APM tools: Track task execution times
            - Performance monitoring: Monitor task throughput
            - Error tracking: Track task failure rates
            - Resource monitoring: Monitor task resource usage
            - SLA tracking: Track task completion rates

        Gotchas:
            - Metrics add overhead (minimal)
            - Store metrics efficiently
            - Consider sampling for high-volume tasks
            - Metrics should be non-blocking
            - Aggregate metrics for performance

        Performance Notes:
            - Metrics collection overhead is minimal
            - Useful for performance optimization
            - Consider async metrics storage
            - Aggregate metrics to reduce storage
        """
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
            print(f"  {status} {task_id}: {duration:.2f}s - {metrics['status']}")

        # Calculate summary statistics
        completed_tasks = [m for m in monitor.task_metrics.values() if m["status"] == "completed"]
        failed_tasks = [m for m in monitor.task_metrics.values() if m["status"] == "failed"]

        if completed_tasks:
            avg_duration = sum(m["duration"] for m in completed_tasks) / len(completed_tasks)
            print(f"\nAverage duration (completed): {avg_duration:.2f}s")

        success_rate = len(completed_tasks) / len(monitor.task_metrics) * 100
        print(f"Success rate: {len(completed_tasks)}/{len(monitor.task_metrics)} ({success_rate:.1f}%)")
        print()

    async def task_cleanup_and_resources(self) -> None:
        """
        Demonstrate proper task cleanup and resource management.

        Shows how to ensure resources are properly cleaned up even
        when tasks fail or are cancelled. Critical for preventing leaks.

        When to Use:
            - Managing resources in tasks
            - Ensuring cleanup on errors
            - Preventing resource leaks
            - Building robust resource management
            - Handling cancellation cleanup

        Real-World Examples:
            - Database connections: Close connections on task completion
            - File handles: Close files even on errors
            - Network connections: Disconnect on task completion
            - Locks: Release locks in finally blocks
            - Transactions: Rollback on errors

        Gotchas:
            - Always use try/finally for cleanup
            - Cleanup must be idempotent
            - Handle exceptions in cleanup code
            - Cleanup happens even on cancellation
            - Resource state should be checked before cleanup

        Performance Notes:
            - Proper cleanup prevents resource leaks
            - Cleanup overhead is minimal
            - Critical for long-running applications
            - Monitor resource usage to detect leaks
        """
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

    async def task_cancellation_real_world_example(self) -> None:
        """
        Real-World Scenario: Task Cancellation - Request Timeout Handler.

        REAL-WORLD SCENARIO:
        ====================
        You're building a request handler:
        - Process user requests
        - Some requests may hang or take too long
        - Problem: Need to cancel slow/hung requests
        
        THE PROBLEM WITHOUT CANCELLATION:
        ==================================
        - Hung request blocks forever → resource waste
        - Slow request delays other requests → poor UX
        - No timeout mechanism → system unresponsive
        - Can't abort operations → stuck system
        - Resource exhaustion → system failure
        
        THE SOLUTION:
        =============
        Task cancellation enables:
        - Cancel slow/hung requests → responsive system
        - Timeout protection → prevent hangs
        - Resource cleanup → efficient
        - Graceful cancellation → reliable
        - System responsiveness → good UX
        
        WHEN TO USE TASK CANCELLATION:
        ==============================
        ✅ Request timeout handling
        ✅ Long-running operation control
        ✅ Resource cleanup on timeout
        ✅ Preventing hung operations
        ✅ User-initiated cancellation
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Request Timeout Handler")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Request handler processing user requests")
        print("  - Some requests may hang or take too long")
        print("  - Problem: Need to cancel slow/hung requests")
        print()
        print("THE PROBLEM:")
        print("  Without cancellation:")
        print("    ❌ Hung request blocks forever → resource waste")
        print("    ❌ Slow request delays other requests → poor UX")
        print("    ❌ No timeout mechanism → system unresponsive")
        print("    ❌ Can't abort operations → stuck system")
        print()
        print("THE SOLUTION:")
        print("  With task cancellation:")
        print("    ✅ Cancel slow/hung requests → responsive system")
        print("    ✅ Timeout protection → prevent hangs")
        print("    ✅ Resource cleanup → efficient")
        print("    ✅ Graceful cancellation → reliable")
        print()
        print("=" * 70)
        print()

        async def process_request(request_id: str, duration: float) -> dict:
            """Simulate processing a request."""
            try:
                await asyncio.sleep(duration)
                return {"request_id": request_id, "status": "completed"}
            except asyncio.CancelledError:
                print(f"  Request {request_id}: Cancelled")
                raise

        print("Processing requests with timeout protection...")
        print()

        # Create tasks with different durations
        tasks = [
            asyncio.create_task(process_request(f"req_{i+1}", 0.1 + i * 0.1))
            for i in range(5)
        ]

        # Cancel tasks that take too long (simulate timeout)
        await asyncio.sleep(0.2)  # Wait a bit
        print("Checking for slow requests...")
        
        cancelled_count = 0
        for task in tasks:
            if not task.done():
                task.cancel()
                cancelled_count += 1

        # Wait for all tasks (cancelled or completed)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        completed = sum(1 for r in results if isinstance(r, dict))
        print()
        print("Results:")
        print(f"  Requests completed: {completed}")
        print(f"  Requests cancelled: {cancelled_count}")
        print("  ✅ Task cancellation enabled timeout protection!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE TASK CANCELLATION:")
        print("   ✅ Request timeout handling")
        print("   ✅ Long-running operation control")
        print("   ✅ Resource cleanup on timeout")
        print("   ✅ Preventing hung operations")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents hung operations")
        print("   - System responsiveness")
        print("   - Resource cleanup")
        print("   - Better user experience")
        print("=" * 70)
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

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    await example.task_cancellation_real_world_example()

    print("All task management examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
