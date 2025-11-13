"""
Basic asyncio examples demonstrating coroutines, event loops, tasks, and futures.

This module covers:
- Defining and calling coroutines with async/await
- Event loop management and execution
- Task creation and concurrent execution
- Future objects and result handling
- Synchronization with asyncio.sleep
- Exception handling in async code
"""

import asyncio # main package for async programming
import time # for timing operations and delays
from typing import Any, Coroutine # Type hints for better code readability and maintainability


class BasicAsyncioExample:
    """
    Basic asyncio examples for coroutines, tasks, and event loops.

    This class demonstrates fundamental async/await patterns and provides
    practical examples for common asyncio operations. Use this as a starting
    point for understanding async programming in Python.

    When to Use:
        - Learning async/await syntax and patterns
        - Understanding the difference between sequential and concurrent execution
        - Implementing I/O-bound operations that can benefit from concurrency
        - Building web servers, API clients, or data processing pipelines
        - Creating responsive applications that handle multiple operations simultaneously

    Real-World Examples:
        - Web scraping: Fetch multiple URLs concurrently instead of sequentially
        - API clients: Make multiple HTTP requests in parallel
        - Database operations: Execute multiple queries concurrently
        - File processing: Read/write multiple files simultaneously
        - Web servers: Handle multiple client connections concurrently

    Gotchas:
        - Coroutines don't run until awaited: Creating a coroutine doesn't execute it
        - Tasks vs coroutines: Tasks schedule coroutines for concurrent execution
        - Exception handling: Use return_exceptions=True in gather() to handle partial failures
        - Event loop: Only one event loop can run per thread
        - CPU-bound work: asyncio doesn't help with CPU-bound tasks (use multiprocessing)

    Performance Notes:
        - Concurrent execution can significantly speed up I/O-bound operations
        - Overhead: Creating many tasks has overhead; batch operations when possible
        - Memory: Each task consumes memory; limit concurrent tasks for large workloads
    """

    @staticmethod
    async def simple_coroutine(name: str, delay: float = 1.0) -> str:
        """
        A simple coroutine that simulates async work.

        This coroutine demonstrates the basic async/await pattern. It simulates
        an asynchronous operation (like network I/O or file reading) by sleeping
        for a specified duration.

        When to Use:
            - Simulating async I/O operations in tests and examples
            - Creating delay-based rate limiting or throttling
            - Demonstrating async patterns without external dependencies
            - Building mock services for development

        Real-World Examples:
            - Simulating API call delays in integration tests
            - Rate limiting: Adding delays between requests
            - Mock services: Simulating slow external services
            - Timeout testing: Testing timeout handling in async code

        Args:
            name: Coroutine identifier for logging and debugging
            delay: Delay in seconds to simulate async work duration

        Returns:
            Result message indicating completion

        Gotchas:
            - This uses asyncio.sleep() which yields control; time.sleep() would block
            - Multiple coroutines can run concurrently if scheduled as tasks
            - The delay is approximate; actual time may vary slightly
        """
        print(f"Coroutine {name} starting...")
        await asyncio.sleep(delay)
        print(f"Coroutine {name} completed after {delay}s")
        return f"Result from {name}"

    @staticmethod
    async def cpu_bound_simulation(iterations: int) -> int:
        """
        Simulate CPU-bound work using asyncio.sleep for context switching.

        This method demonstrates how to make CPU-bound work cooperative in async
        code by periodically yielding control. However, this is NOT the optimal
        solution for true CPU-bound work.

        When to Use:
            - Making CPU-bound code cooperative in async contexts
            - Preventing event loop blocking during long computations
            - Demonstrating context switching patterns
            - Temporary solution while migrating to multiprocessing

        Real-World Examples:
            - Image processing: Yield control during batch processing
            - Data transformation: Break up large computations into chunks
            - Parsing: Process large files in chunks with yields
            - Calculations: Long-running math operations with periodic yields

        Args:
            iterations: Number of iterations for the computation

        Returns:
            Computed result (sum of squares)

        Gotchas:
            - This is NOT efficient for CPU-bound work; use multiprocessing instead
            - Yielding too frequently adds overhead; too rarely blocks the event loop
            - The GIL still limits true parallelism; this only prevents blocking
            - For production CPU-bound work, use ProcessPoolExecutor

        Performance Notes:
            - Yielding every 1000 iterations balances responsiveness and overhead
            - True CPU-bound work should use multiprocessing or separate processes
            - This pattern is acceptable for mixed I/O and CPU workloads
        """
        result = 0
        for i in range(iterations):
            result += i ** 2
            # Yield control to allow other coroutines to run
            if i % 1000 == 0:
                await asyncio.sleep(0)  # Allow other tasks to run
        return result

    async def basic_coroutine_execution(self) -> None:
        """
        Demonstrate basic coroutine definition and sequential execution.

        This method shows how coroutines execute sequentially when awaited directly.
        Each coroutine must complete before the next one starts, resulting in
        total time equal to the sum of all delays.

        When to Use:
            - When operations must complete in order (dependency chain)
            - When you need the result of one operation before starting the next
            - For simple scripts where concurrency isn't needed
            - Understanding the baseline before optimizing with concurrency

        Real-World Examples:
            - Pipeline stages: Each stage needs the previous stage's output
            - Authentication flow: Login, then fetch user data, then load preferences
            - Sequential API calls: Create resource, then update it, then query it
            - File processing: Read file, then parse it, then save results

        Gotchas:
            - Sequential execution is slow for independent operations
            - Total time = sum of all operation times
            - No parallelism benefits; operations block each other
            - Use concurrent execution for independent operations

        Returns:
            Tuple containing results and execution time for comparison
        """
        print("=== Basic Coroutine Execution ===")

        # Call coroutines sequentially
        print("Sequential execution:")
        start_time = time.time()

        # only when result1 is done, result2 and result3 will start
        result1 = await self.simple_coroutine("A", 0.5)
        result2 = await self.simple_coroutine("B", 0.3)
        result3 = await self.simple_coroutine("C", 0.2)

        # so from here, we can see that the coroutines are executed `sequentially` and all these 3 coroutines are executed one after the other and in total takes 1.0 seconds to complete

        sequential_time = time.time() - start_time
        print(f"Sequential execution time: {sequential_time:.2f} seconds")
        print()
        return result1, result2, result3, sequential_time

    async def concurrent_execution(self) -> None:
        """
        Demonstrate concurrent execution of coroutines using tasks.

        This method shows how to run multiple coroutines concurrently by creating
        tasks. Tasks allow the event loop to interleave execution, resulting in
        total time approximately equal to the longest operation.

        When to Use:
            - When operations are independent and can run in parallel
            - I/O-bound operations that spend time waiting (network, disk)
            - Maximizing throughput for multiple similar operations
            - Building responsive applications that handle multiple requests

        Real-World Examples:
            - Web scraping: Fetch multiple pages simultaneously
            - API aggregation: Call multiple APIs in parallel
            - Database queries: Execute multiple independent queries concurrently
            - File operations: Read/write multiple files simultaneously
            - Web servers: Handle multiple client requests concurrently

        Gotchas:
            - Tasks start immediately when created, not when awaited
            - gather() preserves order of results, not execution order
            - Total time ≈ max(individual times) for I/O-bound operations
            - Creating too many tasks can exhaust resources; use semaphores to limit

        Performance Notes:
            - Concurrent execution can be 3-10x faster for I/O-bound operations
            - Overhead is minimal compared to I/O wait times
            - Memory usage increases with number of concurrent tasks
        """
        print("=== Concurrent Execution ===")

        print("Concurrent execution:")
        start_time = time.time()

        # Create task objects for concurrent execution however here with task coroutines has been created, ran with `juggling` not sequentially so it's faster here off course.
        task1 = asyncio.create_task(self.simple_coroutine("A", 0.5))
        task2 = asyncio.create_task(self.simple_coroutine("B", 0.3))
        task3 = asyncio.create_task(self.simple_coroutine("C", 0.2))

        # Wait for all tasks to complete then return the results in order
        results = await asyncio.gather(task1, task2, task3)

        # once again since here it runs concurrently, it takes less than 1.0 seconds to complete.

        concurrent_time = time.time() - start_time
        print(f"Concurrent execution time: {concurrent_time:.2f} seconds")
        print(f"Results: {results}")
        print()

    async def task_vs_coroutine(self) -> None:
        """
        Compare direct coroutine calls vs task creation.

        This method demonstrates the performance difference between sequential
        coroutine execution and concurrent task execution. Tasks enable
        concurrent execution while direct await is sequential.

        When to Use:
            - Understanding when to use tasks vs direct await
            - Deciding between sequential and concurrent execution
            - Learning the performance implications of each approach
            - Optimizing existing sequential code

        Real-World Examples:
            - Sequential: User authentication → fetch profile → load settings
            - Concurrent: Fetch user data, fetch posts, fetch comments simultaneously
            - Sequential: Create order → process payment → send confirmation
            - Concurrent: Load dashboard widgets independently

        Gotchas:
            - Direct await: Sequential, total time = sum of all times
            - Tasks: Concurrent, total time ≈ max of all times
            - Tasks have slight overhead; only beneficial for I/O-bound work
            - Tasks start immediately; don't create more than needed

        Performance Notes:
            - Tasks add ~0.1ms overhead per task
            - Benefit only visible for operations >10ms
            - For CPU-bound work, tasks don't help (use multiprocessing)
        """
        print("=== Task vs Coroutine Comparison ===")

        async def worker(task_id: str) -> str:
            """Worker coroutine."""
            await asyncio.sleep(0.5)
            return f"Task {task_id} result"

        # Method 1: Direct await (sequential)
        print("Direct await (sequential):")
        start_time = time.time()
        result1 = await worker("1")
        result2 = await worker("2")
        sequential_time = time.time() - start_time
        print(f"Sequential time: {sequential_time:.2f} seconds")

        # Method 2: Create tasks (concurrent)
        print("Task creation (concurrent):")
        start_time = time.time()
        task1 = asyncio.create_task(worker("1"))
        task2 = asyncio.create_task(worker("2"))
        results = await asyncio.gather(task1, task2)
        concurrent_time = time.time() - start_time
        print(f"Concurrent time: {concurrent_time:.2f} seconds")
        print()

    async def future_operations(self) -> None:
        """
        Demonstrate Future objects and their operations.

        Futures represent the result of an asynchronous operation that may not
        have completed yet. They allow checking status, waiting with timeouts,
        and handling results asynchronously.

        When to Use:
            - When you need to check if an operation completed without blocking
            - Implementing timeouts for async operations
            - Building cancellation mechanisms
            - Creating lower-level async primitives
            - Integrating with callback-based APIs

        Real-World Examples:
            - HTTP requests: Check if request completed, cancel if needed
            - Database queries: Monitor query status, implement timeouts
            - File operations: Check if file read completed
            - Long-running tasks: Monitor progress, allow cancellation
            - Integration: Wrap callback-based libraries in async interfaces

        Gotchas:
            - ensure_future() is deprecated; use create_task() for coroutines
            - Futures are done when they have a result OR an exception
            - Calling result() on a pending future will block
            - Exceptions are raised when calling result() on failed futures
            - wait() returns sets; order is not guaranteed

        Performance Notes:
            - Futures have minimal overhead
            - Useful for fine-grained control over async operations
            - Prefer gather() for simple "wait for all" scenarios
        """
        print("=== Future Operations ===")

        async def async_operation(name: str, delay: float) -> str:
            """Async operation that returns a Future."""
            await asyncio.sleep(delay)
            return f"Future result: {name}"

        # Create task objects from coroutines (ensure_future is deprecated)
        # Tasks are Futures, so we can use create_task() instead
        future1 = asyncio.create_task(async_operation("A", 0.3))
        future2 = asyncio.create_task(async_operation("B", 0.5))
        future3 = asyncio.create_task(async_operation("C", 0.2))

        print("Futures created, checking status...")
        print(f"Future1 done: {future1.done()}")
        print(f"Future2 done: {future2.done()}")
        print(f"Future3 done: {future3.done()}")

        # Wait for futures with timeout, return the results in order
        done, pending = await asyncio.wait(
            [future1, future2, future3],
            timeout=1.0,
            return_when=asyncio.ALL_COMPLETED
        )

        print(f"Completed: {len(done)}, Pending: {len(pending)}")

        # Get results from completed futures
        for future in done:
            try:
                result = future.result()
                print(f"Future result: {result}")
            except Exception as e:
                print(f"Future exception: {e}")

        print()

    async def exception_handling(self) -> None:
        """
        Demonstrate exception handling in async code.

        Exception handling in async code requires special consideration because
        exceptions can occur in concurrent tasks. This method shows different
        patterns for handling exceptions in async operations.

        When to Use:
            - Handling errors in concurrent operations
            - Implementing robust error recovery
            - Building fault-tolerant async systems
            - Gracefully handling partial failures
            - Creating resilient API clients

        Real-World Examples:
            - API clients: Some requests fail, others succeed
            - Web scraping: Some URLs fail, continue with others
            - Database operations: Handle connection errors gracefully
            - File processing: Skip corrupted files, process valid ones
            - Microservices: Handle service failures without crashing

        Gotchas:
            - gather() without return_exceptions=True stops on first exception
            - return_exceptions=True returns exceptions as results, doesn't raise
            - Exceptions in tasks are stored in the task, not raised immediately
            - Always check isinstance(result, Exception) when using return_exceptions
            - CancelledError is a special exception type for cancellations

        Performance Notes:
            - Exception handling has minimal overhead
            - return_exceptions=True allows partial success patterns
            - Consider retry logic for transient failures
        """
        print("=== Exception Handling ===")

        async def failing_coroutine(name: str, should_fail: bool = False) -> str:
            """Coroutine that may raise an exception."""
            await asyncio.sleep(0.2)
            if should_fail:
                raise ValueError(f"Simulated failure in {name}")
            return f"Success from {name}"

        # Handle exceptions in individual tasks
        print("Individual exception handling:")
        try:
            result1 = await failing_coroutine("Task1", False)
            print(f"Task1: {result1}")
        except Exception as e:
            print(f"Task1 failed: {e}")

        try:
            result2 = await failing_coroutine("Task2", True)
            print(f"Task2: {result2}")
        except Exception as e:
            print(f"Task2 failed: {e}")

        # Handle exceptions in gather
        print("\nException handling with gather:")
        tasks = [
            failing_coroutine("A", False),
            failing_coroutine("B", True),
            failing_coroutine("C", False)
        ]

        # return_exceptions=True - makes gather() return exceptions instead of raising them
        # This allows partial success: some tasks succeed, some fail
        results = await asyncio.gather(*tasks, return_exceptions=True) 
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {chr(65+i)} failed: {result}")
            else:
                print(f"Task {chr(65+i)} succeeded: {result}")

        # Demonstrate what happens without return_exceptions
        print("\nWithout return_exceptions (stops on first error):")
        try:
            await asyncio.gather(
                failing_coroutine("X", False),
                failing_coroutine("Y", True),  # This will cause gather to raise
                failing_coroutine("Z", False)  # This won't execute
            )
        except ValueError as e:
            print(f"Gather raised exception: {e}")
            print("Note: Task Z never executed because Y failed first")

        print()

    async def event_loop_info(self) -> None:
        """
        Demonstrate event loop information and management.

        The event loop is the core of asyncio. It manages the execution of
        coroutines, handles I/O events, and schedules callbacks. Understanding
        the event loop is crucial for advanced async programming.

        When to Use:
            - Understanding how asyncio works internally
            - Scheduling callbacks from sync code
            - Implementing custom async primitives
            - Debugging async code and event loop issues
            - Integrating with blocking libraries

        Real-World Examples:
            - Callbacks: Schedule cleanup from sync code
            - Timers: Implement periodic tasks
            - Integration: Bridge sync and async code
            - Monitoring: Track event loop performance
            - Custom protocols: Build async network protocols

        Gotchas:
            - get_running_loop() raises if no loop is running
            - get_event_loop() creates a new loop if none exists (deprecated)
            - Only one event loop can run per thread
            - call_soon() executes in next iteration; call_later() uses delay
            - Blocking operations freeze the event loop

        Performance Notes:
            - Event loop overhead is minimal (~1% CPU for idle loop)
            - call_soon() is very fast (~0.001ms)
            - Too many callbacks can slow down the event loop
        """
        print("=== Event Loop Information ===")

        loop = asyncio.get_running_loop() # gets the current event loop

        print(f"Event loop: {loop}")
        print(f"Loop is running: {loop.is_running()}") # checks if the loop is currently running
        print(f"Loop is closed: {loop.is_closed()}") # checks if the loop is closed

        # Get loop time
        start_time = loop.time()  # gets the current time of the loop
        await asyncio.sleep(0.1)
        end_time = loop.time()  # gets the current time of the loop

        print(f"Elapsed loop time: {end_time - start_time:.3f} seconds")

        # Schedule callback
        def callback():
            print("Callback executed in event loop")

        loop.call_soon(callback) # schedules a callback to be executed in the event loop

        # Schedule delayed callback
        def delayed_callback():
            print("Delayed callback executed")

        loop.call_later(0.2, delayed_callback) # Schedules a callback to be executed after a delay

        await asyncio.sleep(0.3) # waits for 0.3 seconds
        print()

    async def nested_coroutines(self) -> None:
        """
        Demonstrate nested coroutine calls and composition.

        Async code often involves calling coroutines from within other coroutines.
        This method shows how to compose async operations hierarchically and
        how to mix sequential and concurrent execution.

        When to Use:
            - Building complex async workflows
            - Composing multiple async operations
            - Creating reusable async components
            - Implementing layered async architectures
            - Organizing async code into logical units

        Real-World Examples:
            - API layers: Outer function calls multiple inner API functions
            - Data pipelines: Process data through multiple async stages
            - Web frameworks: Middleware → handler → response processing
            - Database operations: Transaction → queries → commit
            - Microservices: Orchestrate multiple service calls

        Gotchas:
            - Nested coroutines can be awaited sequentially or concurrently
            - gather() enables concurrent execution of nested operations
            - Deep nesting can make code hard to follow; use helper functions
            - Exception propagation works naturally through nested calls
            - Each level can have its own error handling

        Performance Notes:
            - Nesting adds minimal overhead
            - Concurrent nested operations provide best performance
            - Sequential nesting is fine when dependencies require it
        """
        print("=== Nested Coroutines ===")

        async def inner_operation(name: str) -> str:
            """Inner coroutine operation."""
            await asyncio.sleep(0.1)
            return f"Inner result: {name}"

        async def middle_operation(name: str) -> str:
            """Middle coroutine that calls inner operations."""
            result1 = await inner_operation(f"{name}-1")
            result2 = await inner_operation(f"{name}-2")
            await asyncio.sleep(0.1)
            return f"Middle result: {name} [{result1}, {result2}]"

        async def outer_operation() -> str:
            """Outer coroutine that orchestrates everything."""
            # Concurrent execution of middle operations
            tasks = [
                middle_operation("GroupA"),
                middle_operation("GroupB")
            ]

            results = await asyncio.gather(*tasks)
            return f"Outer result: {', '.join(results)}"

        result = await outer_operation()
        print(f"Final result: {result}")
        print()

    async def performance_comparison(self) -> None:
        """
        Compare performance of sequential vs concurrent execution.

        This method provides a quantitative comparison of sequential and
        concurrent execution patterns, demonstrating the performance benefits
        of proper async concurrency for I/O-bound operations.

        When to Use:
            - Understanding performance implications of async patterns
            - Benchmarking async code improvements
            - Deciding between sequential and concurrent execution
            - Demonstrating async benefits to stakeholders
            - Optimizing existing async code

        Real-World Examples:
            - API clients: Concurrent requests vs sequential requests
            - Web scraping: Parallel page fetching vs one-by-one
            - Database operations: Concurrent queries vs sequential
            - File processing: Parallel I/O vs sequential I/O
            - Data pipelines: Parallel stages vs sequential stages

        Gotchas:
            - Speedup depends on I/O wait time, not CPU time
            - CPU-bound work shows no speedup (use multiprocessing)
            - Diminishing returns: Too many concurrent tasks can slow things down
            - Network latency determines maximum speedup
            - Resource limits (connections, memory) affect optimal concurrency

        Performance Notes:
            - I/O-bound: 3-10x speedup typical
            - CPU-bound: No speedup (GIL limitation)
            - Optimal concurrency: Usually 10-100 concurrent tasks
            - Measure, don't guess: Profile to find bottlenecks
        """
        print("=== Performance Comparison ===")

        async def compute_task(task_id: str, iterations: int) -> tuple[str, float]:
            """A compute-intensive task."""
            start = time.time()
            result = await self.cpu_bound_simulation(iterations)
            duration = time.time() - start
            return f"Task {task_id}", duration

        # Sequential execution
        print("Sequential execution:")
        start_time = time.time()
        results_seq = []
        for i in range(3):
            result = await compute_task(f"Seq-{i+1}", 50000)
            results_seq.append(result)
        sequential_time = time.time() - start_time

        print(f"Sequential total time: {sequential_time:.2f} seconds")
        for name, duration in results_seq:
            print(f"  {name}: {duration:.3f} seconds")

        # Concurrent execution
        print("\nConcurrent execution:")
        start_time = time.time()
        tasks = [compute_task(f"Conc-{i+1}", 50000) for i in range(3)]
        results_conc = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        print(f"Concurrent total time: {concurrent_time:.2f} seconds")
        for name, duration in results_conc:
            print(f"  {name}: {duration:.3f} seconds")

        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
        print(f"\nSpeedup: {speedup:.2f}x faster with concurrency")
        print()

    async def concurrent_execution_real_world_example(self) -> None:
        """
        Real-World Scenario: Concurrent Execution - Web Scraper.

        REAL-WORLD SCENARIO:
        ====================
        You're building a web scraper:
        - Fetch data from multiple URLs
        - Each URL takes 1-3 seconds to fetch
        - Problem: Sequential fetching too slow
        
        THE PROBLEM WITHOUT CONCURRENCY:
        =================================
        - Fetch URL 1 → wait 2 seconds
        - Fetch URL 2 → wait 2 seconds
        - Fetch URL 3 → wait 2 seconds
        - 100 URLs = 200+ seconds!
        - Single connection → waste of time
        
        THE SOLUTION:
        =============
        Concurrent execution enables:
        - Fetch multiple URLs simultaneously
        - Overlap I/O wait times
        - 100 URLs = 10-20 seconds (vs 200+ seconds)
        - Optimal resource utilization
        - 10-20x speedup typical
        
        WHEN TO USE CONCURRENT EXECUTION:
        =================================
        ✅ I/O-bound operations (network, file, database)
        ✅ Multiple independent tasks
        ✅ When order doesn't matter
        ✅ Maximizing throughput
        ✅ Web scraping, API calls, file processing
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Web Scraper")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Web scraper fetching data from multiple URLs")
        print("  - Each URL takes 1-3 seconds to fetch")
        print("  - Problem: Sequential fetching too slow")
        print()
        print("THE PROBLEM:")
        print("  Without concurrency:")
        print("    ❌ Fetch URL 1 → wait 2 seconds")
        print("    ❌ Fetch URL 2 → wait 2 seconds")
        print("    ❌ Fetch URL 3 → wait 2 seconds")
        print("    ❌ 100 URLs = 200+ seconds!")
        print("    ❌ Single connection → waste of time")
        print()
        print("THE SOLUTION:")
        print("  With concurrent execution:")
        print("    ✅ Fetch multiple URLs simultaneously")
        print("    ✅ Overlap I/O wait times")
        print("    ✅ 100 URLs = 10-20 seconds (vs 200+ seconds)")
        print("    ✅ Optimal resource utilization")
        print()
        print("=" * 70)
        print()

        async def fetch_url(url_id: int) -> dict:
            """Simulate fetching a URL."""
            await asyncio.sleep(0.1)  # Simulate network I/O
            return {"url_id": url_id, "status": "fetched", "data": f"data_from_url_{url_id}"}

        urls = list(range(1, 11))  # 10 URLs

        # Sequential fetching
        print("Sequential fetching:")
        start_time = time.time()
        sequential_results = []
        for url_id in urls:
            result = await fetch_url(url_id)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        print(f"  Fetched {len(sequential_results)} URLs in {sequential_time:.3f}s")
        print()

        # Concurrent fetching
        print("Concurrent fetching:")
        start_time = time.time()
        tasks = [fetch_url(url_id) for url_id in urls]
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        print(f"  Fetched {len(concurrent_results)} URLs in {concurrent_time:.3f}s")
        print()

        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 1.0
        print("Results:")
        print(f"  Sequential time: {sequential_time:.3f}s")
        print(f"  Concurrent time: {concurrent_time:.3f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print("  ✅ Concurrent execution enabled parallel URL fetching!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE CONCURRENT EXECUTION:")
        print("   ✅ I/O-bound operations (network, file, database)")
        print("   ✅ Multiple independent tasks")
        print("   ✅ When order doesn't matter")
        print("   ✅ Maximizing throughput")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Overlaps I/O wait times")
        print("   - 10-20x speedup typical for I/O-bound tasks")
        print("   - Optimal resource utilization")
        print("   - Essential for scalable systems")
        print("=" * 70)
        print()

    async def task_vs_coroutine_real_world_example(self) -> None:
        """
        Real-World Scenario: Task vs Coroutine - Background Job Processing.

        REAL-WORLD SCENARIO:
        ====================
        You're building a background job processor:
        - Submit jobs to process
        - Jobs run independently
        - Problem: Need to track and manage job execution
        
        THE PROBLEM WITHOUT TASKS:
        ===========================
        - Coroutines must be awaited → blocking
        - Can't track execution state
        - Can't cancel running jobs
        - No introspection → opaque system
        - Difficult to manage → error-prone
        
        THE SOLUTION:
        =============
        Tasks enable:
        - Schedule coroutines for execution
        - Track execution state (pending, running, done)
        - Cancel running jobs
        - Introspect task properties
        - Manage job lifecycle → reliable
        
        WHEN TO USE TASKS:
        ==================
        ✅ Background job processing
        ✅ Fire-and-forget operations
        ✅ Need to track/cancel jobs
        ✅ Task lifecycle management
        ✅ Independent concurrent operations
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Background Job Processor")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Background job processor")
        print("  - Submit jobs to process")
        print("  - Jobs run independently")
        print("  - Problem: Need to track and manage job execution")
        print()
        print("THE PROBLEM:")
        print("  Without tasks:")
        print("    ❌ Coroutines must be awaited → blocking")
        print("    ❌ Can't track execution state")
        print("    ❌ Can't cancel running jobs")
        print("    ❌ No introspection → opaque system")
        print()
        print("THE SOLUTION:")
        print("  With tasks:")
        print("    ✅ Schedule coroutines for execution")
        print("    ✅ Track execution state (pending, running, done)")
        print("    ✅ Cancel running jobs")
        print("    ✅ Introspect task properties")
        print()
        print("=" * 70)
        print()

        async def process_job(job_id: str, duration: float) -> dict:
            """Simulate processing a job."""
            await asyncio.sleep(duration)
            return {"job_id": job_id, "status": "completed", "duration": duration}

        print("Submitting jobs as tasks...")
        print()

        # Create tasks (fire-and-forget)
        tasks = []
        for i in range(5):
            task = asyncio.create_task(process_job(f"job_{i+1}", 0.1))
            tasks.append(task)
            print(f"  Submitted {task.get_name()}: {task.get_coro().__name__}")

        # Monitor task states
        print("\nMonitoring task execution...")
        await asyncio.sleep(0.05)  # Let tasks start
        for task in tasks:
            print(f"  {task.get_name()}: {task._state}")

        # Wait for completion
        results = await asyncio.gather(*tasks)
        print("\nAll jobs completed:")
        for result in results:
            print(f"  ✅ {result['job_id']}: {result['status']}")
        print()
        print("  ✅ Tasks enabled job tracking and management!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE TASKS:")
        print("   ✅ Background job processing")
        print("   ✅ Fire-and-forget operations")
        print("   ✅ Need to track/cancel jobs")
        print("   ✅ Task lifecycle management")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Track execution state")
        print("   - Cancel running operations")
        print("   - Introspect task properties")
        print("   - Manage job lifecycle")
        print("=" * 70)
        print()


