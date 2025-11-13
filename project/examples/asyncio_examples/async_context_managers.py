"""
Async context managers examples demonstrating resource management in async code.

This module covers:
- Creating async context managers with __aenter__ and __aexit__
- Using async context managers with async with
- Resource cleanup and exception handling
- Stacking multiple async context managers
- Real-world examples (database connections, file handles, locks)
"""

import asyncio
import time
from contextlib import asynccontextmanager # Decorator for creating async context managers
from typing import Any, AsyncGenerator, Optional # Type hints for better code readability and maintainability


class AsyncContextManagerExample:
    """
    Examples of async context managers for resource management.

    Async context managers ensure proper resource acquisition and cleanup in async code.
    They follow the RAII (Resource Acquisition Is Initialization) pattern and guarantee
    cleanup even when exceptions occur.

    When to Use:
        - Managing async resources (connections, locks, files)
        - Ensuring cleanup happens even on exceptions
        - Simplifying resource management code
        - Building reusable resource management patterns
        - Implementing database connection pools

    Real-World Examples:
        - Database connections: Acquire connection, use it, release automatically
        - File handles: Open file, read/write, close automatically
        - Network connections: Connect, communicate, disconnect automatically
        - Locks: Acquire lock, use critical section, release automatically
        - Transactions: Begin transaction, execute operations, commit/rollback

    Gotchas:
        - __aenter__ and __aexit__ are called automatically by async with
        - __aexit__ receives exception info; return True to suppress exception
        - Resources cleaned up in reverse order of acquisition
        - Exceptions in __aenter__ prevent __aexit__ from being called
        - Use @asynccontextmanager for simpler generator-based managers

    Performance Notes:
        - Minimal overhead compared to manual try/finally
        - Cleanup guaranteed even on exceptions
        - Can stack multiple managers efficiently
        - Prefer context managers over manual cleanup
    """

    class AsyncTimer:
        """
        Async context manager that measures execution time.

        Demonstrates a simple async context manager for timing operations.
        Useful for performance measurement and debugging.

        When to Use:
            - Measuring async operation performance
            - Debugging slow operations
            - Performance profiling
            - Timing critical sections
            - Benchmarking async code

        Real-World Examples:
            - API call timing: Measure API response times
            - Database query timing: Measure query execution time
            - Processing timing: Measure data processing time
            - Request timing: Measure request handling time

        Gotchas:
            - Start time set in __aenter__
            - Duration calculated in __aexit__
            - Exception info available in __aexit__
            - Always called even on exceptions
        """

        def __init__(self, name: str):
            """Initialize timer with a name."""
            self.name = name
            self.start_time: Optional[float] = None

        async def __aenter__(self) -> 'AsyncTimer':
            """Enter the context manager and start timing."""
            self.start_time = time.time()
            print(f"⏱️  Timer '{self.name}' started")
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """Exit the context manager and print duration."""
            if self.start_time is not None:
                duration = time.time() - self.start_time
                print(f"⏱️  Timer '{self.name}' finished in {duration:.2f}s")
                if exc_type:
                    print(f"❌ Timer '{self.name}' exited with exception: {exc_type.__name__}")

    class AsyncResource:
        """
        Example async resource that needs proper cleanup.

        Demonstrates proper resource acquisition and cleanup pattern.
        Ensures resources are always released, even on exceptions.

        When to Use:
            - Managing async resources (connections, handles, locks)
            - Ensuring cleanup happens automatically
            - Building resource management patterns
            - Implementing connection pools
            - Managing temporary resources

        Real-World Examples:
            - Database connections: Acquire, use, release
            - File handles: Open, read/write, close
            - Network sockets: Connect, communicate, disconnect
            - Locks: Acquire, use critical section, release
            - Transactions: Begin, execute, commit/rollback

        Gotchas:
            - __aexit__ always called, even on exceptions
            - Cleanup should be idempotent (safe to call multiple times)
            - Exception info available in __aexit__ for logging
            - Don't raise exceptions in __aexit__ unless suppressing original
            - Resource state should be checked before cleanup
        """

        def __init__(self, resource_id: str):
            """Initialize resource with an ID."""
            self.resource_id = resource_id
            self.acquired = False
            self.cleaned_up = False

        async def __aenter__(self) -> 'AsyncResource':
            """Acquire the resource asynchronously."""
            print(f"🔓 Acquiring resource '{self.resource_id}'...")
            await asyncio.sleep(0.1)  # Simulate acquisition time
            self.acquired = True
            print(f"✅ Resource '{self.resource_id}' acquired")
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """Release the resource. Always called, even on exceptions."""
            if self.acquired and not self.cleaned_up:
            print(f"🔒 Releasing resource '{self.resource_id}'...")
            await asyncio.sleep(0.05)  # Simulate cleanup time
            self.cleaned_up = True
            print(f"🧹 Resource '{self.resource_id}' cleaned up")

        async def use_resource(self) -> str:
            """Use the acquired resource."""
            if not self.acquired:
                raise RuntimeError("Resource not acquired")
            await asyncio.sleep(0.2)
            return f"Used resource {self.resource_id}"

    async def basic_async_context_manager(self) -> None:
        """
        Demonstrate basic async context manager usage.

        Shows the simplest pattern: async with statement automatically
        calls __aenter__ and __aexit__ methods.

        When to Use:
            - Learning async context manager basics
            - Timing operations
            - Simple resource management
            - Understanding async with syntax

        Real-World Examples:
            - Timing API calls: Measure response time
            - Performance profiling: Profile function execution
            - Resource timing: Measure resource usage time

        Gotchas:
            - async with automatically calls __aenter__ and __aexit__
            - No manual cleanup needed
            - Exception-safe by default
            - Cleaner than try/finally blocks
        """
        print("=== Basic Async Context Manager ===")

        async with self.AsyncTimer("basic_example"):
            await asyncio.sleep(0.5)
            print("Doing some work...")

        print()

    async def resource_management(self) -> None:
        """
        Demonstrate resource acquisition and cleanup.

        Shows how resources are automatically cleaned up when exiting
        the async with block, even if exceptions occur.

        When to Use:
            - Managing resources that need cleanup
            - Ensuring resources are released
            - Building resource management patterns
            - Preventing resource leaks

        Real-World Examples:
            - Database connections: Always close connections
            - File handles: Always close files
            - Network connections: Always disconnect
            - Locks: Always release locks
            - Transactions: Always commit or rollback

        Gotchas:
            - Cleanup happens automatically
            - Works even if exceptions occur
            - No need for try/finally blocks
            - Resource state managed internally
        """
        print("=== Resource Management ===")

        # Resource is automatically cleaned up when exiting the async with block
        async with self.AsyncResource("database_connection") as resource:
            result = await resource.use_resource()
            print(f"Result: {result}")

        print("Resource automatically cleaned up!\n")

    async def exception_handling_in_context(self) -> None:
        """
        Demonstrate exception handling in async context managers.

        Shows that cleanup happens even when exceptions occur.
        This is a key benefit of context managers.

        When to Use:
            - Ensuring cleanup on errors
            - Building robust resource management
            - Handling exceptions gracefully
            - Preventing resource leaks on errors

        Real-World Examples:
            - Database errors: Close connection even on query errors
            - File errors: Close file even on read/write errors
            - Network errors: Disconnect even on communication errors
            - Transaction errors: Rollback on exceptions

        Gotchas:
            - __aexit__ receives exception info (exc_type, exc_val, exc_tb)
            - Return True from __aexit__ to suppress exception
            - Cleanup always happens, even on exceptions
            - Exception info useful for logging
            - Don't raise new exceptions in __aexit__ unless suppressing
        """
        print("=== Exception Handling in Context Managers ===")

        try:
            async with self.AsyncResource("failing_resource") as resource:
                print("Using resource...")
                await resource.use_resource()
                # Simulate an exception
                raise ValueError("Something went wrong!")
        except ValueError as e:
            print(f"Caught exception: {e}")

        print("Resource was still cleaned up despite the exception!\n")

    async def nested_context_managers(self) -> None:
        """Demonstrate nesting async context managers."""
        print("=== Nested Context Managers ===")

        """
        -- The async with statement serves two critical purposes:
        -- Resource Management
        -- Automatically handles setup and cleanup of resources
        -- Ensures cleanup happens even if exceptions occur
        -- Follows the RAII (Resource Acquisition Is Initialization) pattern

        async with self.AsyncTimer("outer"):
            # code here

        timer = self.AsyncTimer("outer")
          try:
             await timer.__aenter__()  # Called automatically
               # code here
          finally:
            await timer.__aexit__(None, None, None)  # Called automatically    

        -- You're absolutely correct! You don't see __aenter__ or __aexit__ being called explicitly in the nested_context_managers method. That's because the async with statement is syntactic sugar - it automatically calls these methods behind the scenes.
        -- What Actually Happens
-- When you write:
-- async with self.AsyncTimer("outer"):    # code here
-- Python automatically translates this to something like:
-- timer = self.AsyncTimer("outer")try:    await timer.__aenter__()  # Called automatically    # code herefinally:    await timer.__aexit__(None, None, None)  # Called automatically
-- The Magic of async with
-- The async with statement:
--Creates the context manager object (self.AsyncTimer("outer"))
-- Automatically calls __aenter__ when entering the block
-- Executes your code in the try block
-- Automatically calls __aexit__ in the finally block, regardless of how the block exits (normal completion, return, exception, etc.)
-- Why You See the Print Statements
-- The print statements you see in the output come from inside the __aenter__ and __aexit__ methods themselves:
-- async def __aenter__(self) -> 'AsyncTimer':    """Enter the context manager."""    self.start_time = time.time()    print(f"⏱️  Timer '{self.name}' started")  # This prints!    return selfasync def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:    """Exit the context manager."""    if self.start_time is not None:        duration = time.time() - self.start_time        print(".2f")  # This prints!        if exc_type:            print(f"❌ Timer '{self.name}' exited with exception: {exc_type.__name__}")
-- So when you run the nested context managers example, you'll see output like:
-- ⏱️  Timer 'outer' startedOuter context entered⏱️  Timer 'inner' startedInner context enteredInner work done⏱️  Timer 'inner' finished in 0.30sBack in outer contextOuter work done⏱️  Timer 'outer' finished in 0.50s
-- The async with statement handles all the boilerplate of calling __aenter__ and __aexit__ for you, making resource management much cleaner and less error-prone!

        
        """

        async with self.AsyncTimer("outer"):
            print("Outer context entered")

            async with self.AsyncTimer("inner"):
                print("Inner context entered")
                await asyncio.sleep(0.3)
                print("Inner work done")

            print("Back in outer context")
            await asyncio.sleep(0.2)
            print("Outer work done")

        print()

    async def multiple_resources(self) -> None:
        """Demonstrate managing multiple resources simultaneously."""
        print("=== Multiple Resources ===")

        async with self.AsyncResource("resource_1") as r1, \
                   self.AsyncResource("resource_2") as r2, \
                   self.AsyncResource("resource_3") as r3:

            # Uses a single async with statement to acquire three AsyncResource instances (resource_1, resource_2, resource_3) concurrently using comma-separated context managers.
            tasks = [
                r1.use_resource(),
                r2.use_resource(),
                r3.use_resource()
            ]

            # to run all resource usage tasks `concurrently` and waits for all of them to complete, collecting their results.
            results = await asyncio.gather(*tasks)
            print("Results from all resources:")
            for result in results:
                print(f"  {result}")

        # Automatic Cleanup: When the async with block exits, all three resources are automatically cleaned up in reverse order (resource_3, then resource_2, then resource_1) thanks to the context manager protocol.
        print("All resources cleaned up!\n")

    async def stacking_with_timer(self) -> None:
        """Demonstrate stacking context managers with timing."""
        print("=== Stacking with Timer ===")

        async with self.AsyncTimer("complete_operation"):
            async with self.AsyncResource("main_resource") as resource:
                print("Performing complex operation...")

                # Nested timing for sub-operations
                async with self.AsyncTimer("sub_operation_1"):
                    await asyncio.sleep(0.2)
                    result1 = await resource.use_resource()

                async with self.AsyncTimer("sub_operation_2"):
                    await asyncio.sleep(0.3)
                    result2 = await resource.use_resource()

                print(f"Operation complete: {result1}, {result2}")

        print()

    """
    -- @asynccontextmanager - KEY: Decorator that converts generator function to context manager
    -- Uses try/finally to ensure cleanup even with exceptions
    -- yield - KEY: Provides the connection object to the async with block
    -- @asynccontextmanager + yield implements the following code for you automatically.

    
    async def __aenter__(self):
        self.gen = database_connection(...)
        return await self.gen.__anext__()

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self.gen.__anext__()
        except StopAsyncIteration:
            pass

    """
    @asynccontextmanager
    async def database_connection(self, connection_string: str) -> AsyncGenerator[dict, None]:
        """
        Example async context manager for database connection.

        Demonstrates using @asynccontextmanager decorator to create
        context managers from async generator functions. Simpler than
        implementing __aenter__ and __aexit__ manually.

        When to Use:
            - Creating context managers from generator functions
            - Managing database connections
            - Simpler syntax than class-based managers
            - One-time resource management

        Real-World Examples:
            - Database connections: Connect, use, disconnect
            - Connection pools: Get connection, use, return to pool
            - Transaction management: Begin, execute, commit/rollback
            - Session management: Start session, use, end session

        Gotchas:
            - @asynccontextmanager converts generator to context manager
            - yield provides value to async with block
            - Code before yield is __aenter__, after is __aexit__
            - finally block ensures cleanup
            - Exception handling works normally

        Args:
            connection_string: Database connection string

        Yields:
            Database connection dictionary with connection info
        """
        print(f"📡 Connecting to database: {connection_string}")
        await asyncio.sleep(0.2)  # Simulate connection time

        # Simulate database connection object
        connection = {
            "id": f"conn_{hash(connection_string) % 1000}",
            "status": "connected",
            "connection_string": connection_string
        }

        try:
            print(f"✅ Database connected: {connection['id']}")
            yield connection # “Pause here, give the yielded value to the async with block, and resume after the block exits.”
        finally:
            print(f"🔌 Disconnecting database: {connection['id']}")
            await asyncio.sleep(0.1)  # Simulate cleanup
            connection["status"] = "disconnected"
            print(f"✅ Database disconnected: {connection['id']}")

    async def database_example(self) -> None:
        """Demonstrate database connection context manager."""
        print("=== Database Connection Example ===")

        async with self.database_connection("postgresql://user:pass@localhost:5432/mydb") as conn:
            print(f"Using connection: {conn['id']}")

            # Simulate database operations
            async with self.AsyncTimer("database_query"):
                await asyncio.sleep(0.3)
                print("Executing query...")
                results = ["row1", "row2", "row3"]

            print(f"Query returned {len(results)} results")

        print()

    # Just like before, this allows us to write an async context manager using a single async def + yield instead of defining a whole class.
    @asynccontextmanager
    async def async_lock_manager(self, lock: asyncio.Lock) -> AsyncGenerator[asyncio.Lock, None]:
        """
        Context manager that acquires and releases an async lock.

        Demonstrates wrapping existing async primitives with context managers
        for cleaner syntax and guaranteed cleanup.

        When to Use:
            - Wrapping locks with context managers
            - Ensuring locks are always released
            - Cleaner lock syntax
            - Preventing lock leaks

        Real-World Examples:
            - Critical sections: Acquire lock, execute, release
            - Resource protection: Protect shared resources
            - Synchronization: Coordinate concurrent access
            - Deadlock prevention: Ensure locks are released

        Gotchas:
            - Lock acquired before yield
            - Lock released in finally block
            - Works even if exception occurs
            - Simpler than manual acquire/release
            - Can wrap any async primitive

        Args:
            lock: The asyncio.Lock to manage

        Yields:
            The acquired lock (can be used in async with block)
        """
        print("🔐 Acquiring lock...")
        await lock.acquire()
        print("✅ Lock acquired")

        try:
            # Below yield is where control is handed over to the async with block wherever this function has called.
            yield lock
        finally:
            lock.release()
            print("🔓 Lock released")

    async def lock_example(self) -> None:
        """Demonstrate async lock management with context manager."""
        print("=== Async Lock Management ===")

        shared_lock = asyncio.Lock()
        shared_counter = {"value": 0}

        async def increment_counter(task_id: str) -> None:
            """Increment shared counter with proper locking."""
            # The expression after as just captures whatever the context manager yields. But since we don't need yielded value so not use `as`
            async with self.async_lock_manager(shared_lock):
                current = shared_counter["value"]
                await asyncio.sleep(0.1)  # Simulate work
                shared_counter["value"] = current + 1
                print(f"Task {task_id}: incremented counter to {shared_counter['value']}")

        # Run multiple tasks that need exclusive access
        tasks = [increment_counter(f"T{i+1}") for i in range(5)]
        await asyncio.gather(*tasks)

        print(f"Final counter value: {shared_counter['value']}")
        print()

    class ConditionalResource:
        """Resource that may or may not be acquired based on conditions."""

        def __init__(self, name: str, should_acquire: bool = True):
            self.name = name
            self.should_acquire = should_acquire
            self.acquired = False

        async def __aenter__(self) -> Optional['ConditionalResource']:
            """Conditionally acquire the resource."""
            if self.should_acquire:
                print(f"🎯 Acquiring conditional resource '{self.name}'")
                await asyncio.sleep(0.1)
                self.acquired = True
                print(f"✅ Conditional resource '{self.name}' acquired")
                return self
            else:
                print(f"⏭️  Skipping resource '{self.name}'")
                return None

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """Clean up if resource was acquired."""
            if self.acquired:
                print(f"🧹 Cleaning up conditional resource '{self.name}'")
                await asyncio.sleep(0.05)

    async def conditional_resources(self) -> None:
        """Demonstrate conditional resource acquisition."""
        print("=== Conditional Resources ===")

        # Test successful acquisition
        async with self.ConditionalResource("important_resource", True) as resource:
            if resource:
                print("Using the acquired resource...")

        print()

        # Test skipped acquisition
        async with self.ConditionalResource("optional_resource", False) as resource:
            if resource:
                print("This won't print")
            else:
                print("Resource was not acquired (as expected)")

        print()

    async def context_manager_stacking(self) -> None:
        """Demonstrate complex stacking of multiple context managers."""
        print("=== Complex Context Manager Stacking ===")

        # These multiple context managers are stacked together and executed in left to right order.
        async with self.AsyncTimer("complex_operation"), \
                   self.database_connection("sqlite:///example.db") as db, \
                   self.AsyncResource("worker_pool") as pool:

            print("All resources acquired, starting complex operation...")

            # Use all resources together
            db_result = f"DB connected: {db['id']}"
            pool_result = await pool.use_resource()

            async with self.AsyncTimer("processing_phase"):
                await asyncio.sleep(0.4)
                print("Processing data...")

            print(f"Operation results: {db_result}, {pool_result}")

        print("All resources automatically cleaned up!\n")

    async def database_connection_real_world_example(self) -> None:
        """
        Real-World Scenario: Async Context Manager - Database Connection Pool.

        REAL-WORLD SCENARIO:
        ====================
        You're building a database service:
        - Need database connections for queries
        - Connections are expensive to create
        - Problem: Must ensure connections are always closed
        
        THE PROBLEM WITHOUT CONTEXT MANAGERS:
        ======================================
        - Manual connection management → error-prone
        - Forget to close → connection leaks
        - Exception → connection not closed → leak
        - Complex try/finally → verbose code
        - Resource leaks → system degradation
        
        THE SOLUTION:
        =============
        Async context managers enable:
        - Automatic connection acquisition/release
        - Guaranteed cleanup even with exceptions
        - Clean, readable code → easy to maintain
        - Resource safety → no leaks
        - Production-ready → reliable
        
        WHEN TO USE ASYNC CONTEXT MANAGERS:
        ===================================
        ✅ Database connections
        ✅ Network connections
        ✅ File handles
        ✅ Locks and semaphores
        ✅ Any resource needing cleanup
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Database Connection Pool")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Database service")
        print("  - Need database connections for queries")
        print("  - Connections are expensive to create")
        print("  - Problem: Must ensure connections are always closed")
        print()
        print("THE PROBLEM:")
        print("  Without context managers:")
        print("    ❌ Manual connection management → error-prone")
        print("    ❌ Forget to close → connection leaks")
        print("    ❌ Exception → connection not closed → leak")
        print("    ❌ Complex try/finally → verbose code")
        print()
        print("THE SOLUTION:")
        print("  With async context managers:")
        print("    ✅ Automatic connection acquisition/release")
        print("    ✅ Guaranteed cleanup even with exceptions")
        print("    ✅ Clean, readable code → easy to maintain")
        print("    ✅ Resource safety → no leaks")
        print()
        print("=" * 70)
        print()

        class DatabaseConnection:
            """Simulate a database connection."""
            def __init__(self, connection_id: str):
                self.connection_id = connection_id
                self.is_open = False

            async def connect(self) -> None:
                """Simulate connection establishment."""
                await asyncio.sleep(0.05)
                self.is_open = True
                print(f"  Connection {self.connection_id}: Opened")

            async def close(self) -> None:
                """Simulate connection closure."""
                await asyncio.sleep(0.02)
                self.is_open = False
                print(f"  Connection {self.connection_id}: Closed")

            async def query(self, sql: str) -> dict:
                """Simulate executing a query."""
                await asyncio.sleep(0.03)
                return {"query": sql, "rows": 10}

        class DatabaseConnectionManager:
            """Async context manager for database connections."""
            def __init__(self, connection_id: str):
                self.connection_id = connection_id
                self.connection = None

            async def __aenter__(self) -> DatabaseConnection:
                """Acquire connection."""
                self.connection = DatabaseConnection(self.connection_id)
                await self.connection.connect()
                return self.connection

            async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
                """Release connection."""
                if self.connection:
                    await self.connection.close()

        print("Using database connection with async context manager...")
        print()

        # Use connection with automatic cleanup
        async with DatabaseConnectionManager("db_conn_1") as conn:
            result = await conn.query("SELECT * FROM users")
            print(f"  Query executed: {result['rows']} rows returned")

        print()
        print("  ✅ Connection automatically closed, even if exception occurs!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE ASYNC CONTEXT MANAGERS:")
        print("   ✅ Database connections")
        print("   ✅ Network connections")
        print("   ✅ File handles")
        print("   ✅ Locks and semaphores")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Guaranteed resource cleanup")
        print("   - Exception-safe")
        print("   - Clean, readable code")
        print("   - Production-ready reliability")
        print("=" * 70)
        print()


async def main() -> None:
    """Run all async context manager examples."""
    print("Asyncio Context Managers Examples")
    print("=" * 35)

    example = AsyncContextManagerExample()

    await example.basic_async_context_manager()
    await example.resource_management()
    await example.exception_handling_in_context()
    await example.nested_context_managers()
    await example.multiple_resources()
    await example.stacking_with_timer()
    await example.database_example()
    await example.lock_example()
    await example.conditional_resources()
    await example.context_manager_stacking()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    await example.database_connection_real_world_example()

    print("All async context manager examples completed!")


if __name__ == "__main__":
    asyncio.run(main())


"""

🎯 Key Concepts Demonstrated in this file:
`__aenter__/__aexit__` - Core async context manager methods
-- async with - Syntax for using async context managers
-- @asynccontextmanager - Decorator for creating context managers from generators
-- Automatic cleanup - Resources cleaned up even with exceptions
-- Resource stacking - Multiple context managers in one statement
-- Exception safety - Cleanup guaranteed in error conditions
-- Real-world patterns - Database connections, locks, conditional resources

🔑 Why Async Context Managers Matter:
-- Guaranteed cleanup - Resources always released, even with exceptions
-- Exception safety - Cleanup happens regardless of how the block exits
-- Cleaner code - No manual try/finally blocks needed
-- Composability - Multiple managers can be stacked easily
-- Async resource management - Proper handling of async acquisition/release

"""