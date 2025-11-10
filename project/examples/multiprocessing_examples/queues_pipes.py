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
    """

    def basic_queue_example(self) -> None:
        """Demonstrate basic queue usage."""
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
        """Demonstrate multiple producers and consumers with a queue."""
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
        """Demonstrate JoinableQueue for task coordination."""
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
        """Demonstrate PriorityQueue for ordered processing."""
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
        """Demonstrate Pipe for direct process communication."""
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
        """Demonstrate duplex pipe communication."""
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
        """Demonstrate queue operations with timeouts."""
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

        def timeout_consumer(queue: multiprocessing.Queue) -> None:
            """Consumer with timeout handling."""
            while True:
                try:
                    item = queue.get(timeout=3)  # 3 second timeout
                    print(f"Consumed: {item}")
                    if item == "C":  # Last item
                        break
                except Exception as e:
                    print(f"Timeout or error: {e}")
                    break

        # Create queue
        queue = multiprocessing.Queue(maxsize=2)  # Small queue to demonstrate blocking

        # Create processes
        producer = multiprocessing.Process(target=timeout_producer, args=(queue,))
        consumer = multiprocessing.Process(target=timeout_consumer, args=(queue,))

        # Start consumer first (will wait for items)
        consumer.start()
        producer.start()

        producer.join()
        consumer.join()

        print("Timeout example completed!\n")

    def message_passing_patterns(self) -> None:
        """Demonstrate common message passing patterns."""
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

    print("All queue and pipe examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()
