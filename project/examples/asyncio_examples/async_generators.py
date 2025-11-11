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
    """

    # async def with return type AsyncGenerator[int, None] - KEY: Indicates this is an async generator
    async def simple_async_generator(self, count: int) -> AsyncGenerator[int, None]:
        """
        Simple async generator that yields numbers with delays.

        Args:
            count: Number of items to generate

        Yields:
            Sequential numbers
        """
        for i in range(count):
            await asyncio.sleep(0.1)  # Simulate async work and always wait 0.1 seconds before yielding the next value
            yield i # yield makes this a generator. Each yield pauses execution and returns a value

    async def fibonacci_async_generator(self, n: int) -> AsyncGenerator[int, None]:
        """
        Async generator for Fibonacci sequence.

        Args:
            n: Number of Fibonacci numbers to generate

        Yields:
            Fibonacci numbers
        """
        a, b = 0, 1
        for _ in range(n):
            await asyncio.sleep(0.05)  # Simulate computation time
            yield a
            a, b = b, a + b

    async def basic_async_iteration(self) -> None:
        """Demonstrate basic async generator usage."""
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

        Yields:
            Status messages
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
        """Demonstrate exception handling in async generators."""
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

        Args:
            chunk_size: Size of each data chunk

        Yields:
            Chunks of data
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
        """Demonstrate consuming streaming data."""
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
        """Demonstrate async generator cleanup with aclose()."""
        print("=== Async Generator Cleanup ===")

        gen = self.async_generator_cleanup()

        # Use some items
        async for item in gen:
            print(f"Received: {item}")
            if "step 2" in item:
                print("Decided to stop early, closing generator...")
                await gen.aclose()
                break

        print("Generator closed and cleaned up\n")

    async def concurrent_async_generators(self) -> None:
        """Demonstrate running multiple async generators concurrently."""
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

        Yields:
            Simulated API response data
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

        Yields:
            Processed data tuples
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