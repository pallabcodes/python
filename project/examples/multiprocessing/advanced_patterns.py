"""
Advanced multiprocessing patterns and real-world examples.

This module covers:
- Process pools with custom worker initialization
- Map-reduce patterns
- Pipeline processing
- Work stealing and load balancing
- Process monitoring and health checks
- Graceful shutdown patterns
- Resource management and cleanup
"""

import multiprocessing
import os
import signal
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


class AdvancedPatternsExample:
    """
    Advanced multiprocessing patterns for real-world applications.
    """

    def custom_worker_initialization(self) -> None:
        """Demonstrate custom worker initialization in process pools."""
        print("=== Custom Worker Initialization ===")

        def init_worker() -> None:
            """Initialize worker process."""
            # Set process name for monitoring
            multiprocessing.current_process().name = f"Worker-{os.getpid()}"

            # Initialize worker-specific resources
            print(f"Initializing worker process {os.getpid()}")

            # Could initialize database connections, load models, etc.
            global worker_data
            worker_data = {"pid": os.getpid(), "start_time": time.time(), "tasks_processed": 0}

        def worker_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
            """Task that uses worker-specific data."""
            global worker_data
            worker_data["tasks_processed"] += 1

            # Simulate processing
            result = {
                "task_id": task_data["id"],
                "processed_by": worker_data["pid"],
                "worker_tasks": worker_data["tasks_processed"],
                "result": task_data["value"] * 2
            }

            time.sleep(0.05)  # Simulate work
            return result

        # Create pool with custom initializer
        with multiprocessing.Pool(processes=3, initializer=init_worker) as pool:
            # Prepare tasks
            tasks = [{"id": i, "value": i * 10} for i in range(9)]

            # Process tasks
            results = pool.map(worker_task, tasks)

            # Display results
            print("Results:")
            for result in results:
                print(f"  Task {result['task_id']}: {result['result']} "
                      f"(by worker {result['processed_by']}, "
                      f"worker processed {result['worker_tasks']} tasks)")

        print()

    def map_reduce_pattern(self) -> None:
        """Demonstrate map-reduce pattern with multiprocessing."""
        print("=== Map-Reduce Pattern ===")

        def mapper(data_chunk: List[int]) -> List[Tuple[str, int]]:
            """Map function: transform data into key-value pairs."""
            result = []
            for num in data_chunk:
                # Create key-value pairs
                key = "even" if num % 2 == 0 else "odd"
                result.append((key, num))
            return result

        def reducer(key: str, values: List[int]) -> Dict[str, Any]:
            """Reduce function: aggregate values for each key."""
            return {
                "key": key,
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0
            }

        # Generate sample data
        data = list(range(1, 101))  # Numbers 1-100

        # Split data into chunks for parallel processing
        chunk_size = 20
        data_chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        print(f"Processing {len(data)} items in {len(data_chunks)} chunks")

        # Map phase: process chunks in parallel
        with multiprocessing.Pool(processes=4) as pool:
            mapped_results = pool.map(mapper, data_chunks)

        # Flatten mapped results
        all_pairs = []
        for chunk_result in mapped_results:
            all_pairs.extend(chunk_result)

        # Shuffle and sort by key (simulate distributed shuffle)
        from collections import defaultdict
        shuffled = defaultdict(list)
        for key, value in all_pairs:
            shuffled[key].append(value)

        # Reduce phase: aggregate results for each key
        final_results = []
        for key, values in shuffled.items():
            result = reducer(key, values)
            final_results.append(result)

        # Display results
        print("Map-Reduce Results:")
        for result in final_results:
            print(f"  {result['key'].upper()}: count={result['count']}, "
                  f"sum={result['sum']}, avg={result['avg']:.1f}")

        print()

    def pipeline_processing(self) -> None:
        """Demonstrate pipeline processing pattern."""
        print("=== Pipeline Processing ===")

        def stage1_producer(output_queue: multiprocessing.Queue) -> None:
            """Stage 1: Data production."""
            data = list(range(1, 21))  # Generate 20 items
            for item in data:
                output_queue.put({"stage1": item, "data": item})
                print(f"Stage 1: Produced {item}")
                time.sleep(0.02)

            output_queue.put(None)  # End signal

        def stage2_processor(input_queue: multiprocessing.Queue,
                           output_queue: multiprocessing.Queue) -> None:
            """Stage 2: Data processing."""
            while True:
                item = input_queue.get()
                if item is None:
                    output_queue.put(None)  # Pass end signal
                    break

                # Process data
                processed = item["data"] * 2
                item["stage2"] = processed
                output_queue.put(item)
                print(f"Stage 2: Processed {item['data']} -> {processed}")
                time.sleep(0.03)

        def stage3_consumer(input_queue: multiprocessing.Queue) -> None:
            """Stage 3: Data consumption."""
            results = []
            while True:
                item = input_queue.get()
                if item is None:
                    break

                # Final processing
                final = item["stage2"] + 10
                item["stage3"] = final
                results.append(item)
                print(f"Stage 3: Final result {item['data']} -> {final}")

            print(f"Pipeline processed {len(results)} items")

        # Create queues for pipeline stages
        queue1 = multiprocessing.Queue()
        queue2 = multiprocessing.Queue()

        # Create pipeline stages
        stage1 = multiprocessing.Process(target=stage1_producer, args=(queue1,))
        stage2 = multiprocessing.Process(target=stage2_processor, args=(queue1, queue2))
        stage3 = multiprocessing.Process(target=stage3_consumer, args=(queue2,))

        print("Starting pipeline processing:")
        stage1.start()
        stage2.start()
        stage3.start()

        stage1.join()
        stage2.join()
        stage3.join()

        print()

    def work_stealing_pool(self) -> None:
        """Demonstrate work-stealing pattern."""
        print("=== Work Stealing Pattern ===")

        class WorkStealingPool:
            """Simple work-stealing thread pool simulation."""
            def __init__(self, num_workers: int):
                self.num_workers = num_workers
                self.work_queues = [multiprocessing.Queue() for _ in range(num_workers)]
                self.workers = []
                self.running = multiprocessing.Value('b', True)

            def start(self) -> None:
                """Start worker processes."""
                for i in range(self.num_workers):
                    worker = multiprocessing.Process(
                        target=self._worker_loop,
                        args=(i, self.work_queues, self.running)
                    )
                    worker.start()
                    self.workers.append(worker)

            def submit(self, task: Tuple[Callable, Tuple]) -> None:
                """Submit task to least loaded queue."""
                # Simple load balancing: round-robin
                queue_index = len(self.workers) % self.num_workers
                self.work_queues[queue_index].put(task)

            def shutdown(self) -> None:
                """Shutdown the pool."""
                self.running.value = False
                # Send poison pills
                for queue in self.work_queues:
                    queue.put(None)

                for worker in self.workers:
                    worker.join()

            @staticmethod
            def _worker_loop(worker_id: int, work_queues: List[multiprocessing.Queue],
                           running: multiprocessing.Value) -> None:
                """Worker loop with work stealing."""
                while running.value:
                    task = None

                    # Try to get work from own queue first
                    task = work_queues[worker_id].get(timeout=0.1)

                    if task is None:  # Poison pill
                        break

                    if task:
                        func, args = task
                        try:
                            result = func(*args)
                            print(f"Worker {worker_id}: {func.__name__}{args} = {result}")
                        except Exception as e:
                            print(f"Worker {worker_id}: Task failed: {e}")

                    # Try to steal work from other queues (simplified)
                    # In a real implementation, this would be more sophisticated

        def sample_task(x: int, y: int) -> int:
            """Sample task for work stealing."""
            time.sleep(0.05)  # Simulate work
            return x + y

        # Create work-stealing pool
        pool = WorkStealingPool(num_workers=3)
        pool.start()

        # Submit tasks
        for i in range(9):
            pool.submit((sample_task, (i, i * 2)))

        time.sleep(1)  # Let workers process tasks
        pool.shutdown()

        print()

    def process_monitoring_health_checks(self) -> None:
        """Demonstrate process monitoring and health checks."""
        print("=== Process Monitoring and Health Checks ===")

        class ProcessMonitor:
            """Monitor process health and performance."""
            def __init__(self):
                self.process_info = multiprocessing.Manager().dict()
                self.health_check_interval = 2

            def monitor_process(self, process_id: int, info_dict: dict) -> None:
                """Monitor a specific process."""
                start_time = time.time()
                last_check = start_time

                while True:
                    current_time = time.time()

                    # Update process info
                    info_dict[process_id] = {
                        "pid": os.getpid(),
                        "alive": True,
                        "uptime": current_time - start_time,
                        "last_check": current_time
                    }

                    # Simulate health check
                    time.sleep(0.5)

                    # Check if we should stop monitoring
                    if current_time - last_check > 10:  # Stop after 10 seconds
                        break

                info_dict[process_id]["alive"] = False

        def monitored_worker(worker_id: int, monitor: ProcessMonitor) -> None:
            """Worker process that reports to monitor."""
            print(f"Worker {worker_id} starting (PID: {os.getpid()})")

            # Register with monitor
            monitor.monitor_process(worker_id, monitor.process_info)

            # Do work
            for i in range(5):
                print(f"Worker {worker_id}: iteration {i+1}")
                time.sleep(0.3)

            print(f"Worker {worker_id} completed")

        def health_checker(monitor: ProcessMonitor) -> None:
            """Health check process."""
            while True:
                print("Health Check:")
                for pid, info in monitor.process_info.items():
                    status = "ALIVE" if info["alive"] else "DEAD"
                    print(f"  Process {pid}: {status} (uptime: {info['uptime']:.1f}s)")

                time.sleep(monitor.health_check_interval)

                # Stop after all processes are done
                if all(not info["alive"] for info in monitor.process_info.values()):
                    break

        # Create monitor and processes
        monitor = ProcessMonitor()

        workers = []
        for i in range(3):
            worker = multiprocessing.Process(target=monitored_worker, args=(i+1, monitor))
            workers.append(worker)

        health_check_process = multiprocessing.Process(target=health_checker, args=(monitor,))

        # Start processes
        health_check_process.start()
        for worker in workers:
            worker.start()

        # Wait for workers
        for worker in workers:
            worker.join()

        # Wait a bit more for final health check
        time.sleep(3)
        health_check_process.terminate()
        health_check_process.join()

        print()

    def graceful_shutdown_patterns(self) -> None:
        """Demonstrate graceful shutdown patterns."""
        print("=== Graceful Shutdown Patterns ===")

        class GracefulShutdownManager:
            """Manage graceful shutdown of processes."""
            def __init__(self):
                self.shutdown_event = multiprocessing.Event()
                self.active_processes = multiprocessing.Manager().list()

            def register_process(self, process_id: str) -> None:
                """Register a process for shutdown management."""
                self.active_processes.append(process_id)

            def unregister_process(self, process_id: str) -> None:
                """Unregister a process."""
                if process_id in self.active_processes:
                    self.active_processes.remove(process_id)

            def initiate_shutdown(self) -> None:
                """Initiate graceful shutdown."""
                print("Initiating graceful shutdown...")
                self.shutdown_event.set()

            def should_shutdown(self) -> bool:
                """Check if shutdown has been requested."""
                return self.shutdown_event.is_set()

        def graceful_worker(worker_id: str, manager: GracefulShutdownManager) -> None:
            """Worker that handles graceful shutdown."""
            manager.register_process(worker_id)
            print(f"Worker {worker_id} started (PID: {os.getpid()})")

            try:
                iteration = 0
                while not manager.should_shutdown():
                    iteration += 1
                    print(f"Worker {worker_id}: iteration {iteration}")

                    # Simulate work
                    time.sleep(0.2)

                    # Check for shutdown signal periodically
                    if iteration >= 10:  # Simulate completion
                        break

            except KeyboardInterrupt:
                print(f"Worker {worker_id}: Received interrupt signal")
            finally:
                print(f"Worker {worker_id}: Cleaning up...")
                manager.unregister_process(worker_id)
                print(f"Worker {worker_id}: Shutdown complete")

        def shutdown_signal_handler(signum, frame) -> None:
            """Handle shutdown signals."""
            print(f"Received signal {signum}, initiating shutdown...")
            shutdown_manager.initiate_shutdown()

        # Setup signal handlers
        signal.signal(signal.SIGINT, shutdown_signal_handler)
        signal.signal(signal.SIGTERM, shutdown_signal_handler)

        # Create shutdown manager
        shutdown_manager = GracefulShutdownManager()

        # Create workers
        workers = []
        for i in range(3):
            worker = multiprocessing.Process(
                target=graceful_worker,
                args=(f"Worker-{i+1}", shutdown_manager)
            )
            workers.append(worker)

        # Start workers
        print("Starting workers (Ctrl+C to initiate graceful shutdown):")
        for worker in workers:
            worker.start()

        try:
            # Wait for workers or shutdown signal
            for worker in workers:
                worker.join(timeout=1)
                if not worker.is_alive():
                    break

            # If we get here without shutdown signal, initiate shutdown
            if not shutdown_manager.should_shutdown():
                shutdown_manager.initiate_shutdown()

            # Wait for all workers to complete shutdown
            for worker in workers:
                worker.join(timeout=5)
                if worker.is_alive():
                    print(f"Worker {worker.name} did not shutdown gracefully, terminating")
                    worker.terminate()
                    worker.join()

        except KeyboardInterrupt:
            shutdown_manager.initiate_shutdown()
            for worker in workers:
                worker.join(timeout=3)

        print("All workers shutdown")
        print()

    def resource_management_cleanup(self) -> None:
        """Demonstrate proper resource management and cleanup."""
        print("=== Resource Management and Cleanup ===")

        class ResourceManager:
            """Manage resources with proper cleanup."""
            def __init__(self):
                self.resources = multiprocessing.Manager().dict()
                self.lock = multiprocessing.Lock()

            def allocate_resource(self, process_id: str, resource_type: str) -> str:
                """Allocate a resource for a process."""
                with self.lock:
                    resource_id = f"{resource_type}_{process_id}_{len(self.resources)}"
                    self.resources[resource_id] = {
                        "process_id": process_id,
                        "type": resource_type,
                        "allocated_at": time.time(),
                        "status": "active"
                    }
                    print(f"Allocated {resource_id} to {process_id}")
                    return resource_id

            def release_resource(self, resource_id: str) -> None:
                """Release a resource."""
                with self.lock:
                    if resource_id in self.resources:
                        self.resources[resource_id]["status"] = "released"
                        self.resources[resource_id]["released_at"] = time.time()
                        print(f"Released {resource_id}")

            def cleanup_process_resources(self, process_id: str) -> None:
                """Clean up all resources for a process."""
                with self.lock:
                    to_cleanup = [rid for rid, res in self.resources.items()
                                if res["process_id"] == process_id and res["status"] == "active"]

                    for resource_id in to_cleanup:
                        self.release_resource(resource_id)

        def resource_using_worker(worker_id: str, manager: ResourceManager) -> None:
            """Worker that properly manages resources."""
            resources = []

            try:
                # Allocate resources
                for i in range(2):
                    resource_id = manager.allocate_resource(worker_id, f"resource_{i}")
                    resources.append(resource_id)
                    time.sleep(0.1)

                # Use resources
                print(f"Worker {worker_id} using {len(resources)} resources")
                time.sleep(0.5)

            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
            finally:
                # Clean up resources
                print(f"Worker {worker_id} cleaning up resources...")
                for resource_id in resources:
                    manager.release_resource(resource_id)

                # Ensure all resources for this process are cleaned up
                manager.cleanup_process_resources(worker_id)

        # Create resource manager
        resource_manager = ResourceManager()

        # Create workers
        workers = []
        for i in range(3):
            worker = multiprocessing.Process(
                target=resource_using_worker,
                args=(f"Worker-{i+1}", resource_manager)
            )
            workers.append(worker)

        # Start workers
        print("Starting resource-managed workers:")
        for worker in workers:
            worker.start()

        # Wait for completion
        for worker in workers:
            worker.join()

        # Final cleanup check
        print("Final resource state:")
        for resource_id, info in resource_manager.resources.items():
            print(f"  {resource_id}: {info['status']}")

        print()


def main() -> None:
    """Run all advanced patterns examples."""
    print("Multiprocessing Advanced Patterns Examples")
    print("=" * 48)

    example = AdvancedPatternsExample()

    example.custom_worker_initialization()
    example.map_reduce_pattern()
    example.pipeline_processing()
    example.work_stealing_pool()
    example.process_monitoring_health_checks()
    example.graceful_shutdown_patterns()
    example.resource_management_cleanup()

    print("All advanced patterns examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()
