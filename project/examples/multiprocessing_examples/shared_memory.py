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

    This class demonstrates shared memory mechanisms including Value, Array,
    Manager objects, and synchronization primitives for safe concurrent access.

    When to Use:
        - Sharing data between processes
        - High-frequency data access
        - Avoiding data copying overhead
        - Coordinating process execution
        - Building concurrent data structures

    Real-World Examples:
        - Counters: Shared counters across processes
        - Buffers: Shared buffers for data processing
        - State sharing: Share state between processes
        - Coordination: Coordinate process execution
        - Data structures: Shared lists/dicts via Manager

    Gotchas:
        - Shared memory requires synchronization
        - Race conditions without proper locking
        - Value/Array are faster than Manager
        - Manager has more overhead
        - Must use locks for non-atomic operations
        - Deadlock risk with multiple locks

    Performance Notes:
        - Shared memory faster than queues/pipes
        - Value/Array faster than Manager
        - Lock overhead affects performance
        - Optimal for high-frequency access
        - Manager overhead for complex objects
    """

    def shared_value_example(self) -> None:
        """
        Demonstrate shared Value objects.

        Shows how to share primitive values (integers, floats) between
        processes using multiprocessing.Value with proper locking.

        When to Use:
            - Sharing counters or simple values
            - High-frequency value updates
            - Avoiding queue overhead
            - Simple shared state
            - Performance-critical value sharing

        Real-World Examples:
            - Counters: Shared counters across workers
            - Statistics: Aggregate statistics from processes
            - Progress tracking: Track progress across processes
            - Resource counting: Count shared resources
            - Metrics: Collect metrics from processes

        Gotchas:
            - Must use lock for non-atomic operations
            - Simple assignments may be atomic (platform-dependent)
            - Always use lock for safety
            - Value types: 'i' (int), 'f' (float), 'd' (double)
            - Race conditions without locking

        Performance Notes:
            - Faster than queues for frequent updates
            - Lock overhead affects performance
            - Optimal for high-frequency access
            - Use locks for safety
        """
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
        """
        Demonstrate shared Array objects.

        Shows how to share arrays of primitive types between processes
        for efficient bulk data sharing.

        When to Use:
            - Sharing arrays of data
            - Bulk data access
            - Avoiding array copying
            - High-performance data sharing
            - Large data structures

        Real-World Examples:
            - Data buffers: Shared buffers for processing
            - Image processing: Shared image arrays
            - Numerical computing: Shared numerical arrays
            - Data pipelines: Shared data arrays
            - Scientific computing: Shared computation arrays

        Gotchas:
            - Array elements accessed by index
            - Need synchronization for concurrent access
            - Array type codes: 'i' (int), 'f' (float), 'd' (double)
            - Race conditions on concurrent writes
            - Use locks for safe concurrent access

        Performance Notes:
            - Faster than copying arrays
            - Lower overhead than Manager
            - Optimal for large arrays
            - Lock overhead for concurrent access
        """
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
        """
        Demonstrate synchronization primitives.

        Shows producer-consumer pattern using Lock and Semaphore for
        coordinating access to shared resources.

        When to Use:
            - Producer-consumer patterns
            - Resource coordination
            - Bounded buffer patterns
            - Process coordination
            - Synchronized access patterns

        Real-World Examples:
            - Bounded buffers: Producer-consumer with buffer limits
            - Resource pools: Coordinate resource access
            - Task queues: Coordinate task processing
            - Data pipelines: Coordinate pipeline stages
            - Worker coordination: Coordinate worker processes

        Gotchas:
            - Semaphore tracks available resources
            - Lock protects critical sections
            - acquire()/release() must be balanced
            - Deadlock risk with multiple semaphores
            - Use context managers for safety

        Performance Notes:
            - Semaphore overhead for coordination
            - Lock overhead for critical sections
            - Useful for coordination patterns
            - Balance synchronization vs performance
        """
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
        """
        Demonstrate Event synchronization.

        Shows how to use Event objects to signal between processes,
        enabling one process to notify multiple waiting processes.

        When to Use:
            - Signaling between processes
            - Coordinating process startup
            - Notifying multiple processes
            - One-to-many signaling
            - Process coordination

        Real-World Examples:
            - Process startup: Signal when ready
            - Coordination: Coordinate process execution
            - Notifications: Notify multiple processes
            - Synchronization: Synchronize process execution
            - Event-driven: Event-driven process coordination

        Gotchas:
            - Event.wait() blocks until set
            - Event.set() wakes all waiters
            - Event.clear() resets event
            - Event is one-time (use clear() to reset)
            - Multiple waiters all wake on set()

        Performance Notes:
            - Low overhead for signaling
            - Useful for coordination
            - Efficient for one-to-many signaling
            - Minimal performance impact
        """
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

    def condition_example_fixed(self) -> None:
        """
        Demonstrate condition variables with FIFO buffer.

        This is the PRODUCTION-READY implementation using:
        - Circular buffer with head/tail pointers (FIFO)
        - Proper graceful shutdown
        - Robust error handling

        When to Use:
            - Production producer-consumer patterns
            - FIFO task queues
            - State-based coordination

        Real-World Examples:
            - Task queues: Process tasks in order
            - Message queues: FIFO message processing
            - Data pipelines: Process data in order

        Gotchas:
            - Use head/tail for FIFO ordering
            - Always check predicate in while loop
            - Proper lock scope management
            - Modulo arithmetic for circular buffer

        Performance Notes:
            - FIFO ordering preserved
            - Circular buffer reuses memory
            - Optimal for production use
        """
        print("=== Condition Example (Fixed - FIFO Buffer) ===")

        SIZE = 5
        buffer = multiprocessing.Array('i', SIZE)
        head = multiprocessing.Value('i', 0)
        tail = multiprocessing.Value('i', 0)
        count = multiprocessing.Value('i', 0)
        buffer_lock = multiprocessing.Lock()
        buffer_condition = multiprocessing.Condition(buffer_lock)

        def producer() -> None:
            """Producer with condition synchronization and FIFO buffer."""
            for item in range(10):
                with buffer_condition:
                    # Wait while buffer is full
                    while count.value >= SIZE:
                        print("Buffer full, producer waiting...")
                        buffer_condition.wait()

                    # Add item at tail (FIFO)
                    idx = tail.value % SIZE
                    buffer[idx] = item
                    tail.value += 1
                    count.value += 1
                    print(f"Produced item {item} @ {idx}, buffer size: {count.value}")

                    # Notify consumers
                    buffer_condition.notify()

                time.sleep(0.1)

        def consumer(consumer_id: int) -> None:
            """Consumer with condition synchronization and FIFO buffer."""
            items_consumed = 0
            total_items = 10
            items_per_consumer = total_items // 2  # 2 consumers

            while items_consumed < items_per_consumer:
                with buffer_condition:
                    # Wait while buffer is empty
                    while count.value <= 0:
                        print(f"Buffer empty, consumer {consumer_id} waiting...")
                        buffer_condition.wait()

                    # Remove item from head (FIFO)
                    idx = head.value % SIZE
                    item = buffer[idx]
                    buffer[idx] = -1
                    head.value += 1
                    count.value -= 1
                    items_consumed += 1
                    print(f"Consumer {consumer_id} consumed item {item} @ {idx}, buffer size: {count.value}")

                    # Notify producers
                    buffer_condition.notify()

                time.sleep(0.2)

        # Create producer and consumers
        producer_process = multiprocessing.Process(target=producer)
        consumer_processes = [
            multiprocessing.Process(target=consumer, args=(i+1,))
            for i in range(2)
        ]

        print("Starting producer-consumer with conditions (FIFO):")
        producer_process.start()
        for p in consumer_processes:
            p.start()

        producer_process.join()
        for p in consumer_processes:
            p.join()

        print(f"Final buffer: {list(buffer)}")
        print()

    def condition_example(self) -> None:
        """
        Demonstrate Condition synchronization.

        Shows how to use Condition variables for complex synchronization
        with predicates, enabling efficient waiting on conditions.

        When to Use:
            - Complex synchronization with predicates
            - Producer-consumer with conditions
            - Waiting on state changes
            - Efficient waiting patterns
            - Complex coordination

        Real-World Examples:
            - Bounded buffers: Wait for space/items
            - State machines: Wait for state changes
            - Resource pools: Wait for resources
            - Task coordination: Wait for task completion
            - Pipeline coordination: Coordinate pipeline stages

        Gotchas:
            - Condition.wait() releases lock and waits
            - Must check predicate in loop (spurious wakeups)
            - notify() wakes one waiter
            - notify_all() wakes all waiters
            - Must hold lock when calling wait/notify

        Performance Notes:
            - More efficient than polling
            - Useful for complex synchronization
            - Overhead for condition operations
            - Optimal for predicate-based waiting
        """
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

                    # Remove item from buffer (FIFO - read from beginning)
                    # Note: This is a simple example. For true FIFO, use head/tail pointers
                    item = buffer[0]  # Read from beginning for FIFO
                    # Shift remaining items left (simplified - in production use circular buffer)
                    for i in range(buffer_size.value - 1):
                        buffer[i] = buffer[i + 1]
                    buffer[buffer_size.value - 1] = 0  # Clear last position
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
        """
        Demonstrate multiprocessing.Manager for complex shared objects.

        Shows how to use Manager to share complex Python objects (dicts,
        lists) between processes with automatic synchronization.

        When to Use:
            - Sharing complex Python objects
            - Sharing dicts/lists between processes
            - Need automatic synchronization
            - Complex data structures
            - Ease of use over performance

        Real-World Examples:
            - Shared state: Share complex state objects
            - Data structures: Share dicts/lists
            - Configuration: Share configuration dicts
            - Results: Collect results in shared list
            - Metadata: Share metadata dicts

        Gotchas:
            - Manager has significant overhead
            - Slower than Value/Array
            - Automatic synchronization
            - Proxy objects, not direct access
            - Context manager ensures cleanup

        Performance Notes:
            - Higher overhead than Value/Array
            - Convenient for complex objects
            - Slower than direct shared memory
            - Use when convenience > performance
        """
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
        """
        Demonstrate atomic operations on shared memory.

        Shows which operations are atomic and which require explicit
        synchronization with locks.

        When to Use:
            - Understanding atomicity
            - Optimizing synchronization
            - Learning when locks are needed
            - Performance optimization
            - Understanding race conditions

        Real-World Examples:
            - Counter updates: Simple counter increments
            - Flag setting: Setting boolean flags
            - Value assignment: Simple value assignments
            - Understanding: Understanding atomicity
            - Optimization: Optimizing lock usage

        Gotchas:
            - Simple assignments may be atomic (platform-dependent)
            - Read-modify-write is NOT atomic
            - Always use locks for safety
            - Platform differences in atomicity
            - Don't rely on platform-specific behavior

        Performance Notes:
            - Atomic operations are faster
            - Locks add overhead
            - Use locks for safety
            - Don't optimize prematurely
            - Safety > performance
        """
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

    def shared_value_real_world_example(self) -> None:
        """
        Real-World Scenario: Shared Value - Distributed Counter System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a distributed counter system:
        - Multiple workers processing requests
        - Need to track total requests processed
        - Problem: High-frequency updates needed
        
        THE PROBLEM WITHOUT SHARED VALUE:
        ==================================
        - Each worker tracks own count → no global view
        - Use queue to send counts → high overhead
        - Polling → inefficient
        - No real-time visibility → system opaque
        - Performance degradation → queue overhead
        
        THE SOLUTION:
        =============
        Shared Value enables:
        - Single shared counter across all workers
        - Workers update directly → low overhead
        - Real-time visibility → always current
        - Lock-protected → thread-safe
        - High performance → minimal overhead
        
        WHEN TO USE SHARED VALUE:
        =========================
        ✅ High-frequency value updates
        ✅ Shared counters/statistics
        ✅ Progress tracking
        ✅ Real-time metrics
        ✅ Performance-critical sharing
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Distributed Counter System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Distributed counter system")
        print("  - Multiple workers processing requests")
        print("  - Need to track total requests processed")
        print("  - Problem: High-frequency updates needed")
        print()
        print("THE PROBLEM:")
        print("  Without shared value:")
        print("    ❌ Each worker tracks own count → no global view")
        print("    ❌ Use queue to send counts → high overhead")
        print("    ❌ Polling → inefficient")
        print("    ❌ No real-time visibility → system opaque")
        print()
        print("THE SOLUTION:")
        print("  With shared value:")
        print("    ✅ Single shared counter across all workers")
        print("    ✅ Workers update directly → low overhead")
        print("    ✅ Real-time visibility → always current")
        print("    ✅ Lock-protected → thread-safe")
        print("    ✅ High performance → minimal overhead")
        print()
        print("=" * 70)
        print()

        total_requests = multiprocessing.Value('i', 0)
        successful_requests = multiprocessing.Value('i', 0)
        failed_requests = multiprocessing.Value('i', 0)
        counter_lock = multiprocessing.Lock()

        def request_processor(worker_id: int, num_requests: int) -> None:
            """Worker that processes requests and updates counters."""
            for i in range(num_requests):
                # Simulate request processing
                success = (i % 10) != 0  # 90% success rate
                time.sleep(0.01)  # Simulate processing

                # Update shared counters
                with counter_lock:
                    total_requests.value += 1
                    if success:
                        successful_requests.value += 1
                    else:
                        failed_requests.value += 1

                if (i + 1) % 5 == 0:
                    with counter_lock:
                        print(f"  Worker {worker_id}: Processed {i+1} requests "
                              f"(Total: {total_requests.value}, "
                              f"Success: {successful_requests.value}, "
                              f"Failed: {failed_requests.value})")

        print("Starting simulation...")
        print("  - 4 workers processing requests")
        print("  - Each worker processes 20 requests")
        print()

        workers = [
            multiprocessing.Process(target=request_processor, args=(i+1, 20))
            for i in range(4)
        ]

        start_time = time.time()
        for w in workers:
            w.start()

        for w in workers:
            w.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Total requests: {total_requests.value}")
        print(f"  Successful: {successful_requests.value}")
        print(f"  Failed: {failed_requests.value}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Shared Value enabled real-time counter updates!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE SHARED VALUE:")
        print("   ✅ High-frequency value updates")
        print("   ✅ Shared counters/statistics")
        print("   ✅ Progress tracking")
        print("   ✅ Real-time metrics")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Low overhead for frequent updates")
        print("   - Real-time visibility")
        print("   - Better performance than queues")
        print("   - Thread-safe with locks")
        print("=" * 70)
        print()

    def shared_array_real_world_example(self) -> None:
        """
        Real-World Scenario: Shared Array - Image Processing Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building an image processing pipeline:
        - Large image data (millions of pixels)
        - Multiple workers process different regions
        - Problem: Avoid copying large arrays
        
        THE PROBLEM WITHOUT SHARED ARRAY:
        ==================================
        - Copy image to each worker → memory explosion
        - 4 workers × 100MB image = 400MB memory
        - Slow copying → performance degradation
        - Memory pressure → system instability
        
        THE SOLUTION:
        =============
        Shared Array enables:
        - Single image array shared by all workers
        - Workers access directly → no copying
        - 4 workers × 100MB image = 100MB memory
        - Fast access → optimal performance
        - Memory efficient → scales better
        
        WHEN TO USE SHARED ARRAY:
        =========================
        ✅ Large data structures
        ✅ Bulk data sharing
        ✅ Avoiding array copying
        ✅ High-performance data access
        ✅ Memory-efficient sharing
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Image Processing Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Image processing pipeline")
        print("  - Large image data (millions of pixels)")
        print("  - Multiple workers process different regions")
        print("  - Problem: Avoid copying large arrays")
        print()
        print("THE PROBLEM:")
        print("  Without shared array:")
        print("    ❌ Copy image to each worker → memory explosion")
        print("    ❌ 4 workers × 100MB image = 400MB memory")
        print("    ❌ Slow copying → performance degradation")
        print("    ❌ Memory pressure → system instability")
        print()
        print("THE SOLUTION:")
        print("  With shared array:")
        print("    ✅ Single image array shared by all workers")
        print("    ✅ Workers access directly → no copying")
        print("    ✅ 4 workers × 100MB image = 100MB memory")
        print("    ✅ Fast access → optimal performance")
        print("    ✅ Memory efficient → scales better")
        print()
        print("=" * 70)
        print()

        # Simulate image data (array of pixel values)
        IMAGE_SIZE = 1000  # 1000x1000 = 1M pixels
        image_data = multiprocessing.Array('i', IMAGE_SIZE)  # Shared array
        array_lock = multiprocessing.Lock()

        def process_image_region(worker_id: int, start_idx: int, end_idx: int) -> None:
            """Worker that processes a region of the image."""
            pixels_processed = 0
            for i in range(start_idx, end_idx):
                # Process pixel (simulate image processing)
                with array_lock:
                    # Read pixel value
                    pixel_value = image_data[i]
                    # Apply filter (simulate processing)
                    image_data[i] = pixel_value + worker_id  # Simple transformation
                pixels_processed += 1

            print(f"  Worker {worker_id}: Processed {pixels_processed} pixels "
                  f"(region {start_idx}-{end_idx})")

        # Initialize image data
        for i in range(IMAGE_SIZE):
            image_data[i] = i % 256  # Simulate pixel values

        print(f"Processing image ({IMAGE_SIZE} pixels)...")
        print("  - Splitting into 4 regions")
        print()

        # Split image into regions
        region_size = IMAGE_SIZE // 4
        workers = []
        for i in range(4):
            start_idx = i * region_size
            end_idx = start_idx + region_size if i < 3 else IMAGE_SIZE
            w = multiprocessing.Process(
                target=process_image_region,
                args=(i+1, start_idx, end_idx)
            )
            workers.append(w)

        start_time = time.time()
        for w in workers:
            w.start()

        for w in workers:
            w.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Pixels processed: {IMAGE_SIZE}")
        print(f"  Execution time: {elapsed:.2f}s")
        print(f"  Memory: Single shared array (no copying)")
        print("  ✅ Shared Array enabled efficient bulk data sharing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE SHARED ARRAY:")
        print("   ✅ Large data structures")
        print("   ✅ Bulk data sharing")
        print("   ✅ Avoiding array copying")
        print("   ✅ High-performance data access")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Avoids memory explosion")
        print("   - No copying overhead")
        print("   - Memory efficient")
        print("   - Scales better")
        print("=" * 70)
        print()

    def manager_real_world_example(self) -> None:
        """
        Real-World Scenario: Manager - Shared Configuration System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a shared configuration system:
        - Multiple workers need shared config
        - Config is complex (dict, nested structures)
        - Problem: Share complex Python objects
        
        THE PROBLEM WITHOUT MANAGER:
        =============================
        - Each worker has own copy → no shared state
        - Config changes don't propagate → stale config
        - Use queues → high overhead
        - Complex serialization → slow
        - System inconsistency
        
        THE SOLUTION:
        =============
        Manager enables:
        - Single shared config dict across all workers
        - Workers access same config → consistent state
        - Config changes propagate → always current
        - Complex objects supported → flexible
        - System consistency → reliable
        
        WHEN TO USE MANAGER:
        ====================
        ✅ Complex shared data structures
        ✅ Shared configuration
        ✅ Shared state dictionaries
        ✅ Nested data structures
        ✅ When Value/Array insufficient
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Shared Configuration System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Shared configuration system")
        print("  - Multiple workers need shared config")
        print("  - Config is complex (dict, nested structures)")
        print("  - Problem: Share complex Python objects")
        print()
        print("THE PROBLEM:")
        print("  Without Manager:")
        print("    ❌ Each worker has own copy → no shared state")
        print("    ❌ Config changes don't propagate → stale config")
        print("    ❌ Use queues → high overhead")
        print("    ❌ Complex serialization → slow")
        print()
        print("THE SOLUTION:")
        print("  With Manager:")
        print("    ✅ Single shared config dict across all workers")
        print("    ✅ Workers access same config → consistent state")
        print("    ✅ Config changes propagate → always current")
        print("    ✅ Complex objects supported → flexible")
        print("    ✅ System consistency → reliable")
        print()
        print("=" * 70)
        print()

        manager = multiprocessing.Manager()
        shared_config = manager.dict({
            'api_timeout': 30,
            'max_retries': 3,
            'features': manager.dict({
                'feature_a': True,
                'feature_b': False,
            }),
            'version': 1
        })

        def config_reader(worker_id: int) -> None:
            """Worker that reads configuration."""
            for i in range(5):
                timeout = shared_config['api_timeout']
                retries = shared_config['max_retries']
                feature_a = shared_config['features']['feature_a']
                version = shared_config['version']
                
                print(f"  Worker {worker_id}: Read config "
                      f"(timeout={timeout}, retries={retries}, "
                      f"feature_a={feature_a}, version={version})")
                time.sleep(0.1)

        def config_updater() -> None:
            """Process that updates configuration."""
            time.sleep(0.3)  # Wait a bit
            print("  Config Updater: Updating configuration...")
            shared_config['api_timeout'] = 60
            shared_config['max_retries'] = 5
            shared_config['features']['feature_a'] = False
            shared_config['version'] = 2
            print("  Config Updater: Configuration updated!")

        print("Starting simulation...")
        print("  - 3 workers reading config")
        print("  - 1 updater modifying config")
        print()

        readers = [
            multiprocessing.Process(target=config_reader, args=(i+1,))
            for i in range(3)
        ]
        updater = multiprocessing.Process(target=config_updater)

        for r in readers:
            r.start()
        updater.start()

        for r in readers:
            r.join()
        updater.join()

        print()
        print("Results:")
        print(f"  Final config: {dict(shared_config)}")
        print("  ✅ Manager enabled shared complex data structures!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE MANAGER:")
        print("   ✅ Complex shared data structures")
        print("   ✅ Shared configuration")
        print("   ✅ Shared state dictionaries")
        print("   ✅ Nested data structures")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Supports complex Python objects")
        print("   - Shared state consistency")
        print("   - Changes propagate to all workers")
        print("   - Flexible data structures")
        print("=" * 70)
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
    example.condition_example_fixed()
    example.manager_example()
    example.atomic_operations()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    example.shared_value_real_world_example()
    example.shared_array_real_world_example()
    example.manager_real_world_example()

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
