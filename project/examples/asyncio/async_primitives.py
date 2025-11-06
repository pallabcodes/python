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
    """

    async def lock_basic_example(self) -> None:
        """Demonstrate basic Lock usage."""
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
        """Demonstrate the issue with Lock reentrance."""
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

                # This would cause a deadlock with Lock
                print("Outer function: calling nested function...")
                try:
                    await nested_function_call()
                except Exception as e:
                    print(f"Deadlock detected: {e}")

                print("Outer function: releasing lock")

        await outer_function()
        print()

    async def semaphore_example(self) -> None:
        """Demonstrate Semaphore for limiting concurrency."""
        print("=== Semaphore Example ===")

        # Semaphore allowing max 3 concurrent operations
        semaphore = asyncio.Semaphore(3)

        async def limited_concurrent_task(task_id: str) -> None:
            """Task that uses semaphore to limit concurrency."""
            async with semaphore:
                print(f"Task {task_id}: acquired semaphore (available: {semaphore._value})")
                await asyncio.sleep(random.uniform(0.2, 0.8))
                print(f"Task {task_id}: releasing semaphore")

        print("Running 8 tasks with semaphore limit of 3:")
        tasks = [limited_concurrent_task(f"T{i+1}") for i in range(8)]
        await asyncio.gather(*tasks)

        print()

    async def bounded_semaphore_example(self) -> None:
        """Demonstrate BoundedSemaphore."""
        print("=== BoundedSemaphore Example ===")

        # BoundedSemaphore prevents semaphore value from exceeding initial value
        bounded_sem = asyncio.BoundedSemaphore(2)

        async def resource_user(task_id: str) -> None:
            """Task that uses a bounded resource."""
            try:
                async with bounded_sem:
                    print(f"Task {task_id}: using resource (available: {bounded_sem._value})")
                    await asyncio.sleep(0.3)

                    # Simulate potential resource leak (don't release properly)
                    # In real code, this should be in a try/finally block
                    if random.random() > 0.7:  # 30% chance
                        print(f"Task {task_id}: Oops, resource leak!")
                        return  # Don't release the semaphore

                print(f"Task {task_id}: properly released resource")
            except Exception as e:
                print(f"Task {task_id}: error - {e}")

        print("Testing bounded semaphore with potential leaks:")
        tasks = [resource_user(f"T{i+1}") for i in range(6)]
        await asyncio.gather(*tasks)

        print(f"Final semaphore value: {bounded_sem._value}")
        print()

    async def event_coordination(self) -> None:
        """Demonstrate Event for task coordination."""
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
        """Demonstrate using Event as a barrier."""
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
        """Demonstrate Condition variables."""
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
        """Demonstrate reader-writer synchronization pattern."""
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
        """Demonstrate deadlock prevention techniques."""
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
            print(".2f")
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
        """Demonstrate synchronization best practices."""
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

    print("All async primitives examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
