"""
Queues and Pipes examples for inter-process communication.

This module covers:
- multiprocessing.Queue for process-safe communication
- multiprocessing.Pipe for direct process-to-process communication
- JoinableQueue for producer-consumer patterns
- PriorityQueue for ordered message processing
- Message passing patterns and best practices
"""

import multiprocessing
import os
import time
from typing import Any, List, Tuple


class QueuePipeExample:
    """
    Examples of queues and pipes for inter-process communication.

    This class demonstrates IPC mechanisms for multiprocessing including
    queues (Queue, JoinableQueue, PriorityQueue) and pipes (unidirectional
    and duplex) with proper synchronization and error handling.

    When to Use:
        - Communicating between processes
        - Producer-consumer patterns
        - Task distribution and collection
        - Direct process-to-process communication
        - Ordered message processing

    Real-World Examples:
        - Task queues: Distribute tasks to worker processes
        - Result collection: Collect results from workers
        - Message passing: Pass messages between processes
        - Pipeline stages: Connect pipeline stages
        - Worker coordination: Coordinate worker processes

    Gotchas:
        - Queues are process-safe (thread-safe too)
        - Pipes are faster but less flexible than queues
        - Use sentinels (None) for graceful shutdown
        - JoinableQueue requires task_done() calls
        - Queue.get() blocks until data available
        - Pipe.recv() blocks until data available
        - Always close pipes when done

    Performance Notes:
        - Queues use pickling (slower but flexible)
        - Pipes are faster for small data
        - Queue overhead increases with data size
        - Bounded queues prevent memory issues
        - Timeouts prevent indefinite blocking
    """

    def basic_queue_example(self) -> None:
        """
        Demonstrate basic queue usage.

        Shows basic producer-consumer pattern using multiprocessing.Queue
        for simple inter-process communication.

        When to Use:
            - Simple producer-consumer patterns
            - One-to-one process communication
            - Learning queue basics
            - Simple message passing

        Real-World Examples:
            - Data processing: Producer generates data, consumer processes
            - Task queues: Producer adds tasks, consumer processes
            - Log aggregation: Producer generates logs, consumer aggregates
            - Event processing: Producer generates events, consumer processes

        Gotchas:
            - Queue.get() blocks until data available
            - Use sentinel (None) for graceful shutdown
            - Queue is process-safe and thread-safe
            - Items are pickled/unpickled automatically
            - Queue size affects memory usage

        Performance Notes:
            - Queue overhead for pickling/unpickling
            - Good for moderate data sizes
            - Bounded queues prevent memory issues
            - Optimal for producer-consumer patterns
        """
        print("=== Basic Queue Usage ===")

        def producer(queue: multiprocessing.Queue) -> None:
            """Producer process."""
            for i in range(5):
                item = f"Item {i+1}"
                queue.put(item)
                print(f"Produced: {item}")
                time.sleep(0.1)

            # Signal end of production
            queue.put(None)

        def consumer(queue: multiprocessing.Queue) -> None:
            """Consumer process."""
            while True:
                item = queue.get()
                if item is None:  # End signal
                    break
                print(f"Consumed: {item}")
                time.sleep(0.2)

        # Create queue
        queue = multiprocessing.Queue()

        # Create producer and consumer
        producer_process = multiprocessing.Process(target=producer, args=(queue,))
        consumer_process = multiprocessing.Process(target=consumer, args=(queue,))

        # Start processes
        producer_process.start()
        consumer_process.start()

        # Wait for completion
        producer_process.join()
        consumer_process.join()

        print("Queue communication completed!\n")

    def multiple_producers_consumers(self) -> None:
        """
        Demonstrate multiple producers and consumers with a queue.

        Shows how multiple producers can feed a single queue and multiple
        consumers can process items concurrently.

        When to Use:
            - Multiple data sources
            - Parallel processing of items
            - Load balancing across consumers
            - Scaling producer-consumer patterns
            - Distributed work processing

        Real-World Examples:
            - Web scraping: Multiple scrapers feed queue, workers process
            - Data ingestion: Multiple sources feed queue, processors consume
            - Task distribution: Multiple task generators, worker pool consumes
            - Log processing: Multiple log sources, aggregators consume
            - Event processing: Multiple event sources, processors consume

        Gotchas:
            - Need sentinel per producer for consumers
            - Consumers must track sentinel count
            - Queue is shared safely across processes
            - Load balancing is automatic
            - Consumers process items concurrently

        Performance Notes:
            - Multiple consumers improve throughput
            - Queue contention increases with many processes
            - Optimal consumer count depends on workload
            - Balance producers vs consumers
        """
        print("=== Multiple Producers and Consumers ===")

        def producer(producer_id: int, queue: multiprocessing.Queue, items_per_producer: int) -> None:
            """Producer process."""
            for i in range(items_per_producer):
                item = f"P{producer_id}-Item{i+1}"
                queue.put(item)
                print(f"Producer {producer_id}: {item}")
                time.sleep(0.05)

        def consumer(consumer_id: int, queue: multiprocessing.Queue, sentinel_count: int) -> None:
            """Consumer process."""
            sentinels_received = 0
            while sentinels_received < sentinel_count:
                item = queue.get()
                if item is None:
                    sentinels_received += 1
                else:
                    print(f"Consumer {consumer_id}: {item}")
                    time.sleep(0.1)

        # Configuration
        num_producers = 3
        num_consumers = 2
        items_per_producer = 4

        # Create queue
        queue = multiprocessing.Queue()

        # Create producers
        producers = []
        for i in range(num_producers):
            p = multiprocessing.Process(target=producer, args=(i+1, queue, items_per_producer))
            producers.append(p)

        # Create consumers
        consumers = []
        for i in range(num_consumers):
            p = multiprocessing.Process(target=consumer, args=(i+1, queue, num_producers))
            consumers.append(p)

        # Start all processes
        for p in producers + consumers:
            p.start()

        # Wait for producers to finish
        for p in producers:
            p.join()

        # Send end signals to consumers
        for _ in range(num_producers):
            queue.put(None)

        # Wait for consumers to finish
        for p in consumers:
            p.join()

        print("Multiple producer-consumer communication completed!\n")

    def joinable_queue_example(self) -> None:
        """
        Demonstrate JoinableQueue for task coordination.

        Shows how JoinableQueue enables coordination between producers
        and consumers, ensuring all tasks are processed before proceeding.

        When to Use:
            - Ensuring all tasks complete
            - Task coordination
            - Producer-consumer with guarantees
            - Batch processing with completion tracking
            - Work distribution with verification

        Real-World Examples:
            - Batch processing: Process batch, wait for completion
            - Task queues: Submit tasks, wait for all to complete
            - Data processing: Process data, verify completion
            - Work distribution: Distribute work, collect all results
            - Pipeline stages: Process stage, wait for completion

        Gotchas:
            - Must call task_done() for each get()
            - join() blocks until all tasks done
            - Poison pills (None) need task_done() too
            - Forgetting task_done() causes hang
            - Use poison pills for worker shutdown

        Performance Notes:
            - Enables deterministic completion
            - Useful for batch processing
            - Overhead minimal
            - Critical for coordination
        """
        print("=== JoinableQueue Example ===")

        def task_processor(task_queue: multiprocessing.JoinableQueue,
                          result_queue: multiprocessing.Queue) -> None:
            """Process tasks from queue."""
            while True:
                task = task_queue.get()
                if task is None:  # Poison pill
                    task_queue.task_done()
                    break

                # Process task (simulate work)
                result = f"Processed: {task}"
                print(f"Processing: {task}")
                time.sleep(0.1)

                result_queue.put(result)
                task_queue.task_done()

        # Create queues
        task_queue = multiprocessing.JoinableQueue()
        result_queue = multiprocessing.Queue()

        # Create worker processes
        num_workers = 3
        workers = []

        for i in range(num_workers):
            p = multiprocessing.Process(target=task_processor, args=(task_queue, result_queue))
            workers.append(p)
            p.start()

        # Add tasks
        tasks = [f"Task {i+1}" for i in range(9)]
        for task in tasks:
            task_queue.put(task)

        # Add poison pills
        for _ in range(num_workers):
            task_queue.put(None)

        # Wait for all tasks to be processed
        task_queue.join()

        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # Wait for workers to finish
        for p in workers:
            p.join()

        print(f"Processed {len(results)} tasks:")
        for result in sorted(results):
            print(f"  {result}")

        print()

    def priority_queue_example(self) -> None:
        """
        Demonstrate PriorityQueue for ordered processing.

        Shows how to implement priority-based processing using a regular
        Queue with priority tuples (lower number = higher priority).

        When to Use:
            - Priority-based task processing
            - Ordered message processing
            - Task scheduling
            - Critical task prioritization
            - Resource allocation

        Real-World Examples:
            - Task scheduling: Process high-priority tasks first
            - Job queues: Prioritize urgent jobs
            - Message processing: Process critical messages first
            - Resource allocation: Allocate resources by priority
            - Event processing: Process critical events first

        Gotchas:
            - Lower number = higher priority (standard)
            - Use tuples (priority, item) for sorting
            - PriorityQueue sorts automatically
            - Regular Queue requires manual sorting
            - End signal needs highest priority

        Performance Notes:
            - PriorityQueue overhead for sorting
            - Useful for priority-based processing
            - Overhead minimal for small queues
            - Consider heap for large queues
        """
        print("=== PriorityQueue Example ===")

        def priority_processor(priority_queue: multiprocessing.Queue) -> None:
            """Process items by priority."""
            processed = []
            while True:
                item = priority_queue.get()
                if item[0] == -1:  # End signal (highest priority)
                    break

                priority, task = item
                processed.append(f"Priority {priority}: {task}")
                print(f"Processed: {task} (priority: {priority})")
                time.sleep(0.05)

            # Send results back
            priority_queue.put(processed)

        # Create priority queue (using regular Queue to store tuples)
        priority_queue = multiprocessing.Queue()

        # Create processor
        processor = multiprocessing.Process(target=priority_processor, args=(priority_queue,))
        processor.start()

        # Add tasks with different priorities (lower number = higher priority)
        tasks = [
            (3, "Low priority task"),
            (1, "High priority task"),
            (2, "Medium priority task"),
            (1, "Another high priority task"),
            (3, "Another low priority task"),
            (2, "Another medium priority task")
        ]

        # Add tasks (PriorityQueue would sort automatically, but we simulate)
        for task in tasks:
            priority_queue.put(task)
            print(f"Added: {task[1]} (priority: {task[0]})")
            time.sleep(0.02)

        # Send end signal
        priority_queue.put((-1, "END"))

        # Get results
        processor.join()
        results = priority_queue.get()

        print("\nProcessing order:")
        for result in results:
            print(f"  {result}")

        print()

    def pipe_example(self) -> None:
        """
        Demonstrate Pipe for direct process communication.

        Shows unidirectional pipe communication between parent and child
        processes. Faster than queues but less flexible.

        When to Use:
            - Direct process-to-process communication
            - Parent-child communication
            - Unidirectional data flow
            - Low-latency communication
            - Simple message passing

        Real-World Examples:
            - Parent-child coordination: Parent sends commands to child
            - Data streaming: Stream data from parent to child
            - Command processing: Send commands, receive responses
            - Pipeline stages: Connect stages with pipes
            - Process control: Control child processes

        Gotchas:
            - Unidirectional (one end sends, other receives)
            - recv() blocks until data available
            - send() blocks if buffer full
            - Must close both ends when done
            - Faster than Queue for small data
            - Less flexible than Queue

        Performance Notes:
            - Faster than Queue for small data
            - Lower overhead than Queue
            - Good for parent-child communication
            - Optimal for unidirectional flow
        """
        print("=== Pipe Example ===")

        def pipe_sender(conn: multiprocessing.Pipe) -> None:
            """Send data through pipe."""
            messages = ["Hello", "from", "the", "sender", "process!"]

            for msg in messages:
                conn.send(msg)
                print(f"Sent: {msg}")
                time.sleep(0.1)

            conn.send(None)  # End signal
            conn.close()

        def pipe_receiver(conn: multiprocessing.Pipe) -> None:
            """Receive data from pipe."""
            while True:
                msg = conn.recv()
                if msg is None:
                    break
                print(f"Received: {msg}")
                time.sleep(0.15)

            conn.close()

        # Create pipe
        parent_conn, child_conn = multiprocessing.Pipe()

        # Create child process
        child = multiprocessing.Process(target=pipe_receiver, args=(child_conn,))
        child.start()

        # Parent sends data
        pipe_sender(parent_conn)

        # Wait for child
        child.join()

        print("Pipe communication completed!\n")

    def duplex_pipe_example(self) -> None:
        """
        Demonstrate duplex pipe communication.

        Shows bidirectional pipe communication where both ends can send
        and receive, enabling request-response patterns.

        When to Use:
            - Bidirectional communication
            - Request-response patterns
            - Interactive process communication
            - Two-way data exchange
            - Process coordination

        Real-World Examples:
            - Request-response: Send request, receive response
            - Interactive processes: Two-way communication
            - Process coordination: Coordinate between processes
            - Command processing: Send commands, receive results
            - Client-server: Client-server communication

        Gotchas:
            - Both ends can send and receive
            - recv() blocks until data available
            - send() blocks if buffer full
            - Must close both ends when done
            - Faster than Queue for small data
            - Deadlock risk if both sides wait

        Performance Notes:
            - Faster than Queue for small data
            - Lower overhead than Queue
            - Good for bidirectional communication
            - Optimal for request-response patterns
        """
        print("=== Duplex Pipe Example ===")

        def duplex_worker(conn: multiprocessing.Pipe) -> None:
            """Worker that sends and receives through pipe."""
            # Receive initial message
            msg = conn.recv()
            print(f"Worker received: {msg}")

            # Process and respond
            response = f"Processed: {msg.upper()}"
            conn.send(response)
            print(f"Worker sent: {response}")

            # Receive another message
            msg2 = conn.recv()
            print(f"Worker received: {msg2}")

            # Send final response
            conn.send(f"Final response to: {msg2}")
            conn.close()

        # Create duplex pipe
        parent_conn, child_conn = multiprocessing.Pipe(duplex=True)

        # Create worker
        worker = multiprocessing.Process(target=duplex_worker, args=(child_conn,))
        worker.start()

        # Parent communication
        parent_conn.send("Hello Worker")
        response1 = parent_conn.recv()
        print(f"Parent received: {response1}")

        parent_conn.send("Another message")
        response2 = parent_conn.recv()
        print(f"Parent received: {response2}")

        parent_conn.close()
        worker.join()

        print("Duplex pipe communication completed!\n")

    def queue_timeout_example(self) -> None:
        """
        Demonstrate queue operations with timeouts.

        Shows how to use timeouts with queue operations to prevent
        indefinite blocking and handle slow producers/consumers.

        When to Use:
            - Preventing indefinite blocking
            - Handling slow producers/consumers
            - Timeout-based error handling
            - Graceful degradation
            - Production systems

        Real-World Examples:
            - Timeout handling: Prevent indefinite waits
            - Error recovery: Handle slow processes
            - Graceful shutdown: Timeout on shutdown
            - Production systems: Robust timeout handling
            - Resource management: Free resources on timeout

        Gotchas:
            - put() timeout if queue full
            - get() timeout if queue empty
            - Timeout exceptions are different
            - Handle timeout exceptions properly
            - Use bounded queues with timeouts
            - Timeouts prevent deadlocks

        Performance Notes:
            - Timeouts prevent indefinite blocking
            - Critical for production systems
            - Overhead minimal
            - Enables graceful degradation
        """
        print("=== Queue Timeout Example ===")

        def timeout_producer(queue: multiprocessing.Queue) -> None:
            """Producer with timeout handling."""
            items = ["A", "B", "C"]

            for item in items:
                try:
                    queue.put(item, timeout=2)  # 2 second timeout
                    print(f"Produced: {item}")
                except Exception as e:
                    print(f"Failed to produce {item}: {e}")
                time.sleep(0.5)

        def timeout_consumer(queue: multiprocessing.Queue, expected_items: int) -> None:
            """Consumer with timeout handling and proper shutdown."""
            items_consumed = 0
            from queue import Empty
            
            while items_consumed < expected_items:
                try:
                    item = queue.get(timeout=3)  # 3 second timeout
                    print(f"Consumed: {item}")
                    items_consumed += 1
                except Empty:
                    print(f"Timeout: No item received within 3 seconds (consumed {items_consumed}/{expected_items})")
                        break
                except Exception as e:
                    print(f"Error: {e}")
                    break

        # Create queue
        queue = multiprocessing.Queue(maxsize=2)  # Small queue to demonstrate blocking

        # Create processes
        expected_items = 3  # Number of items producer will create
        producer = multiprocessing.Process(target=timeout_producer, args=(queue,))
        consumer = multiprocessing.Process(target=timeout_consumer, args=(queue, expected_items))

        # Start consumer first (will wait for items)
        consumer.start()
        producer.start()

        producer.join()
        consumer.join()

        print("Timeout example completed!\n")

    def message_passing_patterns(self) -> None:
        """
        Demonstrate common message passing patterns.

        Shows request-response pattern using queues for client-server
        style communication between processes.

        When to Use:
            - Request-response patterns
            - Client-server communication
            - Service patterns
            - Command processing
            - RPC-style communication

        Real-World Examples:
            - Service processes: Process requests, send responses
            - Command processing: Process commands, return results
            - RPC: Remote procedure calls between processes
            - API servers: Process API requests, return responses
            - Worker coordination: Coordinate workers with requests

        Gotchas:
            - Need separate request and response queues
            - Server must handle multiple clients
            - Response matching can be complex
            - Use QUIT signal for graceful shutdown
            - Handle client disconnection
            - Queue ordering matters

        Performance Notes:
            - Request-response adds latency
            - Useful for service patterns
            - Overhead for queue operations
            - Good for structured communication
        """
        print("=== Message Passing Patterns ===")

        # Pattern 1: Request-Response
        def request_response_server(request_queue: multiprocessing.Queue,
                                   response_queue: multiprocessing.Queue) -> None:
            """Server that processes requests and sends responses."""
            while True:
                request = request_queue.get()
                if request == "QUIT":
                    break

                # Process request
                response = f"Response to: {request}"
                response_queue.put(response)
                print(f"Server: {response}")

        def request_response_client(client_id: int, request_queue: multiprocessing.Queue,
                                  response_queue: multiprocessing.Queue) -> None:
            """Client that sends requests and receives responses."""
            requests = [f"Request {i+1} from client {client_id}" for i in range(2)]

            for request in requests:
                request_queue.put(request)
                response = response_queue.get()
                print(f"Client {client_id}: {response}")
                time.sleep(0.1)

        # Create queues
        request_queue = multiprocessing.Queue()
        response_queue = multiprocessing.Queue()

        # Start server
        server = multiprocessing.Process(target=request_response_server,
                                       args=(request_queue, response_queue))
        server.start()

        # Start clients
        clients = []
        for i in range(2):
            client = multiprocessing.Process(target=request_response_client,
                                           args=(i+1, request_queue, response_queue))
            clients.append(client)
            client.start()

        # Wait for clients
        for client in clients:
            client.join()

        # Stop server
        request_queue.put("QUIT")
        server.join()

        print("Request-response pattern completed!\n")

    def queue_real_world_example(self) -> None:
        """
        Real-World Scenario: Queue - Log Aggregation System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a log aggregation system:
        - Multiple services generating logs
        - Central aggregator processes logs
        - Problem: Decouple log generation from processing
        
        THE PROBLEM WITHOUT QUEUES:
        ===========================
        - Service generates log → waits for aggregator
        - Aggregator busy → service blocked
        - Services slow down → system performance degrades
        - Tight coupling → system fragile
        
        THE SOLUTION:
        =============
        Queue enables:
        - Services put logs in queue (non-blocking)
        - Aggregator processes logs from queue
        - Decoupled → services never blocked
        - Backpressure → queue size limits memory
        - System resilient → services continue working
        
        WHEN TO USE QUEUES:
        ===================
        ✅ Producer-consumer patterns
        ✅ Decoupling producers and consumers
        ✅ Buffering between processes
        ✅ Asynchronous processing
        ✅ Load balancing
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Log Aggregation System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Multiple services generating logs")
        print("  - Central aggregator processes logs")
        print("  - Problem: Decouple log generation from processing")
        print()
        print("THE PROBLEM:")
        print("  Without queues:")
        print("    ❌ Service generates log → waits for aggregator")
        print("    ❌ Aggregator busy → service blocked")
        print("    ❌ Services slow down → system performance degrades")
        print("    ❌ Tight coupling → system fragile")
        print()
        print("THE SOLUTION:")
        print("  With queues:")
        print("    ✅ Services put logs in queue (non-blocking)")
        print("    ✅ Aggregator processes logs from queue")
        print("    ✅ Decoupled → services never blocked")
        print("    ✅ Backpressure → queue size limits memory")
        print("    ✅ System resilient → services continue working")
        print()
        print("=" * 70)
        print()

        log_queue = multiprocessing.Queue(maxsize=10)  # Bounded queue
        processed_logs = multiprocessing.Manager().list()

        def service_generator(service_id: int, num_logs: int) -> None:
            """Service that generates logs."""
            for i in range(num_logs):
                log_entry = f"Service-{service_id}: Log entry {i+1} at {time.time()}"
                log_queue.put(log_entry)  # Non-blocking (unless queue full)
                print(f"  Service {service_id}: Generated log {i+1}")
                time.sleep(0.05)  # Simulate log generation

            print(f"Service {service_id}: Finished generating {num_logs} logs")

        def log_aggregator() -> None:
            """Aggregator that processes logs from queue."""
            logs_processed = 0
            while True:
                try:
                    log_entry = log_queue.get(timeout=2)
                    # Process log (aggregate, store, etc.)
                    processed_logs.append(log_entry)
                    logs_processed += 1
                    print(f"  Aggregator: Processed log {logs_processed}")
                    time.sleep(0.1)  # Simulate processing time
                except:
                    # Timeout - no more logs
                    break

            print(f"Aggregator: Processed {logs_processed} logs total")

        print("Starting simulation...")
        print("  - 3 services generating logs")
        print("  - 1 aggregator processing logs")
        print()

        services = [
            multiprocessing.Process(target=service_generator, args=(i+1, 5))
            for i in range(3)
        ]
        aggregator = multiprocessing.Process(target=log_aggregator)

        start_time = time.time()
        aggregator.start()
        for s in services:
            s.start()

        for s in services:
            s.join()
        aggregator.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Logs processed: {len(processed_logs)}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Queue decoupled services from aggregator!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE QUEUES:")
        print("   ✅ Producer-consumer patterns")
        print("   ✅ Decoupling producers and consumers")
        print("   ✅ Buffering between processes")
        print("   ✅ Asynchronous processing")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Decouples producers from consumers")
        print("   - Prevents blocking")
        print("   - Enables backpressure")
        print("   - Improves system resilience")
        print("=" * 70)
        print()

    def joinable_queue_real_world_example(self) -> None:
        """
        Real-World Scenario: JoinableQueue - Batch Job Processing.

        REAL-WORLD SCENARIO:
        ====================
        You're building a batch job processing system:
        - Submit batch of jobs
        - Workers process jobs
        - Problem: Need to know when all jobs complete
        
        THE PROBLEM WITHOUT JOINABLEQUEUE:
        ==================================
        - Submit jobs → don't know when done
        - Poll workers → inefficient
        - Wait arbitrary time → may wait too long or too short
        - No guarantee all jobs processed
        - System uncertainty
        
        THE SOLUTION:
        =============
        JoinableQueue enables:
        - Submit jobs to queue
        - Workers process and call task_done()
        - join() blocks until all tasks done
        - Deterministic completion → know exactly when done
        - System reliability → guaranteed completion
        
        WHEN TO USE JOINABLEQUEUE:
        ==========================
        ✅ Batch processing with completion tracking
        ✅ Task queues with guarantees
        ✅ Work distribution with verification
        ✅ Pipeline stages with completion
        ✅ Deterministic completion needed
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Batch Job Processing System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Batch job processing system")
        print("  - Submit batch of jobs")
        print("  - Workers process jobs")
        print("  - Problem: Need to know when all jobs complete")
        print()
        print("THE PROBLEM:")
        print("  Without JoinableQueue:")
        print("    ❌ Submit jobs → don't know when done")
        print("    ❌ Poll workers → inefficient")
        print("    ❌ Wait arbitrary time → may wait too long or too short")
        print("    ❌ No guarantee all jobs processed")
        print()
        print("THE SOLUTION:")
        print("  With JoinableQueue:")
        print("    ✅ Submit jobs to queue")
        print("    ✅ Workers process and call task_done()")
        print("    ✅ join() blocks until all tasks done")
        print("    ✅ Deterministic completion → know exactly when done")
        print("    ✅ System reliability → guaranteed completion")
        print()
        print("=" * 70)
        print()

        job_queue = multiprocessing.JoinableQueue()
        results = multiprocessing.Manager().dict()

        def job_worker(worker_id: int) -> None:
            """Worker that processes jobs."""
            jobs_processed = 0
            while True:
                job = job_queue.get()
                if job is None:  # Poison pill
                    job_queue.task_done()
                    break

                # Process job
                print(f"  Worker {worker_id}: Processing job {job}")
                time.sleep(0.1)  # Simulate work
                results[job] = f"Completed by worker {worker_id}"
                jobs_processed += 1
                job_queue.task_done()

            print(f"Worker {worker_id}: Processed {jobs_processed} jobs")

        # Create workers
        num_workers = 3
        workers = [
            multiprocessing.Process(target=job_worker, args=(i+1,))
            for i in range(num_workers)
        ]

        # Submit batch of jobs
        batch_jobs = [f"Job-{i+1}" for i in range(12)]
        print(f"Submitting batch of {len(batch_jobs)} jobs...")
        for job in batch_jobs:
            job_queue.put(job)

        # Start workers
        for w in workers:
            w.start()

        # Wait for all jobs to complete
        print("Waiting for all jobs to complete...")
        job_queue.join()  # Blocks until all tasks done
        print("✅ All jobs completed!")

        # Shutdown workers
        for _ in range(num_workers):
            job_queue.put(None)

        for w in workers:
            w.join()

        print()
        print("Results:")
        print(f"  Jobs submitted: {len(batch_jobs)}")
        print(f"  Jobs completed: {len(results)}")
        print("  ✅ JoinableQueue guaranteed all jobs processed!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE JOINABLEQUEUE:")
        print("   ✅ Batch processing with completion tracking")
        print("   ✅ Task queues with guarantees")
        print("   ✅ Work distribution with verification")
        print("   ✅ Deterministic completion needed")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Guarantees all tasks processed")
        print("   - Deterministic completion")
        print("   - No polling needed")
        print("   - System reliability")
        print("=" * 70)
        print()

    def pipe_real_world_example(self) -> None:
        """
        Real-World Scenario: Pipe - Command Execution Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building a command execution pipeline:
        - Parent sends commands to child
        - Child executes and sends results back
        - Problem: Bidirectional communication needed
        
        THE PROBLEM WITHOUT PIPES:
        ==========================
        - Parent can't send commands to child
        - Child can't send results to parent
        - Need complex workarounds
        - System inflexible
        
        THE SOLUTION:
        =============
        Pipe enables:
        - Parent sends commands via pipe
        - Child receives commands and executes
        - Child sends results back via pipe
        - Bidirectional communication → flexible
        - Simple and efficient → low overhead
        
        WHEN TO USE PIPES:
        ==================
        ✅ Bidirectional communication
        ✅ Parent-child command pattern
        ✅ Simple two-process communication
        ✅ Low-latency communication
        ✅ Direct process communication
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Command Execution Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Command execution pipeline")
        print("  - Parent sends commands to child")
        print("  - Child executes and sends results back")
        print("  - Problem: Bidirectional communication needed")
        print()
        print("THE PROBLEM:")
        print("  Without pipes:")
        print("    ❌ Parent can't send commands to child")
        print("    ❌ Child can't send results to parent")
        print("    ❌ Need complex workarounds")
        print("    ❌ System inflexible")
        print()
        print("THE SOLUTION:")
        print("  With pipes:")
        print("    ✅ Parent sends commands via pipe")
        print("    ✅ Child receives commands and executes")
        print("    ✅ Child sends results back via pipe")
        print("    ✅ Bidirectional communication → flexible")
        print("    ✅ Simple and efficient → low overhead")
        print()
        print("=" * 70)
        print()

        parent_conn, child_conn = multiprocessing.Pipe(duplex=True)

        def command_executor(conn: multiprocessing.connection.Connection) -> None:
            """Child process that executes commands."""
            while True:
                command = conn.recv()
                if command == "EXIT":
                    conn.send("Goodbye")
                    break

                # Execute command (simulate)
                result = f"Executed: {command} (result: success)"
                print(f"  Executor: Received command '{command}'")
                time.sleep(0.1)  # Simulate execution
                conn.send(result)

        executor = multiprocessing.Process(target=command_executor, args=(child_conn,))
        executor.start()

        # Send commands
        commands = ["task1", "task2", "task3"]
        print("Sending commands to executor...")
        for cmd in commands:
            parent_conn.send(cmd)
            result = parent_conn.recv()
            print(f"  Parent: Received result - {result}")

        # Shutdown
        parent_conn.send("EXIT")
        final_result = parent_conn.recv()
        print(f"  Parent: Final result - {final_result}")

        executor.join()

        print()
        print("Results:")
        print(f"  Commands sent: {len(commands)}")
        print("  ✅ Pipe enabled bidirectional communication!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PIPES:")
        print("   ✅ Bidirectional communication")
        print("   ✅ Parent-child command pattern")
        print("   ✅ Simple two-process communication")
        print("   ✅ Low-latency communication")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Enables bidirectional communication")
        print("   - Simple and efficient")
        print("   - Low overhead")
        print("   - Direct process communication")
        print("=" * 70)
        print()


def main() -> None:
    """Run all queue and pipe examples."""
    print("Multiprocessing Queues and Pipes Examples")
    print("=" * 46)

    example = QueuePipeExample()

    example.basic_queue_example()
    example.multiple_producers_consumers()
    example.joinable_queue_example()
    example.priority_queue_example()
    example.pipe_example()
    example.duplex_pipe_example()
    example.queue_timeout_example()
    example.message_passing_patterns()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    example.queue_real_world_example()
    example.joinable_queue_real_world_example()
    example.pipe_real_world_example()

    print("All queue and pipe examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()
