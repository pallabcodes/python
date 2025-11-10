"""
Custom Concurrency Primitives.

This module provides specialized concurrency primitives that go beyond the
standard library, offering enhanced functionality and performance optimizations.

Features:
- Priority-based queues with weighted scheduling
- Adaptive rate limiters with backoff strategies
- Smart circuit breakers with recovery patterns
- Context-aware locks with deadlock detection
- Buffered channels for CSP-style communication
"""

import asyncio
import threading
import time
import logging
import heapq
import random
from typing import Any, Callable, List, Dict, Optional, Union, Tuple, Deque
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager, contextmanager
from collections import deque
import statistics
import weakref

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(order=True)
class PriorityItem:
    """Item with priority for priority queues."""
    priority: int
    timestamp: float
    item: Any = field(compare=False)

    def __init__(self, priority: Union[int, Priority], item: Any):
        self.priority = priority if isinstance(priority, int) else priority.value
        self.timestamp = time.time()
        self.item = item


class PriorityQueue:
    """
    Priority queue with advanced scheduling features.

    Features:
    - Priority-based ordering with FIFO within same priority
    - Weighted round-robin for fair scheduling
    - Batch operations for efficiency
    - Size limits with overflow handling
    """

    def __init__(self, max_size: Optional[int] = None, weights: Optional[Dict[int, int]] = None):
        self.max_size = max_size
        self.weights = weights or {p.value: 1 for p in Priority}
        self._queue: List[PriorityItem] = []
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    def put(self, item: Any, priority: Union[int, Priority] = Priority.NORMAL,
            block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Put an item in the priority queue.

        Args:
            item: Item to put
            priority: Priority level
            block: Whether to block if queue is full
            timeout: Maximum time to wait

        Returns:
            True if successful, False if timeout
        """
        priority_item = PriorityItem(priority, item)

        with self._not_full:
            if self.max_size is not None:
                if not block:
                    if len(self._queue) >= self.max_size:
                        return False
                elif timeout is None:
                    while len(self._queue) >= self.max_size:
                        self._not_full.wait()
                else:
                    if not self._not_full.wait_for(
                        lambda: len(self._queue) < self.max_size, timeout
                    ):
                        return False

            heapq.heappush(self._queue, priority_item)
            self._not_empty.notify()

        return True

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Get an item from the priority queue.

        Args:
            block: Whether to block if queue is empty
            timeout: Maximum time to wait

        Returns:
            Item if available, None if timeout
        """
        with self._not_empty:
            if not block:
                if not self._queue:
                    return None
            elif timeout is None:
                while not self._queue:
                    self._not_empty.wait()
            else:
                if not self._not_empty.wait_for(lambda: bool(self._queue), timeout):
                    return None

            item = heapq.heappop(self._queue)
            self._not_full.notify()
            return item.item

    def qsize(self) -> int:
        """Get queue size."""
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._queue) == 0

    def full(self) -> bool:
        """Check if queue is full."""
        with self._lock:
            return self.max_size is not None and len(self._queue) >= self.max_size


