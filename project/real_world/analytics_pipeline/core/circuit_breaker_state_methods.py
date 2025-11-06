"""
CircuitBreaker method implementations.

This module contains the method implementations for the CircuitBreaker class
to keep the main class file focused and under the 200-line limit.
"""

import time
from typing import Optional

from .circuit_breaker_core import CircuitBreaker, CircuitBreakerStats, CircuitState


def allow_request(self: CircuitBreaker) -> bool:
    """Check if request should be allowed.

    Returns:
        True if request should proceed, False if circuit is open
    """
    with self._state_lock:
        current_time = time.time()

        if self._state == CircuitState.CLOSED:
            return True

        elif self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self._last_failure_time and
                current_time - self._last_failure_time >= self.config.recovery_timeout):
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False

        elif self._state == CircuitState.HALF_OPEN:
            return True

        return False


def record_success(self: CircuitBreaker) -> None:
    """Record a successful request."""
    with self._state_lock:
        with self._stats_lock:
            self._stats.total_requests += 1
            self._stats.successful_requests += 1
            self._stats.consecutive_successes += 1
            self._stats.consecutive_failures = 0

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1

            # Check if we've met success threshold for recovery
            if self._success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self._success_count = 0


def record_failure(self: CircuitBreaker) -> None:
    """Record a failed request."""
    current_time = time.time()

    with self._state_lock:
        with self._stats_lock:
            self._stats.total_requests += 1
            self._stats.failed_requests += 1
            self._stats.consecutive_failures += 1
            self._stats.consecutive_successes = 0
            self._last_failure_time = current_time

        if self._state == CircuitState.CLOSED:
            self._failure_count += 1

            # Check if we've exceeded failure threshold
            if self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                self._failure_count = 0

        elif self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open state immediately opens circuit
            self._transition_to(CircuitState.OPEN)
            self._success_count = 0


def get_stats(self: CircuitBreaker) -> CircuitBreakerStats:
    """Get circuit breaker statistics."""
    with self._stats_lock:
        return CircuitBreakerStats(
            total_requests=self._stats.total_requests,
            successful_requests=self._stats.successful_requests,
            failed_requests=self._stats.failed_requests,
            state_changes=self._stats.state_changes,
            last_state_change=self._stats.last_state_change,
            last_failure_time=self._stats.last_failure_time,
            consecutive_successes=self._stats.consecutive_successes,
            consecutive_failures=self._stats.consecutive_failures
        )


def reset(self: CircuitBreaker) -> None:
    """Reset circuit breaker to closed state."""
# Control methods moved to circuit_breaker_control_methods.py
