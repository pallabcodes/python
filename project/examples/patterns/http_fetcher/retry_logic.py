"""
Retry logic for HTTP requests.

This module provides configurable retry strategies with exponential
backoff, jitter, and intelligent error classification for HTTP requests.
"""

import time
import random
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Retry strategies for failed requests."""
    FIXED = "fixed"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"


class RetryCondition(Enum):
    """Conditions that trigger retries."""
    HTTP_5XX = "http_5xx"
    HTTP_429 = "http_429"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    conditions: List[RetryCondition] = None

    def __post_init__(self):
        """Validate configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")

        if self.conditions is None:
            # Default retry conditions
            self.conditions = [
                RetryCondition.HTTP_5XX,
                RetryCondition.HTTP_429,
                RetryCondition.CONNECTION_ERROR,
                RetryCondition.TIMEOUT
            ]


class RetryContext:
    """Context information for retry attempts."""

    def __init__(self, attempt: int, max_attempts: int, start_time: float):
        """Initialize retry context.

        Args:
            attempt: Current attempt number (1-based)
            max_attempts: Maximum number of attempts
            start_time: When the retry sequence started
        """
        self.attempt = attempt
        self.max_attempts = max_attempts
        self.start_time = start_time
        self.elapsed_time = time.time() - start_time
        self.last_error = None

    @property
    def is_last_attempt(self) -> bool:
        """Check if this is the last attempt."""
        return self.attempt >= self.max_attempts

    @property
    def attempts_remaining(self) -> int:
        """Get number of attempts remaining."""
        return max(0, self.max_attempts - self.attempt)


class RetryHandler:
    """Handles retry logic for HTTP requests."""

    def __init__(self, config: RetryConfig):
        """Initialize retry handler.

        Args:
            config: Retry configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)

    def should_retry(self, error: Exception, response: Optional[Any] = None) -> bool:
        """Determine if a request should be retried based on the error.

        Args:
            error: The exception that occurred
            response: Optional HTTP response object

        Returns:
            True if the request should be retried
        """
        # Check HTTP status codes
        if response is not None and hasattr(response, 'status_code'):
            status_code = response.status_code

            if (RetryCondition.HTTP_5XX in self.config.conditions and
                500 <= status_code < 600):
                return True

            if (RetryCondition.HTTP_429 in self.config.conditions and
                status_code == 429):
                return True

        # Check exception types
        error_type = type(error).__name__

        if (RetryCondition.CONNECTION_ERROR in self.config.conditions and
            "Connection" in error_type):
            return True

        if (RetryCondition.TIMEOUT in self.config.conditions and
            "Timeout" in error_type):
            return True

        if (RetryCondition.NETWORK_ERROR in self.config.conditions and
            any(net_error in error_type.lower() for net_error in
                ['network', 'socket', 'ssl', 'certificate'])):
            return True

        return False

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds before next attempt
        """
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay

        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt

        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (2 ** (attempt - 1))

        else:
            delay = self.config.base_delay

        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)

        # Apply jitter if enabled
        if self.config.jitter:
            # Add random jitter of ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Minimum 100ms delay

        return delay

    def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            Exception: The last exception if all retries are exhausted
        """
        start_time = time.time()
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            context = RetryContext(attempt, self.config.max_attempts, start_time)

            try:
                self._logger.debug(
                    f"Executing attempt {attempt}/{self.config.max_attempts}",
                    extra={"attempt": attempt, "max_attempts": self.config.max_attempts}
                )

                result = func(*args, **kwargs)
                return result

            except Exception as e:
                last_exception = e
                context.last_error = e

                self._logger.warning(
                    f"Attempt {attempt} failed: {e}",
                    extra={
                        "attempt": attempt,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

                # Check if we should retry
                if attempt < self.config.max_attempts and self.should_retry(e):
                    delay = self.calculate_delay(attempt)
                    self._logger.info(
                        f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.max_attempts})",
                        extra={"delay": delay, "next_attempt": attempt + 1}
                    )
                    time.sleep(delay)
                else:
                    break

        # All retries exhausted
        self._logger.error(
            f"All {self.config.max_attempts} attempts failed",
            extra={
                "max_attempts": self.config.max_attempts,
                "total_time": time.time() - start_time,
                "final_error": str(last_exception)
            }
        )
        raise last_exception

    def get_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics."""
        return {
            "max_attempts": self.config.max_attempts,
            "strategy": self.config.strategy.value,
            "base_delay": self.config.base_delay,
            "max_delay": self.config.max_delay,
            "jitter": self.config.jitter,
            "conditions": [c.value for c in self.config.conditions]
        }


def create_retry_handler(
    max_attempts: int = 3,
    strategy: str = "exponential_backoff",
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> RetryHandler:
    """Create a retry handler with the specified configuration.

    Args:
        max_attempts: Maximum number of retry attempts
        strategy: Retry strategy ("fixed", "exponential_backoff", "linear_backoff")
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter to delays

    Returns:
        Configured RetryHandler instance
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=RetryStrategy(strategy),
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter
    )
    return RetryHandler(config)