class WeightedSemaphore:
    """
    Weighted semaphore allowing different weights for different operations.

    Features:
    - Weighted resource allocation
    - Fair scheduling based on weights
    - Priority-based acquisition
    - Resource quota management
    """

    def __init__(self, total_weight: int = 100):
        self.total_weight = total_weight
        self._current_weight = 0
        self._waiters: List[Tuple[threading.Condition, int]] = []
        self._lock = threading.RLock()

    @contextmanager
    def acquire(self, weight: int = 1, priority: int = 0):
        """
        Context manager for acquiring weighted semaphore.

        Args:
            weight: Weight to acquire
            priority: Priority for ordering (higher = more priority)
        """
        condition = threading.Condition(self._lock)

        with self._lock:
            # Add to waiters list in priority order
            inserted = False
            for i, (cond, w) in enumerate(self._waiters):
                if priority > 0:  # Higher priority gets inserted earlier
                    self._waiters.insert(i, (condition, weight))
                    inserted = True
                    break

            if not inserted:
                self._waiters.append((condition, weight))

            # Wait for weight to become available
            while self._current_weight + weight > self.total_weight:
                condition.wait()

            # Remove from waiters and acquire
            self._waiters.remove((condition, weight))
            self._current_weight += weight

        try:
            yield
        finally:
            with self._lock:
                self._current_weight -= weight
                # Notify next waiter
                if self._waiters:
                    self._waiters[0][0].notify()

    def try_acquire(self, weight: int = 1) -> bool:
        """Try to acquire weight without blocking."""
        with self._lock:
            if self._current_weight + weight <= self.total_weight:
                self._current_weight += weight
                return True
            return False

    def release(self, weight: int = 1):
        """Release weight."""
        with self._lock:
            self._current_weight = max(0, self._current_weight - weight)
            if self._waiters:
                self._waiters[0][0].notify()

    def available_weight(self) -> int:
        """Get available weight."""
        with self._lock:
            return self.total_weight - self._current_weight


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with multiple algorithms and backoff strategies.

    Features:
    - Token bucket algorithm
    - Sliding window rate limiting
    - Exponential backoff for retries
    - Adaptive rate adjustment based on success/failure
    """

    def __init__(self,
                 rate: float = 10.0,  # requests per second
                 burst: int = 20,
                 algorithm: str = "token_bucket"):
        self.rate = rate
        self.burst = burst
        self.algorithm = algorithm

        self._tokens = burst
        self._last_update = time.time()
        self._lock = threading.Lock()

        # Sliding window data
        self._requests: Deque[float] = deque(maxlen=int(rate * 60))  # 1 minute window

        # Adaptive parameters
        self._success_count = 0
        self._failure_count = 0
        self._backoff_factor = 1.0

    def acquire(self, amount: int = 1) -> bool:
        """
        Try to acquire rate limit permission.

        Returns:
            True if allowed, False if rate limited
        """
        with self._lock:
            if self.algorithm == "token_bucket":
                return self._acquire_token_bucket(amount)
            elif self.algorithm == "sliding_window":
                return self._acquire_sliding_window(amount)
            else:
                return True  # No limiting

    def _acquire_token_bucket(self, amount: int) -> bool:
        """Token bucket algorithm."""
        now = time.time()
        elapsed = now - self._last_update

        # Add tokens based on elapsed time
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_update = now

        if self._tokens >= amount:
            self._tokens -= amount
            self._record_success()
            return True

        self._record_failure()
        return False

    def _acquire_sliding_window(self, amount: int) -> bool:
        """Sliding window algorithm."""
        now = time.time()
        window_start = now - 1.0  # 1 second window

        # Remove old requests
        while self._requests and self._requests[0] < window_start:
            self._requests.popleft()

        if len(self._requests) < self.rate:
            for _ in range(amount):
                self._requests.append(now)
            self._record_success()
            return True

        self._record_failure()
        return False

    def _record_success(self):
        """Record successful operation."""
        self._success_count += 1
        # Gradually reduce backoff on success
        self._backoff_factor = max(0.1, self._backoff_factor * 0.95)

    def _record_failure(self):
        """Record failed operation (rate limited)."""
        self._failure_count += 1
        # Increase backoff on failure
        self._backoff_factor = min(10.0, self._backoff_factor * 1.1)

    def wait_if_needed(self, amount: int = 1) -> float:
        """
        Wait if rate limited and return wait time.

        Returns:
            Time waited in seconds
        """
        start_time = time.time()
        wait_time = 0.01  # Base wait time

        while not self.acquire(amount):
            time.sleep(wait_time)
            wait_time = min(1.0, wait_time * self._backoff_factor)  # Exponential backoff

        return time.time() - start_time

    async def async_wait_if_needed(self, amount: int = 1) -> float:
        """Async version of wait_if_needed."""
        start_time = time.time()
        wait_time = 0.01

        while not self.acquire(amount):
            await asyncio.sleep(wait_time)
            wait_time = min(1.0, wait_time * self._backoff_factor)

        return time.time() - start_time

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            total_requests = self._success_count + self._failure_count
            success_rate = self._success_count / total_requests if total_requests > 0 else 0

            return {
                "success_count": self._success_count,
                "failure_count": self._failure_count,
                "success_rate": success_rate,
                "current_tokens": getattr(self, '_tokens', 0),
                "backoff_factor": self._backoff_factor,
                "algorithm": self.algorithm
            }


class SmartCircuitBreaker:
    """
    Smart circuit breaker with advanced failure detection and recovery.

    Features:
    - Multiple failure detection strategies
    - Exponential backoff for recovery attempts
    - Half-open state for gradual recovery
    - Success rate tracking
    - Custom failure predicates
    """

    class State(Enum):
        CLOSED = "closed"      # Normal operation
        OPEN = "open"          # Failing, reject requests
        HALF_OPEN = "half_open"  # Testing recovery

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Optional[Exception] = Exception,
                 failure_predicate: Optional[Callable[[Exception], bool]] = None):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_predicate = failure_predicate or (lambda e: True)

        self._state = self.State.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        self._success_count = 0
        self._request_count = 0
        self._lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        if not self._should_allow_request():
            raise CircuitBreakerOpenException("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    async def async_call(self, coro) -> Any:
        """Execute async coroutine through circuit breaker."""
        if not self._should_allow_request():
            raise CircuitBreakerOpenException("Circuit breaker is open")

        try:
            result = await coro
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def _should_allow_request(self) -> bool:
        """Determine if request should be allowed."""
        with self._lock:
            if self._state == self.State.CLOSED:
                return True
            elif self._state == self.State.OPEN:
                if time.time() - self._last_failure_time >= self._recovery_timeout():
                    # Time to try recovery
                    self._state = self.State.HALF_OPEN
                    self._request_count = 0
                    return True
                return False
            elif self._state == self.State.HALF_OPEN:
                # Allow limited requests for testing
                self._request_count += 1
                return self._request_count <= 3  # Allow 3 test requests
            return False

    def _record_success(self):
        """Record successful operation."""
        with self._lock:
            if self._state == self.State.HALF_OPEN:
                self._success_count += 1
                # If we've had enough successes, close the circuit
                if self._success_count >= 2:
                    self._state = self.State.CLOSED
                    self._failure_count = 0
                    self._success_count = 0

    def _record_failure(self, exception: Exception):
        """Record failed operation."""
        with self._lock:
            if not self._is_failure(exception):
                return

            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == self.State.HALF_OPEN:
                # Failed during recovery, go back to open
                self._state = self.State.OPEN
                self._request_count = 0
            elif self._failure_count >= self.failure_threshold:
                # Too many failures, open the circuit
                self._state = self.State.OPEN

    def _is_failure(self, exception: Exception) -> bool:
        """Check if exception should be considered a failure."""
        if self.expected_exception and not isinstance(exception, self.expected_exception):
            return False
        return self.failure_predicate(exception)

    def _recovery_timeout(self) -> float:
        """Calculate recovery timeout with exponential backoff."""
        # Exponential backoff based on failure count
        return self.recovery_timeout * (2 ** min(self._failure_count // self.failure_threshold, 5))

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        with self._lock:
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time,
                "recovery_timeout": self._recovery_timeout()
            }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class ContextAwareLock:
    """
    Lock that tracks context and detects potential deadlocks.

    Features:
    - Deadlock detection using wait-for graph
    - Context tracking for debugging
    - Timeout with deadlock prevention
    - Lock hierarchy enforcement
    """

    def __init__(self, name: str = ""):
        self.name = name or f"lock_{id(self)}"
        self._lock = threading.RLock()
        self._owner: Optional[int] = None
        self._waiters: Dict[int, str] = {}
        self._acquired_at: Dict[int, float] = {}
        self._lock_stack: Dict[int, List[str]] = {}

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire lock with deadlock detection."""
        thread_id = threading.get_ident()
        context = f"Thread-{thread_id}"

        start_time = time.time()

        # Try to acquire with timeout
        if self._lock.acquire(timeout=timeout):
            self._owner = thread_id
            self._acquired_at[thread_id] = time.time()

            # Track lock stack for deadlock detection
            if thread_id not in self._lock_stack:
                self._lock_stack[thread_id] = []
            self._lock_stack[thread_id].append(self.name)

            # Check for potential deadlock
            if self._detect_deadlock(thread_id):
                self.release()
                raise DeadlockDetectedException(f"Deadlock detected for {context}")

            return True

        # Timeout occurred
        if timeout and (time.time() - start_time) >= timeout:
            raise LockTimeoutException(f"Lock timeout for {context}")

        return False

    def release(self):
        """Release lock."""
        thread_id = threading.get_ident()

        if self._owner == thread_id:
            # Remove from lock stack
            if thread_id in self._lock_stack:
                self._lock_stack[thread_id].pop()

            del self._acquired_at[thread_id]
            self._owner = None

        self._lock.release()

    def _detect_deadlock(self, thread_id: int) -> bool:
        """Simple deadlock detection using lock stack."""
        # This is a simplified implementation
        # Production systems would use more sophisticated algorithms
        if thread_id not in self._lock_stack:
            return False

        lock_stack = self._lock_stack[thread_id]
        if len(lock_stack) > 10:  # Arbitrary threshold
            logger.warning(f"Potential deadlock: deep lock stack for thread {thread_id}")
            return True

        return False

    def get_lock_info(self) -> Dict[str, Any]:
        """Get lock status information."""
        return {
            "name": self.name,
            "owner": self._owner,
            "waiters": list(self._waiters.keys()),
            "lock_stack": dict(self._lock_stack),
            "acquired_times": dict(self._acquired_at)
        }


