"""
Concurrency patterns examples demonstrating different approaches to concurrent execution.

This module covers:
- Fan-out/fan-in patterns
- Worker pool patterns
- Pipeline patterns
- Producer-consumer patterns
- Scatter-gather patterns
- Circuit breaker patterns
- Timeout and cancellation patterns
"""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional


class ConcurrencyPatternsExample:
    """
    Examples of common concurrency patterns in asyncio.
    """

    async def worker_task(self, worker_id: str, task_data: Any) -> Dict[str, Any]:
        """
        Simulate a worker task that processes data.

        Args:
            worker_id: Identifier for the worker
            task_data: Data to process

        Returns:
            Processing result
        """
        # Simulate variable processing time
        processing_time = random.uniform(0.1, 0.5)
        await asyncio.sleep(processing_time)

        return {
            "worker": worker_id,
            "input": task_data,
            "result": f"processed_{task_data}",
            "processing_time": processing_time
        }

    """
    # Pitfalls & suggestions
    -- If any worker raises, awaiting its future will raise; catch exceptions per result if you want to continue.
    -- If you want to cancel remaining tasks on first failure, do so explicitly.
    """
    async def fan_out_fan_in_pattern(self) -> None:
        """Demonstrate fan-out/fan-in pattern."""
        print("=== Fan-Out/Fan-In Pattern ===")

        # Generate work items
        work_items = [f"task_{i}" for i in range(10)]
        print(f"Work items: {work_items}")

        # Fan-out: Create tasks for each work item
        print("\n📤 Fan-out: Creating worker tasks...")
        tasks = []
        for i, item in enumerate(work_items):
            worker_id = f"worker_{i % 3 + 1}"  # 3 workers
            task = asyncio.create_task(self.worker_task(worker_id, item))
            tasks.append(task)

        # Fan-in: Collect results as they complete
        print("📥 Fan-in: Collecting results...")
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            print(f"  ✓ {result['worker']} completed {result['input']}")

        print(f"\nTotal results collected: {len(results)}")
        print()

    async def worker_pool_pattern(
    self,
    num_workers: int = 3,
    work_items: Optional[list] = None,
    timeout: Optional[float] = None,
    exit_on_timeout: bool = True,
    use_put_nowait: bool = False,
) -> None:
    """
    Robust worker-pool with optional timeout behavior.

    Args:
        self: object with async worker_task(worker_id, item) coroutine.
        num_workers: number of concurrent worker coroutines to run.
        work_items: optional list of items to enqueue (defaults to 8 sample jobs).
        timeout: if set (float seconds), will use asyncio.wait_for(queue.get(), timeout).
                 If None (default) workers wait indefinitely for items.
        exit_on_timeout: only used if timeout is set.
            - True: worker breaks/returns on a TimeoutError (original behavior).
            - False: worker logs idle and continues waiting (safer).
        use_put_nowait: if True, uses put_nowait for enqueuing (fast, no backpressure).
        Default False -> await queue.put(...) (safe with maxsize).                
    """

    print("=== Worker Pool Pattern ===")

    # Default sample items if none provided
    if work_items is None:
        work_items = [f"job_{i}" for i in range(8)]

    # Create the asyncio queue (optionally you can pass maxsize to enable backpressure)
    work_queue: asyncio.Queue = asyncio.Queue()

    async def worker_pool_worker(worker_id: str, queue: asyncio.Queue):
        """Worker coroutine: get items, process them, always call task_done()."""
        while True:
            # Choose whether to use a timeout on queue.get() or wait indefinitely.
            try:
                if timeout is None:
                    item = await queue.get()  # blocks (suspends) until an item is available
                else:
                    # If timeout is set, we attempt to get an item with that timeout.
                    item = await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                # Timeout occurred while waiting for an item.
                # Behavior depends on exit_on_timeout flag.
                if exit_on_timeout:
                    print(f"🏭 {worker_id} timed out waiting for work (exiting).")
                    return  # Exit worker (original semantics)
                else:
                    print(f"🏭 {worker_id} idle for {timeout}s, continuing to wait...")
                    continue  # Retry getting an item

            # At this point we've successfully received an item from the queue.
            try:
                # Sentinel (poison pill) handling
                if item is None:
                    # We got the shutdown signal; break out so the worker can finish.
                    # (task_done will be called in finally for this get)
                    print(f"🛑 {worker_id} received shutdown sentinel")
                    break

                # process the item (suspends inside worker_task)
                result = await self.worker_task(worker_id, item)

                # Print nicely, handling optional processing_time metadata
                proc_time = result.get("processing_time")
                if proc_time is not None:
                    print(f"🏭 {result['worker']} processed {result['input']} ({proc_time:.2f}s)")
                else:
                    print(f"🏭 {result['worker']} processed {result['input']}")

            except Exception as e:
                # Log and continue — always ensure task_done in finally
                print(f"❌ {worker_id} error while processing {item}: {e}")
            finally:
                # IMPORTANT: always notify queue that this 'get' has been processed.
                # This runs whether processing succeeded, raised, or the item was sentinel.
                queue.task_done()

        # Worker exiting gracefully
        print(f"🏁 {worker_id} exiting")

    # --- Producer: enqueue work items ---
    if use_put_nowait:
        for it in work_items:
            work_queue.put_nowait(it)
    else:
        for it in work_items:
            await work_queue.put(it)

    print(f"Starting {num_workers} workers for {len(work_items)} jobs (timeout={timeout}, exit_on_timeout={exit_on_timeout})...")

    # Start workers (both version does same with nuanced differences)

    # workers = []
    # for i in range(num_workers):
    #     t = asyncio.create_task(worker_pool_worker(f"pool_worker_{i+1}", q))
    #     workers.append(t)
    #     await asyncio.sleep(0)  # let event loop schedule worker start

    # this is list comprehension version of the above
    workers = [
        asyncio.create_task(worker_pool_worker(f"pool_worker_{i+1}", work_queue))
        for i in range(num_workers)
    ]

    # suspends the caller (the coroutine that awaits it) until the queue’s internal counter unfinished_tasks becomes zero.
    await work_queue.join()

    # Enqueue one sentinel (None) per worker so they can shut down cleanly.
    # Use await queue.put to ensure no queue-full issues
    for _ in range(num_workers):
        if use_put_nowait:
            work_queue.put_nowait(None)
        else:
            await work_queue.put(None)

    # Wait for all worker tasks to exit. Use return_exceptions=True if you prefer not to raise.
    await asyncio.gather(*workers, return_exceptions=True)

    print("✅ Worker pool completed all tasks!\n")

   
    async def pipeline_pattern(self) -> None:
        """Demonstrate pipeline pattern with multiple stages."""
        print("=== Pipeline Pattern ===")

        async def stage1_producer(queue: asyncio.Queue) -> None:
            """Stage 1: Data production."""
            data_items = [f"data_{i}" for i in range(6)]
            for item in data_items:
                await queue.put({"stage": 1, "data": item})
                print(f"📦 Produced: {item}")
                await asyncio.sleep(0.1)

            # Signal end of data
            await queue.put(None)

        async def stage2_processor(input_queue: asyncio.Queue, output_queue: asyncio.Queue) -> None:
            """Stage 2: Data processing."""
            while True:
                item = await input_queue.get()
                if item is None:
                    await output_queue.put(None)
                    break

                # Process data
                processed = f"{item['data']}_processed"
                result = {"stage": 2, "original": item['data'], "processed": processed}
                await output_queue.put(result)
                print(f"⚙️  Processed: {item['data']} -> {processed}")
                await asyncio.sleep(0.15)

        async def stage3_consumer(queue: asyncio.Queue) -> None:
            """Stage 3: Data consumption."""
            results = []
            while True:
                item = await queue.get()
                if item is None:
                    break

                results.append(item)
                print(f"📊 Consumed: {item['original']} -> {item['processed']}")

            print(f"Pipeline processed {len(results)} items")

        # Create pipeline queues
        queue1 = asyncio.Queue()
        queue2 = asyncio.Queue()

        # Start pipeline stages
        producer = asyncio.create_task(stage1_producer(queue1))
        processor = asyncio.create_task(stage2_processor(queue1, queue2))
        consumer = asyncio.create_task(stage3_consumer(queue2))

        # Wait for pipeline completion
        await asyncio.gather(producer, processor, consumer)

        print()

    async def producer_consumer_pattern(self) -> None:
        """Demonstrate producer-consumer pattern with bounded buffer."""
        print("=== Producer-Consumer Pattern ===")

        async def producer(producer_id: str, queue: asyncio.Queue, max_items: int) -> None:
            """Producer that generates items."""
            for i in range(max_items):
                item = f"{producer_id}_item_{i+1}"

                # Wait if queue is full (simulate bounded buffer)
                while queue.qsize() >= 3:  # Max buffer size of 3
                    await asyncio.sleep(0.1)

                await queue.put(item)
                print(f"🛍️  {producer_id} produced: {item}")
                await asyncio.sleep(random.uniform(0.1, 0.3))

        async def consumer(consumer_id: str, queue: asyncio.Queue) -> None:
            """Consumer that processes items."""
            while True:
                try:
                    # Get item with timeout
                    item = await asyncio.wait_for(queue.get(), timeout=2.0)

                    # Process item
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    print(f"🍽️  {consumer_id} consumed: {item}")

                    queue.task_done()

                except asyncio.TimeoutError:
                    print(f"🍽️  {consumer_id} timed out, finishing...")
                    break

        # Create shared queue
        buffer = asyncio.Queue()

        # Start producers and consumers
        producers = [
            asyncio.create_task(producer(f"Producer_{i+1}", buffer, 4))
            for i in range(2)
        ]

        consumers = [
            asyncio.create_task(consumer(f"Consumer_{i+1}", buffer))
            for i in range(2)
        ]

        # Wait for producers to complete
        await asyncio.gather(*producers)

        # Wait for queue to be empty
        await buffer.join()

        # Cancel consumers (they'll timeout)
        for consumer_task in consumers:
            consumer_task.cancel()

        try:
            await asyncio.gather(*consumers, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        print("Producer-consumer pattern completed!\n")

    async def scatter_gather_pattern(self) -> None:
        """Demonstrate scatter-gather pattern for parallel processing."""
        print("=== Scatter-Gather Pattern ===")

        async def scatter_phase(tasks: List[str], num_workers: int) -> List[asyncio.Queue]:
            """Scatter phase: distribute work to worker queues."""
            queues = [asyncio.Queue() for _ in range(num_workers)]

            print(f"📤 Scattering {len(tasks)} tasks to {num_workers} workers...")

            # Distribute tasks round-robin
            for i, task in enumerate(tasks):
                queue_idx = i % num_workers
                await queues[queue_idx].put(task)
                print(f"  Task '{task}' -> Worker {queue_idx + 1}")

            # Signal end of work for each queue
            for queue in queues:
                await queue.put(None)

            return queues

        async def worker_process(worker_id: int, queue: asyncio.Queue) -> List[Dict[str, Any]]:
            """Worker process for scatter-gather."""
            results = []

            while True:
                task = await queue.get()
                if task is None:
                    break

                result = await self.worker_task(f"worker_{worker_id}", task)
                results.append(result)
                print(f"👷 Worker {worker_id} completed: {task}")

            return results

        async def gather_phase(queues: List[asyncio.Queue]) -> List[Dict[str, Any]]:
            """Gather phase: collect results from all workers."""
            print("📥 Gathering results from workers...")

            # Start worker processes
            worker_tasks = [
                worker_process(i + 1, queues[i])
                for i in range(len(queues))
            ]

            # Collect all results
            all_results = []
            worker_results = await asyncio.gather(*worker_tasks)

            for worker_result in worker_results:
                all_results.extend(worker_result)

            return all_results

        # Scatter phase
        tasks = [f"operation_{i+1}" for i in range(8)]
        queues = await scatter_phase(tasks, 3)

        # Gather phase
        results = await gather_phase(queues)

        print(f"Scatter-gather completed: {len(results)} results")
        for result in results:
            print(f"  {result['worker']}: {result['input']} -> {result['result']}")

        print()

    async def circuit_breaker_pattern(self) -> None:
        """Demonstrate circuit breaker pattern for fault tolerance."""
        print("=== Circuit Breaker Pattern ===")

        class AsyncCircuitBreaker:
            """Async circuit breaker implementation."""

            def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 2.0):
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = "closed"  # closed, open, half-open

            async def call(self, coro_func, *args, **kwargs):
                """Execute coroutine with circuit breaker protection."""
                if self.state == "open":
                    if self._should_attempt_reset():
                        self.state = "half-open"
                        print("🔄 Circuit breaker: attempting reset")
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = await coro_func(*args, **kwargs)
                    self._on_success()
                    return result

                except Exception as e:
                    self._on_failure()
                    raise e

            def _on_success(self):
                """Handle successful call."""
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                    print("✅ Circuit breaker: reset successful, closed")

            def _on_failure(self):
                """Handle failed call."""
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    print(f"🚫 Circuit breaker: opened after {self.failure_count} failures")

            def _should_attempt_reset(self) -> bool:
                """Check if we should attempt to reset the circuit."""
                if self.last_failure_time is None:
                    return True
                return time.time() - self.last_failure_time >= self.recovery_timeout

        async def unreliable_operation(should_fail: bool) -> str:
            """Unreliable operation that may fail."""
            if should_fail:
                await asyncio.sleep(0.1)
                raise Exception("Operation failed")
            await asyncio.sleep(0.2)
            return "Operation succeeded"

        # Create circuit breaker
        breaker = AsyncCircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        # Test operations
        test_cases = [True, True, False, False, True]  # fail, fail, succeed, succeed, fail

        print("Testing circuit breaker with mixed success/failure:")
        for i, should_fail in enumerate(test_cases):
            try:
                result = await breaker.call(unreliable_operation, should_fail)
                print(f"Test {i+1}: ✅ {result}")
            except Exception as e:
                print(f"Test {i+1}: ❌ {e}")

            await asyncio.sleep(0.5)

        print()

    async def timeout_cancellation_pattern(self) -> None:
        """Demonstrate timeout and cancellation patterns."""
        print("=== Timeout and Cancellation Patterns ===")

        async def cancellable_task(task_id: str, duration: float) -> str:
            """Task that can be cancelled."""
            try:
                print(f"🕐 Task {task_id} starting ({duration}s)...")
                await asyncio.sleep(duration)
                print(f"✅ Task {task_id} completed")
                return f"Task {task_id} result"
            except asyncio.CancelledError:
                print(f"🚫 Task {task_id} was cancelled")
                raise

        async def timeout_wrapper(task_coro, timeout: float) -> Any:
            """Wrap a task with timeout."""
            try:
                return await asyncio.wait_for(task_coro, timeout=timeout)
            except asyncio.TimeoutError:
                print(f"⏰ Task timed out after {timeout}s")
                raise

        # Test timeout
        print("Testing timeout behavior:")
        try:
            result = await timeout_wrapper(
                cancellable_task("timeout_test", 2.0),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            print("Timeout handled correctly")

        print()

        # Test cancellation
        print("Testing cancellation:")
        task = asyncio.create_task(cancellable_task("cancel_test", 3.0))

        # Let it run for a bit
        await asyncio.sleep(1.0)

        # Cancel the task
        task.cancel()

        try:
            result = await task
        except asyncio.CancelledError:
            print("Cancellation handled correctly")

        print()

        # Test multiple tasks with different timeouts
        print("Testing multiple tasks with different timeouts:")
        tasks = [
            timeout_wrapper(cancellable_task("fast", 0.5), timeout=2.0),
            timeout_wrapper(cancellable_task("slow", 2.0), timeout=1.0),
            timeout_wrapper(cancellable_task("medium", 1.0), timeout=2.0)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i+1}: ❌ {type(result).__name__}")
            else:
                print(f"Task {i+1}: ✅ {result}")

        print()

    async def concurrent_map_reduce(self) -> None:
        """Demonstrate map-reduce pattern with concurrency."""
        print("=== Concurrent Map-Reduce Pattern ===")

        async def map_function(data_chunk: List[int]) -> List[Tuple[str, int]]:
            """Map function: transform data."""
            results = []
            for num in data_chunk:
                # Simulate async mapping
                await asyncio.sleep(0.01)
                key = "even" if num % 2 == 0 else "odd"
                results.append((key, num))
            return results

        async def reduce_function(key: str, values: List[int]) -> Dict[str, Any]:
            """Reduce function: aggregate data."""
            await asyncio.sleep(0.05)  # Simulate reduction work
            return {
                "key": key,
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values) if values else 0
            }

        # Generate data
        data = list(range(1, 51))  # 1 to 50
        chunk_size = 10
        data_chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        print(f"Processing {len(data)} items in {len(data_chunks)} chunks")

        # Map phase: process chunks concurrently
        print("📊 Map phase...")
        map_tasks = [map_function(chunk) for chunk in data_chunks]
        map_results = await asyncio.gather(*map_results)

        # Flatten and shuffle (group by key)
        from collections import defaultdict
        shuffled = defaultdict(list)
        for chunk_result in map_results:
            for key, value in chunk_result:
                shuffled[key].append(value)

        # Reduce phase: process each key
        print("🔄 Reduce phase...")
        reduce_tasks = [reduce_function(key, values) for key, values in shuffled.items()]
        reduce_results = await asyncio.gather(*reduce_tasks)

        # Display results
        print("Map-Reduce Results:")
        for result in reduce_results:
            print(f"  {result['key'].upper()}: count={result['count']}, "
                  f"sum={result['sum']}, avg={result['avg']:.1f}")

        print()


