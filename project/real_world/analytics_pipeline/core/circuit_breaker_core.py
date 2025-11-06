"""
Core circuit breaker functionality.

This module contains the main CircuitBreaker class and core
fault tolerance logic for preventing cascade failures.
"""

import time
import threading
import logging
from typing import Optional, Callable
from enum import Enum
from dataclasses import dataclass


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    success_threshold: int = 3
    monitoring_window: float = 300.0  # 5 minutes

    def __post_init__(self):
        """Validate configuration."""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be at least 1")
        if self.monitoring_window <= 0:
            raise ValueError("monitoring_window must be positive")


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    state_changes: int = 0
    last_state_change: Optional[float] = None
    last_failure_time: Optional[float] = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance.

    This class implements the circuit breaker pattern to prevent cascade
    failures by monitoring service health and automatically transitioning
    between closed, open, and half-open states.
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[str, CircuitState, CircuitState], None]] = None
    ):
        """Initialize circuit breaker.

        Args:
            name: Circuit breaker name for identification
            config: Circuit breaker configuration
            on_state_change: Callback for state changes
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._on_state_change = on_state_change

        # State management
        self._state = CircuitState.CLOSED
        self._state_lock = threading.RLock()
        self._last_failure_time: Optional[float] = None

        # Statistics
        self._stats = CircuitBreakerStats()
        self._stats_lock = threading.Lock()

        # Failure tracking
        self._failure_count = 0
        self._success_count = 0

        # Logging
        self._logger = logging.getLogger(f"{__name__}.{name}")

        self._logger.info(
            f"Initialized circuit breaker '{name}' with failure_threshold={self.config.failure_threshold}, "
            f"recovery_timeout={self.config.recovery_timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        with self._state_lock:
            return self._state

    def allow_request(self) -> bool:
        """Check if request should be allowed.

        Returns:
            True if request should proceed, False if circuit is open
        """
        with self._state_lock:
            current_time = time.time()

            if self._state == CircuitState.CLOSED:
                return True

            elif self._state == CircuitState.OPEN:
                return False

# Import circuit breaker methods
from .circuit_breaker_state_methods import (
    allow_request, record_success, record_failure, get_stats
)
from .circuit_breaker_control_methods import (
    reset, force_open, force_close, _transition_to
)
