"""
Async generators examples demonstrating async iteration and streaming.

This module covers:
- Defining async generators with async def and yield
- Using async for loops for iteration
- Async generator cleanup with aclose()
- Combining async generators with other async constructs
- Real-world streaming examples (data processing, API responses)
- Error handling in async generators
"""

import asyncio # For asynchronous coroutine operations
import random # For random numbers
import time # For timestamps
from typing import AsyncGenerator, List, Tuple # AsyncGenerator type hint for async generators


class AsyncGeneratorExample:
    """
    Examples of async generators for streaming and iteration.

    Async generators combine the power of generators (lazy evaluation, memory efficiency)
    with async/await (non-blocking I/O, concurrency). They're essential for streaming
    data processing, real-time feeds, and memory-efficient data pipelines.

    When to Use:
        - Processing large datasets without loading everything into memory
        - Streaming data from APIs, databases, or files
        - Real-time data feeds (logs, metrics, events)
        - Data pipelines with multiple processing stages
        - Memory-constrained environments

    Real-World Examples:
        - API pagination: Stream paginated API responses
        - Log processing: Process log files line-by-line
        - Database cursors: Stream query results
        - WebSocket messages: Stream real-time messages
        - File processing: Process large files in chunks

    Gotchas:
        - Must use async for (not regular for) to iterate
        - Generators must be closed with aclose() if iteration stops early
        - Exceptions in generators propagate to consumer
        - Cannot use return statement with value (use yield instead)
        - StopAsyncIteration is raised when generator exhausts

    Performance Notes:
        - Memory efficient: Only holds one item at a time
        - Lazy evaluation: Values generated on-demand
        - Can process infinite streams
        - Overhead minimal compared to loading all data
        - Use for large or unbounded data sources
    """

    async def simple_async_generator(self, count: int) -> AsyncGenerator[int, None]:
        """
        Simple async generator that yields numbers with delays.

        Demonstrates the basic pattern of async generators: async def + yield.
        Each yield pauses execution and returns control to the caller.

        When to Use:
            - Generating sequences with async delays
            - Simulating async data sources
            - Learning async generator basics
            - Creating test data streams

        Real-World Examples:
            - Paginated API: Yield pages one at a time
            - Database cursor: Yield rows as they're fetched
            - Sensor data: Yield readings as they arrive
            - Event stream: Yield events as they occur

        Gotchas:
            - Return type AsyncGenerator[int, None] indicates async generator
            - None means no send value (generator doesn't accept input)
            - Each yield pauses and yields control
            - Generator state is preserved between yields
            - Must be consumed with async for or aiter/anext

        Args:
            count: Number of items to generate

        Yields:
            Sequential numbers from 0 to count-1
        """
        for i in range(count):
            await asyncio.sleep(0.1)  # Simulate async work and always wait 0.1 seconds before yielding the next value
            yield i # yield makes this a generator. Each yield pauses execution and returns a value

    async def fibonacci_async_generator(self, n: int) -> AsyncGenerator[int, None]:
        """
        Async generator for Fibonacci sequence.

        Demonstrates stateful async generators that maintain state between yields.
        Useful for sequences that depend on previous values.

        When to Use:
            - Generating mathematical sequences
            - Stateful data generation
            - Sequences with dependencies
            - Infinite sequences (with proper termination)

        Real-World Examples:
            - ID generation: Generate sequential IDs with delays
            - Time series: Generate time-series data points
            - Sequence numbers: Generate sequence numbers for messages
            - Counter streams: Generate counter values over time

        Gotchas:
            - State persists between yields
            - Can generate infinite sequences (be careful!)
            - Each yield pauses execution
            - State is generator-specific (each instance has own state)

        Args:
            n: Number of Fibonacci numbers to generate

        Yields:
            Fibonacci numbers starting from 0, 1, 1, 2, 3, 5...
        """
        a, b = 0, 1
        for _ in range(n):
            await asyncio.sleep(0.05)  # Simulate computation time
            yield a
            a, b = b, a + b

    async def basic_async_iteration(self) -> None:
        """
        Demonstrate basic async generator usage.

        Shows how to consume async generators using async for loops.
        This is the most common pattern for iterating over async generators.

        When to Use:
            - Consuming async generators
            - Processing async data streams
            - Iterating over async sequences
            - Learning async iteration patterns

        Real-World Examples:
            - Processing API responses: async for page in paginated_api()
            - Reading log files: async for line in async_read_logs()
            - Database queries: async for row in async_query()
            - WebSocket messages: async for msg in websocket_stream()

        Gotchas:
            - Must use async for (not regular for)
            - Loop automatically handles StopAsyncIteration
            - Generator pauses at each yield
            - Can break early (but should close generator)
            - Exception handling works normally

        Performance Notes:
            - Efficient: Only one item in memory at a time
            - Non-blocking: Yields control during async operations
            - Can process infinite streams
        """
        print("=== Basic Async Iteration ===")

        # async for - KEY: Special syntax for iterating over async generators

        print("Iterating over simple async generator:")
        async for number in self.simple_async_generator(5):
            print(f"Received: {number}")

        print("\nFibonacci sequence:")
        async for fib_num in self.fibonacci_async_generator(8):
            print(f"Fib: {fib_num}")

        print()

    async def async_generator_with_exception(self) -> AsyncGenerator[str, None]:
        """
        Async generator that demonstrates exception handling.

        Shows how exceptions propagate from generators to consumers and how
        to handle cleanup in finally blocks.

        When to Use:
            - Handling errors in data streams
            - Implementing robust streaming pipelines
            - Error recovery in generators
            - Cleanup on errors

        Real-World Examples:
            - API clients: Handle API errors gracefully
            - File readers: Handle file read errors
            - Database cursors: Handle query errors
            - Network streams: Handle connection errors

        Gotchas:
            - Exceptions propagate to consumer
            - finally blocks always execute (good for cleanup)
            - Can yield error messages before raising
            - Consumer should handle exceptions
            - Generator state may be inconsistent after exception

        Yields:
            Status messages, including error messages if exception occurs
        """
        try:
            for i in range(5):
                if i == 3:
                    raise ValueError("Simulated error at iteration 3")
                await asyncio.sleep(0.1)
                yield f"Step {i+1}"
        except Exception as e:
            yield f"Error occurred: {e}"
        finally:
            yield "Cleanup completed"

    async def exception_handling_example(self) -> None:
        """
        Demonstrate exception handling in async generators.

        Shows how exceptions in generators are handled by consumers.
        Important for building robust streaming systems.

        When to Use:
            - Understanding exception propagation in generators
            - Building error-tolerant data pipelines
            - Handling failures in streaming operations
            - Learning error handling patterns

        Real-World Examples:
            - Retry logic: Retry on transient errors
            - Error logging: Log errors without stopping stream
            - Fallback data: Provide fallback on errors
            - Circuit breakers: Stop stream on repeated errors

        Gotchas:
            - Exceptions propagate immediately to consumer
            - Generator state may be inconsistent after exception
            - finally blocks execute even on exceptions
            - Consumer must handle exceptions appropriately
            - Consider yielding error info before raising
        """
        print("=== Exception Handling in Async Generators ===")

        try:
            async for item in self.async_generator_with_exception():
                print(f"Generator output: {item}")
        except Exception as e:
            print(f"Caught exception outside generator: {e}")

        print()

    async def data_streaming_generator(self, chunk_size: int = 3) -> AsyncGenerator[List[int], None]:
        """
        Async generator that simulates streaming data in chunks.

        Demonstrates chunked data streaming, which is common for processing
        large datasets efficiently without loading everything into memory.

        When to Use:
            - Processing large datasets in chunks
            - Streaming data from APIs or databases
            - Batch processing with async operations
            - Memory-efficient data processing

        Real-World Examples:
            - API pagination: Process pages of results
            - File processing: Process files in chunks
            - Database batching: Process query results in batches
            - Log processing: Process log files in chunks
            - Data import: Import data in batches

        Gotchas:
            - Chunk size affects memory usage and performance
            - Last chunk may be smaller than chunk_size
            - Consumer can break early (should close generator)
            - Chunks are yielded as they're ready (not all at once)
            - Processing time affects throughput

        Performance Notes:
            - Memory efficient: Only one chunk in memory
            - Can process very large datasets
            - Chunk size balances memory vs overhead
            - Optimal chunk size depends on data and processing

        Args:
            chunk_size: Size of each data chunk

        Yields:
            Chunks of data as lists
        """
        total_items = 12
        for i in range(0, total_items, chunk_size):
            # Simulate network delay or I/O
            await asyncio.sleep(0.2)

            # range(0, 3) = [0, 1, 2]
            # range(3, 6) = [3, 4, 5]
            # range(6, 9) = [6, 7, 8]
            # range(9, 12) = [9, 10, 11]
            chunk = list(range(i, min(i + chunk_size, total_items)))
            print(f"Generated chunk: {chunk}")

            # yields it — gives that chunk to the consumer, pausing here until the consumer  (i.e. whomever calls or uses this function) is ready for the next one
            # suspends the generator until the consumer calls for the next chunk.
            yield chunk

    async def streaming_consumer(self) -> None:
        """
        Demonstrate consuming streaming data.

        Shows how to consume chunked data streams and handle early termination.
        Important for processing large datasets efficiently.

        When to Use:
            - Consuming chunked data streams
            - Processing data as it arrives
            - Implementing early termination logic
            - Building data processing pipelines

        Real-World Examples:
            - Data processing: Process data as it streams in
            - Search results: Stop when enough results found
            - Monitoring: Process metrics as they arrive
            - ETL pipelines: Transform data as it streams

        Gotchas:
            - Can break early from loop
            - Should close generator if breaking early (use aclose())
            - Processing time affects generator throughput
            - Memory accumulates if not processing fast enough
            - Consider backpressure for slow consumers

        Performance Notes:
            - Process chunks as they arrive (low latency)
            - Memory efficient (only one chunk at a time)
            - Early termination saves resources
            - Processing speed should match generation speed
        """
        print("=== Streaming Data Consumption ===")

        total_received = []
        
        # when each iteration done within this async for then its producer resumes execution and yields new value and then again as this below async for works (meantime producr paused)
        async for chunk in self.data_streaming_generator():
            print(f"Processing chunk: {chunk}")
            total_received.extend(chunk)

            # Simulate processing time
            await asyncio.sleep(0.1)

            # Could add early termination logic here and break out of the loop
            if len(total_received) >= 8:
                print("Received enough data, stopping...")
                break


        print(f"Total items received: {len(total_received)}")
        print(f"Items: {total_received}")
        print()

    async def async_generator_with_aiter(self) -> AsyncGenerator[str, None]:
        """
        Async generator demonstrating aiter() usage.

        Yields:
            Status messages
        """
        messages = ["Starting", "Processing", "Almost done", "Complete"]

        for message in messages:
            await asyncio.sleep(0.15)
            yield message

    """
    -- This is a low-level manual version that async for does
    -- aiter() - KEY: Converts async iterable to async iterator
    -- anext() - KEY: Manually get next item from async iterator
    -- StopAsyncIteration - KEY: Exception raised when iteration is complete
    """
    async def aiter_example(self) -> None:
        """Demonstrate aiter() and anext() functions."""
        print("=== aiter() and anext() Usage ===")

        # self.async_generator_with_aiter() returns an async generator object (that could be iterable) but it is not yet iterable.

        # Create async iterator object (that could be iterable) from the async generator that looks like <async_generator object> and now That object can yield values one by one when you call await anext(async_iter).
        async_iter = aiter(self.async_generator_with_aiter())

        try:
            while True:

                """
                --So, await anext(async_iter):
                -- Starts or resumes the async generator

                -- Waits until it reaches the next yield

                -- Returns that yielded value

                -- If the generator finishes (no more yields), anext() raises a StopAsyncIteration exception.

                -- That’s exactly what Python’s async for loop does automatically under the hood.
                """

                item = await anext(async_iter) # gets the next item from it, awaiting it as needed.
                print(f"Manual iteration: {item}")
        except StopAsyncIteration:
            print("Iteration completed")

        print()

    async def async_generator_cleanup(self) -> AsyncGenerator[str, None]:
        """
        Async generator that demonstrates proper cleanup.

        Yields:
            Resource usage messages
        """
        resource_id = f"resource_{random.randint(1000, 9999)}"
        print(f"🔓 Acquired resource: {resource_id}")

        try:
            for i in range(4):
                await asyncio.sleep(0.1)
                yield f"Using {resource_id} - step {i+1}"
        finally:
            print(f"🧹 Cleaning up resource: {resource_id}")
            await asyncio.sleep(0.05)  # Simulate cleanup
            print(f"✅ Resource {resource_id} cleaned up")

    async def cleanup_example(self) -> None:
        """
        Demonstrate async generator cleanup with aclose().

        Shows how to properly close async generators when stopping early.
        Critical for resource management and preventing leaks.

        When to Use:
            - Stopping iteration early
            - Releasing resources held by generators
            - Ensuring cleanup code executes
            - Preventing resource leaks

        Real-World Examples:
            - Database connections: Close connections on early exit
            - File handles: Close files when done early
            - Network connections: Close connections on cancellation
            - Locks: Release locks on early termination

        Gotchas:
            - async for automatically closes on completion
            - Must manually call aclose() if breaking early
            - aclose() triggers finally block execution
            - Generator cannot be used after aclose()
            - Always close generators that hold resources

        Performance Notes:
            - Proper cleanup prevents resource leaks
            - Early termination saves resources
            - Cleanup overhead is minimal
        """
        print("=== Async Generator Cleanup ===")

        gen = self.async_generator_cleanup()

        # Use some items
        try:
        async for item in gen:
            print(f"Received: {item}")
            if "step 2" in item:
                print("Decided to stop early, closing generator...")
                    await gen.aclose()  # Proper cleanup on early exit
                    break
        except Exception:
            # Ensure cleanup on exception
            await gen.aclose()
        finally:
            # Ensure cleanup even if exception occurs (aclose is idempotent)
            try:
                await gen.aclose()
            except (RuntimeError, StopAsyncIteration):
                # Generator already closed or exhausted
                pass

        print("Generator closed and cleaned up\n")

    async def concurrent_async_generators(self) -> None:
        """
        Demonstrate running multiple async generators concurrently.

        Shows how to process multiple async generators simultaneously using
        asyncio.gather(). Useful for parallel data processing.

        When to Use:
            - Processing multiple data streams in parallel
            - Aggregating results from multiple sources
            - Parallel data processing
            - Fan-out/fan-in patterns

        Real-World Examples:
            - Multiple API calls: Fetch from multiple APIs concurrently
            - Database shards: Query multiple shards in parallel
            - File processing: Process multiple files concurrently
            - Data aggregation: Aggregate from multiple sources

        Gotchas:
            - Each generator runs independently
            - Results order matches input order (gather preserves order)
            - Exceptions in one generator don't stop others (with return_exceptions)
            - Memory usage multiplies by number of generators
            - Use semaphores to limit concurrent generators

        Performance Notes:
            - Parallel processing improves throughput
            - Limited by slowest generator
            - Memory usage increases with concurrency
            - Optimal concurrency depends on I/O vs CPU
        """
        print("=== Concurrent Async Generators ===")

        async def process_generator(gen_id: str, count: int) -> List[int]:
            """Process items from an async generator."""
            results = []
            async for item in self.simple_async_generator(count):
                results.append(f"{gen_id}:{item}")
                await asyncio.sleep(0.05)  # Simulate processing
            return results

        # Run multiple generators concurrently
        tasks = [
            process_generator("GenA", 4),
            process_generator("GenB", 3),
            process_generator("GenC", 5)
        ]

        results = await asyncio.gather(*tasks)

        print("Results from all generators:")
        for i, result in enumerate(results):
            print(f"  Generator {i+1}: {result}")

        print()

    async def nested_async_generators(self) -> AsyncGenerator[str, None]:
        """
        Async generator that yields from other async generators.

        Yields:
            Combined output from nested generators
        """
        async for item in self.simple_async_generator(3):
            yield f"Outer-{item}"
            # Simulate nested processing
            async for sub_item in self.fibonacci_async_generator(2):
                yield f"  Nested-{item}:{sub_item}"

    async def nested_iteration_example(self) -> None:
        """Demonstrate nested async generator iteration."""
        print("=== Nested Async Generators ===")

        async for item in self.nested_async_generators():
            print(f"Processing: {item}")
            await asyncio.sleep(0.05)

        print()

    async def async_generator_with_timeout(self, timeout: float = 2.0) -> AsyncGenerator[str, None]:
        """
        Async generator with timeout simulation.

        Args:
            timeout: Maximum time to run

        Yields:
            Progress messages
        """
        start_time = time.time()
        i = 0

        while time.time() - start_time < timeout:
            await asyncio.sleep(0.2)
            yield f"Progress update {i+1}"
            i += 1

        yield "Timeout reached, stopping"

    async def timeout_example(self) -> None:
        """Demonstrate timeout handling with async generators."""
        print("=== Timeout Handling ===")

        async for message in self.async_generator_with_timeout(1.0):
            print(f"Status: {message}")

        print()

    async def real_world_streaming_example(self) -> AsyncGenerator[dict, None]:
        """
        Simulate a real-world streaming data source (like API responses).

        Demonstrates realistic streaming patterns with multiple data types,
        variable delays, and structured data. Common pattern for real-time
        data processing systems.

        When to Use:
            - Processing real-time event streams
            - Handling multiple data types in one stream
            - Simulating production data sources
            - Building monitoring and analytics systems

        Real-World Examples:
            - Event streams: User actions, system events, errors
            - Metrics collection: CPU, memory, disk metrics
            - Log aggregation: Collecting logs from multiple sources
            - Analytics: Real-time analytics data streams
            - IoT data: Sensor readings and device events

        Gotchas:
            - Streams can be infinite (need termination condition)
            - Variable delays simulate real-world unpredictability
            - Multiple data types require type checking
            - Consumer must handle all data types
            - Consider backpressure for slow consumers

        Performance Notes:
            - Processes data as it arrives (low latency)
            - Memory efficient (one item at a time)
            - Can handle high-throughput streams
            - Variable delays affect throughput

        Yields:
            Dictionaries with different structures based on data type
        """
        # Simulate different types of data streams
        data_types = ["user_activity", "system_metrics", "error_logs"]

        for data_type in data_types:
            # Simulate batch processing
            batch_size = random.randint(3, 7)

            for i in range(batch_size):
                # Simulate network delay
                await asyncio.sleep(random.uniform(0.1, 0.3))

                # Generate realistic-looking data
                if data_type == "user_activity":
                    item = {
                        "type": "user_action",
                        "user_id": f"user_{random.randint(1000, 9999)}",
                        "action": random.choice(["login", "click", "purchase", "logout"]),
                        "timestamp": time.time(),
                        "session_id": f"session_{random.randint(10000, 99999)}"
                    }
                elif data_type == "system_metrics":
                    item = {
                        "type": "system_metric",
                        "metric": random.choice(["cpu_usage", "memory_usage", "disk_io"]),
                        "value": random.uniform(0, 100),
                        "server": f"server-{random.randint(1, 10)}",
                        "timestamp": time.time()
                    }
                else:  # error_logs
                    item = {
                        "type": "error_log",
                        "level": random.choice(["ERROR", "WARNING", "CRITICAL"]),
                        "message": f"Simulated error {random.randint(100, 999)}",
                        "component": random.choice(["auth", "database", "network", "cache"]),
                        "timestamp": time.time()
                    }

                yield item

    async def real_world_processing(self) -> None:
        """Demonstrate real-world streaming data processing."""
        print("=== Real-World Streaming Example ===")

        # Process streaming data
        user_actions = []
        system_metrics = []
        error_count = 0

        async for item in self.real_world_streaming_example():
            if item["type"] == "user_action":
                user_actions.append(item)
                print(f"👤 User {item['user_id']} performed {item['action']}")
            elif item["type"] == "system_metric":
                system_metrics.append(item)
                print(f"📊 {item['server']}: {item['metric']} = {item['value']:.1f}")
            elif item["type"] == "error_log":
                error_count += 1
                print(f"❌ {item['level']} in {item['component']}: {item['message']}")

            # Simulate processing delay
            await asyncio.sleep(0.05)

        print("\n📈 Streaming Summary:")
        print(f"  User actions processed: {len(user_actions)}")
        print(f"  System metrics collected: {len(system_metrics)}")
        print(f"  Errors logged: {error_count}")
        print()

    async def async_generator_pipeline(self) -> AsyncGenerator[Tuple[str, int], None]:
        """
        Async generator pipeline: raw data -> processing -> results.

        Demonstrates how to chain async generators to create processing pipelines.
        Each stage transforms data and passes it to the next stage.

        When to Use:
            - Multi-stage data processing
            - ETL pipelines
            - Data transformation workflows
            - Chaining processing steps
            - Building composable data pipelines

        Real-World Examples:
            - ETL pipelines: Extract -> Transform -> Load
            - Data processing: Filter -> Transform -> Aggregate
            - Log processing: Parse -> Filter -> Analyze
            - Image processing: Load -> Resize -> Compress
            - Text processing: Tokenize -> Filter -> Analyze

        Gotchas:
            - Each stage is an async generator
            - Can chain multiple generators together
            - Pipeline processes one item at a time
            - Errors propagate through pipeline
            - Memory efficient (one item per stage)

        Performance Notes:
            - Processes items sequentially through pipeline
            - Memory efficient (one item per stage)
            - Pipeline latency = sum of stage latencies
            - Can parallelize independent stages
            - Backpressure flows backward through pipeline

        Yields:
            Processed data tuples (name, transformed_value)
        """
        # Stage 1: Generate raw data
        async for raw_item in self.simple_async_generator(6):
            # Stage 2: Transform data
            transformed = raw_item * 10

            # Stage 3: Add metadata
            result = (f"item_{raw_item}", transformed)

            await asyncio.sleep(0.1)  # Simulate pipeline delay
            yield result

    async def pipeline_example(self) -> None:
        """Demonstrate async generator pipeline processing."""
        print("=== Async Generator Pipeline ===")

        print("Processing pipeline: raw -> transform -> result")
        async for name, value in self.async_generator_pipeline():
            print(f"  {name} -> {value}")

        print()

    async def async_generator_real_world_example(self) -> None:
        """
        Real-World Scenario: Async Generator - Streaming API Data.

        REAL-WORLD SCENARIO:
        ====================
        You're building a data streaming system:
        - Fetch data from paginated API
        - Process data as it arrives (don't wait for all pages)
        - Problem: Loading all data into memory too slow/expensive
        
        THE PROBLEM WITHOUT ASYNC GENERATORS:
        ======================================
        - Fetch all pages → wait for all data → slow
        - Load all data into memory → memory explosion
        - Can't process until all fetched → high latency
        - No streaming → inefficient
        - System overwhelmed → poor performance
        
        THE SOLUTION:
        =============
        Async generators enable:
        - Yield data as it arrives → low latency
        - Process data incrementally → low memory
        - Stream processing → efficient
        - Start processing immediately → responsive
        - Memory efficient → scalable
        
        WHEN TO USE ASYNC GENERATORS:
        =============================
        ✅ Streaming data from APIs
        ✅ Paginated data processing
        ✅ Large dataset processing
        ✅ Real-time data feeds
        ✅ Memory-efficient data pipelines
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Streaming API Data")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Data streaming system")
        print("  - Fetch data from paginated API")
        print("  - Process data as it arrives (don't wait for all pages)")
        print("  - Problem: Loading all data into memory too slow/expensive")
        print()
        print("THE PROBLEM:")
        print("  Without async generators:")
        print("    ❌ Fetch all pages → wait for all data → slow")
        print("    ❌ Load all data into memory → memory explosion")
        print("    ❌ Can't process until all fetched → high latency")
        print("    ❌ No streaming → inefficient")
        print()
        print("THE SOLUTION:")
        print("  With async generators:")
        print("    ✅ Yield data as it arrives → low latency")
        print("    ✅ Process data incrementally → low memory")
        print("    ✅ Stream processing → efficient")
        print("    ✅ Start processing immediately → responsive")
        print()
        print("=" * 70)
        print()

        async def paginated_api_generator(total_pages: int) -> AsyncGenerator[dict, None]:
            """Simulate paginated API that yields data page by page."""
            for page in range(1, total_pages + 1):
                await asyncio.sleep(0.05)  # Simulate API call delay
                # Yield page data
                yield {
                    "page": page,
                    "data": [f"item_{page}_{i}" for i in range(10)],
                    "total_items": page * 10
                }

        print("Streaming data from paginated API (5 pages)...")
        print("  Processing data as it arrives...")
        print()

        processed_items = 0
        async for page_data in paginated_api_generator(5):
            print(f"  Received page {page_data['page']}: {len(page_data['data'])} items")
            # Process data immediately (don't wait for all pages)
            processed_items += len(page_data['data'])

        print()
        print("Results:")
        print(f"  Total items processed: {processed_items}")
        print("  ✅ Async generator enabled streaming data processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE ASYNC GENERATORS:")
        print("   ✅ Streaming data from APIs")
        print("   ✅ Paginated data processing")
        print("   ✅ Large dataset processing")
        print("   ✅ Real-time data feeds")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Low memory usage (process incrementally)")
        print("   - Low latency (start processing immediately)")
        print("   - Efficient streaming")
        print("   - Scalable for large datasets")
        print("=" * 70)
        print()


async def main() -> None:
    """Run all async generator examples."""
    print("Asyncio Generators Examples")
    print("=" * 28)

    example = AsyncGeneratorExample()

    await example.basic_async_iteration()
    await example.exception_handling_example()
    await example.streaming_consumer()
    await example.aiter_example()
    await example.cleanup_example()
    await example.concurrent_async_generators()
    await example.nested_iteration_example()
    await example.timeout_example()
    await example.real_world_processing()
    await example.pipeline_example()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    await example.async_generator_real_world_example()

    print("All async generator examples completed!")


if __name__ == "__main__":
    asyncio.run(main())


"""
🎯 Key Concepts Demonstrated:
async def + yield - Creating async generators
async for - Iterating over async generators
AsyncGenerator[T, None] - Type hints for async generators
aiter() / anext() - Manual async iteration
aclose() - Manual cleanup of async generators
Exception handling - In async generators with try/except/finally
Streaming data - Processing data as it becomes available
Concurrent generators - Multiple generators running simultaneously
Nested iteration - Generators calling other generators
Resource cleanup - Proper cleanup with finally blocks
Real-world patterns - API streaming, data pipelines, timeouts

🌊 Why Async Generators Matter:
Memory efficiency - Process large datasets without loading everything into memory
Streaming - Handle real-time data feeds, large files, API responses
Lazy evaluation - Generate values only when needed
Resource management - Proper cleanup of resources
Composability - Chain generators together in pipelines
Concurrency - Multiple generators can run simultaneously
"""