async def main() -> None:
    """Run all concurrency pattern examples."""
    print("Asyncio Concurrency Patterns Examples")
    print("=" * 38)

    example = ConcurrencyPatternsExample()

    await example.fan_out_fan_in_pattern()
    await example.worker_pool_pattern()
    await example.pipeline_pattern()
    await example.producer_consumer_pattern()
    await example.scatter_gather_pattern()
    await example.circuit_breaker_pattern()
    await example.timeout_cancellation_pattern()
    await example.concurrent_map_reduce()

    print("All concurrency pattern examples completed!")


if __name__ == "__main__":
    asyncio.run(main())

"""
🎯 Key Concurrency Patterns Demonstrated:
Fan-out/Fan-in - Distribute work and collect results
Worker Pool - Fixed pool of workers processing queue items
Pipeline - Multi-stage data processing with queues
Producer-Consumer - Bounded buffer with backpressure
Scatter-Gather - Distribute and collect from multiple workers
Circuit Breaker - Fault tolerance with failure thresholds
Timeout/Cancellation - Graceful task termination
Map-Reduce - Parallel data processing and aggregation
🔑 Why These Patterns Matter:
Scalability - Handle varying workloads efficiently
Fault Tolerance - Circuit breakers prevent cascade failures
Resource Management - Bounded buffers prevent memory issues
Performance - Concurrent processing maximizes throughput
Maintainability - Well-known patterns are easier to understand
Real-world - These patterns solve common distributed system problems
This file provides a comprehensive toolkit of concurrency patterns essential for building robust, scalable async applications! 🚀📊
"""