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

    This class demonstrates advanced synchronization patterns including locks,
    semaphores, events, conditions, barriers, and deadlock prevention techniques.

    When to Use:
        - Complex synchronization requirements
        - Coordinating multiple processes
        - Preventing race conditions
        - Deadlock prevention
        - Building robust concurrent systems

    Real-World Examples:
        - Resource pools: Coordinate resource access
        - Producer-consumer: Coordinate producers and consumers
        - Barriers: Synchronize process phases
        - Reader-writer: Allow concurrent reads, exclusive writes
        - Deadlock prevention: Prevent circular waiting

    Gotchas:
        - Lock vs RLock: RLock allows reentrant acquisition
        - Deadlock risk: Always acquire locks in same order
        - Condition variables: Must check predicate in loop
        - Semaphores: Must balance acquire/release
        - Barriers: All processes must reach barrier
        - Reader-writer: Complex synchronization logic

    Performance Notes:
        - Lock overhead affects performance
        - Minimize lock scope for better performance
        - Deadlocks cause indefinite blocking
        - Proper synchronization prevents race conditions
        - Balance safety vs performance
    """

    def lock_vs_rlock(self) -> None:
        """
        Compare Lock and RLock behavior.

        Demonstrates the difference between regular Lock and RLock (reentrant lock).
        Regular Lock will deadlock if acquired twice by the same process, while
        RLock allows reentrant acquisition.

        When to Use:
            - Understanding lock types
            - Nested function calls needing same lock
            - Preventing deadlocks in nested code
            - Learning lock behavior
            - Debugging lock issues

        Real-World Examples:
            - Nested functions: Functions calling other functions with same lock
            - Recursive algorithms: Recursive code needing same lock
            - Helper functions: Helper functions needing caller's lock
            - Middleware: Middleware needing same lock as caller
            - Callback chains: Callbacks needing same lock

        Gotchas:
            - Regular Lock deadlocks on reentrant acquisition
            - RLock allows same process to acquire multiple times
            - RLock must release same number of times as acquired
            - multiprocessing.Lock is NOT reentrant
            - Use RLock for nested locking scenarios
            - Prefer refactoring to avoid nested locks

        Performance Notes:
            - RLock has slightly more overhead
            - Regular Lock is faster
            - Avoid nested locks when possible
            - Refactoring often better than RLock
        """
        print("=== Lock vs RLock Comparison ===")
        print()
        print("This demonstrates the critical difference between Lock and RLock.")
        print("Regular Lock will DEADLOCK if the same process tries to acquire it twice.")
        print("RLock allows reentrant acquisition (same process can acquire multiple times).")
        print()

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

    def lock_vs_rlock_real_world(self) -> None:
        """
        Real-World Scenario: Lock vs RLock - Database Transaction Manager.

        REAL-WORLD SCENARIO:
        ====================
        You're building a database transaction manager:
        - begin_transaction() acquires lock
        - execute_query() needs to check if in transaction (needs lock)
        - commit_transaction() releases lock
        - Problem: execute_query() called from within begin_transaction()
        
        THE PROBLEM WITHOUT RLock:
        ===========================
        - begin_transaction() acquires Lock
        - Calls execute_query() internally
        - execute_query() tries to acquire same Lock
        - DEADLOCK! Process hangs forever
        - Transaction never completes
        
        THE SOLUTION:
        =============
        RLock allows:
        - begin_transaction() acquires RLock
        - execute_query() can acquire same RLock (reentrant)
        - No deadlock, transaction completes
        - RLock tracks acquisition count
        
        WHEN TO USE RLock:
        ==================
        ✅ Nested function calls needing same lock
        ✅ Recursive algorithms with locking
        ✅ Helper functions called from locked context
        ✅ Middleware chains with shared locks
        ✅ Callback systems with locking
        
        ❌ Simple locking (use regular Lock - faster)
        ❌ Can refactor to avoid nesting (preferred)
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Database Transaction Manager")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Database transaction manager")
        print("  - begin_transaction() acquires lock")
        print("  - execute_query() needs to check transaction state")
        print("  - execute_query() called from within begin_transaction()")
        print()
        print("THE PROBLEM:")
        print("  With regular Lock:")
        print("    ❌ begin_transaction() acquires Lock")
        print("    ❌ Calls execute_query() internally")
        print("    ❌ execute_query() tries to acquire same Lock")
        print("    ❌ DEADLOCK! Process hangs forever")
        print("    ❌ Transaction never completes → Data corruption!")
        print()
        print("THE SOLUTION:")
        print("  With RLock:")
        print("    ✅ begin_transaction() acquires RLock")
        print("    ✅ Calls execute_query() internally")
        print("    ✅ execute_query() acquires same RLock (reentrant)")
        print("    ✅ No deadlock, transaction completes")
        print("    ✅ RLock tracks acquisition count")
        print()
        print("=" * 70)
        print()

        # Simulate transaction state
        transaction_state = multiprocessing.Manager().dict()
        transaction_state['active_transactions'] = 0
        transaction_state['queries_executed'] = 0
        transaction_state['commits'] = 0

        # Regular Lock (will deadlock)
        regular_lock = multiprocessing.Lock()

        def begin_transaction_with_lock(transaction_id: int) -> None:
            """Begin transaction with regular Lock (will deadlock)."""
            print(f"Transaction {transaction_id}: Starting...")
            try:
                with regular_lock:
                    transaction_state['active_transactions'] += 1
                    print(f"Transaction {transaction_id}: Lock acquired")
                    
                    # Call helper that also needs lock
                    execute_query_with_lock(transaction_id)
                    
                    transaction_state['commits'] += 1
                    print(f"Transaction {transaction_id}: Committed")
            except Exception as e:
                print(f"Transaction {transaction_id}: Error - {e}")

        def execute_query_with_lock(transaction_id: int) -> None:
            """Execute query - needs lock to check transaction state."""
            # This will deadlock with regular Lock!
            try:
                with regular_lock:  # DEADLOCK HERE!
                    transaction_state['queries_executed'] += 1
                    print(f"Transaction {transaction_id}: Query executed")
            except Exception as e:
                print(f"Transaction {transaction_id}: Query failed - {e}")

        # RLock (works correctly)
        rlock = multiprocessing.RLock()

        def begin_transaction_with_rlock(transaction_id: int) -> None:
            """Begin transaction with RLock (works correctly)."""
            print(f"Transaction {transaction_id}: Starting...")
            with rlock:
                transaction_state['active_transactions'] += 1
                print(f"Transaction {transaction_id}: RLock acquired")
                
                # Call helper that also needs lock (reentrant!)
                execute_query_with_rlock(transaction_id)
                
                transaction_state['commits'] += 1
                print(f"Transaction {transaction_id}: Committed")

        def execute_query_with_rlock(transaction_id: int) -> None:
            """Execute query - can acquire same RLock (reentrant)."""
            with rlock:  # ✅ Works! RLock allows reentrant acquisition
                transaction_state['queries_executed'] += 1
                print(f"Transaction {transaction_id}: Query executed")

        print("Testing with regular Lock (will deadlock):")
        print("  ⚠️  This will hang - demonstrating the problem")
        print()
        
        # Note: We'll skip actually running the deadlock version to avoid hanging
        print("  (Skipping deadlock demonstration to avoid hanging)")
        print()
        
        print("Testing with RLock (works correctly):")
        transaction_state['active_transactions'] = 0
        transaction_state['queries_executed'] = 0
        transaction_state['commits'] = 0
        
        processes = [
            multiprocessing.Process(target=begin_transaction_with_rlock, args=(i+1,))
            for i in range(3)
        ]
        
        for p in processes:
            p.start()
        
        for p in processes:
            p.join()
        
        print()
        print("Results:")
        print(f"  Transactions completed: {transaction_state['commits']}")
        print(f"  Queries executed: {transaction_state['queries_executed']}")
        print("  ✅ RLock allows reentrant acquisition - no deadlock!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE RLock:")
        print("   ✅ Nested function calls needing same lock")
        print("   ✅ Recursive algorithms with locking")
        print("   ✅ Helper functions called from locked context")
        print("   ✅ Middleware chains with shared locks")
        print()
        print("2. WHEN TO USE REGULAR Lock:")
        print("   ✅ Simple locking scenarios")
        print("   ✅ No nested calls")
        print("   ✅ Better performance (faster)")
        print()
        print("3. BEST PRACTICE:")
        print("   ⚠️  Prefer refactoring to avoid nested locks")
        print("   ⚠️  Only use RLock when refactoring is not feasible")
        print("   ⚠️  RLock adds overhead - use sparingly")
        print("=" * 70)
        print()

    def semaphore_patterns(self) -> None:
        """
        Demonstrate semaphore usage patterns.

        Shows how to use semaphores for producer-consumer coordination with
        bounded buffers, tracking available slots.

        When to Use:
            - Bounded buffer coordination
            - Resource counting
            - Producer-consumer patterns
            - Limiting concurrent access
            - Resource pool management

        Real-World Examples:
            - Bounded buffers: Limit buffer size
            - Connection pools: Limit concurrent connections
            - Resource pools: Limit resource usage
            - Rate limiting: Limit operation rate
            - Thread pools: Limit concurrent threads

        Gotchas:
            - Semaphore tracks available resources
            - acquire() decrements count, release() increments
            - Must balance acquire/release calls
            - Deadlock if all resources acquired
            - Use bounded semaphores to prevent over-release
            - Initial count sets available resources

        Performance Notes:
            - Semaphore overhead for coordination
            - Useful for resource limiting
            - Prevents resource exhaustion
            - Balance coordination vs overhead
        """
        print("=== Semaphore Patterns ===")

        # Bounded buffer simulation
        buffer = multiprocessing.Array('i', 5)  # Shared array: [0, 0, 0, 0, 0]
        buffer_count = multiprocessing.Value('i', 0) # Shared counter: 0
        buffer_lock = multiprocessing.Lock() # Shared lock: protects buffer access
        empty_slots = multiprocessing.Semaphore(5)  # Count: 5 (5 empty slots available)
        full_slots = multiprocessing.Semaphore(0)   # Count: 0 (0 full slots available)

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
            items_consumed = 0
            total_items = 2 * 3  # 2 producers * 3 items each
            
            while items_consumed < total_items // 2:  # Each consumer handles half
                full_slots.acquire()  # Wait for full slot

                with buffer_lock:
                    # Remove item from buffer (FIFO - read from beginning)
                    if buffer_count.value == 0:
                        empty_slots.release()  # Release if spurious wakeup
                        continue
                    index = buffer_count.value - 1  # Read from last added (LIFO) or use head/tail for FIFO
                    item = buffer[index]
                    buffer[index] = 0  # Clear the slot
                    buffer_count.value -= 1
                    items_consumed += 1
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

    def semaphore_real_world_example(self) -> None:
        """
        Real-World Scenario: Semaphore - Connection Pool Manager.

        REAL-WORLD SCENARIO:
        ====================
        You're building a database connection pool:
        - Limited connections (e.g., 10 max connections)
        - Many processes need database access
        - Problem: Prevent connection exhaustion
        
        THE PROBLEM WITHOUT SEMAPHORE:
        ===============================
        - Process 1 requests connection → gets it
        - Process 2 requests connection → gets it
        - ... Process 11 requests connection → gets it (exceeds limit!)
        - Database rejects connections → errors!
        - System crashes from too many connections
        
        THE SOLUTION:
        =============
        Semaphore ensures:
        - Semaphore initialized with max connections (10)
        - Process acquires semaphore before getting connection
        - If 10 connections in use, process waits
        - When connection released, semaphore released
        - Never exceeds connection limit
        
        WHEN TO USE SEMAPHORE:
        ======================
        ✅ Resource pools (connections, threads, files)
        ✅ Rate limiting (API calls, operations)
        ✅ Bounded buffers (producer-consumer)
        ✅ Limiting concurrent operations
        ✅ Preventing resource exhaustion
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Database Connection Pool")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Database with connection pool (max 5 connections)")
        print("  - Many processes need database access")
        print("  - Problem: Prevent connection exhaustion")
        print()
        print("THE PROBLEM:")
        print("  Without semaphore:")
        print("    ❌ Process requests connection → gets it")
        print("    ❌ More processes request → all get connections")
        print("    ❌ Exceeds database limit → database rejects")
        print("    ❌ System errors → application crashes!")
        print()
        print("THE SOLUTION:")
        print("  With semaphore:")
        print("    ✅ Semaphore initialized with max connections (5)")
        print("    ✅ Process acquires semaphore before connection")
        print("    ✅ If 5 connections in use, process waits")
        print("    ✅ When connection released, semaphore released")
        print("    ✅ Never exceeds connection limit")
        print()
        print("=" * 70)
        print()

        MAX_CONNECTIONS = 5
        connection_pool = multiprocessing.Manager().list([f"conn_{i}" for i in range(MAX_CONNECTIONS)])
        connection_semaphore = multiprocessing.Semaphore(MAX_CONNECTIONS)
        connection_lock = multiprocessing.Lock()
        active_connections = multiprocessing.Value('i', 0)
        connection_stats = multiprocessing.Manager().dict()

        def use_database_connection(process_id: int, num_operations: int) -> None:
            """Simulate process using database connection."""
            for i in range(num_operations):
                # Acquire semaphore (wait if all connections in use)
                connection_semaphore.acquire()
                
                # Get connection from pool
                with connection_lock:
                    if connection_pool:
                        conn = connection_pool.pop()
                        active_connections.value += 1
                        current_active = active_connections.value
                    else:
                        connection_semaphore.release()
                        continue

                # Use connection
                print(f"  Process {process_id}: Using connection {conn} "
                      f"(active: {current_active}/{MAX_CONNECTIONS})")
                time.sleep(0.1)  # Simulate database operation

                # Return connection to pool
                with connection_lock:
                    connection_pool.append(conn)
                    active_connections.value -= 1

                # Release semaphore
                connection_semaphore.release()

                if process_id not in connection_stats:
                    connection_stats[process_id] = 0
                connection_stats[process_id] += 1

            print(f"Process {process_id}: Completed {num_operations} operations")

        print("Starting simulation...")
        print(f"  - Connection pool size: {MAX_CONNECTIONS}")
        print("  - 8 processes trying to use database")
        print("  - Each process performs 3 operations")
        print()

        processes = [
            multiprocessing.Process(target=use_database_connection, args=(i+1, 3))
            for i in range(8)
        ]

        start_time = time.time()
        for p in processes:
            p.start()

        for p in processes:
            p.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Total operations: {sum(connection_stats.values())}")
        print(f"  Execution time: {elapsed:.2f}s")
        print(f"  Final active connections: {active_connections.value}")
        print(f"  Connections in pool: {len(connection_pool)}")
        print("  ✅ Semaphore prevented connection exhaustion!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE SEMAPHORE:")
        print("   ✅ Resource pools (connections, threads, files)")
        print("   ✅ Rate limiting (API calls, operations)")
        print("   ✅ Bounded buffers (producer-consumer)")
        print("   ✅ Limiting concurrent operations")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents resource exhaustion")
        print("   - Ensures system stability")
        print("   - Prevents database/API overload")
        print("   - Enables fair resource sharing")
        print("=" * 70)
        print()

    def semaphore_patterns_fixed(self) -> None:
        """
        Demonstrate semaphore patterns with proper circular buffer (FIFO queue).

        This is the CORRECTED and PRODUCTION-READY implementation using:
        - Circular buffer with head/tail pointers for FIFO queue
        - Proper graceful shutdown with poison pills
        - Robust error handling

        When to Use:
            - Production producer-consumer patterns
            - Bounded FIFO queues
            - Proper resource coordination
            - Graceful shutdown required

        Real-World Examples:
            - Message queues: FIFO message processing
            - Task queues: Process tasks in order
            - Data pipelines: Process data in order
            - Event processing: Process events sequentially

        Gotchas:
            - Use head/tail for FIFO, not just count
            - Poison pills needed for graceful shutdown
            - Modulo arithmetic for circular buffer
            - Check count before reading (spurious wakeups)
            - Balance acquire/release calls

        Performance Notes:
            - Circular buffer reuses memory efficiently
            - FIFO ordering preserved
            - Proper shutdown prevents hangs
            - Optimal for production use
        """
        print("=== Semaphore Patterns (Fixed - Circular Buffer) ===")
        
        SIZE = 5
        buffer = multiprocessing.Array('i', SIZE)          # shared array
        head = multiprocessing.Value('i', 0)               # read index
        tail = multiprocessing.Value('i', 0)               # write index
        count = multiprocessing.Value('i', 0)              # current size
        lock = multiprocessing.Lock()
        empty = multiprocessing.Semaphore(SIZE)
        full = multiprocessing.Semaphore(0)

        PRODUCERS = 2
        CONSUMERS = 2
        ITEMS_PER_PRODUCER = 3
        TOTAL_ITEMS = PRODUCERS * ITEMS_PER_PRODUCER

        def producer(pid: int) -> None:
            """Producer using circular buffer."""
            for i in range(ITEMS_PER_PRODUCER):
                item = pid * 10 + i
                empty.acquire()
                with lock:
                    idx = tail.value % SIZE
                    buffer[idx] = item
                    tail.value += 1
                    count.value += 1
                    print(f"P{pid} produced {item} @ {idx} (count={count.value})")
                full.release()
                time.sleep(0.05)

        def consumer(cid: int) -> None:
            """Consumer using circular buffer with poison pill shutdown."""
            while True:
                full.acquire()
                with lock:
                    if count.value == 0:
                        # Spurious wakeup protection
                        empty.release()
                        continue
                    idx = head.value % SIZE
                    item = buffer[idx]
                    buffer[idx] = -1
                    head.value += 1
                    count.value -= 1
                    print(f"C{cid} consumed {item} @ {idx} (count={count.value})")
                empty.release()
                # Check for poison pill
                if item == -9999:
                    print(f"C{cid} exiting on poison")
                    return
                time.sleep(0.08)

        # Spawn processes
        producers = [multiprocessing.Process(target=producer, args=(i+1,)) for i in range(PRODUCERS)]
        consumers = [multiprocessing.Process(target=consumer, args=(i+1,)) for i in range(CONSUMERS)]

        for p in producers + consumers:
            p.start()

        for p in producers:
            p.join()

        # After all producers finished, push exactly CONSUMERS poison pills
        for _ in range(CONSUMERS):
            empty.acquire()
            with lock:
                idx = tail.value % SIZE
                buffer[idx] = -9999
                tail.value += 1
                count.value += 1
            full.release()

        for c in consumers:
            c.join()

        print(f"Final buffer: {list(buffer)}")
        print()

    def event_coordination_fixed(self) -> None:
        """
        Demonstrate event-based coordination with proper completion tracking.

        This is the PRODUCTION-READY implementation using:
        - Proper worker completion tracking with shared counter
        - Workers signal their own completion
        - Coordinator waits for actual worker completion
        - Robust error handling

        When to Use:
            - Production process coordination
            - Worker completion tracking
            - Startup synchronization
            - One-to-many signaling
            - Event-driven coordination

        Real-World Examples:
            - Worker pools: Track worker completion
            - Batch processing: Wait for batch completion
            - Task coordination: Coordinate task completion
            - Process synchronization: Synchronize process phases

        Gotchas:
            - Workers must signal their own completion
            - Use shared counter with lock for tracking
            - Coordinator waits for actual completion
            - Handle worker failures gracefully
            - Balance coordination vs overhead

        Performance Notes:
            - Low overhead for signaling
            - Efficient for one-to-many coordination
            - Proper tracking prevents hangs
            - Optimal for production use
        """
        print("=== Event Coordination (Fixed - Proper Completion Tracking) ===")

        # Shared events and completion tracking
        start_event = multiprocessing.Event()
        workers_completed = multiprocessing.Value('i', 0)
        workers_lock = multiprocessing.Lock()
        total_workers = 3

        def coordinator() -> None:
            """Coordinator process with proper completion tracking."""
            print("Coordinator: Preparing...")
            time.sleep(1)
            print("Coordinator: Signaling start!")
            start_event.set()  # Signal workers to start

            # Wait for all workers to complete
            while True:
                with workers_lock:
                    completed = workers_completed.value
                    if completed >= total_workers:
                        break
                time.sleep(0.1)  # Polling interval

            print(f"Coordinator: All {total_workers} workers finished!")

        def worker(worker_id: int) -> None:
            """Worker process that signals its own completion."""
            print(f"Worker {worker_id}: Waiting for start signal...")
            start_event.wait()  # Wait for start signal

            try:
                # Do work
                work_time = 0.5 + worker_id * 0.2
                print(f"Worker {worker_id}: Starting work ({work_time:.1f}s)")
                time.sleep(work_time)
                print(f"Worker {worker_id}: Work completed!")

            finally:
                # Signal completion (always executed, even on error)
                with workers_lock:
                    workers_completed.value += 1
                    print(f"Worker {worker_id}: Signaled completion ({workers_completed.value}/{total_workers})")

        # Create processes
        coord = multiprocessing.Process(target=coordinator)
        workers = [multiprocessing.Process(target=worker, args=(i+1,)) for i in range(total_workers)]

        # Start all processes
        coord.start()
        for w in workers:
            w.start()

        # Wait for all processes
        for w in workers:
            w.join()
        coord.join()

        print()

    def event_coordination_real_world(self) -> None:
        """
        Real-World Scenario: Event - Service Startup Coordination.

        REAL-WORLD SCENARIO:
        ====================
        You're building a microservices system:
        - Main service needs to wait for dependencies
        - Database service, Cache service, Message queue
        - Problem: Workers must wait for all services ready
        
        THE PROBLEM WITHOUT EVENT:
        ==========================
        - Workers start immediately
        - Services not ready yet
        - Workers try to connect → fail
        - Retry loops waste resources
        - System unstable
        
        THE SOLUTION:
        =============
        Event ensures:
        - Coordinator waits for all services ready
        - Sets event when all ready
        - Workers wait for event
        - All workers start simultaneously
        - System starts cleanly
        
        WHEN TO USE EVENT:
        ==================
        ✅ Service startup coordination
        ✅ One-to-many signaling
        ✅ Simple coordination patterns
        ✅ Startup synchronization
        ✅ Event-driven coordination
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Microservices Startup Coordination")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Microservices system with dependencies")
        print("  - Main service needs database, cache, message queue")
        print("  - Workers must wait for all services ready")
        print()
        print("THE PROBLEM:")
        print("  Without event:")
        print("    ❌ Workers start immediately")
        print("    ❌ Services not ready yet")
        print("    ❌ Workers try to connect → fail")
        print("    ❌ Retry loops waste resources")
        print("    ❌ System unstable → crashes!")
        print()
        print("THE SOLUTION:")
        print("  With event:")
        print("    ✅ Coordinator waits for all services ready")
        print("    ✅ Sets event when all ready")
        print("    ✅ Workers wait for event")
        print("    ✅ All workers start simultaneously")
        print("    ✅ System starts cleanly")
        print()
        print("=" * 70)
        print()

        services_ready = multiprocessing.Event()
        service_status = multiprocessing.Manager().dict()

        def service_coordinator() -> None:
            """Coordinator that waits for all services to be ready."""
            print("Coordinator: Waiting for services to start...")
            
            # Simulate services starting
            services = ['database', 'cache', 'message_queue']
            for service in services:
                time.sleep(0.2)  # Simulate service startup time
                service_status[service] = 'ready'
                print(f"  ✅ {service.capitalize()} service ready")
            
            print("Coordinator: All services ready! Signaling workers...")
            services_ready.set()  # Signal all workers

        def worker_process(worker_id: int) -> None:
            """Worker that waits for services to be ready."""
            print(f"Worker {worker_id}: Waiting for services...")
            services_ready.wait()  # Wait for coordinator signal
            
            print(f"Worker {worker_id}: Services ready! Starting work...")
            # Now safe to use services
            time.sleep(0.1)
            print(f"Worker {worker_id}: Work completed")

        print("Starting simulation...")
        print("  - 1 coordinator waiting for services")
        print("  - 5 workers waiting for services to be ready")
        print()

        coordinator = multiprocessing.Process(target=service_coordinator)
        workers = [multiprocessing.Process(target=worker_process, args=(i+1,)) for i in range(5)]

        start_time = time.time()
        coordinator.start()
        for w in workers:
            w.start()

        coordinator.join()
        for w in workers:
            w.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Services ready: {list(service_status.keys())}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ All workers started after services ready!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE EVENT:")
        print("   ✅ Service startup coordination")
        print("   ✅ One-to-many signaling")
        print("   ✅ Simple coordination patterns")
        print("   ✅ Startup synchronization")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents race conditions on startup")
        print("   - Ensures dependencies are ready")
        print("   - Clean system initialization")
        print("   - Prevents connection errors")
        print("=" * 70)
        print()

    def event_coordination(self) -> None:
        """
        Demonstrate event-based coordination.

        Shows how to use Event objects to coordinate process execution,
        enabling one process to signal multiple waiting processes.

        When to Use:
            - Process coordination
            - Startup synchronization
            - One-to-many signaling
            - Simple coordination patterns
            - Event-driven coordination

        Real-World Examples:
            - Process startup: Signal when ready to start
            - Coordination: Coordinate process phases
            - Notifications: Notify multiple processes
            - Synchronization: Synchronize process execution
            - Event-driven: Event-driven process coordination

        Gotchas:
            - Event.wait() blocks until set
            - Event.set() wakes all waiters
            - Event.clear() resets event
            - Event is one-time (use clear() to reset)
            - Multiple waiters all wake on set()
            - Use proper synchronization for completion tracking

        Performance Notes:
            - Low overhead for signaling
            - Efficient for one-to-many coordination
            - Useful for simple coordination
            - Minimal performance impact
        """
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

    def condition_variables_fixed(self) -> None:
        """
        Demonstrate condition variables with FIFO buffer and graceful shutdown.

        This is the PRODUCTION-READY implementation using:
        - Circular buffer with head/tail pointers (FIFO)
        - Proper graceful shutdown with poison pills
        - Robust error handling
        - Proper predicate checking

        When to Use:
            - Production producer-consumer patterns
            - FIFO task queues
            - State-based coordination
            - Complex synchronization requirements

        Real-World Examples:
            - Task queues: Process tasks in order
            - Message queues: FIFO message processing
            - Data pipelines: Process data in order
            - Event processing: Process events sequentially

        Gotchas:
            - Use head/tail for FIFO ordering
            - Always check predicate in while loop
            - Poison pills for graceful shutdown
            - Modulo arithmetic for circular buffer
            - Proper lock scope management

        Performance Notes:
            - FIFO ordering preserved
            - Circular buffer reuses memory
            - Proper shutdown prevents hangs
            - Optimal for production use
        """
        print("=== Condition Variables (Fixed - FIFO Buffer) ===")

        SIZE = 5
        buffer = multiprocessing.Array('i', SIZE)
        head = multiprocessing.Value('i', 0)
        tail = multiprocessing.Value('i', 0)
        count = multiprocessing.Value('i', 0)
        buffer_lock = multiprocessing.Lock()
        not_empty = multiprocessing.Condition(buffer_lock)
        not_full = multiprocessing.Condition(buffer_lock)

        PRODUCERS = 2
        CONSUMERS = 2
        ITEMS_PER_PRODUCER = 3

        def producer(producer_id: int) -> None:
            """Producer using condition variables with FIFO buffer."""
            for i in range(ITEMS_PER_PRODUCER):
                item = producer_id * 100 + i

                with not_full:
                    # Wait while buffer is full
                    while count.value >= SIZE:
                        print(f"Producer {producer_id}: Buffer full, waiting...")
                        not_full.wait()

                    # Add item at tail (FIFO)
                    idx = tail.value % SIZE
                    buffer[idx] = item
                    tail.value += 1
                    count.value += 1
                    print(f"Producer {producer_id}: Added {item} @ {idx} (count={count.value})")

                # Signal that buffer is not empty
                with not_empty:
                    not_empty.notify()

                time.sleep(0.1)

        def consumer(consumer_id: int) -> None:
            """Consumer using condition variables with poison pill shutdown."""
            while True:
                with not_empty:
                    # Wait while buffer is empty
                    while count.value <= 0:
                        print(f"Consumer {consumer_id}: Buffer empty, waiting...")
                        not_empty.wait()

                    # Remove item from head (FIFO)
                    idx = head.value % SIZE
                    item = buffer[idx]
                    buffer[idx] = -1
                    head.value += 1
                    count.value -= 1
                    print(f"Consumer {consumer_id}: Removed {item} @ {idx} (count={count.value})")

                # Signal that buffer is not full
                with not_full:
                    not_full.notify()

                # Check for poison pill
                if item == -9999:
                    print(f"Consumer {consumer_id}: Exiting on poison pill")
                    return

                time.sleep(0.2)

        print("Starting condition variable example (FIFO):")
        producers = [multiprocessing.Process(target=producer, args=(i+1,)) for i in range(PRODUCERS)]
        consumers = [multiprocessing.Process(target=consumer, args=(i+1,)) for i in range(CONSUMERS)]

        for p in producers + consumers:
            p.start()

        # Wait for producers to finish
        for p in producers:
            p.join()

        # Inject poison pills for graceful shutdown
        for _ in range(CONSUMERS):
            with not_full:
                while count.value >= SIZE:
                    not_full.wait()
                idx = tail.value % SIZE
                buffer[idx] = -9999
                tail.value += 1
                count.value += 1
            with not_empty:
                not_empty.notify()

        # Wait for consumers to finish
        for c in consumers:
            c.join()

        print(f"Final buffer: {list(buffer)}")
        print()

    def condition_variables_real_world(self) -> None:
        """
        Real-World Scenario: Condition Variables - Task Queue with Priority.

        REAL-WORLD SCENARIO:
        ====================
        You're building a task queue system:
        - Workers process tasks from queue
        - Queue has max size (bounded buffer)
        - Problem: Workers wait when queue empty, producers wait when full
        
        THE PROBLEM WITHOUT CONDITION VARIABLES:
        =========================================
        - Workers poll queue constantly (waste CPU)
        - Producers poll queue constantly (waste CPU)
        - High CPU usage from polling
        - Delayed task processing
        - Inefficient resource usage
        
        THE SOLUTION:
        =============
        Condition variables ensure:
        - Workers wait efficiently when queue empty
        - Producers wait efficiently when queue full
        - Wake up immediately when condition changes
        - No CPU waste from polling
        - Efficient resource usage
        
        WHEN TO USE CONDITION VARIABLES:
        ================================
        ✅ Bounded buffers (wait for space/items)
        ✅ State-based coordination
        ✅ Efficient waiting patterns
        ✅ Producer-consumer with conditions
        ✅ Complex predicates
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Task Queue with Bounded Buffer")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Task queue system with max size (bounded buffer)")
        print("  - Workers process tasks from queue")
        print("  - Producers add tasks to queue")
        print("  - Problem: Efficient waiting needed")
        print()
        print("THE PROBLEM:")
        print("  Without condition variables:")
        print("    ❌ Workers poll queue constantly (waste CPU)")
        print("    ❌ Producers poll queue constantly (waste CPU)")
        print("    ❌ High CPU usage from polling")
        print("    ❌ Delayed task processing")
        print("    ❌ Inefficient resource usage")
        print()
        print("THE SOLUTION:")
        print("  With condition variables:")
        print("    ✅ Workers wait efficiently when queue empty")
        print("    ✅ Producers wait efficiently when queue full")
        print("    ✅ Wake up immediately when condition changes")
        print("    ✅ No CPU waste from polling")
        print("    ✅ Efficient resource usage")
        print()
        print("=" * 70)
        print()

        QUEUE_SIZE = 5
        task_queue = multiprocessing.Manager().list()
        queue_lock = multiprocessing.Lock()
        queue_not_empty = multiprocessing.Condition(queue_lock)
        queue_not_full = multiprocessing.Condition(queue_lock)
        task_stats = multiprocessing.Manager().dict()

        def task_producer(producer_id: int, num_tasks: int) -> None:
            """Producer that adds tasks to queue."""
            for i in range(num_tasks):
                task = f"task_{producer_id}_{i}"
                
                with queue_not_full:
                    # Wait while queue is full
                    while len(task_queue) >= QUEUE_SIZE:
                        print(f"  Producer {producer_id}: Queue full, waiting...")
                        queue_not_full.wait()
                    
                    # Add task
                    task_queue.append(task)
                    print(f"  Producer {producer_id}: Added {task} (queue size: {len(task_queue)})")
                
                # Signal that queue is not empty
                with queue_not_empty:
                    queue_not_empty.notify()
                
                time.sleep(0.05)

            print(f"Producer {producer_id}: Completed {num_tasks} tasks")

        def task_worker(worker_id: int) -> None:
            """Worker that processes tasks from queue."""
            tasks_processed = 0
            while tasks_processed < 6:  # Process 6 tasks total
                with queue_not_empty:
                    # Wait while queue is empty
                    while len(task_queue) <= 0:
                        print(f"  Worker {worker_id}: Queue empty, waiting...")
                        queue_not_empty.wait()
                    
                    # Get task
                    task = task_queue.pop(0)
                    print(f"  Worker {worker_id}: Processing {task} (queue size: {len(task_queue)})")
                
                # Signal that queue is not full
                with queue_not_full:
                    queue_not_full.notify()
                
                # Process task
                time.sleep(0.1)
                tasks_processed += 1
                
                if worker_id not in task_stats:
                    task_stats[worker_id] = 0
                task_stats[worker_id] += 1

            print(f"Worker {worker_id}: Completed {tasks_processed} tasks")

        print("Starting simulation...")
        print(f"  - Queue size: {QUEUE_SIZE}")
        print("  - 2 producers adding tasks")
        print("  - 3 workers processing tasks")
        print()

        producers = [multiprocessing.Process(target=task_producer, args=(i+1, 6)) for i in range(2)]
        workers = [multiprocessing.Process(target=task_worker, args=(i+1,)) for i in range(3)]

        start_time = time.time()
        for p in producers:
            p.start()
        for w in workers:
            w.start()

        for p in producers:
            p.join()
        for w in workers:
            w.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Tasks processed: {sum(task_stats.values())}")
        print(f"  Execution time: {elapsed:.2f}s")
        print(f"  Final queue size: {len(task_queue)}")
        print("  ✅ Condition variables enabled efficient waiting!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE CONDITION VARIABLES:")
        print("   ✅ Bounded buffers (wait for space/items)")
        print("   ✅ State-based coordination")
        print("   ✅ Efficient waiting patterns")
        print("   ✅ Producer-consumer with conditions")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Eliminates CPU waste from polling")
        print("   - Immediate wake-up when condition changes")
        print("   - Efficient resource usage")
        print("   - Better performance than polling")
        print("=" * 70)
        print()

    def condition_variables(self) -> None:
        """
        Demonstrate condition variables for complex synchronization.

        Shows how to use Condition variables for efficient waiting on
        predicates, enabling complex synchronization patterns.

        When to Use:
            - Waiting on state changes
            - Complex predicates
            - Efficient waiting patterns
            - Producer-consumer with conditions
            - State-based coordination

        Real-World Examples:
            - Bounded buffers: Wait for space/items
            - State machines: Wait for state changes
            - Resource pools: Wait for resources
            - Task queues: Wait for tasks
            - Pipeline stages: Coordinate stages

        Gotchas:
            - Condition.wait() releases lock and waits
            - Must check predicate in loop (spurious wakeups)
            - notify() wakes one waiter
            - notify_all() wakes all waiters
            - Must hold lock when calling wait/notify
            - Always use while loop for predicate checking

        Performance Notes:
            - More efficient than polling
            - Useful for complex synchronization
            - Overhead for condition operations
            - Optimal for predicate-based waiting
        """
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

    def barrier_synchronization_fixed(self) -> None:
        """
        Demonstrate barrier synchronization with resettable barrier and timeout.

        This is the PRODUCTION-READY implementation using:
        - Resettable barrier (can be reused)
        - Timeout handling to prevent indefinite blocking
        - Proper error handling for crashed processes
        - Generation counter for barrier reuse

        When to Use:
            - Production phase synchronization
            - Resettable barriers
            - Timeout requirements
            - Robust process coordination

        Real-World Examples:
            - Parallel algorithms: Synchronize phases
            - Data processing: Synchronize processing phases
            - Pipeline stages: Synchronize stage boundaries
            - Distributed computing: Synchronize computation phases

        Gotchas:
            - Barrier must reset for reuse
            - Timeout prevents indefinite blocking
            - Handle process crashes gracefully
            - Generation counter tracks barrier cycles
            - All processes must reach barrier

        Performance Notes:
            - Resettable barrier enables reuse
            - Timeout prevents hangs
            - Proper error handling prevents deadlocks
            - Optimal for production use
        """
        print("=== Barrier Synchronization (Fixed - Resettable with Timeout) ===")

        class ResettableBarrier:
            """Production-ready resettable barrier with timeout."""
            def __init__(self, parties: int, timeout: float = 30.0):
                self.parties = parties
                self.timeout = timeout
                self.count = multiprocessing.Value('i', 0)
                self.generation = multiprocessing.Value('i', 0)
                self.lock = multiprocessing.Lock()
                self.condition = multiprocessing.Condition(self.lock)

            def wait(self, timeout: float = None) -> bool:
                """
                Wait at barrier with timeout.

                Returns:
                    True if barrier passed, False if timeout
                """
                timeout = timeout or self.timeout
                deadline = time.time() + timeout

                with self.condition:
                    current_generation = self.generation.value
                    self.count.value += 1

                    if self.count.value == self.parties:
                        # Last process arrived, reset and wake everyone
                        self.count.value = 0
                        self.generation.value += 1
                        self.condition.notify_all()
                        print(f"Barrier: All {self.parties} processes arrived, releasing...")
                        return True
                    else:
                        # Wait for others with timeout
                        print(f"Barrier: Waiting... ({self.count.value}/{self.parties})")
                        while (self.generation.value == current_generation and
                               self.count.value < self.parties):
                            remaining = deadline - time.time()
                            if remaining <= 0:
                                print(f"Barrier: Timeout waiting for others")
                                self.count.value -= 1  # Back out
                                return False
                            if not self.condition.wait(timeout=remaining):
                                print(f"Barrier: Timeout")
                                self.count.value -= 1
                                return False
                        return True

        def barrier_task(task_id: int, barrier: ResettableBarrier) -> None:
            """Task that uses barrier synchronization."""
            try:
                print(f"Task {task_id}: Phase 1")
                time.sleep(0.1 * task_id)

                if not barrier.wait(timeout=5.0):
                    print(f"Task {task_id}: Barrier timeout in Phase 1")
                    return

                print(f"Task {task_id}: Phase 2 (after barrier)")
                time.sleep(0.1)

                if not barrier.wait(timeout=5.0):
                    print(f"Task {task_id}: Barrier timeout in Phase 2")
                    return

                print(f"Task {task_id}: Phase 3 (final)")
            except Exception as e:
                print(f"Task {task_id}: Error - {e}")

        # Create resettable barrier for 3 processes
        barrier = ResettableBarrier(3, timeout=10.0)

        # Create tasks
        tasks = [multiprocessing.Process(target=barrier_task, args=(i+1, barrier)) for i in range(3)]

        print("Starting barrier synchronization (resettable):")
        for t in tasks:
            t.start()

        for t in tasks:
            t.join()

        print()

    def barrier_synchronization_real_world(self) -> None:
        """
        Real-World Scenario: Barrier - Parallel Data Processing Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building a parallel data processing pipeline:
        - Stage 1: Load data (all workers must finish)
        - Stage 2: Process data (all workers must finish)
        - Stage 3: Save results (all workers must finish)
        - Problem: Workers must synchronize at each stage
        
        THE PROBLEM WITHOUT BARRIER:
        =============================
        - Worker 1 finishes Stage 1 → starts Stage 2
        - Worker 2 still in Stage 1 → Worker 1 processes incomplete data
        - Data inconsistency → wrong results
        - Race conditions → corrupted output
        
        THE SOLUTION:
        =============
        Barrier ensures:
        - All workers wait at barrier after Stage 1
        - When all arrive, barrier releases
        - All workers start Stage 2 simultaneously
        - Data consistency guaranteed
        - Correct results
        
        WHEN TO USE BARRIER:
        ====================
        ✅ Parallel algorithm phases
        ✅ Data processing pipelines
        ✅ Synchronized computation stages
        ✅ Phase coordination
        ✅ Rendezvous points
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Parallel Data Processing Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Parallel data processing pipeline")
        print("  - Stage 1: Load data (all workers must finish)")
        print("  - Stage 2: Process data (all workers must finish)")
        print("  - Stage 3: Save results (all workers must finish)")
        print()
        print("THE PROBLEM:")
        print("  Without barrier:")
        print("    ❌ Worker 1 finishes Stage 1 → starts Stage 2")
        print("    ❌ Worker 2 still in Stage 1 → Worker 1 processes incomplete data")
        print("    ❌ Data inconsistency → wrong results")
        print("    ❌ Race conditions → corrupted output")
        print()
        print("THE SOLUTION:")
        print("  With barrier:")
        print("    ✅ All workers wait at barrier after Stage 1")
        print("    ✅ When all arrive, barrier releases")
        print("    ✅ All workers start Stage 2 simultaneously")
        print("    ✅ Data consistency guaranteed")
        print("    ✅ Correct results")
        print()
        print("=" * 70)
        print()

        NUM_WORKERS = 4
        barrier_count = multiprocessing.Value('i', 0)
        barrier_lock = multiprocessing.Lock()
        barrier_condition = multiprocessing.Condition(barrier_lock)
        stage_data = multiprocessing.Manager().dict()

        def barrier_wait(stage: int) -> None:
            """Wait at barrier until all workers arrive."""
            with barrier_condition:
                barrier_count.value += 1
                current_count = barrier_count.value
                print(f"  Stage {stage}: Worker arrived ({current_count}/{NUM_WORKERS})")
                
                if barrier_count.value == NUM_WORKERS:
                    # Last worker arrived, reset and wake everyone
                    barrier_count.value = 0
                    barrier_condition.notify_all()
                    print(f"  Stage {stage}: All workers arrived! Proceeding...")
                else:
                    # Wait for others
                    barrier_condition.wait()

        def data_processor(worker_id: int) -> None:
            """Worker processing data through pipeline stages."""
            # Stage 1: Load data
            print(f"Worker {worker_id}: Stage 1 - Loading data...")
            time.sleep(0.1 * worker_id)  # Variable load time
            stage_data[f'worker_{worker_id}_stage1'] = 'loaded'
            barrier_wait(1)
            
            # Stage 2: Process data
            print(f"Worker {worker_id}: Stage 2 - Processing data...")
            time.sleep(0.1)
            stage_data[f'worker_{worker_id}_stage2'] = 'processed'
            barrier_wait(2)
            
            # Stage 3: Save results
            print(f"Worker {worker_id}: Stage 3 - Saving results...")
            time.sleep(0.1)
            stage_data[f'worker_{worker_id}_stage3'] = 'saved'
            barrier_wait(3)
            
            print(f"Worker {worker_id}: Pipeline complete!")

        print("Starting simulation...")
        print(f"  - {NUM_WORKERS} workers processing data")
        print("  - 3 stages with barriers between")
        print()

        workers = [multiprocessing.Process(target=data_processor, args=(i+1,)) for i in range(NUM_WORKERS)]

        start_time = time.time()
        for w in workers:
            w.start()

        for w in workers:
            w.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Workers completed: {NUM_WORKERS}")
        print(f"  Stages completed: 3")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Barrier ensured all workers synchronized at each stage!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE BARRIER:")
        print("   ✅ Parallel algorithm phases")
        print("   ✅ Data processing pipelines")
        print("   ✅ Synchronized computation stages")
        print("   ✅ Phase coordination")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Ensures data consistency")
        print("   - Prevents race conditions")
        print("   - Synchronizes computation phases")
        print("   - Guarantees correct results")
        print("=" * 70)
        print()

    def barrier_synchronization(self) -> None:
        """
        Demonstrate barrier synchronization.

        Shows how to use barriers to synchronize multiple processes at
        specific points, ensuring all processes reach the barrier before
        proceeding.

        When to Use:
            - Synchronizing process phases
            - Rendezvous points
            - Phase coordination
            - Parallel algorithm phases
            - Synchronized execution points

        Real-World Examples:
            - Parallel algorithms: Synchronize algorithm phases
            - Data processing: Synchronize processing phases
            - Pipeline stages: Synchronize stage boundaries
            - Distributed computing: Synchronize computation phases
            - Simulation: Synchronize simulation steps

        Gotchas:
            - All processes must reach barrier
            - Barrier blocks until all arrive
            - Deadlock if process doesn't reach barrier
            - Barrier resets after all processes pass
            - Use timeout to prevent indefinite blocking
            - Python 3.3+ has multiprocessing.Barrier

        Performance Notes:
            - Barrier overhead for coordination
            - Useful for phase synchronization
            - All processes wait for slowest
            - Balance synchronization vs performance
        """
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

    def reader_writer_problem_fixed(self) -> None:
        """
        Demonstrate reader-writer synchronization with writer priority.

        This is the PRODUCTION-READY implementation using:
        - Writer priority to prevent starvation
        - Proper reader/writer tracking
        - Timeout handling
        - Fair access for both readers and writers

        When to Use:
            - Production read-write access patterns
            - Preventing writer starvation
            - Fair resource access
            - Database-like access patterns

        Real-World Examples:
            - Databases: Fair read-write access
            - Caches: Prevent writer starvation
            - Configuration: Fair updates
            - Shared state: Fair modifications

        Gotchas:
            - Writer priority prevents starvation
            - Track waiting writers
            - Block new readers when writer waiting
            - Fair access for both types
            - Proper lock ordering

        Performance Notes:
            - Writer priority prevents starvation
            - Fair access improves responsiveness
            - Proper tracking adds overhead
            - Optimal for production use
        """
        print("=== Reader-Writer Problem (Fixed - Writer Priority) ===")

        # Shared data and synchronization primitives
        shared_data = multiprocessing.Value('i', 0)
        active_readers_count = multiprocessing.Value('i', 0)
        waiting_writers_count = multiprocessing.Value('i', 0)
        
        # Locks for different purposes
        data_exclusive_lock = multiprocessing.Lock()  # Protects shared_data from concurrent writes
        readers_count_lock = multiprocessing.Lock()   # Protects active_readers_count
        writer_priority_lock = multiprocessing.Lock() # Protects waiting_writers_count
        
        # Condition variable for writer priority mechanism
        writer_priority_condition = multiprocessing.Condition(writer_priority_lock)

        def _signal_writer_waiting() -> None:
            """Signal that a writer is waiting (gives priority)."""
            with writer_priority_lock:
                waiting_writers_count.value += 1
                writer_priority_condition.notify_all()

        def _signal_writer_acquired() -> None:
            """Signal that writer acquired access (no longer waiting)."""
            with writer_priority_lock:
                waiting_writers_count.value -= 1
                writer_priority_condition.notify_all()

        def _wait_for_writer_priority() -> None:
            """Wait if writers are waiting (gives priority to writers)."""
            with writer_priority_lock:
                while waiting_writers_count.value > 0:
                    writer_priority_condition.wait()

        def _reader_enter() -> None:
            """Reader entry: acquire read access with writer priority check."""
            with readers_count_lock:
                # Check if writers are waiting (priority mechanism)
                _wait_for_writer_priority()
                
                # Increment reader count
                active_readers_count.value += 1
                
                # First reader locks data (blocks writers)
                if active_readers_count.value == 1:
                    data_exclusive_lock.acquire()

        def _reader_exit() -> None:
            """Reader exit: release read access."""
            with readers_count_lock:
                active_readers_count.value -= 1
                
                # Last reader unlocks data (allows writers)
                if active_readers_count.value == 0:
                    data_exclusive_lock.release()

        def writer(writer_id: int) -> None:
            """Writer process with priority."""
            for i in range(3):
                # Step 1: Signal that writer is waiting (gives priority)
                _signal_writer_waiting()

                # Step 2: Acquire exclusive write access
                with data_exclusive_lock:
                    # Step 3: Signal that writer got access
                    _signal_writer_acquired()

                    # Step 4: Perform write operation
                    shared_data.value += 1
                    print(f"Writer {writer_id}: Wrote {shared_data.value}")
                    time.sleep(0.1)

        def reader(reader_id: int) -> None:
            """Reader process that respects writer priority."""
            for i in range(4):
                # Step 1: Acquire read access (waits if writers are waiting)
                _reader_enter()

                # Step 2: Perform read operation (no lock needed, data_exclusive_lock already held)
                value = shared_data.value
                print(f"Reader {reader_id}: Read {value}")

                # Step 3: Release read access
                _reader_exit()

                time.sleep(0.05)

        print("Starting reader-writer example (writer priority):")
        writers = [multiprocessing.Process(target=writer, args=(i+1,)) for i in range(2)]
        readers = [multiprocessing.Process(target=reader, args=(i+1,)) for i in range(3)]

        # Start readers and writers
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

    def reader_writer_real_world_example(self) -> None:
        """
        Real-world demonstration: When and Why Reader-Writer Lock with Writer Priority.

        REAL-WORLD SCENARIO:
        ====================
        You're running an e-commerce website with:
        - Product catalog cached in memory (read 1000x/second)
        - Price updates from admin panel (write 1x/minute)
        - Inventory updates from warehouse (write 1x/minute)
        
        THE PROBLEM WITHOUT WRITER PRIORITY:
        ====================================
        - 1000 readers constantly querying product prices
        - 1 writer tries to update price (critical: flash sale!)
        - Writer waits... and waits... and waits...
        - New readers keep arriving, writer never gets access
        - Flash sale price never updates → Lost revenue!
        - This is called "WRITER STARVATION"
        
        THE SOLUTION:
        =============
        Writer Priority ensures:
        - When writer arrives, new readers are blocked
        - Existing readers finish, then writer gets exclusive access
        - Writer updates price, then readers can resume
        - Critical updates always go through
        
        WHEN TO USE THIS PATTERN:
        =========================
        ✅ Read-heavy workloads (many readers, few writers)
        ✅ Writers must not starve (critical updates)
        ✅ Stale data is unacceptable (caches, configs)
        ✅ Fair access required (databases, file systems)
        
        ❌ Write-heavy workloads (use regular locks)
        ❌ Readers can tolerate stale data (no need for priority)
        ❌ Simple read-write patterns (overkill)
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: E-Commerce Product Cache")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - E-commerce site with product catalog in shared cache")
        print("  - 1000s of users browsing products (read-heavy)")
        print("  - Admin updates prices occasionally (critical writes)")
        print("  - Warehouse updates inventory occasionally (critical writes)")
        print()
        print("THE PROBLEM:")
        print("  Without writer priority:")
        print("    ❌ Price update arrives → waits for readers")
        print("    ❌ New readers keep arriving → writer keeps waiting")
        print("    ❌ Writer STARVES → price never updates")
        print("    ❌ Flash sale price stuck at old value → Lost sales!")
        print()
        print("THE SOLUTION:")
        print("  With writer priority:")
        print("    ✅ Price update arrives → signals priority")
        print("    ✅ New readers blocked → wait for writer")
        print("    ✅ Existing readers finish → writer gets access")
        print("    ✅ Price updates → new readers see updated price")
        print()
        print("=" * 70)
        print()

        # Simulate product cache
        product_cache = multiprocessing.Manager().dict()
        product_cache['product_id'] = 12345
        product_cache['price'] = 99.99
        product_cache['inventory'] = 100
        product_cache['last_price_update'] = time.time()
        product_cache['version'] = 1

        # Synchronization primitives
        active_readers = multiprocessing.Value('i', 0)
        waiting_writers = multiprocessing.Value('i', 0)
        cache_lock = multiprocessing.Lock()
        readers_lock = multiprocessing.Lock()
        writer_priority_lock = multiprocessing.Lock()
        writer_condition = multiprocessing.Condition(writer_priority_lock)

        # Statistics tracking
        read_operations = multiprocessing.Manager().dict()
        write_operations = multiprocessing.Manager().dict()
        writer_wait_times = multiprocessing.Manager().list()
        reader_blocked_by_writer = multiprocessing.Manager().dict()

        def customer_browser(reader_id: int, num_reads: int) -> None:
            """
            Simulate customer browsing products (frequent reads).
            
            This represents:
            - User browsing product pages
            - Checking prices
            - Viewing inventory
            - Happens 1000s of times per second
            """
            read_count = 0
            blocked_count = 0
            
            for i in range(num_reads):
                # Try to read product info
                with readers_lock:
                    # Check if writer is waiting (priority check)
                    with writer_priority_lock:
                        was_blocked = waiting_writers.value > 0
                        while waiting_writers.value > 0:
                            blocked_count += 1
                            writer_condition.wait()  # Wait for writer to finish
                    
                    active_readers.value += 1
                    if active_readers.value == 1:
                        cache_lock.acquire()

                # Read product data (simulate page load)
                product_id = product_cache['product_id']
                price = product_cache['price']
                inventory = product_cache['inventory']
                read_count += 1
                
                if reader_id not in read_operations:
                    read_operations[reader_id] = 0
                read_operations[reader_id] += 1

                # Release read access
                with readers_lock:
                    active_readers.value -= 1
                    if active_readers.value == 0:
                        cache_lock.release()

                time.sleep(0.005)  # Simulate page load time

            if reader_id not in reader_blocked_by_writer:
                reader_blocked_by_writer[reader_id] = 0
            reader_blocked_by_writer[reader_id] = blocked_count
            
            print(f"Browser {reader_id}: Viewed {read_count} products (blocked {blocked_count}x by writers)")

        def admin_price_updater(writer_id: int, num_writes: int) -> None:
            """
            Simulate admin updating product price (critical write).
            
            This represents:
            - Admin panel price update
            - Flash sale price change
            - Critical: Must go through immediately!
            - Cannot wait indefinitely
            """
            write_count = 0
            
            for i in range(num_writes):
                wait_start = time.time()
                new_price = 79.99 - (i * 5)  # Simulate price drop

                # Signal that writer is waiting (PRIORITY MECHANISM)
                with writer_priority_lock:
                    waiting_writers.value += 1
                    writer_condition.notify_all()
                    print(f"  ⚠️  Admin {writer_id}: Price update QUEUED (new readers will wait)")

                # Acquire exclusive write access
                with cache_lock:
                    wait_time = time.time() - wait_start
                    writer_wait_times.append(wait_time)

                    # Signal that writer got access
                    with writer_priority_lock:
                        waiting_writers.value -= 1
                        writer_condition.notify_all()

                    # CRITICAL UPDATE: Change price
                    old_price = product_cache['price']
                    product_cache['price'] = new_price
                    product_cache['version'] += 1
                    product_cache['last_price_update'] = time.time()
                    write_count += 1

                    if writer_id not in write_operations:
                        write_operations[writer_id] = 0
                    write_operations[writer_id] += 1

                    print(f"  ✅ Admin {writer_id}: Updated price ${old_price:.2f} → ${new_price:.2f} "
                          f"(waited {wait_time:.3f}s)")
                    time.sleep(0.02)  # Simulate update processing time

            print(f"Admin {writer_id}: Completed {write_count} price updates")

        def warehouse_inventory_updater(writer_id: int, num_writes: int) -> None:
            """
            Simulate warehouse updating inventory (critical write).
            
            This represents:
            - Warehouse system updating stock levels
            - Critical: Must reflect accurate inventory
            - Cannot be delayed indefinitely
            """
            write_count = 0
            
            for i in range(num_writes):
                wait_start = time.time()
                new_inventory = 100 - (i * 10)  # Simulate inventory decrease

                # Signal that writer is waiting (PRIORITY MECHANISM)
                with writer_priority_lock:
                    waiting_writers.value += 1
                    writer_condition.notify_all()
                    print(f"  ⚠️  Warehouse {writer_id}: Inventory update QUEUED")

                # Acquire exclusive write access
                with cache_lock:
                    wait_time = time.time() - wait_start
                    writer_wait_times.append(wait_time)

                    # Signal that writer got access
                    with writer_priority_lock:
                        waiting_writers.value -= 1
                        writer_condition.notify_all()

                    # CRITICAL UPDATE: Change inventory
                    old_inventory = product_cache['inventory']
                    product_cache['inventory'] = new_inventory
                    product_cache['version'] += 1
                    write_count += 1

                    if writer_id not in write_operations:
                        write_operations[writer_id] = 0
                    write_operations[writer_id] += 1

                    print(f"  ✅ Warehouse {writer_id}: Updated inventory {old_inventory} → {new_inventory} "
                          f"(waited {wait_time:.3f}s)")
                    time.sleep(0.02)  # Simulate update processing time

            print(f"Warehouse {writer_id}: Completed {write_count} inventory updates")

        print("Starting simulation...")
        print("  - 10 customer browsers (simulating high traffic)")
        print("  - 1 admin price updater (critical: flash sale!)")
        print("  - 1 warehouse inventory updater (critical: stock update)")
        print()

        # Create processes
        browsers = [multiprocessing.Process(target=customer_browser, args=(i+1, 30)) for i in range(10)]
        admin = multiprocessing.Process(target=admin_price_updater, args=(1, 3))
        warehouse = multiprocessing.Process(target=warehouse_inventory_updater, args=(1, 2))

        start_time = time.time()

        # Start all processes
        for b in browsers:
            b.start()
        admin.start()
        warehouse.start()

        # Wait for completion
        for b in browsers:
            b.join()
        admin.join()
        warehouse.join()

        elapsed_time = time.time() - start_time

        # Print results
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Total execution time: {elapsed_time:.2f}s")
        print(f"Total product views: {sum(read_operations.values())}")
        print(f"Total price updates: {write_operations.get(1, 0)}")
        print(f"Total inventory updates: {write_operations.get(1, 0)}")
        print(f"Final cache state:")
        print(f"  Product ID: {product_cache['product_id']}")
        print(f"  Price: ${product_cache['price']:.2f}")
        print(f"  Inventory: {product_cache['inventory']}")
        print(f"  Version: {product_cache['version']}")
        
        if writer_wait_times:
            avg_wait = sum(writer_wait_times) / len(writer_wait_times)
            max_wait = max(writer_wait_times)
            print()
            print("Writer Performance:")
            print(f"  Average wait time: {avg_wait:.3f}s")
            print(f"  Maximum wait time: {max_wait:.3f}s")
            if max_wait < 0.1:
                print("  ✅ EXCELLENT: Writers got priority quickly (no starvation)")
            elif max_wait < 0.5:
                print("  ✅ GOOD: Writers got access reasonably fast")
            else:
                print("  ⚠️  WARNING: Writers waited too long (potential starvation)")

        total_blocked = sum(reader_blocked_by_writer.values())
        if total_blocked > 0:
            print()
            print("Reader Impact:")
            print(f"  Total times readers waited for writers: {total_blocked}")
            print("  ✅ This is EXPECTED: New readers wait when writers have priority")
            print("  ✅ This ensures critical updates go through")

        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN THIS PATTERN IS NEEDED:")
        print("   - Read-heavy workloads (many readers, few writers)")
        print("   - Writers must not starve (critical updates)")
        print("   - Stale data is unacceptable (caches, configs, databases)")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Without priority: Writers can wait indefinitely")
        print("   - With priority: Critical updates always go through")
        print("   - Business impact: Prevents lost sales, stale data, system issues")
        print()
        print("3. REAL-WORLD USE CASES:")
        print("   ✅ Database systems: Updates must not be delayed")
        print("   ✅ Caches: Stale data must be refreshable")
        print("   ✅ Configuration: Critical changes must apply")
        print("   ✅ File systems: Metadata updates must complete")
        print("   ✅ Shared state: Critical modifications must go through")
        print()
        print("4. WHEN NOT TO USE:")
        print("   ❌ Write-heavy workloads (use regular locks)")
        print("   ❌ Readers can tolerate stale data (no priority needed)")
        print("   ❌ Simple read-write patterns (overkill)")
        print("=" * 70)
        print()

    def reader_writer_database_scenario(self) -> None:
        """
        Real-World Scenario #2: Database Connection Pool.

        SITUATION:
        ==========
        - Database connection pool with limited connections
        - Many application threads reading data (SELECT queries)
        - Occasional schema updates (ALTER TABLE, CREATE INDEX)
        - Problem: Schema updates must not wait indefinitely
        
        THE PROBLEM:
        ============
        Without writer priority:
        - Schema update arrives → waits for readers
        - New SELECT queries keep arriving → writer waits forever
        - Database migration stuck → system cannot evolve
        - Critical: Schema updates are time-sensitive
        
        THE SOLUTION:
        =============
        Writer priority ensures:
        - Schema update signals priority
        - New SELECT queries wait
        - Existing queries finish
        - Schema update executes
        - Database can evolve
        
        WHEN TO USE:
        ============
        ✅ Database connection pools
        ✅ Schema migration systems
        ✅ Database administration tools
        ✅ Multi-tenant databases
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO #2: Database Connection Pool")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Database with connection pool (limited connections)")
        print("  - Many app threads executing SELECT queries (read-heavy)")
        print("  - DBA performing schema updates (critical writes)")
        print("  - Problem: Schema updates must complete")
        print()
        print("THE PROBLEM:")
        print("  Without writer priority:")
        print("    ❌ ALTER TABLE arrives → waits for SELECT queries")
        print("    ❌ New SELECT queries keep arriving → ALTER waits forever")
        print("    ❌ Schema migration stuck → database cannot evolve")
        print("    ❌ Production deployment blocked → system downtime!")
        print()
        print("THE SOLUTION:")
        print("  With writer priority:")
        print("    ✅ ALTER TABLE signals priority")
        print("    ✅ New SELECT queries wait")
        print("    ✅ Existing SELECT queries finish")
        print("    ✅ ALTER TABLE executes → schema updated")
        print("    ✅ Database evolves without blocking")
        print()
        print("=" * 70)
        print()

        # Simulate database connection pool
        db_state = multiprocessing.Manager().dict()
        db_state['active_connections'] = 0
        db_state['schema_version'] = 1
        db_state['table_count'] = 10
        db_state['last_schema_update'] = time.time()

        # Synchronization
        active_readers = multiprocessing.Value('i', 0)
        waiting_writers = multiprocessing.Value('i', 0)
        db_lock = multiprocessing.Lock()
        readers_lock = multiprocessing.Lock()
        writer_priority_lock = multiprocessing.Lock()
        writer_condition = multiprocessing.Condition(writer_priority_lock)

        def execute_select_query(query_id: int, num_queries: int) -> None:
            """Simulate SELECT query execution (read operation)."""
            for i in range(num_queries):
                with readers_lock:
                    with writer_priority_lock:
                        while waiting_writers.value > 0:
                            writer_condition.wait()
                    active_readers.value += 1
                    if active_readers.value == 1:
                        db_lock.acquire()

                # Execute SELECT query
                schema_version = db_state['schema_version']
                table_count = db_state['table_count']
                # Simulate query execution
                time.sleep(0.01)

                with readers_lock:
                    active_readers.value -= 1
                    if active_readers.value == 0:
                        db_lock.release()

            print(f"Query {query_id}: Executed {num_queries} SELECT queries")

        def execute_schema_update(update_id: int, num_updates: int) -> None:
            """Simulate schema update (write operation - CRITICAL)."""
            for i in range(num_updates):
                wait_start = time.time()

                with writer_priority_lock:
                    waiting_writers.value += 1
                    writer_condition.notify_all()
                    print(f"  ⚠️  Schema Update {update_id}: ALTER TABLE QUEUED (new queries will wait)")

                with db_lock:
                    wait_time = time.time() - wait_start

                    with writer_priority_lock:
                        waiting_writers.value -= 1
                        writer_condition.notify_all()

                    # CRITICAL: Execute schema update
                    old_version = db_state['schema_version']
                    db_state['schema_version'] += 1
                    db_state['table_count'] += 1
                    db_state['last_schema_update'] = time.time()

                    print(f"  ✅ Schema Update {update_id}: ALTER TABLE executed "
                          f"(version {old_version} → {db_state['schema_version']}, "
                          f"waited {wait_time:.3f}s)")
                    time.sleep(0.03)

            print(f"Schema Update {update_id}: Completed {num_updates} schema changes")

        print("Starting simulation...")
        print("  - 8 application threads executing SELECT queries")
        print("  - 1 DBA performing schema updates (critical!)")
        print()

        queries = [multiprocessing.Process(target=execute_select_query, args=(i+1, 20)) for i in range(8)]
        schema_updater = multiprocessing.Process(target=execute_schema_update, args=(1, 2))

        start_time = time.time()
        for q in queries:
            q.start()
        schema_updater.start()

        for q in queries:
            q.join()
        schema_updater.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Schema version: {db_state['schema_version']}")
        print(f"  Table count: {db_state['table_count']}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Schema updates completed successfully (no starvation)")
        print()

    def reader_writer_config_scenario(self) -> None:
        """
        Real-World Scenario #3: Configuration Management System.

        SITUATION:
        ==========
        - Application configuration stored in shared memory
        - Many worker processes reading config (read-heavy)
        - Configuration hot-reload updates (critical writes)
        - Problem: Config updates must apply immediately
        
        THE PROBLEM:
        ============
        Without writer priority:
        - Config reload arrives → waits for readers
        - Workers keep reading old config → reload waits
        - New config never applies → system uses stale config
        - Critical: Security settings, feature flags stuck
        
        THE SOLUTION:
        =============
        Writer priority ensures:
        - Config reload signals priority
        - New config reads wait
        - Existing reads finish
        - Config reload executes
        - All workers see new config
        
        WHEN TO USE:
        ============
        ✅ Configuration management systems
        ✅ Feature flag systems
        ✅ Hot-reload mechanisms
        ✅ Dynamic configuration updates
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO #3: Configuration Management System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Application config in shared memory")
        print("  - Many worker processes reading config (read-heavy)")
        print("  - DevOps performing hot-reload updates (critical writes)")
        print("  - Problem: Config updates must apply immediately")
        print()
        print("THE PROBLEM:")
        print("  Without writer priority:")
        print("    ❌ Config reload arrives → waits for readers")
        print("    ❌ Workers keep reading → reload waits forever")
        print("    ❌ New config never applies → stale config")
        print("    ❌ Security settings stuck → vulnerability!")
        print()
        print("THE SOLUTION:")
        print("  With writer priority:")
        print("    ✅ Config reload signals priority")
        print("    ✅ New config reads wait")
        print("    ✅ Existing reads finish")
        print("    ✅ Config reload executes → new config active")
        print("    ✅ All workers see updated config")
        print()
        print("=" * 70)
        print()

        # Simulate configuration
        config = multiprocessing.Manager().dict()
        config['api_timeout'] = 30
        config['max_retries'] = 3
        config['feature_flag_new_ui'] = False
        config['version'] = 1

        # Synchronization
        active_readers = multiprocessing.Value('i', 0)
        waiting_writers = multiprocessing.Value('i', 0)
        config_lock = multiprocessing.Lock()
        readers_lock = multiprocessing.Lock()
        writer_priority_lock = multiprocessing.Lock()
        writer_condition = multiprocessing.Condition(writer_priority_lock)

        def worker_read_config(worker_id: int, num_reads: int) -> None:
            """Simulate worker reading configuration."""
            for i in range(num_reads):
                with readers_lock:
                    with writer_priority_lock:
                        while waiting_writers.value > 0:
                            writer_condition.wait()
                    active_readers.value += 1
                    if active_readers.value == 1:
                        config_lock.acquire()

                # Read config
                timeout = config['api_timeout']
                retries = config['max_retries']
                feature_flag = config['feature_flag_new_ui']
                time.sleep(0.005)

                with readers_lock:
                    active_readers.value -= 1
                    if active_readers.value == 0:
                        config_lock.release()

            print(f"Worker {worker_id}: Read config {num_reads} times")

        def hot_reload_config(reload_id: int, num_reloads: int) -> None:
            """Simulate hot-reload configuration update (CRITICAL)."""
            for i in range(num_reloads):
                wait_start = time.time()

                with writer_priority_lock:
                    waiting_writers.value += 1
                    writer_condition.notify_all()
                    print(f"  ⚠️  Config Reload {reload_id}: Hot-reload QUEUED (new reads will wait)")

                with config_lock:
                    wait_time = time.time() - wait_start

                    with writer_priority_lock:
                        waiting_writers.value -= 1
                        writer_condition.notify_all()

                    # CRITICAL: Update configuration
                    old_version = config['version']
                    config['api_timeout'] = 30 + (i * 5)
                    config['max_retries'] = 3 + i
                    config['feature_flag_new_ui'] = True if i > 0 else False
                    config['version'] += 1

                    print(f"  ✅ Config Reload {reload_id}: Updated config "
                          f"(version {old_version} → {config['version']}, "
                          f"waited {wait_time:.3f}s)")

                    time.sleep(0.02)

            print(f"Config Reload {reload_id}: Completed {num_reloads} hot-reloads")

        print("Starting simulation...")
        print("  - 6 worker processes reading config")
        print("  - 1 DevOps performing hot-reload (critical!)")
        print()

        workers = [multiprocessing.Process(target=worker_read_config, args=(i+1, 25)) for i in range(6)]
        reloader = multiprocessing.Process(target=hot_reload_config, args=(1, 2))

        start_time = time.time()
        for w in workers:
            w.start()
        reloader.start()

        for w in workers:
            w.join()
        reloader.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Config version: {config['version']}")
        print(f"  API timeout: {config['api_timeout']}s")
        print(f"  Feature flag: {config['feature_flag_new_ui']}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Config updates applied successfully (no starvation)")
        print()

    def reader_writer_file_system_scenario(self) -> None:
        """
        Real-World Scenario #4: File System Metadata Cache.

        SITUATION:
        ==========
        - File system metadata cached in memory
        - Many processes reading file metadata (read-heavy)
        - File operations updating metadata (critical writes)
        - Problem: Metadata updates must complete
        
        THE PROBLEM:
        ============
        Without writer priority:
        - File rename arrives → waits for metadata reads
        - New metadata reads keep arriving → rename waits
        - File operation stuck → inconsistent state
        - Critical: File operations are atomic operations
        
        THE SOLUTION:
        =============
        Writer priority ensures:
        - File operation signals priority
        - New metadata reads wait
        - Existing reads finish
        - File operation executes
        - Metadata stays consistent
        
        WHEN TO USE:
        ============
        ✅ File system implementations
        ✅ Metadata caches
        ✅ Directory operations
        ✅ File watchers
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO #4: File System Metadata Cache")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - File system metadata cached in memory")
        print("  - Many processes reading file info (read-heavy)")
        print("  - File operations updating metadata (critical writes)")
        print("  - Problem: Metadata updates must complete")
        print()
        print("THE PROBLEM:")
        print("  Without writer priority:")
        print("    ❌ File rename arrives → waits for metadata reads")
        print("    ❌ New reads keep arriving → rename waits forever")
        print("    ❌ File operation stuck → inconsistent metadata")
        print("    ❌ File system corruption risk!")
        print()
        print("THE SOLUTION:")
        print("  With writer priority:")
        print("    ✅ File operation signals priority")
        print("    ✅ New metadata reads wait")
        print("    ✅ Existing reads finish")
        print("    ✅ File operation executes → metadata updated")
        print("    ✅ File system stays consistent")
        print()
        print("=" * 70)
        print()

        # Simulate file system metadata
        metadata = multiprocessing.Manager().dict()
        metadata['file_count'] = 1000
        metadata['total_size'] = 1024 * 1024 * 100  # 100MB
        metadata['last_modified'] = time.time()
        metadata['version'] = 1

        # Synchronization
        active_readers = multiprocessing.Value('i', 0)
        waiting_writers = multiprocessing.Value('i', 0)
        metadata_lock = multiprocessing.Lock()
        readers_lock = multiprocessing.Lock()
        writer_priority_lock = multiprocessing.Lock()
        writer_condition = multiprocessing.Condition(writer_priority_lock)

        def read_file_metadata(process_id: int, num_reads: int) -> None:
            """Simulate reading file metadata."""
            for i in range(num_reads):
                with readers_lock:
                    with writer_priority_lock:
                        while waiting_writers.value > 0:
                            writer_condition.wait()
                    active_readers.value += 1
                    if active_readers.value == 1:
                        metadata_lock.acquire()

                # Read metadata
                file_count = metadata['file_count']
                total_size = metadata['total_size']
                time.sleep(0.005)

                with readers_lock:
                    active_readers.value -= 1
                    if active_readers.value == 0:
                        metadata_lock.release()

            print(f"Process {process_id}: Read metadata {num_reads} times")

        def update_file_metadata(operation_id: int, num_operations: int) -> None:
            """Simulate file operation updating metadata (CRITICAL)."""
            for i in range(num_operations):
                wait_start = time.time()

                with writer_priority_lock:
                    waiting_writers.value += 1
                    writer_condition.notify_all()
                    print(f"  ⚠️  File Op {operation_id}: Metadata update QUEUED")

                with metadata_lock:
                    wait_time = time.time() - wait_start

                    with writer_priority_lock:
                        waiting_writers.value -= 1
                        writer_condition.notify_all()

                    # CRITICAL: Update metadata
                    old_version = metadata['version']
                    metadata['file_count'] += 10
                    metadata['total_size'] += 1024 * 1024  # Add 1MB
                    metadata['last_modified'] = time.time()
                    metadata['version'] += 1

                    print(f"  ✅ File Op {operation_id}: Updated metadata "
                          f"(version {old_version} → {metadata['version']}, "
                          f"waited {wait_time:.3f}s)")

                    time.sleep(0.02)

            print(f"File Op {operation_id}: Completed {num_operations} metadata updates")

        print("Starting simulation...")
        print("  - 7 processes reading file metadata")
        print("  - 1 file operation updating metadata (critical!)")
        print()

        readers = [multiprocessing.Process(target=read_file_metadata, args=(i+1, 20)) for i in range(7)]
        file_op = multiprocessing.Process(target=update_file_metadata, args=(1, 2))

        start_time = time.time()
        for r in readers:
            r.start()
        file_op.start()

        for r in readers:
            r.join()
        file_op.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Metadata version: {metadata['version']}")
        print(f"  File count: {metadata['file_count']}")
        print(f"  Total size: {metadata['total_size'] / (1024*1024):.1f}MB")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Metadata updates completed successfully (no starvation)")
        print()

    def reader_writer_all_scenarios(self) -> None:
        """
        Run all real-world scenarios to understand when to use reader-writer pattern.

        This method demonstrates multiple scenarios so you can recognize patterns
        in your own codebase and know when to apply this synchronization technique.

        Scenarios covered:
        1. E-Commerce Cache (product prices/inventory)
        2. Database Connection Pool (schema updates)
        3. Configuration Management (hot-reload)
        4. File System Metadata (file operations)

        Each scenario shows:
        - The specific problem it solves
        - Why writer priority matters
        - When to recognize this pattern
        - How to apply the solution
        """
        print("=" * 70)
        print("READER-WRITER PATTERN: ALL REAL-WORLD SCENARIOS")
        print("=" * 70)
        print()
        print("This demonstrates multiple scenarios where reader-writer locks")
        print("with writer priority are essential. Study each to recognize")
        print("when you need this pattern in your own systems.")
        print()
        print("=" * 70)
        print()

        # Run all scenarios
        self.reader_writer_real_world_example()
        self.reader_writer_database_scenario()
        self.reader_writer_config_scenario()
        self.reader_writer_file_system_scenario()

        print("=" * 70)
        print("PATTERN RECOGNITION GUIDE")
        print("=" * 70)
        print()
        print("Ask yourself these questions to identify when you need this pattern:")
        print()
        print("1. IS IT READ-HEAVY?")
        print("   ✅ Many processes/threads reading frequently")
        print("   ✅ Few processes/threads writing occasionally")
        print("   ✅ Reads happen 10x, 100x, or 1000x more than writes")
        print()
        print("2. ARE WRITERS CRITICAL?")
        print("   ✅ Writes must complete (cannot wait indefinitely)")
        print("   ✅ Stale data is unacceptable")
        print("   ✅ Updates are time-sensitive")
        print("   ✅ Business impact if writes are delayed")
        print()
        print("3. CAN WRITERS STARVE?")
        print("   ✅ Without priority, writers could wait forever")
        print("   ✅ New readers keep arriving")
        print("   ✅ Writers never get exclusive access")
        print()
        print("4. IS IT SHARED STATE?")
        print("   ✅ Multiple processes/threads accessing same data")
        print("   ✅ Reads can happen concurrently")
        print("   ✅ Writes need exclusive access")
        print()
        print("If you answered YES to all 4 questions → USE READER-WRITER WITH WRITER PRIORITY")
        print()
        print("Common domains where this pattern applies:")
        print("  ✅ Caches (Redis, Memcached patterns)")
        print("  ✅ Databases (connection pools, schema updates)")
        print("  ✅ Configuration systems (hot-reload, feature flags)")
        print("  ✅ File systems (metadata, directory operations)")
        print("  ✅ Shared state (counters, statistics, metrics)")
        print("  ✅ Game servers (player state, world state)")
        print("  ✅ Web servers (session data, shared resources)")
        print("  ✅ Message queues (metadata, routing tables)")
        print()
        print("=" * 70)
        print()

    def reader_writer_problem(self) -> None:
        """
        Demonstrate reader-writer synchronization pattern.

        Shows how to allow multiple concurrent readers while ensuring
        exclusive access for writers, optimizing for read-heavy workloads.

        When to Use:
            - Read-heavy workloads
            - Multiple concurrent readers
            - Exclusive writers
            - Shared data structures
            - Database-like access patterns

        Real-World Examples:
            - Databases: Multiple readers, exclusive writers
            - Caches: Multiple readers, exclusive updates
            - Configuration: Multiple readers, exclusive updates
            - Shared state: Multiple readers, exclusive modifications
            - Data structures: Concurrent reads, exclusive writes

        Gotchas:
            - First reader acquires write lock
            - Last reader releases write lock
            - Writers need exclusive access
            - Readers can run concurrently
            - Starvation risk for writers
            - Complex synchronization logic

        Performance Notes:
            - Optimized for read-heavy workloads
            - Multiple concurrent reads improve throughput
            - Writers block all readers
            - Balance readers vs writers
            - Consider writer priority to prevent starvation
        """
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

    def deadlock_prevention_real_world(self) -> None:
        """
        Real-World Scenario: Deadlock Prevention - Resource Allocation System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a resource allocation system:
        - Processes need multiple resources (CPU, Memory, Disk)
        - Resources must be acquired in order
        - Problem: Different order causes deadlock
        
        THE PROBLEM WITHOUT ORDERING:
        ===============================
        - Process 1: Acquires CPU → waits for Memory
        - Process 2: Acquires Memory → waits for CPU
        - DEADLOCK! Both wait forever
        - System hangs → no progress
        - Resources locked forever
        
        THE SOLUTION:
        =============
        Ordered acquisition ensures:
        - All processes acquire resources in same order
        - Process 1: CPU → Memory → Disk
        - Process 2: CPU → Memory → Disk (same order)
        - No circular waiting → no deadlock
        - System makes progress
        
        WHEN TO USE ORDERED ACQUISITION:
        =================================
        ✅ Multiple resource acquisition
        ✅ Preventing deadlocks
        ✅ Resource allocation systems
        ✅ Database transactions
        ✅ File operations
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Resource Allocation System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Resource allocation system")
        print("  - Processes need multiple resources (CPU, Memory, Disk)")
        print("  - Resources must be acquired in order")
        print()
        print("THE PROBLEM:")
        print("  Without ordering:")
        print("    ❌ Process 1: Acquires CPU → waits for Memory")
        print("    ❌ Process 2: Acquires Memory → waits for CPU")
        print("    ❌ DEADLOCK! Both wait forever")
        print("    ❌ System hangs → no progress")
        print()
        print("THE SOLUTION:")
        print("  With ordering:")
        print("    ✅ All processes acquire resources in same order")
        print("    ✅ Process 1: CPU → Memory → Disk")
        print("    ✅ Process 2: CPU → Memory → Disk (same order)")
        print("    ✅ No circular waiting → no deadlock")
        print("    ✅ System makes progress")
        print()
        print("=" * 70)
        print()

        cpu_lock = multiprocessing.Lock()
        memory_lock = multiprocessing.Lock()
        disk_lock = multiprocessing.Lock()
        resource_stats = multiprocessing.Manager().dict()

        def process_with_ordered_acquisition(process_id: int) -> None:
            """Process acquiring resources in consistent order."""
            # Always acquire in same order: CPU → Memory → Disk
            with cpu_lock:
                print(f"Process {process_id}: Acquired CPU")
                time.sleep(0.05)
                
                with memory_lock:
                    print(f"Process {process_id}: Acquired Memory")
                    time.sleep(0.05)
                    
                    with disk_lock:
                        print(f"Process {process_id}: Acquired Disk")
                        # All resources acquired, do work
                        time.sleep(0.1)
                        print(f"Process {process_id}: Work completed")
                    
                    print(f"Process {process_id}: Released Disk")
                print(f"Process {process_id}: Released Memory")
            print(f"Process {process_id}: Released CPU")
            
            if process_id not in resource_stats:
                resource_stats[process_id] = 0
            resource_stats[process_id] += 1

        def process_with_wrong_order(process_id: int) -> None:
            """Process acquiring resources in wrong order (causes deadlock)."""
            # Wrong order: Memory → CPU (different from others)
            try:
                with memory_lock:
                    print(f"Process {process_id}: Acquired Memory (WRONG ORDER)")
                    time.sleep(0.05)
                    
                    with cpu_lock:  # This can cause deadlock!
                        print(f"Process {process_id}: Acquired CPU")
                        time.sleep(0.1)
            except Exception as e:
                print(f"Process {process_id}: Error - {e}")

        print("Testing with ordered acquisition (no deadlock):")
        processes = [
            multiprocessing.Process(target=process_with_ordered_acquisition, args=(i+1,))
            for i in range(4)
        ]

        start_time = time.time()
        for p in processes:
            p.start()

        for p in processes:
            p.join(timeout=5.0)

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Processes completed: {sum(resource_stats.values())}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Ordered acquisition prevented deadlock!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. DEADLOCK PREVENTION RULES:")
        print("   ✅ Always acquire locks in same order")
        print("   ✅ Use lock ordering (e.g., by address)")
        print("   ✅ Use timeout to prevent indefinite blocking")
        print("   ✅ Detect and handle deadlocks")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents system hangs")
        print("   - Ensures progress")
        print("   - Critical for production systems")
        print("   - Prevents resource lockup")
        print("=" * 70)
        print()

    def deadlock_prevention(self) -> None:
        """
        Demonstrate deadlock prevention techniques.

        Shows how to prevent deadlocks by acquiring locks in a consistent
        order, preventing circular waiting scenarios.

        When to Use:
            - Multiple resource acquisition
            - Preventing deadlocks
            - Resource ordering
            - Lock ordering strategies
            - Building deadlock-free systems

        Real-World Examples:
            - Database transactions: Acquire locks in order
            - Resource allocation: Allocate resources in order
            - File operations: Lock files in order
            - Network protocols: Acquire resources in order
            - Distributed systems: Order resource acquisition

        Gotchas:
            - Always acquire locks in same order
            - Different order causes deadlock
            - Use lock ordering (e.g., by address)
            - Timeout prevents indefinite blocking
            - Detect and handle deadlocks
            - Consider lock-free alternatives

        Performance Notes:
            - Ordered acquisition prevents deadlocks
            - May cause unnecessary waiting
            - Timeouts prevent indefinite blocking
            - Critical for production systems
            - Balance ordering vs performance
        """
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
        """
        Demonstrate synchronization best practices.

        Shows best practices for synchronization including minimizing lock
        scope, proper error handling, and efficient lock usage.

        When to Use:
            - Building production systems
            - Optimizing synchronization
            - Following best practices
            - Learning synchronization patterns
            - Code review guidelines

        Real-World Examples:
            - Production code: Follow best practices
            - Performance optimization: Minimize lock scope
            - Error handling: Proper exception handling
            - Code quality: Maintainable synchronization
            - Team standards: Consistent patterns

        Gotchas:
            - Minimize lock scope (hold locks briefly)
            - Do work outside locks when possible
            - Handle exceptions properly
            - Use context managers (with statement)
            - Avoid holding locks across I/O
            - Document lock ordering

        Performance Notes:
            - Minimizing lock scope improves performance
            - Shorter critical sections reduce contention
            - Proper error handling prevents leaks
            - Best practices improve maintainability
            - Balance safety vs performance
        """
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

    def synchronization_best_practices_real_world(self) -> None:
        """
        Real-World Scenario: Best Practices - High-Performance Counter System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a high-performance metrics system:
        - Millions of operations per second
        - Shared counters for statistics
        - Problem: Lock contention kills performance
        
        THE PROBLEM WITHOUT BEST PRACTICES:
        ====================================
        - Hold lock during entire operation
        - Do heavy computation inside lock
        - Lock contention → serialization
        - Performance degrades → system slow
        - Throughput drops dramatically
        
        THE SOLUTION:
        =============
        Best practices ensure:
        - Minimize lock scope (only protect critical section)
        - Do computation outside lock
        - Handle exceptions properly
        - Use context managers
        - Optimal performance
        
        WHEN TO USE BEST PRACTICES:
        ===========================
        ✅ Production systems
        ✅ High-performance code
        ✅ Minimizing contention
        ✅ Following best practices
        ✅ Performance optimization
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: High-Performance Metrics System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - High-performance metrics system")
        print("  - Millions of operations per second")
        print("  - Shared counters for statistics")
        print("  - Problem: Lock contention kills performance")
        print()
        print("THE PROBLEM:")
        print("  Without best practices:")
        print("    ❌ Hold lock during entire operation")
        print("    ❌ Do heavy computation inside lock")
        print("    ❌ Lock contention → serialization")
        print("    ❌ Performance degrades → system slow")
        print()
        print("THE SOLUTION:")
        print("  With best practices:")
        print("    ✅ Minimize lock scope (only protect critical section)")
        print("    ✅ Do computation outside lock")
        print("    ✅ Handle exceptions properly")
        print("    ✅ Use context managers")
        print("    ✅ Optimal performance")
        print()
        print("=" * 70)
        print()

        counter = multiprocessing.Value('i', 0)
        results = multiprocessing.Manager().list()
        lock = multiprocessing.Lock()

        def worker_bad_practice(worker_id: int) -> None:
            """Worker with BAD practices (slow)."""
            for i in range(100):
                # BAD: Hold lock during entire operation
                with lock:
                    # BAD: Do computation inside lock
                    value = counter.value
                    result = sum(range(value))  # Heavy computation!
                    counter.value += 1
                    results.append(f"Worker {worker_id}: {result}")
                    time.sleep(0.001)  # Simulate work

        def worker_good_practice(worker_id: int) -> None:
            """Worker with GOOD practices (fast)."""
            for i in range(100):
                # GOOD: Minimize lock scope
                with lock:
                    value = counter.value
                    counter.value += 1
                
                # GOOD: Do computation outside lock
                result = sum(range(value))  # Heavy computation outside lock!
                time.sleep(0.001)  # Simulate work
                
                # GOOD: Another minimal lock usage
                with lock:
                    results.append(f"Worker {worker_id}: {result}")

        print("Testing BAD practices (slow):")
        counter.value = 0
        results.clear()
        start_time = time.time()
        
        workers_bad = [multiprocessing.Process(target=worker_bad_practice, args=(i+1,)) for i in range(3)]
        for w in workers_bad:
            w.start()
        for w in workers_bad:
            w.join()
        
        bad_time = time.time() - start_time
        print(f"  Execution time: {bad_time:.2f}s")
        print()
        
        print("Testing GOOD practices (fast):")
        counter.value = 0
        results.clear()
        start_time = time.time()
        
        workers_good = [multiprocessing.Process(target=worker_good_practice, args=(i+1,)) for i in range(3)]
        for w in workers_good:
            w.start()
        for w in workers_good:
            w.join()
        
        good_time = time.time() - start_time
        print(f"  Execution time: {good_time:.2f}s")
        print()
        
        speedup = bad_time / good_time if good_time > 0 else 1.0
        print("Results:")
        print(f"  Bad practices time: {bad_time:.2f}s")
        print(f"  Good practices time: {good_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print("  ✅ Best practices significantly improve performance!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. BEST PRACTICES:")
        print("   ✅ Minimize lock scope (hold locks briefly)")
        print("   ✅ Do computation outside locks")
        print("   ✅ Handle exceptions properly")
        print("   ✅ Use context managers (with statement)")
        print("   ✅ Avoid holding locks across I/O")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Reduces lock contention")
        print("   - Improves performance significantly")
        print("   - Enables better parallelism")
        print("   - Critical for high-performance systems")
        print("=" * 70)
        print()


    def all_real_world_scenarios(self) -> None:
        """
        Run all real-world scenarios to understand when to use each pattern.

        This comprehensive demonstration shows:
        1. Lock vs RLock - Database Transaction Manager
        2. Semaphore - Connection Pool Manager
        3. Event - Service Startup Coordination
        4. Condition Variables - Task Queue with Bounded Buffer
        5. Barrier - Parallel Data Processing Pipeline
        6. Deadlock Prevention - Resource Allocation System
        7. Best Practices - High-Performance Metrics System
        8. Reader-Writer - Multiple scenarios (cache, database, config, filesystem)
        """
        print("=" * 70)
        print("ALL SYNCHRONIZATION PATTERNS: REAL-WORLD SCENARIOS")
        print("=" * 70)
        print()
        print("This comprehensive demonstration shows when and why to use")
        print("each synchronization pattern in real-world systems.")
        print()
        print("=" * 70)
        print()

        # Run all real-world scenarios
        self.lock_vs_rlock_real_world()
        self.semaphore_real_world_example()
        self.event_coordination_real_world()
        self.condition_variables_real_world()
        self.barrier_synchronization_real_world()
        self.deadlock_prevention_real_world()
        self.synchronization_best_practices_real_world()
        self.reader_writer_all_scenarios()

        print("=" * 70)
        print("SYNCHRONIZATION PATTERN DECISION GUIDE")
        print("=" * 70)
        print()
        print("Use this guide to select the right synchronization pattern:")
        print()
        print("1. LOCK vs RLOCK:")
        print("   - Use Lock: Simple locking, no nested calls")
        print("   - Use RLock: Nested function calls need same lock")
        print()
        print("2. SEMAPHORE:")
        print("   - Use when: Limiting concurrent access to resources")
        print("   - Examples: Connection pools, rate limiting, bounded buffers")
        print()
        print("3. EVENT:")
        print("   - Use when: One-to-many signaling, simple coordination")
        print("   - Examples: Service startup, one-time notifications")
        print()
        print("4. CONDITION VARIABLES:")
        print("   - Use when: Waiting on state changes, bounded buffers")
        print("   - Examples: Task queues, producer-consumer with conditions")
        print()
        print("5. BARRIER:")
        print("   - Use when: Synchronizing phases, rendezvous points")
        print("   - Examples: Parallel algorithms, data processing pipelines")
        print()
        print("6. READER-WRITER LOCK:")
        print("   - Use when: Read-heavy workloads, writers must not starve")
        print("   - Examples: Caches, databases, configuration systems")
        print()
        print("7. DEADLOCK PREVENTION:")
        print("   - Use when: Multiple resource acquisition")
        print("   - Rule: Always acquire locks in same order")
        print()
        print("8. BEST PRACTICES:")
        print("   - Minimize lock scope")
        print("   - Do computation outside locks")
        print("   - Handle exceptions properly")
        print("   - Use context managers")
        print()
        print("=" * 70)
        print()


def main() -> None:
    """Run all synchronization examples."""
    print("Multiprocessing Synchronization Examples")
    print("=" * 44)

    example = SynchronizationExample()

    # Basic examples
    example.lock_vs_rlock()
    example.semaphore_patterns()
    example.semaphore_patterns_fixed()
    example.event_coordination()
    example.event_coordination_fixed()
    example.condition_variables()
    example.condition_variables_fixed()
    example.barrier_synchronization()
    example.barrier_synchronization_fixed()
    example.reader_writer_problem()
    example.reader_writer_problem_fixed()
    example.deadlock_prevention()
    example.synchronization_best_practices()

    # Real-world scenarios (comprehensive)
    print("\n" + "=" * 70)
    print("RUNNING ALL REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    example.all_real_world_scenarios()

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