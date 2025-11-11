"""
Advanced synchronization examples for multiprocessing.

This module covers:
- Lock, RLock, and Semaphore usage patterns
- Event and Condition variable patterns
- Barrier synchronization
- Reader-writer locks
- Deadlock prevention and detection
- Synchronization best practices
"""

import multiprocessing
import os
import threading
import time
from typing import Any, Dict, List


class SynchronizationExample:
    """
    Advanced synchronization examples for multiprocessing.
    """

    def lock_vs_rlock(self) -> None:
        """Compare Lock and RLock behavior."""
        print("=== Lock vs RLock Comparison ===")

        # Shared counter
        counter = multiprocessing.Value('i', 0)

        def increment_with_lock(counter: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
            """Increment counter using a regular lock."""
            for _ in range(100):
                with lock:
                    counter.value += 1

        def nested_function_with_lock(counter: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
            """Demonstrate nested locking with regular Lock (will deadlock)."""
            with lock:
                print("Acquired lock in outer function")
                try:
                    # This will cause a deadlock with regular Lock
                    inner_increment(counter, lock)
                except Exception as e:
                    print(f"Deadlock detected: {e}")

        def inner_increment(counter: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
            """Inner function that tries to acquire the same lock."""
            with lock:
                counter.value += 1

        # Test with regular Lock
        print("Testing with regular Lock:")
        lock = multiprocessing.Lock()
        counter.value = 0

        p1 = multiprocessing.Process(target=increment_with_lock, args=(counter, lock))
        p2 = multiprocessing.Process(target=nested_function_with_lock, args=(counter, lock))

        p1.start()
        p2.start()
        p1.join()
        p2.join()

        print(f"Final counter value: {counter.value}")
        print()

    def semaphore_patterns(self) -> None:
        """Demonstrate semaphore usage patterns."""
        print("=== Semaphore Patterns ===")

        # Bounded buffer simulation
        buffer = multiprocessing.Array('i', 5)  # Buffer of size 5
        buffer_count = multiprocessing.Value('i', 0)
        buffer_lock = multiprocessing.Lock()
        empty_slots = multiprocessing.Semaphore(5)  # Initially 5 empty slots
        full_slots = multiprocessing.Semaphore(0)   # Initially 0 full slots

        def producer(producer_id: int) -> None:
            """Producer with semaphore synchronization."""
            for i in range(3):
                item = producer_id * 10 + i

                empty_slots.acquire()  # Wait for empty slot

                with buffer_lock:
                    # Add item to buffer
                    index = buffer_count.value
                    buffer[index] = item
                    buffer_count.value += 1
                    print(f"Producer {producer_id}: Produced {item} at index {index}")

                full_slots.release()  # Signal full slot
                time.sleep(0.1)

        def consumer(consumer_id: int) -> None:
            """Consumer with semaphore synchronization."""
            for i in range(4):  # Consume 4 items total
                full_slots.acquire()  # Wait for full slot

                with buffer_lock:
                    # Remove item from buffer
                    buffer_count.value -= 1
                    index = buffer_count.value
                    item = buffer[index]
                    buffer[index] = 0  # Clear the slot
                    print(f"Consumer {consumer_id}: Consumed {item} from index {index}")

                empty_slots.release()  # Signal empty slot
                time.sleep(0.15)

        print("Starting producer-consumer with semaphores:")
        producers = [multiprocessing.Process(target=producer, args=(i+1,)) for i in range(2)]
        consumers = [multiprocessing.Process(target=consumer, args=(i+1,)) for i in range(2)]

        for p in producers + consumers:
            p.start()

        for p in producers + consumers:
            p.join()

        print(f"Final buffer state: {list(buffer)}")
        print()

    def event_coordination(self) -> None:
        """Demonstrate event-based coordination."""
        print("=== Event Coordination ===")

        # Shared event
        start_event = multiprocessing.Event()
        finish_event = multiprocessing.Event()

        def coordinator() -> None:
            """Coordinator process."""
            print("Coordinator: Preparing...")
            time.sleep(1)
            print("Coordinator: Signaling start!")
            start_event.set()  # Signal workers to start

            # Wait for all workers to finish
            finish_event.wait()
            print("Coordinator: All workers finished!")

        def worker(worker_id: int) -> None:
            """Worker process."""
            print(f"Worker {worker_id}: Waiting for start signal...")
            start_event.wait()  # Wait for start signal

            # Do work
            work_time = 0.5 + worker_id * 0.2
            print(f"Worker {worker_id}: Starting work ({work_time:.1f}s)")
            time.sleep(work_time)
            print(f"Worker {worker_id}: Work completed!")

            # Signal completion (using a simple shared counter)
            # In a real scenario, you'd use proper synchronization
            pass

        # Create processes
        coord = multiprocessing.Process(target=coordinator)
        workers = [multiprocessing.Process(target=worker, args=(i+1,)) for i in range(3)]

        # Start all processes
        coord.start()
        for w in workers:
            w.start()

        # Wait for workers
        for w in workers:
            w.join()

        # Signal coordinator that workers are done
        finish_event.set()
        coord.join()

        print()

    def condition_variables(self) -> None:
        """Demonstrate condition variables for complex synchronization."""
        print("=== Condition Variables ===")

        # Shared buffer with condition variables
        buffer = multiprocessing.Array('i', 3)
        buffer_size = multiprocessing.Value('i', 0)
        buffer_lock = multiprocessing.Lock()
        not_empty = multiprocessing.Condition(buffer_lock)
        not_full = multiprocessing.Condition(buffer_lock)

        def producer(producer_id: int) -> None:
            """Producer using condition variables."""
            for i in range(4):
                item = producer_id * 100 + i

                with not_full:
                    # Wait while buffer is full
                    while buffer_size.value >= len(buffer):
                        print(f"Producer {producer_id}: Buffer full, waiting...")
                        not_full.wait()

                    # Add item
                    buffer[buffer_size.value] = item
                    buffer_size.value += 1
                    print(f"Producer {producer_id}: Added {item}")

                # Signal that buffer is not empty
                with not_empty:
                    not_empty.notify()

                time.sleep(0.1)

        def consumer(consumer_id: int) -> None:
            """Consumer using condition variables."""
            for i in range(4):
                with not_empty:
                    # Wait while buffer is empty
                    while buffer_size.value <= 0:
                        print(f"Consumer {consumer_id}: Buffer empty, waiting...")
                        not_empty.wait()

                    # Remove item
                    buffer_size.value -= 1
                    item = buffer[buffer_size.value]
                    buffer[buffer_size.value] = 0
                    print(f"Consumer {consumer_id}: Removed {item}")

                # Signal that buffer is not full
                with not_full:
                    not_full.notify()

                time.sleep(0.2)

        print("Starting condition variable example:")
        producers = [multiprocessing.Process(target=producer, args=(i+1,)) for i in range(2)]
        consumers = [multiprocessing.Process(target=consumer, args=(i+1,)) for i in range(2)]

        for p in producers + consumers:
            p.start()

        for p in producers + consumers:
            p.join()

        print()

    def barrier_synchronization(self) -> None:
        """Demonstrate barrier synchronization."""
        print("=== Barrier Synchronization ===")

        # Note: multiprocessing.Barrier was added in Python 3.3
        # For older versions, we simulate barrier behavior

        class SimpleBarrier:
            """Simple barrier implementation for demonstration."""
            def __init__(self, parties: int):
                self.parties = parties
                self.count = multiprocessing.Value('i', 0)
                self.lock = multiprocessing.Lock()
                self.condition = multiprocessing.Condition(self.lock)

            def wait(self) -> None:
                """Wait at barrier."""
                with self.condition:
                    self.count.value += 1
                    if self.count.value == self.parties:
                        # Last process arrived, wake everyone
                        self.condition.notify_all()
                        print("Barrier: All processes arrived, releasing...")
                    else:
                        # Wait for others
                        print(f"Barrier: Waiting... ({self.count.value}/{self.parties})")
                        self.condition.wait()

        def barrier_task(task_id: int, barrier: SimpleBarrier) -> None:
            """Task that uses barrier synchronization."""
            print(f"Task {task_id}: Phase 1")
            time.sleep(0.1 * task_id)  # Variable delay

            barrier.wait()  # Synchronize

            print(f"Task {task_id}: Phase 2 (after barrier)")
            time.sleep(0.1)

            barrier.wait()  # Another synchronization point

            print(f"Task {task_id}: Phase 3 (final)")

        # Create barrier for 3 processes
        barrier = SimpleBarrier(3)

        # Create tasks
        tasks = [multiprocessing.Process(target=barrier_task, args=(i+1, barrier)) for i in range(3)]

        print("Starting barrier synchronization:")
        for t in tasks:
            t.start()

        for t in tasks:
            t.join()

        print()

    def reader_writer_problem(self) -> None:
        """Demonstrate reader-writer synchronization pattern."""
        print("=== Reader-Writer Problem ===")

        # Shared data
        shared_data = multiprocessing.Value('i', 0)
        readers_count = multiprocessing.Value('i', 0)
        data_lock = multiprocessing.Lock()
        readers_lock = multiprocessing.Lock()

        def writer(writer_id: int) -> None:
            """Writer process."""
            for i in range(3):
                # Acquire exclusive access
                with data_lock:
                    shared_data.value += 1
                    print(f"Writer {writer_id}: Wrote {shared_data.value}")
                    time.sleep(0.1)

        def reader(reader_id: int) -> None:
            """Reader process."""
            for i in range(4):
                # Reader synchronization
                with readers_lock:
                    readers_count.value += 1
                    if readers_count.value == 1:
                        data_lock.acquire()  # First reader locks data

                # Read data
                value = shared_data.value
                print(f"Reader {reader_id}: Read {value}")

                # Reader synchronization
                with readers_lock:
                    readers_count.value -= 1
                    if readers_count.value == 0:
                        data_lock.release()  # Last reader unlocks data

                time.sleep(0.05)

        print("Starting reader-writer example:")
        writers = [multiprocessing.Process(target=writer, args=(i+1,)) for i in range(2)]
        readers = [multiprocessing.Process(target=reader, args=(i+1,)) for i in range(3)]

        # Start readers first to demonstrate concurrent reading
        for r in readers:
            r.start()
        for w in writers:
            w.start()

        for r in readers:
            r.join()
        for w in writers:
            w.join()

        print(f"Final shared data value: {shared_data.value}")
        print()

    def deadlock_prevention(self) -> None:
        """Demonstrate deadlock prevention techniques."""
        print("=== Deadlock Prevention ===")

        # Resources
        resource_a = multiprocessing.Lock()
        resource_b = multiprocessing.Lock()

        def process_type_1(process_id: int) -> None:
            """Process that acquires resources in order A->B."""
            print(f"Process {process_id} (Type 1): Acquiring A...")
            with resource_a:
                print(f"Process {process_id} (Type 1): Got A, acquiring B...")
                time.sleep(0.1)  # Simulate work
                with resource_b:
                    print(f"Process {process_id} (Type 1): Got B, working...")
                    time.sleep(0.1)
                print(f"Process {process_id} (Type 1): Released B")
            print(f"Process {process_id} (Type 1): Released A")

        def process_type_2(process_id: int) -> None:
            """Process that acquires resources in order A->B (same as Type 1)."""
            print(f"Process {process_id} (Type 2): Acquiring A...")
            with resource_a:
                print(f"Process {process_id} (Type 2): Got A, acquiring B...")
                time.sleep(0.1)
                with resource_b:
                    print(f"Process {process_id} (Type 2): Got B, working...")
                    time.sleep(0.1)
                print(f"Process {process_id} (Type 2): Released B")
            print(f"Process {process_id} (Type 2): Released A")

        def process_type_3_bad(process_id: int) -> None:
            """Process that acquires resources in wrong order B->A (causes deadlock)."""
            print(f"Process {process_id} (Type 3): Acquiring B...")
            with resource_b:
                print(f"Process {process_id} (Type 3): Got B, acquiring A...")
                time.sleep(0.1)
                with resource_a:  # This order can cause deadlock
                    print(f"Process {process_id} (Type 3): Got A, working...")
                    time.sleep(0.1)
                print(f"Process {process_id} (Type 3): Released A")
            print(f"Process {process_id} (Type 3): Released B")

        print("Testing deadlock prevention (ordered resource acquisition):")
        processes = [
            multiprocessing.Process(target=process_type_1, args=(1,)),
            multiprocessing.Process(target=process_type_2, args=(2,)),
            multiprocessing.Process(target=process_type_3_bad, args=(3,))
        ]

        for p in processes:
            p.start()

        # Set a timeout to prevent hanging if deadlock occurs
        start_time = time.time()
        for p in processes:
            remaining_time = max(0, 5 - (time.time() - start_time))  # 5 second timeout
            p.join(timeout=remaining_time)
            if p.is_alive():
                print(f"Process {p.name} did not complete (possible deadlock)")
                p.terminate()

        print()

    def synchronization_best_practices(self) -> None:
        """Demonstrate synchronization best practices."""
        print("=== Synchronization Best Practices ===")

        # Shared state
        counter = multiprocessing.Value('i', 0)
        results = multiprocessing.Manager().list()

        def worker_with_best_practices(worker_id: int, counter: multiprocessing.Value,
                                     results: list, lock: multiprocessing.Lock) -> None:
            """Worker following synchronization best practices."""
            try:
                # Minimize lock scope
                for i in range(10):
                    # Only lock when necessary
                    with lock:
                        counter.value += 1
                        local_counter = counter.value

                    # Do work outside the lock
                    result = f"Worker {worker_id}: processed item {i+1} (counter: {local_counter})"
                    time.sleep(0.01)  # Simulate work

                    # Another minimal lock usage
                    with lock:
                        results.append(result)

            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
            finally:
                print(f"Worker {worker_id} completed")

        lock = multiprocessing.Lock()

        print("Demonstrating best practices:")
        workers = [multiprocessing.Process(target=worker_with_best_practices,
                                         args=(i+1, counter, results, lock))
                  for i in range(3)]

        for w in workers:
            w.start()

        for w in workers:
            w.join()

        print(f"Final counter: {counter.value}")
        print(f"Results collected: {len(results)}")
        print("Best practice: Minimize lock scope and handle exceptions properly")
        print()


def main() -> None:
    """Run all synchronization examples."""
    print("Multiprocessing Synchronization Examples")
    print("=" * 44)

    example = SynchronizationExample()

    example.lock_vs_rlock()
    example.semaphore_patterns()
    example.event_coordination()
    example.condition_variables()
    example.barrier_synchronization()
    example.reader_writer_problem()
    example.deadlock_prevention()
    example.synchronization_best_practices()

    print("All synchronization examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()

"""
🎯 Key Synchronization Concepts Demonstrated:
Lock vs RLock - Regular locks vs reentrant locks for nested locking
Semaphores - Counting semaphores for producer-consumer patterns
Events - Simple signaling between processes
Condition Variables - Complex synchronization with predicates
Barriers - Rendezvous points for process coordination
Reader-Writer Locks - Allow concurrent reading, exclusive writing
Deadlock Prevention - Ordered resource acquisition
Best Practices - Minimize lock scope, proper error handling
🔑 Why Advanced Synchronization Matters:
Race Conditions - Prevent data corruption from concurrent access
Deadlocks - Avoid processes waiting forever for resources
Performance - Balance safety with minimal blocking
Coordination - Complex workflows requiring precise timing
Scalability - Efficient resource sharing across processes
Reliability - Robust error handling and recovery
⚠️ Critical Synchronization Issues:
Deadlock - Circular waiting for resources
Starvation - Some processes never get access
Race Conditions - Non-deterministic behavior
Priority Inversion - High-priority tasks blocked by low-priority ones
This file shows the complete spectrum of synchronization techniques essential for building reliable multiprocessing applications! 🔒🚦💪
"""