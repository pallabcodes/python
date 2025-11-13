"""
Thread-safe counter implementation with locking.

This module demonstrates the fundamental concept of thread synchronization
using locks to prevent race conditions in shared mutable state.
"""

import threading
import logging
from typing import Optional

from utilities.profilers import profile


class ThreadSafeCounter:
    """
    A thread-safe counter using explicit locking.

    This class demonstrates basic thread synchronization by protecting
    a shared mutable counter variable with a threading.Lock. Without
    proper locking, concurrent access would lead to race conditions
    and incorrect results.

    When to Use:
        - Shared counters across threads
        - Thread-safe state management
        - Preventing race conditions
        - Learning thread synchronization
        - Production counter implementations

    Real-World Examples:
        - Request counters: Count requests across threads
        - Statistics: Aggregate statistics from threads
        - Progress tracking: Track progress across threads
        - Resource counting: Count shared resources
        - Metrics: Collect metrics from threads

    Gotchas:
        - All operations must use lock
        - Read operations also need lock
        - Lock overhead affects performance
        - Deadlock risk with multiple locks
        - Use context manager (with statement)
        - Lock scope should be minimal

    Performance Notes:
        - Lock overhead for each operation
        - Optimal for moderate contention
        - Consider lock-free alternatives for high contention
        - Balance safety vs performance

    Attributes:
        _value: The current counter value (private).
        _lock: Threading lock for synchronization.
        _logger: Logger for debugging and monitoring.

    Example:
        >>> counter = ThreadSafeCounter()
        >>> counter.increment()
        >>> counter.get_value()
        1
    """

    def __init__(self, initial_value: int = 0) -> None:
        """Initialize the thread-safe counter.

        Args:
            initial_value: Starting value for the counter.

        Raises:
            ValueError: If initial_value is negative.
        """
        if initial_value < 0:
            raise ValueError("Initial value must be non-negative")

        self._value: int = initial_value
        self._lock: threading.Lock = threading.Lock()
        self._logger: logging.Logger = logging.getLogger(__name__)

        self._logger.info(
            f"ThreadSafeCounter initialized with value {initial_value}",
            extra={"initial_value": initial_value}
        )

    def increment(self) -> None:
        """
        Increment the counter by one (thread-safe).

        This method uses explicit locking to ensure atomicity.
        Without the lock, concurrent increments could lead to
        race conditions where increments are lost.

        When to Use:
            - Incrementing shared counters
            - Thread-safe counter operations
            - Preventing lost increments
            - Atomic counter updates

        Real-World Examples:
            - Request counting: Increment request count
            - Progress tracking: Increment progress counter
            - Statistics: Increment statistic counters
            - Resource tracking: Increment resource counters

        Gotchas:
            - Lock ensures atomicity
            - Without lock, increments can be lost
            - Lock overhead affects performance
            - Critical section must be protected

        Performance Notes:
            - Lock overhead per increment
            - Optimal for moderate contention
            - Consider batching for high frequency
        """
        with self._lock:
            self._value += 1

    def decrement(self) -> None:
        """
        Decrement the counter by one (thread-safe).

        When to Use:
            - Decrementing shared counters
            - Thread-safe counter operations
            - Preventing negative values
            - Atomic counter updates

        Real-World Examples:
            - Resource tracking: Decrement resource count
            - Queue management: Decrement queue size
            - Inventory: Decrement inventory count
            - Connection pools: Decrement connection count

        Gotchas:
            - Lock ensures atomicity
            - Validates non-negative constraint
            - Raises ValueError if would go negative
            - Check-then-act must be atomic

        Performance Notes:
            - Lock overhead per decrement
            - Validation adds minimal overhead
            - Optimal for moderate contention

        Args:
            None

        Raises:
            ValueError: If decrementing would result in negative value.

        Note:
            Negative values are not allowed to maintain business
            logic constraints.
        """
        with self._lock:
            if self._value <= 0:
                raise ValueError("Cannot decrement counter below zero")
            self._value -= 1

    def get_value(self) -> int:
        """
        Get the current counter value (thread-safe).

        When to Use:
            - Reading shared counter values
            - Thread-safe value retrieval
            - Getting current state
            - Reading counter for display

        Real-World Examples:
            - Status display: Display current counter value
            - Logging: Log current counter state
            - Monitoring: Monitor counter values
            - Reporting: Report counter statistics

        Gotchas:
            - Read operations need lock too
            - Without lock, may read inconsistent value
            - Lock ensures consistent read
            - Snapshot may be outdated immediately

        Performance Notes:
            - Lock overhead for reads
            - Consider if reads need locking
            - Balance consistency vs performance

        Returns:
            Current counter value.

        Note:
            Even read operations need to be protected when the
            value could be modified concurrently.
        """
        with self._lock:
            return self._value

    def reset(self, new_value: int = 0) -> None:
        """Reset the counter to a new value (thread-safe).

        Args:
            new_value: New value for the counter.

        Raises:
            ValueError: If new_value is negative.
        """
        if new_value < 0:
            raise ValueError("Reset value must be non-negative")

        with self._lock:
            self._value = new_value
            self._logger.info(
                f"Counter reset to {new_value}",
                extra={"new_value": new_value}
            )

    def thread_safe_counter_real_world_example(self) -> None:
        """
        Real-World Scenario: Thread-Safe Counter - Request Counter System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a web server request counter:
        - Multiple threads handle requests concurrently
        - Each request increments a shared counter
        - Problem: Race conditions cause lost increments
        
        THE PROBLEM WITHOUT THREAD-SAFE COUNTER:
        =========================================
        - Multiple threads increment → race conditions
        - Lost increments → incorrect count
        - Non-atomic operations → data corruption
        - Unpredictable results → system unreliable
        - Production bugs → critical issues
        
        THE SOLUTION:
        =============
        Thread-safe counter enables:
        - Atomic increments → no lost updates
        - Correct counting → reliable statistics
        - Thread-safe operations → production-ready
        - Predictable behavior → system reliable
        - Accurate metrics → business insights
        
        WHEN TO USE THREAD-SAFE COUNTER:
        ================================
        ✅ Shared counters across threads
        ✅ Request/event counting
        ✅ Statistics aggregation
        ✅ Progress tracking
        ✅ Resource counting
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Request Counter System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Web server request counter")
        print("  - Multiple threads handle requests concurrently")
        print("  - Each request increments a shared counter")
        print("  - Problem: Race conditions cause lost increments")
        print()
        print("THE PROBLEM:")
        print("  Without thread-safe counter:")
        print("    ❌ Multiple threads increment → race conditions")
        print("    ❌ Lost increments → incorrect count")
        print("    ❌ Non-atomic operations → data corruption")
        print("    ❌ Unpredictable results → system unreliable")
        print()
        print("THE SOLUTION:")
        print("  With thread-safe counter:")
        print("    ✅ Atomic increments → no lost updates")
        print("    ✅ Correct counting → reliable statistics")
        print("    ✅ Thread-safe operations → production-ready")
        print("    ✅ Predictable behavior → system reliable")
        print()
        print("=" * 70)
        print()

        def handle_request(request_id: int, counter: ThreadSafeCounter) -> None:
            """Simulate handling a request."""
            counter.increment()
            print(f"  Request {request_id}: Processed (counter={counter.get_value()})")

        counter = ThreadSafeCounter(initial_value=0)
        num_requests = 10

        print(f"Simulating {num_requests} requests across multiple threads...")
        print()

        threads = []
        for i in range(num_requests):
            thread = threading.Thread(
                target=handle_request,
                args=(i+1, counter)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        final_count = counter.get_value()
        print()
        print("Results:")
        print(f"  Requests processed: {num_requests}")
        print(f"  Counter value: {final_count}")
        print(f"  Expected: {num_requests}")
        if final_count == num_requests:
            print("  ✅ Thread-safe counter prevented lost increments!")
        else:
            print(f"  ❌ Counter mismatch! Lost {num_requests - final_count} increments")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE THREAD-SAFE COUNTER:")
        print("   ✅ Shared counters across threads")
        print("   ✅ Request/event counting")
        print("   ✅ Statistics aggregation")
        print("   ✅ Progress tracking")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents race conditions")
        print("   - Ensures correct counting")
        print("   - Production-ready reliability")
        print("   - Accurate metrics")
        print("=" * 70)
        print()


class UnsafeCounter:
    """
    Unsafe counter without locking (for demonstration).

    This class intentionally lacks thread synchronization to
    demonstrate race conditions. DO NOT use in production code.

    When to Use:
        - Educational purposes only
        - Demonstrating race conditions
        - Learning thread safety
        - Testing race condition detection
        - Benchmarking comparison

    Real-World Examples:
        - None (DO NOT USE IN PRODUCTION)
        - Educational: Teaching race conditions
        - Testing: Testing race condition detectors
        - Benchmarking: Comparing with safe implementations

    Gotchas:
        - NOT thread-safe
        - Race conditions guaranteed
        - Incorrect results under concurrency
        - Lost increments/decrements
        - DO NOT USE IN PRODUCTION

    Performance Notes:
        - Faster than thread-safe (no locks)
        - But produces incorrect results
        - Only for educational purposes

    WARNING: This class is not thread-safe and will produce
    incorrect results under concurrent access.
    """

    def __init__(self, initial_value: int = 0) -> None:
        """Initialize unsafe counter."""
        self._value: int = initial_value
        self._logger: logging.Logger = logging.getLogger(__name__)

    def increment(self) -> None:
        """Increment counter without synchronization (unsafe)."""
        # No lock - race condition possible!
        self._value += 1

    def get_value(self) -> int:
        """Get counter value without synchronization (unsafe)."""
        return self._value


def increment_counter(counter: ThreadSafeCounter, iterations: int) -> None:
    """Increment counter multiple times in a loop.

    This function demonstrates how a thread would use the counter.
    Each thread performs multiple increments to increase the chance
    of race conditions in unsafe implementations.

    Args:
        counter: Counter instance to increment.
        iterations: Number of times to increment.
    """
    for _ in range(iterations):
        counter.increment()


@profile
def benchmark_thread_safe_counter(
    num_threads: int,
    iterations_per_thread: int
) -> ThreadSafeCounter:
    """Benchmark thread-safe counter performance.

    This function creates multiple threads that concurrently
    increment a shared counter, measuring the performance impact
    of proper synchronization.

    Args:
        num_threads: Number of threads to create.
        iterations_per_thread: Increments per thread.

    Returns:
        Final counter state after all operations.
    """
    counter = ThreadSafeCounter()
    threads: list[threading.Thread] = []

    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(
            target=increment_counter,
            args=(counter, iterations_per_thread)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return counter


@profile
def benchmark_unsafe_counter(
    num_threads: int,
    iterations_per_thread: int
) -> UnsafeCounter:
    """Benchmark unsafe counter (demonstrates race conditions).

    WARNING: This function is for educational purposes only.
    The unsafe counter will produce incorrect results under
    concurrent access.

    Args:
        num_threads: Number of threads to create.
        iterations_per_thread: Increments per thread.

    Returns:
        Final counter state (likely incorrect due to races).
    """
    counter = UnsafeCounter()
    threads: list[threading.Thread] = []

    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(
            target=lambda: increment_counter(counter, iterations_per_thread)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return counter


if __name__ == "__main__":
    """Demonstrate counter usage."""
    logging.basicConfig(level=logging.INFO)

    # Single-threaded test
    print("=== Single-threaded test ===")
    counter = ThreadSafeCounter()
    counter.increment()
    print(f"Counter value: {counter.get_value()}")

    # Multi-threaded benchmark
    print("\n=== Multi-threaded benchmark ===")
    result = benchmark_thread_safe_counter(
        num_threads=4,
        iterations_per_thread=1000
    )
    expected = 4 * 1000
    actual = result.get_value()

    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    print(f"Correct: {actual == expected}")

    # Demonstrate unsafe counter race condition
    print("\n=== Unsafe counter (race condition demo) ===")
    unsafe_result = benchmark_unsafe_counter(
        num_threads=4,
        iterations_per_thread=1000
    )
    unsafe_actual = unsafe_result.get_value()

    print(f"Unsafe counter result: {unsafe_actual}")
    print(f"Race condition detected: {unsafe_actual != expected}")

    # Real-world scenario
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIO")
    print("=" * 70 + "\n")
    counter = ThreadSafeCounter()
    counter.thread_safe_counter_real_world_example()

