"""
Shared memory and synchronization examples.

This module covers:
- Shared memory objects (Value, Array)
- Synchronization primitives (Lock, Event, Condition, Semaphore)
- Process-safe data structures
- Atomic operations
- Memory management in multiprocessing
"""

import multiprocessing
import os
import time
from typing import Any, List


class SharedMemoryExample:
    """
    Examples of shared memory and synchronization in multiprocessing.
    """

    def shared_value_example(self) -> None:
        """Demonstrate shared Value objects."""
        print("=== Shared Value Objects ===")

        def increment_counter(counter: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
            """Increment a shared counter."""
            for _ in range(1000):
                with lock:
                    counter.value += 1

        def decrement_counter(counter: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
            """Decrement a shared counter."""
            for _ in range(500):
                with lock:
                    counter.value -= 1

        # Create shared counter
        counter = multiprocessing.Value('i', 0)  # 'i' = integer, initial value 0
        lock = multiprocessing.Lock()

        # Create processes
        processes = [
            multiprocessing.Process(target=increment_counter, args=(counter, lock)),
            multiprocessing.Process(target=increment_counter, args=(counter, lock)),
            multiprocessing.Process(target=decrement_counter, args=(counter, lock))
        ]

        print(f"Initial counter value: {counter.value}")

        # Start processes
        for p in processes:
            p.start()

        # Wait for completion
        for p in processes:
            p.join()

        print(f"Final counter value: {counter.value}")
        print("Expected: 1000 + 1000 - 500 = 1500")
        print()

    def shared_array_example(self) -> None:
        """Demonstrate shared Array objects."""
        print("=== Shared Array Objects ===")

        def modify_array(shared_array: multiprocessing.Array, process_id: int) -> None:
            """Modify elements in shared array."""
            start_idx = process_id * 3
            for i in range(3):
                if start_idx + i < len(shared_array):
                    shared_array[start_idx + i] = process_id * 10 + i

        # Create shared array
        shared_array = multiprocessing.Array('i', 9)  # 9 integers, initialized to 0

        print(f"Initial array: {list(shared_array)}")

        # Create processes to modify different parts of the array
        processes = []
        for i in range(3):
            p = multiprocessing.Process(target=modify_array, args=(shared_array, i))
            processes.append(p)

        # Start processes
        for p in processes:
            p.start()

        # Wait for completion
        for p in processes:
            p.join()

        print(f"Final array: {list(shared_array)}")
        print()

    def synchronization_primitives(self) -> None:
        """Demonstrate synchronization primitives."""
        print("=== Synchronization Primitives ===")

        # Shared counter
        counter = multiprocessing.Value('i', 0)

        def producer(lock: multiprocessing.Lock, empty: multiprocessing.Semaphore,
                    full: multiprocessing.Semaphore) -> None:
            """Producer process."""
            for i in range(5):
                empty.acquire()  # Wait for empty slot

                with lock:
                    counter.value += 1
                    print(f"Produced: {counter.value}")

                full.release()  # Signal full slot
                time.sleep(0.1)

        def consumer(lock: multiprocessing.Lock, empty: multiprocessing.Semaphore,
                    full: multiprocessing.Semaphore) -> None:
            """Consumer process."""
            for i in range(5):
                full.acquire()  # Wait for full slot

                with lock:
                    print(f"Consumed: {counter.value}")
                    counter.value -= 1

                empty.release()  # Signal empty slot
                time.sleep(0.15)

        # Create synchronization objects
        lock = multiprocessing.Lock()
        empty = multiprocessing.Semaphore(1)  # Start with 1 empty slot
        full = multiprocessing.Semaphore(0)   # Start with 0 full slots

        # Create producer and consumer
        producer_process = multiprocessing.Process(target=producer, args=(lock, empty, full))
        consumer_process = multiprocessing.Process(target=consumer, args=(lock, empty, full))

        print("Starting producer-consumer with semaphores:")
        producer_process.start()
        consumer_process.start()

        producer_process.join()
        consumer_process.join()

        print(f"Final counter: {counter.value}")
        print()

    def event_example(self) -> None:
        """Demonstrate Event synchronization."""
        print("=== Event Synchronization ===")

        def waiter(event: multiprocessing.Event, process_id: int) -> None:
            """Process that waits for an event."""
            print(f"Process {process_id} waiting for event...")
            event.wait()  # Block until event is set
            print(f"Process {process_id} received event!")

        def setter(event: multiprocessing.Event) -> None:
            """Process that sets an event after a delay."""
            time.sleep(2)
            print("Setting event!")
            event.set()

        # Create event
        event = multiprocessing.Event()

        # Create waiter processes
        waiters = []
        for i in range(3):
            p = multiprocessing.Process(target=waiter, args=(event, i+1))
            waiters.append(p)

        # Create setter process
        setter_process = multiprocessing.Process(target=setter, args=(event,))

        # Start waiters first
        for p in waiters:
            p.start()

        # Start setter
        setter_process.start()

        # Wait for all
        for p in waiters:
            p.join()
        setter_process.join()

        print()

    def condition_example(self) -> None:
        """Demonstrate Condition synchronization."""
        print("=== Condition Synchronization ===")

        # Shared buffer
        buffer = multiprocessing.Array('i', 5)
        buffer_size = multiprocessing.Value('i', 0)
        buffer_lock = multiprocessing.Lock()
        buffer_condition = multiprocessing.Condition(buffer_lock)

        def producer() -> None:
            """Producer with condition synchronization."""
            for item in range(10):
                with buffer_condition:
                    # Wait while buffer is full
                    while buffer_size.value >= len(buffer):
                        print("Buffer full, producer waiting...")
                        buffer_condition.wait()

                    # Add item to buffer
                    buffer[buffer_size.value] = item
                    buffer_size.value += 1
                    print(f"Produced item {item}, buffer size: {buffer_size.value}")

                    # Notify consumers
                    buffer_condition.notify()

                time.sleep(0.1)

        def consumer(consumer_id: int) -> None:
            """Consumer with condition synchronization."""
            for _ in range(5):  # Consume 5 items each
                with buffer_condition:
                    # Wait while buffer is empty
                    while buffer_size.value <= 0:
                        print(f"Buffer empty, consumer {consumer_id} waiting...")
                        buffer_condition.wait()

                    # Remove item from buffer
                    item = buffer[buffer_size.value - 1]
                    buffer_size.value -= 1
                    print(f"Consumer {consumer_id} consumed item {item}, buffer size: {buffer_size.value}")

                    # Notify producers
                    buffer_condition.notify()

                time.sleep(0.2)

        # Create producer and consumers
        producer_process = multiprocessing.Process(target=producer)
        consumer_processes = [
            multiprocessing.Process(target=consumer, args=(i+1,))
            for i in range(2)
        ]

        print("Starting producer-consumer with conditions:")
        producer_process.start()
        for p in consumer_processes:
            p.start()

        producer_process.join()
        for p in consumer_processes:
            p.join()

        print()

    def manager_example(self) -> None:
        """Demonstrate multiprocessing.Manager for complex shared objects."""
        print("=== multiprocessing.Manager Example ===")

        def update_shared_dict(shared_dict: dict, process_id: int) -> None:
            """Update a shared dictionary."""
            for i in range(3):
                key = f"process_{process_id}_item_{i}"
                shared_dict[key] = process_id * 10 + i
                time.sleep(0.1)

        def update_shared_list(shared_list: list, process_id: int) -> None:
            """Update a shared list."""
            for i in range(3):
                shared_list.append(f"Process {process_id}: item {i}")
                time.sleep(0.1)

        # Create manager
        with multiprocessing.Manager() as manager:
            # Create shared objects
            shared_dict = manager.dict()
            shared_list = manager.list()

            # Create processes
            dict_processes = []
            list_processes = []

            for i in range(2):
                # Dict updater
                p1 = multiprocessing.Process(target=update_shared_dict, args=(shared_dict, i+1))
                dict_processes.append(p1)

                # List updater
                p2 = multiprocessing.Process(target=update_shared_list, args=(shared_list, i+1))
                list_processes.append(p2)

            # Start all processes
            for p in dict_processes + list_processes:
                p.start()

            # Wait for completion
            for p in dict_processes + list_processes:
                p.join()

            # Display results
            print(f"Shared dict: {dict(shared_dict)}")
            print(f"Shared list: {list(shared_list)}")

        print()

    def atomic_operations(self) -> None:
        """Demonstrate atomic operations on shared memory."""
        print("=== Atomic Operations ===")

        # Shared counters
        counter1 = multiprocessing.Value('i', 0)
        counter2 = multiprocessing.Value('i', 0)

        def atomic_increment(counter: multiprocessing.Value) -> None:
            """Perform atomic increment operations."""
            for _ in range(1000):
                # These operations are atomic for single values
                counter.value += 1

        def non_atomic_increment(counter: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
            """Perform potentially non-atomic operations (for demonstration)."""
            for _ in range(1000):
                # Simulate a non-atomic operation that needs locking
                with lock:
                    temp = counter.value
                    time.sleep(0.000001)  # Tiny delay to increase chance of race condition
                    counter.value = temp + 1

        # Test atomic operations
        processes = [
            multiprocessing.Process(target=atomic_increment, args=(counter1,)),
            multiprocessing.Process(target=atomic_increment, args=(counter1,))
        ]

        print("Testing atomic operations on single Value:")
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        print(f"Counter1 (atomic): {counter1.value} (expected: 2000)")

        # Test operations requiring synchronization
        lock = multiprocessing.Lock()
        processes = [
            multiprocessing.Process(target=non_atomic_increment, args=(counter2, lock)),
            multiprocessing.Process(target=non_atomic_increment, args=(counter2, lock))
        ]

        print("Testing operations with explicit synchronization:")
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        print(f"Counter2 (with lock): {counter2.value} (expected: 2000)")
        print()


def main() -> None:
    """Run all shared memory examples."""
    print("Multiprocessing Shared Memory Examples")
    print("=" * 42)

    example = SharedMemoryExample()

    example.shared_value_example()
    example.shared_array_example()
    example.synchronization_primitives()
    example.event_example()
    example.condition_example()
    example.manager_example()
    example.atomic_operations()

    print("All shared memory examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()

"""
🎯 Key Shared Memory Concepts Demonstrated:
Value Objects - Shared primitive types across processes
Array Objects - Shared arrays for bulk data sharing
Synchronization Primitives - Locks, Events, Conditions, Semaphores
Producer-Consumer - Classic synchronization pattern with semaphores
Event Coordination - Signaling between processes
Condition Variables - Complex synchronization with predicates
Manager Objects - Complex shared data structures (dict, list)
Atomic Operations - Single operations that don't need locking
🔑 Why Shared Memory Matters:
Performance - Faster than queues/pipes for frequent communication
Direct Access - Processes can read/write shared data directly
Synchronization - Primitives ensure thread/process safety
Memory Efficiency - Avoids copying large data structures
Complex Data - Manager allows sharing of complex Python objects
Coordination - Events and conditions for complex synchronization
⚠️ Important Considerations:
Race Conditions - Shared memory requires proper synchronization
Platform Limits - Some features may not work on all platforms
Memory Overhead - Manager objects have more overhead than raw types
Pickle Limitations - Functions must be importable by child processes
Deadlock Risk - Improper lock usage can cause deadlocks
This file shows the complete spectrum of shared memory techniques for building robust multiprocessing applications! 🚀💾🔒
"""
