"""
Resilience Pattern: Circuit Breaker
Target: L7 Systems (Discord/Scale standard)

Concept:
- Prevents cascading failures in distributed systems.
- States: CLOSED (Normal), OPEN (Failing Fast), HALF_OPEN (Testing Recovery).
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 10.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("Circuit HALF_OPEN: Testing for recovery...")
                self.state = CircuitState.HALF_OPEN
            else:
                logger.warning("Circuit OPEN: Failing fast to prevent cascading failure.")
                raise Exception("CircuitBreaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure()
            raise e

    def _handle_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit CLOSED: System recovered.")
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def _handle_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.error(f"Failure {self.failure_count}/{self.failure_threshold} detected.")
        
        if self.failure_count >= self.failure_threshold:
            logger.critical("Circuit OPENED: Threshold exceeded.")
            self.state = CircuitState.OPEN

# Decorator version for L7 readability
def circuit_breaker(cb: CircuitBreaker):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb(func, *args, **kwargs)
        return wrapper
    return decorator
