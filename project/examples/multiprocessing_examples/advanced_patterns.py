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

    This class demonstrates advanced patterns used in production systems
    including custom initialization, map-reduce, pipelines, work stealing,
    monitoring, graceful shutdown, and resource management.

    When to Use:
        - Building production multiprocessing systems
        - Complex data processing workflows
        - Scalable distributed systems
        - Enterprise-grade applications
        - Real-world production scenarios

    Real-World Examples:
        - Data processing: Map-reduce for large datasets
        - Pipelines: Multi-stage data processing
        - Worker pools: Custom initialized worker pools
        - Monitoring: Process health monitoring
        - Shutdown: Graceful shutdown handling
        - Resources: Resource management and cleanup

    Gotchas:
        - Worker initialization runs once per worker
        - Global variables in workers are process-local
        - Proper cleanup prevents resource leaks
        - Graceful shutdown requires coordination
        - Monitoring adds overhead
        - Work stealing complexity

    Performance Notes:
        - Custom initialization reduces per-task overhead
        - Map-reduce scales to large datasets
        - Pipelines enable parallel stage processing
        - Work stealing improves load balancing
        - Monitoring overhead is minimal
        - Proper cleanup prevents leaks
    """

    def custom_worker_initialization(self) -> None:
        """
        Demonstrate custom worker initialization in process pools.

        Shows how to use initializer functions to set up worker processes
        once, reducing per-task overhead for expensive initialization.

        When to Use:
            - Expensive initialization (DB connections, model loading)
            - Worker-specific setup
            - Resource initialization
            - Configuration loading
            - One-time setup per worker

        Real-World Examples:
            - Database connections: Initialize connection pools
            - ML models: Load models once per worker
            - Configuration: Load config per worker
            - Resource setup: Initialize resources per worker
            - Cache warming: Warm caches per worker

        Gotchas:
            - Initializer runs once per worker process
            - Global variables are process-local
            - Initializer must be picklable
            - Errors in initializer affect worker
            - Initializer runs before any tasks
            - Use global variables for worker state

        Performance Notes:
            - Reduces per-task initialization overhead
            - Useful for expensive setup
            - Initialization cost amortized over tasks
            - Optimal for long-running workers
        """
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
        """
        Demonstrate map-reduce pattern with multiprocessing.

        Shows how to implement map-reduce for parallel data processing
        with map phase (parallel) and reduce phase (aggregation).

        When to Use:
            - Processing large datasets
            - Parallel data transformation
            - Aggregating distributed data
            - Big data processing
            - Distributed computing

        Real-World Examples:
            - Log analysis: Map logs, reduce to statistics
            - Data aggregation: Map data, reduce to summaries
            - Search: Map queries, reduce to results
            - Analytics: Map events, reduce to metrics
            - ETL: Map extract, reduce to load

        Gotchas:
            - Map and reduce phases are separate
            - Shuffle phase groups data by key
            - Reduce operates on grouped data
            - Both phases can be parallelized
            - Memory usage depends on data distribution
            - Optimal chunk size balances overhead

        Performance Notes:
            - Parallel map improves throughput
            - Reduce parallelism depends on key distribution
            - Optimal chunk size balances overhead vs parallelism
            - Can process very large datasets
            - Shuffle phase can be expensive
        """
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
        """
        Demonstrate pipeline processing pattern.

        Shows how to build multi-stage processing pipelines with queues
        connecting stages, enabling parallel processing across stages.

        When to Use:
            - Multi-stage data processing
            - ETL pipelines
            - Data transformation workflows
            - Streaming data processing
            - Building data processing systems

        Real-World Examples:
            - ETL pipelines: Extract -> Transform -> Load
            - Log processing: Parse -> Filter -> Analyze -> Store
            - Image processing: Load -> Resize -> Compress -> Save
            - Data pipelines: Fetch -> Process -> Aggregate -> Store
            - Message processing: Receive -> Validate -> Route -> Send

        Gotchas:
            - Each stage runs concurrently
            - Queues buffer data between stages
            - Sentinel values (None) signal end of data
            - Pipeline throughput limited by slowest stage
            - Backpressure flows backward through pipeline
            - Proper cleanup required for all stages

        Performance Notes:
            - Stages process in parallel (better than sequential)
            - Memory usage depends on queue sizes
            - Optimal for streaming data processing
            - Can process infinite streams
            - Balance stage parallelism vs memory
        """
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
        """
        Demonstrate work-stealing pattern.

        Shows how to implement work stealing for dynamic load balancing,
        where idle workers steal work from busy workers.

        When to Use:
            - Dynamic load balancing
            - Variable task durations
            - Improving worker utilization
            - Handling uneven workloads
            - Optimizing resource usage

        Real-World Examples:
            - Task queues: Steal tasks from busy workers
            - Load balancing: Balance load dynamically
            - Resource optimization: Improve utilization
            - Work distribution: Distribute work efficiently
            - Performance optimization: Optimize throughput

        Gotchas:
            - Work stealing adds complexity
            - Queue contention affects performance
            - Stealing overhead vs benefit
            - Implementation complexity
            - Need proper synchronization
            - Balance stealing vs overhead

        Performance Notes:
            - Improves load balancing
            - Reduces idle worker time
            - Stealing overhead affects performance
            - Optimal for variable task durations
            - Balance stealing frequency vs overhead
        """
        print("=== Work Stealing Pattern ===")

        class WorkStealingPool:
            """Simple work-stealing thread pool simulation."""
            def __init__(self, num_workers: int):
                self.num_workers = num_workers
                self.work_queues = [multiprocessing.Queue() for _ in range(num_workers)]
                self.workers = []
                self.running = multiprocessing.Value('b', True)
                self.task_counter = multiprocessing.Value('i', 0)
                self.counter_lock = multiprocessing.Lock()

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
                with self.counter_lock:
                    queue_index = self.task_counter.value % self.num_workers
                    self.task_counter.value += 1
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
                from queue import Empty
                
                while running.value:
                    task = None

                    # Try to get work from own queue first
                    try:
                    task = work_queues[worker_id].get(timeout=0.1)
                    except Empty:
                        # No work available, try to steal from other queues
                        task = None

                    if task is None:  # No work or poison pill
                        # Try to steal work from other queues
                        stolen = False
                        for i, queue in enumerate(work_queues):
                            if i != worker_id:
                                try:
                                    task = queue.get_nowait()
                                    if task is None:  # Poison pill
                                        continue
                                    stolen = True
                                    break
                                except Empty:
                                    continue
                        
                        if not stolen:
                            continue  # No work available, check running flag again

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
        """
        Demonstrate process monitoring and health checks.

        Shows how to monitor process health and performance, enabling
        detection of failures and performance issues.

        When to Use:
            - Production systems
            - Process health monitoring
            - Failure detection
            - Performance tracking
            - System observability

        Real-World Examples:
            - Health checks: Monitor process health
            - Performance monitoring: Track performance metrics
            - Failure detection: Detect process failures
            - System monitoring: Monitor system state
            - Alerting: Alert on health issues

        Gotchas:
            - Monitoring adds overhead
            - Health checks must be lightweight
            - False positives cause unnecessary alerts
            - Monitor frequency affects overhead
            - Proper cleanup on shutdown
            - Handle monitor failures

        Performance Notes:
            - Monitoring overhead is minimal
            - Useful for production systems
            - Health checks should be fast
            - Balance monitoring frequency vs overhead
            - Critical for reliability
        """
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

        def health_checker(monitor: ProcessMonitor, shutdown_event: multiprocessing.Event) -> None:
            """Health check process with proper shutdown."""
            max_checks = 20  # Maximum health checks before timeout
            check_count = 0
            
            while check_count < max_checks:
                if shutdown_event.is_set():
                    break
                    
                print("Health Check:")
                for pid, info in monitor.process_info.items():
                    status = "ALIVE" if info["alive"] else "DEAD"
                    print(f"  Process {pid}: {status} (uptime: {info['uptime']:.1f}s)")

                time.sleep(monitor.health_check_interval)
                check_count += 1

                # Stop after all processes are done
                if all(not info["alive"] for info in monitor.process_info.values()):
                    break

        # Create monitor and processes
        monitor = ProcessMonitor()
        shutdown_event = multiprocessing.Event()

        workers = []
        for i in range(3):
            worker = multiprocessing.Process(target=monitored_worker, args=(i+1, monitor))
            workers.append(worker)

        health_check_process = multiprocessing.Process(target=health_checker, args=(monitor, shutdown_event))

        # Start processes
        health_check_process.start()
        for worker in workers:
            worker.start()

        # Wait for workers
        for worker in workers:
            worker.join()

        # Signal shutdown to health checker
        shutdown_event.set()
        
        # Wait for health checker with timeout
        health_check_process.join(timeout=5.0)
        if health_check_process.is_alive():
            print("Health checker did not shutdown gracefully, terminating...")
        health_check_process.terminate()
        health_check_process.join()

        print()

    def graceful_shutdown_patterns(self) -> None:
        """
        Demonstrate graceful shutdown patterns.

        Shows how to implement graceful shutdown that allows processes
        to complete current work and clean up resources before exiting.

        When to Use:
            - Production systems
            - Long-running processes
            - Resource cleanup
            - Data consistency
            - Service shutdown

        Real-World Examples:
            - Service shutdown: Gracefully shutdown services
            - Data processing: Complete current work before exit
            - Resource cleanup: Clean up resources on shutdown
            - Connection closing: Close connections gracefully
            - State saving: Save state before exit

        Gotchas:
            - Signal handlers must be set before processes start
            - Processes must check shutdown signal periodically
            - Timeout prevents indefinite waiting
            - Proper cleanup in finally blocks
            - Handle SIGTERM and SIGINT
            - Terminate if graceful shutdown fails

        Performance Notes:
            - Graceful shutdown prevents data loss
            - Critical for production systems
            - Timeout prevents indefinite blocking
            - Proper cleanup prevents leaks
            - Balance shutdown time vs responsiveness
        """
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
        """
        Demonstrate proper resource management and cleanup.

        Shows how to properly manage and clean up resources in multiprocessing,
        preventing resource leaks and ensuring proper cleanup.

        When to Use:
            - Managing shared resources
            - Preventing resource leaks
            - Ensuring cleanup on errors
            - Resource tracking
            - Production systems

        Real-World Examples:
            - Database connections: Track and close connections
            - File handles: Track and close files
            - Network connections: Track and close connections
            - Locks: Release locks properly
            - Memory: Free allocated memory

        Gotchas:
            - Always use try/finally for cleanup
            - Cleanup must be idempotent
            - Handle exceptions in cleanup code
            - Cleanup happens even on errors
            - Resource state should be checked before cleanup
            - Track resources per process

        Performance Notes:
            - Proper cleanup prevents resource leaks
            - Cleanup overhead is minimal
            - Critical for long-running applications
            - Monitor resource usage to detect leaks
            - Balance cleanup frequency vs overhead
        """
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

    def map_reduce_real_world_example(self) -> None:
        """
        Real-World Scenario: Map-Reduce - Big Data Analytics System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a big data analytics system:
        - Process millions of log entries
        - Count events by type, calculate statistics
        - Problem: Sequential processing too slow
        
        THE PROBLEM WITHOUT MAP-REDUCE:
        ================================
        - Process logs sequentially → hours
        - Single process → CPU underutilized
        - No parallelization → slow
        - Memory issues → can't fit all data
        - System overwhelmed
        
        THE SOLUTION:
        =============
        Map-Reduce enables:
        - Map phase: Process logs in parallel
        - Shuffle phase: Group by key
        - Reduce phase: Aggregate statistics
        - Distributed processing → fast
        - Scales to millions of records
        
        WHEN TO USE MAP-REDUCE:
        =======================
        ✅ Large dataset processing
        ✅ Parallel data transformation
        ✅ Aggregating distributed data
        ✅ Big data analytics
        ✅ Distributed computing
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Big Data Analytics System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Big data analytics system")
        print("  - Process millions of log entries")
        print("  - Count events by type, calculate statistics")
        print("  - Problem: Sequential processing too slow")
        print()
        print("THE PROBLEM:")
        print("  Without map-reduce:")
        print("    ❌ Process logs sequentially → hours")
        print("    ❌ Single process → CPU underutilized")
        print("    ❌ No parallelization → slow")
        print("    ❌ Memory issues → can't fit all data")
        print()
        print("THE SOLUTION:")
        print("  With map-reduce:")
        print("    ✅ Map phase: Process logs in parallel")
        print("    ✅ Shuffle phase: Group by key")
        print("    ✅ Reduce phase: Aggregate statistics")
        print("    ✅ Distributed processing → fast")
        print("    ✅ Scales to millions of records")
        print()
        print("=" * 70)
        print()

        def map_logs(log_chunk: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
            """Map function: Extract event type and count."""
            result = []
            for log in log_chunk:
                event_type = log.get('event_type', 'unknown')
                result.append((event_type, 1))
            return result

        def reduce_stats(event_type: str, counts: List[int]) -> Dict[str, Any]:
            """Reduce function: Aggregate statistics."""
            total_count = sum(counts)
            return {
                "event_type": event_type,
                "total_events": total_count,
                "percentage": 0.0  # Will calculate after
            }

        # Simulate log data
        log_data = []
        event_types = ['login', 'logout', 'purchase', 'view', 'error']
        for i in range(100):
            log_data.append({
                'id': i,
                'event_type': event_types[i % len(event_types)],
                'timestamp': time.time() + i
            })

        # Split into chunks
        chunk_size = 20
        chunks = [log_data[i:i+chunk_size] for i in range(0, len(log_data), chunk_size)]

        print(f"Processing {len(log_data)} log entries in {len(chunks)} chunks")
        print()

        # Map phase (parallel)
        with multiprocessing.Pool(processes=4) as pool:
            mapped_results = pool.map(map_logs, chunks)

        # Flatten and group by key (shuffle phase)
        grouped = {}
        for chunk_result in mapped_results:
            for event_type, count in chunk_result:
                if event_type not in grouped:
                    grouped[event_type] = []
                grouped[event_type].append(count)

        # Reduce phase (can be parallel too)
        final_stats = []
        for event_type, counts in grouped.items():
            stats = reduce_stats(event_type, counts)
            final_stats.append(stats)

        # Calculate percentages
        total_events = sum(s['total_events'] for s in final_stats)
        for stats in final_stats:
            stats['percentage'] = (stats['total_events'] / total_events * 100) if total_events > 0 else 0

        print("Analytics Results:")
        for stats in sorted(final_stats, key=lambda x: x['total_events'], reverse=True):
            print(f"  {stats['event_type']}: {stats['total_events']} events "
                  f"({stats['percentage']:.1f}%)")
        print()
        print("  ✅ Map-Reduce enabled efficient big data analytics!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE MAP-REDUCE:")
        print("   ✅ Large dataset processing")
        print("   ✅ Parallel data transformation")
        print("   ✅ Aggregating distributed data")
        print("   ✅ Big data analytics")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Scales to millions of records")
        print("   - Parallel processing")
        print("   - Efficient aggregation")
        print("   - Industry-standard pattern")
        print("=" * 70)
        print()

    def pipeline_real_world_example(self) -> None:
        """
        Real-World Scenario: Pipeline - ETL Data Processing Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building an ETL (Extract, Transform, Load) pipeline:
        - Stage 1: Extract data from source
        - Stage 2: Transform data
        - Stage 3: Load data to destination
        - Problem: Sequential processing too slow
        
        THE PROBLEM WITHOUT PIPELINE:
        =============================
        - Extract all → then transform all → then load all
        - Each stage waits for previous to complete
        - No parallelism → slow
        - Memory pressure → hold all data
        - System inefficient
        
        THE SOLUTION:
        =============
        Pipeline enables:
        - Stage 1 extracts → feeds Stage 2 immediately
        - Stage 2 transforms → feeds Stage 3 immediately
        - All stages run concurrently → fast
        - Streaming processing → low memory
        - Optimal throughput → maximum efficiency
        
        WHEN TO USE PIPELINE:
        =====================
        ✅ Multi-stage data processing
        ✅ ETL pipelines
        ✅ Streaming data processing
        ✅ Pipeline architectures
        ✅ Continuous data flow
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: ETL Data Processing Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - ETL (Extract, Transform, Load) pipeline")
        print("  - Stage 1: Extract data from source")
        print("  - Stage 2: Transform data")
        print("  - Stage 3: Load data to destination")
        print("  - Problem: Sequential processing too slow")
        print()
        print("THE PROBLEM:")
        print("  Without pipeline:")
        print("    ❌ Extract all → then transform all → then load all")
        print("    ❌ Each stage waits for previous to complete")
        print("    ❌ No parallelism → slow")
        print("    ❌ Memory pressure → hold all data")
        print()
        print("THE SOLUTION:")
        print("  With pipeline:")
        print("    ✅ Stage 1 extracts → feeds Stage 2 immediately")
        print("    ✅ Stage 2 transforms → feeds Stage 3 immediately")
        print("    ✅ All stages run concurrently → fast")
        print("    ✅ Streaming processing → low memory")
        print("    ✅ Optimal throughput → maximum efficiency")
        print()
        print("=" * 70)
        print()

        extract_queue = multiprocessing.Queue()
        transform_queue = multiprocessing.Queue()
        results = multiprocessing.Manager().list()

        def extract_stage(num_items: int) -> None:
            """Stage 1: Extract data from source."""
            for i in range(num_items):
                data = {"id": i, "raw_data": f"data_{i}", "source": "database"}
                extract_queue.put(data)
                print(f"  Extract: Extracted item {i}")
                time.sleep(0.05)
            extract_queue.put(None)  # Sentinel

        def transform_stage() -> None:
            """Stage 2: Transform data."""
            while True:
                item = extract_queue.get()
                if item is None:
                    transform_queue.put(None)
                    break
                
                # Transform
                transformed = {
                    "id": item["id"],
                    "transformed_data": item["raw_data"].upper(),
                    "status": "transformed"
                }
                transform_queue.put(transformed)
                print(f"  Transform: Transformed item {item['id']}")
                time.sleep(0.05)

        def load_stage() -> None:
            """Stage 3: Load data to destination."""
            while True:
                item = transform_queue.get()
                if item is None:
                    break
                
                # Load (simulate)
                results.append(item)
                print(f"  Load: Loaded item {item['id']}")
                time.sleep(0.05)

        print("Starting pipeline...")
        print("  - Extract stage: 10 items")
        print("  - Transform stage: Processing")
        print("  - Load stage: Processing")
        print()

        extractor = multiprocessing.Process(target=extract_stage, args=(10,))
        transformer = multiprocessing.Process(target=transform_stage)
        loader = multiprocessing.Process(target=load_stage)

        start_time = time.time()
        extractor.start()
        transformer.start()
        loader.start()

        extractor.join()
        transformer.join()
        loader.join()

        elapsed = time.time() - start_time
        print()
        print("Results:")
        print(f"  Items processed: {len(results)}")
        print(f"  Execution time: {elapsed:.2f}s")
        print("  ✅ Pipeline enabled concurrent stage processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PIPELINE:")
        print("   ✅ Multi-stage data processing")
        print("   ✅ ETL pipelines")
        print("   ✅ Streaming data processing")
        print("   ✅ Continuous data flow")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Concurrent stage processing")
        print("   - Streaming (low memory)")
        print("   - Optimal throughput")
        print("   - Industry-standard pattern")
        print("=" * 70)
        print()

    def graceful_shutdown_real_world_example(self) -> None:
        """
        Real-World Scenario: Graceful Shutdown - Production Service.

        REAL-WORLD SCENARIO:
        ====================
        You're running a production service:
        - Long-running workers processing tasks
        - Service receives shutdown signal (SIGTERM)
        - Problem: Abrupt shutdown loses data
        
        THE PROBLEM WITHOUT GRACEFUL SHUTDOWN:
        =======================================
        - SIGTERM → workers killed immediately
        - Tasks in progress → lost
        - Data corruption → inconsistent state
        - No cleanup → resource leaks
        - Poor user experience
        
        THE SOLUTION:
        =============
        Graceful shutdown enables:
        - Signal handler catches SIGTERM
        - Workers finish current tasks
        - Cleanup resources properly
        - Save state before exit
        - System reliability → production-ready
        
        WHEN TO USE GRACEFUL SHUTDOWN:
        ==============================
        ✅ Production systems
        ✅ Long-running processes
        ✅ Data consistency critical
        ✅ Resource cleanup needed
        ✅ Service deployment
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Production Service Shutdown")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Production service running")
        print("  - Long-running workers processing tasks")
        print("  - Service receives shutdown signal (SIGTERM)")
        print("  - Problem: Abrupt shutdown loses data")
        print()
        print("THE PROBLEM:")
        print("  Without graceful shutdown:")
        print("    ❌ SIGTERM → workers killed immediately")
        print("    ❌ Tasks in progress → lost")
        print("    ❌ Data corruption → inconsistent state")
        print("    ❌ No cleanup → resource leaks")
        print()
        print("THE SOLUTION:")
        print("  With graceful shutdown:")
        print("    ✅ Signal handler catches SIGTERM")
        print("    ✅ Workers finish current tasks")
        print("    ✅ Cleanup resources properly")
        print("    ✅ Save state before exit")
        print("    ✅ System reliability → production-ready")
        print()
        print("=" * 70)
        print()

        shutdown_event = multiprocessing.Event()
        tasks_completed = multiprocessing.Value('i', 0)
        tasks_lock = multiprocessing.Lock()

        def signal_handler(signum, frame):
            """Handle shutdown signal gracefully."""
            print(f"\n  Received signal {signum}, initiating graceful shutdown...")
            shutdown_event.set()

        def worker_process(worker_id: int) -> None:
            """Worker that respects shutdown signal."""
            tasks_done = 0
            while not shutdown_event.is_set():
                # Process task
                with tasks_lock:
                    tasks_completed.value += 1
                    tasks_done = tasks_completed.value
                
                print(f"  Worker {worker_id}: Processing task {tasks_done}")
                time.sleep(0.1)  # Simulate work
                
                # Check shutdown periodically
                if shutdown_event.is_set():
                    print(f"  Worker {worker_id}: Shutdown signal received, finishing current task...")
                    break

            print(f"  Worker {worker_id}: Gracefully shut down (completed {tasks_done} tasks)")

        # Set up signal handler
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        print("Starting service...")
        print("  - 3 workers processing tasks")
        print("  - Simulating shutdown after 1 second")
        print()

        workers = [
            multiprocessing.Process(target=worker_process, args=(i+1,))
            for i in range(3)
        ]

        for w in workers:
            w.start()

        # Simulate shutdown after 1 second
        time.sleep(1.0)
        print("\n  Simulating SIGTERM signal...")
        shutdown_event.set()

        for w in workers:
            w.join(timeout=5)

        print()
        print("Results:")
        print(f"  Tasks completed before shutdown: {tasks_completed.value}")
        print("  ✅ Graceful shutdown completed successfully!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. GRACEFUL SHUTDOWN BEST PRACTICES:")
        print("   ✅ Handle SIGTERM and SIGINT")
        print("   ✅ Workers check shutdown signal periodically")
        print("   ✅ Finish current tasks before exit")
        print("   ✅ Cleanup resources in finally blocks")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents data loss")
        print("   - Ensures data consistency")
        print("   - Prevents resource leaks")
        print("   - Production-ready systems")
        print("=" * 70)
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

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    example.map_reduce_real_world_example()
    example.pipeline_real_world_example()
    example.graceful_shutdown_real_world_example()

    print("All advanced patterns examples completed!")


if __name__ == "__main__":
    # Set start method for cross-platform compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()


"""
🎯 Key Advanced Patterns Demonstrated:
Custom Worker Initialization - Setup code that runs once per worker process
Map-Reduce - Distributed data processing with parallel map and sequential reduce phases
Pipeline Processing - Multi-stage data processing with queues between stages
Work Stealing - Dynamic load balancing across worker processes
Process Monitoring - Health checks and performance tracking
Graceful Shutdown - Proper cleanup on termination signals
Resource Management - Tracking and cleanup of shared resources
🔑 Why Advanced Patterns Matter:
Production Ready - Real-world patterns for scalable applications
Resource Efficiency - Proper initialization and cleanup
Fault Tolerance - Monitoring and graceful failure handling
Scalability - Pipelines and work stealing for large workloads
Maintainability - Structured patterns for complex systems
Reliability - Comprehensive error handling and cleanup
This file shows enterprise-grade multiprocessing patterns essential for building robust, scalable distributed systems! 🚀⚙️🏗️
"""