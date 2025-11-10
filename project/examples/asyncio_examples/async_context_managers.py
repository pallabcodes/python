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
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional


class AsyncContextManagerExample:
    """
    Examples of async context managers for resource management.
    """

    class AsyncTimer:
        """Async context manager that measures execution time."""

        def __init__(self, name: str):
            self.name = name
            self.start_time: Optional[float] = None

        async def __aenter__(self) -> 'AsyncTimer':
            """Enter the context manager."""
            self.start_time = time.time()
            print(f"⏱️  Timer '{self.name}' started")
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """Exit the context manager."""
            if self.start_time is not None:
                duration = time.time() - self.start_time
                print(".2f")
                if exc_type:
                    print(f"❌ Timer '{self.name}' exited with exception: {exc_type.__name__}")

    class AsyncResource:
        """Example async resource that needs proper cleanup."""

        def __init__(self, resource_id: str):
            self.resource_id = resource_id
            self.acquired = False
            self.cleaned_up = False

        async def __aenter__(self) -> 'AsyncResource':
            """Acquire the resource."""
            print(f"🔓 Acquiring resource '{self.resource_id}'...")
            await asyncio.sleep(0.1)  # Simulate acquisition time
            self.acquired = True
            print(f"✅ Resource '{self.resource_id}' acquired")
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """Release the resource."""
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
        """Demonstrate basic async context manager usage."""
        print("=== Basic Async Context Manager ===")

        async with self.AsyncTimer("basic_example"):
            await asyncio.sleep(0.5)
            print("Doing some work...")

        print()

    async def resource_management(self) -> None:
        """Demonstrate resource acquisition and cleanup."""
        print("=== Resource Management ===")

        async with self.AsyncResource("database_connection") as resource:
            result = await resource.use_resource()
            print(f"Result: {result}")

        print("Resource automatically cleaned up!\n")

    async def exception_handling_in_context(self) -> None:
        """Demonstrate exception handling in async context managers."""
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

            # Use all resources concurrently
            tasks = [
                r1.use_resource(),
                r2.use_resource(),
                r3.use_resource()
            ]

            results = await asyncio.gather(*tasks)
            print("Results from all resources:")
            for result in results:
                print(f"  {result}")

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

    @asynccontextmanager
    async def database_connection(self, connection_string: str) -> AsyncGenerator[dict, None]:
        """
        Example async context manager for database connection.

        Args:
            connection_string: Database connection string

        Yields:
            Database connection info
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
            yield connection
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

    @asynccontextmanager
    async def async_lock_manager(self, lock: asyncio.Lock) -> AsyncGenerator[asyncio.Lock, None]:
        """
        Context manager that acquires and releases an async lock.

        Args:
            lock: The asyncio.Lock to manage

        Yields:
            The acquired lock
        """
        print("🔐 Acquiring lock...")
        await lock.acquire()
        print("✅ Lock acquired")

        try:
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

    print("All async context manager examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
