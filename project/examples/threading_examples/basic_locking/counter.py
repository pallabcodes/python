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
    """A thread-safe counter using explicit locking.

    This class demonstrates basic thread synchronization by protecting
    a shared mutable counter variable with a threading.Lock. Without
    proper locking, concurrent access would lead to race conditions
    and incorrect results.

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
        """Increment the counter by one (thread-safe).

        This method uses explicit locking to ensure atomicity.
        Without the lock, concurrent increments could lead to
        race conditions where increments are lost.

        Note:
            This is a critical section that must be protected
            to maintain data integrity.
        """
        with self._lock:
            self._value += 1

    def decrement(self) -> None:
        """Decrement the counter by one (thread-safe).

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
        """Get the current counter value (thread-safe).

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


class UnsafeCounter:
    """Unsafe counter without locking (for demonstration).

    This class intentionally lacks thread synchronization to
    demonstrate race conditions. DO NOT use in production code.

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