async def main() -> None:
    """Run all basic asyncio examples."""
    print("Asyncio Basic Examples")
    print("=" * 25)

    example = BasicAsyncioExample()

    await example.basic_coroutine_execution()
    await example.concurrent_execution()
    await example.task_vs_coroutine()
    await example.future_operations()
    await example.exception_handling()
    await example.event_loop_info()
    await example.nested_coroutines()
    await example.performance_comparison()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    await example.concurrent_execution_real_world_example()
    await example.task_vs_coroutine_real_world_example()

    print("All basic examples completed!")


"""
`__name__` is a special Python variable that contains the module's name
-- When you run a Python file directly: python basic_asyncio.py, __name__ is set to "__main__"
-- When you import the file: import basic_asyncio, __name__ is set to "basic_asyncio"
-- Purpose: This condition is True only when the file is run directly, not when imported



-- asyncio.run() is the main entry point for asyncio programs
-- It creates a new event loop, runs the coroutine main(), and handles cleanup
-- main() is the async function defined at line 306 that runs all the examples

-- Why this pattern exists:
-- Importable: You can import this module without running anything: from basic_asyncio import BasicAsyncioExample
-- Executable: You can run it directly: python basic_asyncio.py
-- Clean separation: Code inside if __name__ == "__main__": only runs when the file is executed directly
-- Without this code: You could only import the module, not run it directly
-- To run examples, you'd need to write separate scripts
"""


if __name__ == "__main__":
    asyncio.run(main())
