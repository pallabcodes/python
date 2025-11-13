"""
Async synchronization primitives examples.

This module covers:
- asyncio.Lock for mutual exclusion
- asyncio.Semaphore for limiting concurrency
- asyncio.Event for coordination
- asyncio.Condition for complex synchronization
- Reader-writer patterns with asyncio primitives
- Deadlock prevention and best practices
"""

import asyncio
import random
import time
from typing import Dict, List, Optional


class AsyncPrimitivesExample:
    """
    Examples of asyncio synchronization primitives.

    This class demonstrates various synchronization primitives available in asyncio
    for coordinating concurrent async operations. Understanding these primitives is
    essential for building robust concurrent async applications.

    When to Use:
        - Coordinating access to shared resources in async code
        - Limiting concurrency to prevent resource exhaustion
        - Signaling between async tasks
        - Implementing producer-consumer patterns
        - Building complex synchronization patterns

    Real-World Examples:
        - Rate limiting: Use Semaphore to limit API request concurrency
        - Resource pools: Use Lock to protect database connection pools
        - Task coordination: Use Event to signal when initialization completes
        - Producer-consumer: Use Condition for bounded buffer coordination
        - Reader-writer: Use custom RWLock for read-heavy workloads

    Gotchas:
        - asyncio.Lock is not reentrant (unlike threading.Lock)
        - Semaphores don't prevent resource leaks; use context managers
        - Events are one-time; create new Event for repeated signaling
        - Condition variables require holding the associated lock
        - Deadlocks can occur with nested lock acquisition

    Performance Notes:
        - Locks have minimal overhead but can serialize execution
        - Semaphores are efficient for limiting concurrency
        - Events are very lightweight for signaling
        - Condition variables add overhead; use only when needed
    """

    async def lock_basic_example(self) -> None:
        """
        Demonstrate basic Lock usage for mutual exclusion.

        Locks ensure that only one coroutine can execute a critical section at a time.
        This is essential for protecting shared mutable state from race conditions.

        When to Use:
            - Protecting shared data structures from concurrent modification
            - Ensuring atomic operations on shared state
            - Implementing thread-safe counters or accumulators
            - Protecting resource pools (connections, file handles)
            - Coordinating access to external APIs or services

        Real-World Examples:
            - Database connection pool: Lock protects pool state
            - Cache updates: Lock ensures cache consistency
            - Counter increments: Lock prevents lost updates
            - Configuration updates: Lock prevents inconsistent state
            - File writing: Lock prevents interleaved writes

        Gotchas:
            - asyncio.Lock is NOT reentrant (unlike threading.Lock)
            - Locking too much code reduces concurrency
            - Deadlocks possible with multiple locks
            - Always use async with for automatic release
            - Don't hold locks during I/O operations

        Performance Notes:
            - Lock acquisition is very fast (~0.001ms)
            - Contention reduces parallelism; minimize lock scope
            - Fine-grained locking better than coarse-grained
        """
        print("=== Basic Lock Usage ===")

        shared_counter = {"value": 0}
        lock = asyncio.Lock()

        async def increment_counter(task_id: str) -> None:
            """Increment shared counter with lock protection."""
            async with lock:
                current = shared_counter["value"]
                print(f"Task {task_id}: acquired lock, current value: {current}")

                # Simulate some work
                await asyncio.sleep(0.1)

                shared_counter["value"] = current + 1
                print(f"Task {task_id}: released lock, new value: {shared_counter['value']}")

        # Run multiple tasks that need exclusive access
        tasks = [increment_counter(f"T{i+1}") for i in range(5)]
        await asyncio.gather(*tasks)

        print(f"Final counter value: {shared_counter['value']}")
        print()

    async def lock_reentrance_issue(self) -> None:
        """
        Demonstrate the issue with Lock reentrance.

        asyncio.Lock is NOT reentrant, meaning a coroutine cannot acquire the same
        lock twice, even if it already holds it. This is different from threading.Lock
        which is reentrant. Attempting to acquire a lock you already hold will deadlock.

        When to Use:
            - Understanding why nested lock acquisition fails
            - Learning to refactor code to avoid reentrance
            - Debugging deadlock issues in async code
            - Designing lock-free or single-acquisition patterns

        Real-World Examples:
            - Helper functions: Don't acquire locks in helpers if caller already has it
            - Recursive algorithms: Use lock-free data structures instead
            - Callback chains: Pass lock state explicitly rather than reacquiring
            - Middleware: Design to not require locks in nested calls

        Gotchas:
            - asyncio.Lock raises RuntimeError on reentrant acquisition
            - This is different from threading.Lock which allows reentrance
            - Solution: Refactor to avoid nested acquisition
            - Alternative: Use a reentrant lock implementation (not built-in)
            - Best practice: Design code to not need reentrant locks

        Performance Notes:
            - Reentrant locks add overhead; asyncio chose simplicity
            - Non-reentrant locks are faster and simpler
            - Design patterns can avoid need for reentrance
        """
        print("=== Lock Reentrance Issue ===")

        lock = asyncio.Lock()

        async def nested_function_call() -> None:
            """Inner function that also needs the lock."""
            async with lock:
                print("Inner function: acquired lock")
                await asyncio.sleep(0.1)
                print("Inner function: releasing lock")

        async def outer_function() -> None:
            """Outer function that calls nested function."""
            async with lock:
                print("Outer function: acquired lock")
                await asyncio.sleep(0.1)

                # This will raise RuntimeError because lock is not reentrant
                print("Outer function: calling nested function...")
                try:
                    await nested_function_call()
                except RuntimeError as e:
                    print(f"RuntimeError (expected): {e}")
                    print("asyncio.Lock is not reentrant - cannot acquire twice")

                print("Outer function: releasing lock")

        await outer_function()
        print()

    async def semaphore_example(self) -> None:
        """
        Demonstrate Semaphore for limiting concurrency.

        Semaphores allow a fixed number of coroutines to access a resource
        simultaneously. This is useful for rate limiting, connection pooling,
        and preventing resource exhaustion.

        When to Use:
            - Rate limiting API requests to external services
            - Limiting concurrent database connections
            - Controlling concurrent file operations
            - Throttling network requests
            - Managing resource pools (workers, connections)

        Real-World Examples:
            - API clients: Limit concurrent requests to respect rate limits
            - Web scraping: Control number of simultaneous page fetches
            - Database pools: Limit concurrent queries
            - File processing: Control concurrent file I/O
            - Worker pools: Limit number of active workers

        Gotchas:
            - Semaphore doesn't prevent resource leaks; always use context manager
            - Releasing more than acquired increases count (use BoundedSemaphore)
            - Count can go negative if not properly managed
            - Not suitable for mutual exclusion (use Lock instead)
            - Must release in finally block to prevent leaks

        Performance Notes:
            - Semaphore overhead is minimal
            - Very efficient for concurrency limiting
            - Better than creating fixed-size task pools
            - Allows dynamic adjustment of concurrency
        """
        print("=== Semaphore Example ===")

        # Semaphore allowing max 3 concurrent operations
        semaphore = asyncio.Semaphore(3)

        async def limited_concurrent_task(task_id: str) -> None:
            """Task that uses semaphore to limit concurrency."""
            async with semaphore:
                # Note: _value is private; in production, track separately if needed
                print(f"Task {task_id}: acquired semaphore")
                await asyncio.sleep(random.uniform(0.2, 0.8))
                print(f"Task {task_id}: releasing semaphore")

        print("Running 8 tasks with semaphore limit of 3:")
        tasks = [limited_concurrent_task(f"T{i+1}") for i in range(8)]
        await asyncio.gather(*tasks)

        print()

    async def bounded_semaphore_example(self) -> None:
        """
        Demonstrate BoundedSemaphore for preventing semaphore leaks.

        BoundedSemaphore prevents the semaphore count from exceeding its initial value,
        which helps detect bugs where release() is called more times than acquire().

        When to Use:
            - When you want to detect semaphore leaks
            - Debugging semaphore usage issues
            - Ensuring semaphore count never exceeds limit
            - Production code where leaks would be catastrophic
            - Resource pools where leaks cause problems

        Real-World Examples:
            - Connection pools: Detect if connections aren't properly released
            - Worker pools: Ensure workers are properly returned
            - Rate limiters: Detect if releases exceed acquisitions
            - Resource managers: Catch resource management bugs early

        Gotchas:
            - BoundedSemaphore raises ValueError if release() exceeds initial count
            - Use context manager (async with) to prevent leaks automatically
            - Not a substitute for proper resource management
            - Helps detect bugs but doesn't prevent them
            - Regular Semaphore allows count to grow unbounded

        Performance Notes:
            - Same performance as Semaphore
            - Adds validation overhead on release()
            - Use in production to catch bugs early
        """
        print("=== BoundedSemaphore Example ===")

        # BoundedSemaphore prevents semaphore value from exceeding initial value
        bounded_sem = asyncio.BoundedSemaphore(2)

        async def resource_user(task_id: str) -> None:
            """Task that uses a bounded resource."""
            try:
                async with bounded_sem:
                    print(f"Task {task_id}: using resource")
                    await asyncio.sleep(0.3)

                    # Simulate potential resource leak (don't release properly)
                    # In real code, this should be in a try/finally block
                    if random.random() > 0.7:  # 30% chance
                        print(f"Task {task_id}: Simulated error (but context manager releases)")
                        return  # Context manager ensures release happens

                print(f"Task {task_id}: properly released resource")
            except Exception as e:
                print(f"Task {task_id}: error - {e}")

        print("Testing bounded semaphore with potential leaks:")
        tasks = [resource_user(f"T{i+1}") for i in range(6)]
        await asyncio.gather(*tasks)

        # Note: _value is private; in production, track semaphore state separately
        # This is just for demonstration
        print("All tasks completed (semaphore properly managed via context manager)")
        print()

    async def event_coordination(self) -> None:
        """
        Demonstrate Event for task coordination and signaling.

        Events allow one coroutine to signal others that something has happened.
        Multiple coroutines can wait for the same event, and all will be notified
        when the event is set.

        When to Use:
            - Signaling that initialization is complete
            - Coordinating start of multiple workers
            - Notifying that a condition has been met
            - Implementing one-time barriers
            - Simple producer-consumer signaling

        Real-World Examples:
            - Service startup: Signal when service is ready to accept requests
            - Worker coordination: Start all workers simultaneously
            - Cache warming: Signal when cache is populated
            - Configuration loading: Signal when config is loaded
            - Graceful shutdown: Signal shutdown to all workers

        Gotchas:
            - Events are one-time; create new Event for repeated signaling
            - wait() doesn't consume the event; multiple waits see same state
            - clear() resets event; waiting coroutines continue waiting
            - Not suitable for counting or complex conditions (use Condition)
            - Race condition: check event.is_set() before wait() if needed

        Performance Notes:
            - Events are very lightweight
            - Efficient for one-to-many signaling
            - Minimal overhead for coordination
        """
        print("=== Event Coordination ===")

        start_event = asyncio.Event()
        all_started_event = asyncio.Event()

        async def worker(worker_id: str) -> None:
            """Worker that waits for start signal."""
            print(f"Worker {worker_id}: ready and waiting")

            # Signal that this worker is ready
            await start_event.wait()
            print(f"Worker {worker_id}: started working")

            await asyncio.sleep(random.uniform(0.5, 1.5))
            print(f"Worker {worker_id}: completed work")

        async def coordinator() -> None:
            """Coordinator that manages the workflow."""
            await asyncio.sleep(0.2)  # Let workers get ready

            print("Coordinator: All workers ready, starting...")
            start_event.set()  # Signal all workers to start

            await asyncio.sleep(2)  # Let workers complete

            print("Coordinator: Workflow completed")

        # Start coordinator and workers
        coordinator_task = asyncio.create_task(coordinator())
        worker_tasks = [asyncio.create_task(worker(f"W{i+1}")) for i in range(4)]

        await asyncio.gather(coordinator_task, *worker_tasks)

        print()

    async def event_barrier_simulation(self) -> None:
        """
        Demonstrate using Event as a barrier for synchronization.

        A barrier ensures that a group of coroutines wait for each other before
        proceeding. All coroutines must reach the barrier before any can continue.
        Python 3.11+ has asyncio.Barrier, but this shows how to implement it with Events.

        When to Use:
            - Synchronizing multiple workers at checkpoints
            - Ensuring all tasks complete a phase before next phase
            - Coordinating parallel algorithm phases
            - Implementing distributed consensus patterns
            - Synchronizing test execution

        Real-World Examples:
            - Parallel algorithms: Synchronize at algorithm phases
            - Data processing: Wait for all workers to finish a batch
            - Testing: Ensure all test setup completes before tests run
            - Distributed systems: Coordinate across nodes
            - Pipeline stages: Synchronize between pipeline stages

        Gotchas:
            - Barrier is one-time use; create new barrier for each synchronization
            - All parties must call wait() or barrier never releases
            - Deadlock if one party never reaches barrier
            - Use timeout to prevent indefinite waiting
            - Python 3.11+ has built-in asyncio.Barrier (use that if available)

        Performance Notes:
            - Barrier overhead is minimal
            - All parties wait for slowest one
            - Use timeout to prevent hanging on failures
        """
        print("=== Event as Barrier ===")

        # Note: asyncio.Barrier was added in Python 3.11
        # We'll simulate barrier behavior with Events

        class EventBarrier:
            """Simple barrier using Events."""
            def __init__(self, parties: int):
                self.parties = parties
                self.waiting = 0
                self.event = asyncio.Event()
                self.lock = asyncio.Lock()

            async def wait(self) -> None:
                """Wait at barrier."""
                async with self.lock:
                    self.waiting += 1
                    if self.waiting == self.parties:
                        # Last party arrived, release everyone
                        self.event.set()
                    else:
                        # Wait for others
                        pass

                await self.event.wait()

            def reset(self) -> None:
                """Reset barrier for reuse."""
                self.waiting = 0
                self.event.clear()

        async def barrier_task(task_id: str, barrier: EventBarrier) -> None:
            """Task that uses barrier synchronization."""
            print(f"Task {task_id}: approaching barrier")
            await asyncio.sleep(random.uniform(0.1, 0.5))  # Variable arrival time

            await barrier.wait()
            print(f"Task {task_id}: passed barrier, continuing")

            await asyncio.sleep(0.2)
            print(f"Task {task_id}: completed")

        # Create barrier for 3 tasks
        barrier = EventBarrier(3)

        print("Testing barrier synchronization:")
        tasks = [barrier_task(f"T{i+1}", barrier) for i in range(3)]
        await asyncio.gather(*tasks)

        print()

    async def condition_variables(self) -> None:
        """
        Demonstrate Condition variables for complex synchronization.

        Condition variables allow coroutines to wait for a condition to become true.
        They combine a lock with notification mechanisms, enabling efficient
        producer-consumer patterns and complex coordination.

        When to Use:
            - Producer-consumer patterns with bounded buffers
            - Waiting for complex conditions to become true
            - Coordinating multiple coroutines based on state
            - Implementing blocking queues
            - Synchronizing based on data state

        Real-World Examples:
            - Task queues: Wait for tasks to be available
            - Bounded buffers: Wait for space or data
            - Resource pools: Wait for resources to become available
            - State machines: Wait for state transitions
            - Data pipelines: Coordinate between pipeline stages

        Gotchas:
            - Must acquire the associated lock before waiting
            - Always use while loop to check condition (not if)
            - Spurious wakeups can occur; recheck condition
            - notify() wakes one waiter; notify_all() wakes all
            - Condition uses the lock's acquire/release semantics

        Performance Notes:
            - More overhead than Events or Locks
            - Efficient for complex coordination
            - Prefer Events for simple signaling
            - Use only when condition-based waiting is needed
        """
        print("=== Condition Variables ===")

        # Shared buffer
        buffer = []
        buffer_size = 5
        lock = asyncio.Lock()
        not_empty = asyncio.Condition(lock)
        not_full = asyncio.Condition(lock)

        async def producer(producer_id: str) -> None:
            """Producer using condition variables."""
            for i in range(4):
                item = f"{producer_id}_item_{i+1}"

                async with not_full:
                    # Wait while buffer is full
                    while len(buffer) >= buffer_size:
                        print(f"Producer {producer_id}: buffer full, waiting...")
                        await not_full.wait()

                    buffer.append(item)
                    print(f"Producer {producer_id}: added {item} (buffer: {len(buffer)}/{buffer_size})")

                # Notify consumers
                async with not_empty:
                    not_empty.notify()

                await asyncio.sleep(random.uniform(0.1, 0.3))

        async def consumer(consumer_id: str) -> None:
            """Consumer using condition variables."""
            for i in range(4):
                async with not_empty:
                    # Wait while buffer is empty
                    while len(buffer) == 0:
                        print(f"Consumer {consumer_id}: buffer empty, waiting...")
                        await not_empty.wait()

                    item = buffer.pop(0)
                    print(f"Consumer {consumer_id}: removed {item} (buffer: {len(buffer)}/{buffer_size})")

                # Notify producers
                async with not_full:
                    not_full.notify()

                await asyncio.sleep(random.uniform(0.2, 0.5))

        print("Starting producer-consumer with condition variables:")
        producers = [asyncio.create_task(producer(f"P{i+1}")) for i in range(2)]
        consumers = [asyncio.create_task(consumer(f"C{i+1}")) for i in range(2)]

        await asyncio.gather(*producers, *consumers)

        print(f"Final buffer state: {buffer}")
        print()

    async def reader_writer_lock(self) -> None:
        """
        Demonstrate reader-writer synchronization pattern.

        Reader-writer locks allow multiple readers or one writer, but not both.
        This optimizes for read-heavy workloads where reads can happen concurrently
        but writes need exclusive access.

        When to Use:
            - Read-heavy workloads with occasional writes
            - Caches that are frequently read but rarely updated
            - Configuration that is read often but updated rarely
            - Shared data structures with many readers, few writers
            - Optimizing for read performance

        Real-World Examples:
            - Configuration caches: Many reads, rare updates
            - Database caches: Frequent reads, occasional invalidation
            - Shared state: Many observers, few modifiers
            - Read replicas: Multiple readers, single writer
            - Document stores: Many readers, occasional updates

        Gotchas:
            - Writer starvation: Readers can starve writers
            - Complex implementation: Easy to introduce bugs
            - Not built into asyncio; must implement custom
            - Consider if simpler Lock is sufficient
            - Deadlock risk with nested acquisitions

        Performance Notes:
            - Allows concurrent reads (better than exclusive lock)
            - Writers still block all readers
            - Overhead higher than simple Lock
            - Only beneficial for read-heavy workloads
        """
        print("=== Reader-Writer Pattern ===")

        class AsyncRWLock:
            """Async reader-writer lock implementation."""
            def __init__(self):
                self.lock = asyncio.Lock()
                self.readers = 0
                self.writer_active = False
                self.read_waiters = asyncio.Condition(self.lock)
                self.write_waiters = asyncio.Condition(self.lock)

            async def acquire_read(self) -> None:
                """Acquire lock for reading."""
                async with self.lock:
                    while self.writer_active:
                        await self.read_waiters.wait()

                    self.readers += 1

            async def release_read(self) -> None:
                """Release read lock."""
                async with self.lock:
                    self.readers -= 1
                    if self.readers == 0:
                        self.write_waiters.notify()

            async def acquire_write(self) -> None:
                """Acquire lock for writing."""
                async with self.lock:
                    while self.readers > 0 or self.writer_active:
                        await self.write_waiters.wait()

                    self.writer_active = True

            async def release_write(self) -> None:
                """Release write lock."""
                async with self.lock:
                    self.writer_active = False
                    # Notify both readers and writers
                    self.read_waiters.notify_all()
                    self.write_waiters.notify()

        # Shared resource
        shared_data = {"value": 0}
        rw_lock = AsyncRWLock()

        async def reader(reader_id: str) -> None:
            """Reader task."""
            for i in range(3):
                await rw_lock.acquire_read()
                try:
                    value = shared_data["value"]
                    print(f"Reader {reader_id}: read value {value}")
                    await asyncio.sleep(0.1)
                finally:
                    await rw_lock.release_read()

                await asyncio.sleep(random.uniform(0.1, 0.3))

        async def writer(writer_id: str) -> None:
            """Writer task."""
            for i in range(2):
                await rw_lock.acquire_write()
                try:
                    shared_data["value"] += 1
                    print(f"Writer {writer_id}: wrote new value {shared_data['value']}")
                    await asyncio.sleep(0.2)
                finally:
                    await rw_lock.release_write()

                await asyncio.sleep(random.uniform(0.2, 0.5))

        print("Starting readers and writers:")
        readers = [asyncio.create_task(reader(f"R{i+1}")) for i in range(3)]
        writers = [asyncio.create_task(writer(f"W{i+1}")) for i in range(2)]

        await asyncio.gather(*readers, *writers)

        print(f"Final shared data: {shared_data}")
        print()

    async def deadlock_prevention(self) -> None:
        """
        Demonstrate deadlock prevention techniques.

        Deadlocks occur when coroutines wait for each other indefinitely. This method
        shows techniques to prevent deadlocks: consistent lock ordering and timeouts.

        When to Use:
            - Acquiring multiple locks in the same coroutine
            - Complex synchronization patterns
            - Preventing indefinite hangs
            - Building robust concurrent systems
            - Debugging lock-related issues

        Real-World Examples:
            - Database transactions: Consistent lock ordering prevents deadlocks
            - Resource allocation: Order resources consistently
            - Multi-step operations: Use timeouts to prevent hangs
            - Service coordination: Timeout prevents indefinite waiting
            - Error recovery: Timeouts enable graceful degradation

        Gotchas:
            - Always acquire locks in the same order
            - Use timeouts to prevent indefinite waiting
            - Release locks in reverse order of acquisition
            - Consider if you really need multiple locks
            - Deadlocks are hard to debug; prevent proactively

        Performance Notes:
            - Consistent ordering adds no overhead
            - Timeouts add minimal overhead
            - Better than deadlock detection (prevent vs detect)
            - Timeout values should be based on expected operation time
        """
        print("=== Deadlock Prevention ===")

        # Resources with proper ordering
        resource_a = asyncio.Lock()
        resource_b = asyncio.Lock()

        async def ordered_access_task(task_id: str) -> None:
            """Task that acquires resources in consistent order."""
            print(f"Task {task_id}: acquiring resources in order A->B")

            # Always acquire in the same order
            async with resource_a:
                print(f"Task {task_id}: acquired A")
                await asyncio.sleep(0.1)

                async with resource_b:
                    print(f"Task {task_id}: acquired B")
                    await asyncio.sleep(0.1)
                    print(f"Task {task_id}: releasing B")

                print(f"Task {task_id}: releasing A")

        async def timeout_protected_access(task_id: str) -> None:
            """Task with timeout protection to prevent hanging."""
            print(f"Task {task_id}: attempting resource access with timeout")

            try:
                # Use wait_for to prevent indefinite waiting
                await asyncio.wait_for(
                    self._acquire_nested_resources(task_id),
                    timeout=2.0
                )
                print(f"Task {task_id}: completed successfully")
            except asyncio.TimeoutError:
                print(f"Task {task_id}: timed out, avoiding deadlock")

        async def _acquire_nested_resources(task_id: str) -> None:
            """Helper method for nested resource acquisition."""
            async with resource_a:
                print(f"Task {task_id}: acquired A in nested call")
                await asyncio.sleep(0.2)

                async with resource_b:
                    print(f"Task {task_id}: acquired B in nested call")
                    await asyncio.sleep(0.1)

        print("Testing ordered resource acquisition:")
        tasks = [ordered_access_task(f"Ordered{i+1}") for i in range(3)]
        await asyncio.gather(*tasks)

        print("\nTesting timeout protection:")
        tasks = [timeout_protected_access(f"Timeout{i+1}") for i in range(2)]
        await asyncio.gather(*tasks)

        print()

    async def lock_performance_comparison(self) -> None:
        """Compare performance of different synchronization approaches."""
        print("=== Synchronization Performance Comparison ===")

        shared_counter = {"value": 0}
        iterations = 1000

        # Test 1: No synchronization (race condition)
        async def increment_no_sync(task_id: str) -> None:
            """Increment without synchronization."""
            for _ in range(iterations // 10):  # Reduce iterations for speed
                shared_counter["value"] += 1

        # Test 2: With Lock
        lock = asyncio.Lock()
        async def increment_with_lock(task_id: str) -> None:
            """Increment with lock."""
            for _ in range(iterations // 10):
                async with lock:
                    shared_counter["value"] += 1

        # Test 3: Coarse-grained locking
        async def increment_coarse_lock(task_id: str) -> None:
            """Increment with coarse-grained locking."""
            async with lock:
                for _ in range(iterations // 10):
                    shared_counter["value"] += 1

        # Helper function to run performance test
        async def run_performance_test(test_name: str, test_func) -> float:
            """Run a performance test and return execution time."""
            shared_counter["value"] = 0
            start_time = time.time()

            tasks = [test_func(f"T{i+1}") for i in range(5)]
            await asyncio.gather(*tasks)

            elapsed = time.time() - start_time
            print(f"{test_name}: {elapsed:.2f} seconds, final value: {shared_counter['value']}")
            return elapsed

        print("Comparing synchronization overhead:")

        # Note: These tests demonstrate concepts but actual performance
        # will depend on many factors including task switching overhead

        await run_performance_test("No synchronization", increment_no_sync)
        await run_performance_test("Fine-grained locking", increment_with_lock)
        await run_performance_test("Coarse-grained locking", increment_coarse_lock)

        print("Note: Fine-grained locking reduces contention but increases overhead")
        print("Coarse-grained locking reduces overhead but increases contention")
        print()

    async def synchronization_best_practices(self) -> None:
        """
        Demonstrate synchronization best practices.

        This method shows important best practices for using synchronization primitives
        effectively: minimal lock scope, exception safety, and avoiding locks during I/O.

        When to Use:
            - Writing production async code with synchronization
            - Optimizing lock performance
            - Preventing common synchronization bugs
            - Building maintainable concurrent code
            - Learning async synchronization patterns

        Real-World Examples:
            - Minimize scope: Update counters quickly, release lock
            - Exception safety: Always release locks in finally blocks
            - I/O separation: Use semaphores for I/O, locks for state
            - Resource management: Context managers ensure cleanup
            - Performance: Keep critical sections small

        Gotchas:
            - Holding locks during I/O blocks other coroutines
            - Exceptions can leave locks held; use context managers
            - Large critical sections reduce parallelism
            - Nested locks increase deadlock risk
            - Always use async with for automatic cleanup

        Performance Notes:
            - Smaller lock scope = better parallelism
            - Context managers add minimal overhead
            - Exception handling overhead is negligible
            - I/O outside locks improves throughput
        """
        print("=== Synchronization Best Practices ===")

        # Best Practice 1: Minimize lock scope
        lock = asyncio.Lock()
        shared_data = {"counter": 0, "data": []}

        async def minimal_lock_scope(task_id: str) -> None:
            """Demonstrate minimal lock scope."""
            # Do work outside the lock
            new_item = f"item_from_{task_id}"
            processed_data = new_item.upper()

            # Only lock when absolutely necessary
            async with lock:
                shared_data["counter"] += 1
                shared_data["data"].append(processed_data)

            print(f"Task {task_id}: added item (total: {len(shared_data['data'])})")

        # Best Practice 2: Handle exceptions properly
        async def exception_safe_operations(task_id: str) -> None:
            """Demonstrate exception-safe operations."""
            try:
                # Simulate operation that might fail
                if random.random() > 0.8:  # 20% chance
                    raise ValueError(f"Simulated failure in {task_id}")

                async with lock:
                    shared_data["counter"] += 1

                print(f"Task {task_id}: operation succeeded")

            except Exception as e:
                print(f"Task {task_id}: operation failed - {e}")
                # In real code, you might want to retry or log the error

        # Best Practice 3: Avoid holding locks during I/O
        semaphore = asyncio.Semaphore(2)  # Limit concurrent I/O

        async def io_with_limited_concurrency(task_id: str) -> None:
            """Demonstrate I/O with limited concurrency."""
            # Use semaphore for I/O operations
            async with semaphore:
                # Simulate I/O operation
                print(f"Task {task_id}: starting I/O operation")
                await asyncio.sleep(random.uniform(0.2, 0.8))  # Simulate I/O delay
                print(f"Task {task_id}: I/O operation completed")

                # Now update shared state with minimal lock time
                async with lock:
                    shared_data["counter"] += 1

        print("Demonstrating best practices:")

        # Test minimal lock scope
        print("\n1. Minimal lock scope:")
        tasks = [minimal_lock_scope(f"Min{i+1}") for i in range(3)]
        await asyncio.gather(*tasks)

        # Test exception safety
        print("\n2. Exception safety:")
        tasks = [exception_safe_operations(f"Safe{i+1}") for i in range(5)]
        await asyncio.gather(*tasks)

        # Test I/O concurrency control
        print("\n3. I/O concurrency control:")
        tasks = [io_with_limited_concurrency(f"IO{i+1}") for i in range(6)]
        await asyncio.gather(*tasks)

        print(f"\nFinal shared state: counter={shared_data['counter']}, items={len(shared_data['data'])}")
        print()

    async def semaphore_real_world_example(self) -> None:
        """
        Real-World Scenario: Semaphore - Rate-Limited API Client.

        REAL-WORLD SCENARIO:
        ====================
        You're building an API client:
        - Make requests to external API
        - API has rate limit (10 requests/second)
        - Problem: Need to respect rate limits
        
        THE PROBLEM WITHOUT SEMAPHORE:
        ==============================
        - Send all requests at once → rate limit exceeded
        - API rejects requests → errors
        - Need manual rate limiting → complex
        - Inefficient retry logic → waste
        - Poor user experience
        
        THE SOLUTION:
        =============
        Semaphore enables:
        - Limit concurrent requests to rate limit
        - Automatic throttling → respects limits
        - Simple to use → easy to implement
        - Prevents rate limit errors → reliable
        - Optimal request rate → efficient
        
        WHEN TO USE SEMAPHORE:
        ======================
        ✅ Rate-limited API clients
        ✅ Resource pool management
        ✅ Limiting concurrent operations
        ✅ Connection pooling
        ✅ Throttling requests
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Rate-Limited API Client")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - API client making requests")
        print("  - External API has rate limit (10 requests/second)")
        print("  - Problem: Need to respect rate limits")
        print()
        print("THE PROBLEM:")
        print("  Without semaphore:")
        print("    ❌ Send all requests at once → rate limit exceeded")
        print("    ❌ API rejects requests → errors")
        print("    ❌ Need manual rate limiting → complex")
        print("    ❌ Inefficient retry logic → waste")
        print()
        print("THE SOLUTION:")
        print("  With semaphore:")
        print("    ✅ Limit concurrent requests to rate limit")
        print("    ✅ Automatic throttling → respects limits")
        print("    ✅ Simple to use → easy to implement")
        print("    ✅ Prevents rate limit errors → reliable")
        print()
        print("=" * 70)
        print()

        # Rate limit: max 3 concurrent requests
        semaphore = asyncio.Semaphore(3)

        async def make_api_request(request_id: int) -> dict:
            """Simulate making an API request."""
            async with semaphore:  # Acquire semaphore (limit concurrency)
                print(f"  Request {request_id}: Making API call...")
                await asyncio.sleep(0.1)  # Simulate API call
                print(f"  Request {request_id}: API call completed")
                return {"request_id": request_id, "status": "success"}

        print("Making 10 API requests with rate limiting (max 3 concurrent)...")
        print()

        start_time = time.time()
        tasks = [make_api_request(i+1) for i in range(10)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        print()
        print("Results:")
        print(f"  Requests completed: {len(results)}")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Average rate: {len(results)/elapsed:.1f} requests/second")
        print("  ✅ Semaphore prevented rate limit violations!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE SEMAPHORE:")
        print("   ✅ Rate-limited API clients")
        print("   ✅ Resource pool management")
        print("   ✅ Limiting concurrent operations")
        print("   ✅ Connection pooling")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents rate limit violations")
        print("   - Automatic throttling")
        print("   - Simple to implement")
        print("   - Reliable API interactions")
        print("=" * 70)
        print()

    async def event_real_world_example(self) -> None:
        """
        Real-World Scenario: Event - Service Startup Coordination.

        REAL-WORLD SCENARIO:
        ====================
        You're building a microservice:
        - Multiple components need to initialize
        - Service ready only when all components ready
        - Problem: Coordinate startup across components
        
        THE PROBLEM WITHOUT EVENT:
        ===========================
        - Components start independently → race conditions
        - Service accepts requests before ready → errors
        - Polling for readiness → inefficient
        - No coordination → unreliable startup
        - System fragile → production issues
        
        THE SOLUTION:
        =============
        Event enables:
        - Components signal when ready
        - Service waits for all components → reliable
        - One-to-many signaling → efficient
        - Simple coordination → easy to implement
        - Guaranteed readiness → production-ready
        
        WHEN TO USE EVENT:
        ==================
        ✅ Service startup coordination
        ✅ One-to-many signaling
        ✅ Simple coordination needs
        ✅ Ready state notification
        ✅ Component initialization
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Service Startup Coordination")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Microservice with multiple components")
        print("  - Components need to initialize")
        print("  - Service ready only when all components ready")
        print("  - Problem: Coordinate startup across components")
        print()
        print("THE PROBLEM:")
        print("  Without event:")
        print("    ❌ Components start independently → race conditions")
        print("    ❌ Service accepts requests before ready → errors")
        print("    ❌ Polling for readiness → inefficient")
        print("    ❌ No coordination → unreliable startup")
        print()
        print("THE SOLUTION:")
        print("  With event:")
        print("    ✅ Components signal when ready")
        print("    ✅ Service waits for all components → reliable")
        print("    ✅ One-to-many signaling → efficient")
        print("    ✅ Simple coordination → easy to implement")
        print()
        print("=" * 70)
        print()

        ready_event = asyncio.Event()

        async def initialize_component(component_name: str, init_time: float) -> None:
            """Simulate component initialization."""
            print(f"  {component_name}: Initializing...")
            await asyncio.sleep(init_time)  # Simulate initialization
            print(f"  {component_name}: Ready!")
            ready_event.set()  # Signal readiness

        async def wait_for_service_ready() -> None:
            """Wait for service to be ready."""
            print("Waiting for all components to be ready...")
            await ready_event.wait()  # Wait for event
            print("✅ Service is ready to accept requests!")

        print("Starting service initialization...")
        print()

        # Initialize components concurrently
        components = [
            ("Database", 0.1),
            ("Cache", 0.15),
            ("API Gateway", 0.2),
        ]

        init_tasks = [
            initialize_component(name, time)
            for name, time in components
        ]

        # Wait for service ready (in parallel with initialization)
        await asyncio.gather(
            *init_tasks,
            wait_for_service_ready()
        )

        print()
        print("  ✅ Event coordinated service startup!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE EVENT:")
        print("   ✅ Service startup coordination")
        print("   ✅ One-to-many signaling")
        print("   ✅ Simple coordination needs")
        print("   ✅ Ready state notification")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Reliable startup coordination")
        print("   - One-to-many signaling")
        print("   - Simple to implement")
        print("   - Production-ready systems")
        print("=" * 70)
        print()


async def main() -> None:
    """Run all async primitives examples."""
    print("Asyncio Primitives Examples")
    print("=" * 28)

    example = AsyncPrimitivesExample()

    await example.lock_basic_example()
    await example.lock_reentrance_issue()
    await example.semaphore_example()
    await example.bounded_semaphore_example()
    await example.event_coordination()
    await example.event_barrier_simulation()
    await example.condition_variables()
    await example.reader_writer_lock()
    await example.deadlock_prevention()
    await example.lock_performance_comparison()
    await example.synchronization_best_practices()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    await example.semaphore_real_world_example()
    await example.event_real_world_example()

    print("All async primitives examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