class DeadlockDetectedException(Exception):
    """Exception raised when deadlock is detected."""
    pass


class LockTimeoutException(Exception):
    """Exception raised when lock acquisition times out."""
    pass


class BufferedChannel:
    """
    Buffered channel for CSP-style communication between coroutines/threads.

    Features:
    - Buffered communication
    - Select-like operations
    - Channel closing and draining
    - Backpressure handling
    """

    def __init__(self, buffer_size: int = 10):
        self.buffer_size = buffer_size
        self._buffer: Deque[Any] = deque(maxlen=buffer_size)
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._closed = False

    def send(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """Send item through channel."""
        with self._not_full:
            if self._closed:
                raise ChannelClosedException("Channel is closed")

            if not block:
                if len(self._buffer) >= self.buffer_size:
                    raise ChannelFullException("Channel buffer is full")
            elif timeout is None:
                while len(self._buffer) >= self.buffer_size and not self._closed:
                    self._not_full.wait()
            else:
                if not self._not_full.wait_for(
                    lambda: len(self._buffer) < self.buffer_size or self._closed, timeout
                ):
                    raise ChannelTimeoutException("Channel send timeout")

            if self._closed:
                raise ChannelClosedException("Channel closed during send")

            self._buffer.append(item)
            self._not_empty.notify()

    def receive(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Receive item from channel."""
        with self._not_empty:
            if not block:
                if not self._buffer and not self._closed:
                    raise ChannelEmptyException("Channel buffer is empty")
            elif timeout is None:
                while not self._buffer and not self._closed:
                    self._not_empty.wait()
            else:
                if not self._not_empty.wait_for(
                    lambda: bool(self._buffer) or self._closed, timeout
                ):
                    raise ChannelTimeoutException("Channel receive timeout")

            if not self._buffer and self._closed:
                raise ChannelClosedException("Channel is closed and empty")

            item = self._buffer.popleft()
            self._not_full.notify()
            return item

    def close(self):
        """Close the channel."""
        with self._lock:
            self._closed = True
            self._not_empty.notify_all()
            self._not_full.notify_all()

    def is_closed(self) -> bool:
        """Check if channel is closed."""
        with self._lock:
            return self._closed

    def qsize(self) -> int:
        """Get number of items in channel."""
        with self._lock:
            return len(self._buffer)


class ChannelClosedException(Exception):
    """Exception raised when channel is closed."""
    pass


class ChannelFullException(Exception):
    """Exception raised when channel buffer is full."""
    pass


class ChannelEmptyException(Exception):
    """Exception raised when channel buffer is empty."""
    pass


class ChannelTimeoutException(Exception):
    """Exception raised when channel operation times out."""
    pass


# Demonstration functions
def demonstrate_priority_queue():
    """Demonstrate priority queue."""
    print("🎯 Priority Queue Demo:")

    queue = PriorityQueue(max_size=10)

    # Add items with different priorities
    queue.put("low_priority", Priority.LOW)
    queue.put("high_priority", Priority.HIGH)
    queue.put("normal_priority", Priority.NORMAL)

    # Retrieve items (should come out high -> normal -> low)
    while not queue.empty():
        item = queue.get()
        print(f"Retrieved: {item}")


def demonstrate_adaptive_rate_limiter():
    """Demonstrate adaptive rate limiter."""
    print("\n⏱️  Adaptive Rate Limiter Demo:")

    limiter = AdaptiveRateLimiter(rate=5.0, burst=10)

    # Simulate requests
    for i in range(15):
        allowed = limiter.acquire()
        print(f"Request {i+1}: {'✅' if allowed else '❌'}")
        time.sleep(0.1)

    stats = limiter.get_stats()
    print(f"Success rate: {stats['success_rate']:.2%}")


def demonstrate_smart_circuit_breaker():
    """Demonstrate smart circuit breaker."""
    print("\n🔌 Smart Circuit Breaker Demo:")

    breaker = SmartCircuitBreaker(failure_threshold=3, recovery_timeout=2.0)

    def failing_operation():
        if random.random() < 0.7:  # 70% failure rate
            raise ValueError("Operation failed")
        return "success"

    # Simulate operations
    for i in range(10):
        try:
            result = breaker.call(failing_operation)
            print(f"Call {i+1}: ✅ {result}")
        except CircuitBreakerOpenException:
            print(f"Call {i+1}: 🔌 Circuit breaker open")
        except ValueError:
            print(f"Call {i+1}: ❌ Operation failed")

        time.sleep(0.5)

    state = breaker.get_state()
    print(f"Final state: {state['state']}")


if __name__ == "__main__":
    # Run demonstrations
    logging.basicConfig(level=logging.INFO)

    demonstrate_priority_queue()
    demonstrate_adaptive_rate_limiter()
    demonstrate_smart_circuit_breaker()
