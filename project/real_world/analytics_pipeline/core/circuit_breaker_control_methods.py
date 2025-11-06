
def force_open(self: CircuitBreaker) -> None:
    """Force circuit breaker to open state."""
    with self._state_lock:
        self._transition_to(CircuitState.OPEN)


def force_close(self: CircuitBreaker) -> None:
    """Force circuit breaker to closed state."""
    with self._state_lock:
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0

        with self._stats_lock:
            self._stats.state_changes += 1
            self._stats.last_state_change = time.time()

        self._logger.info(f"Circuit breaker '{self.name}' force closed from {old_state.value}")

        if self._on_state_change and old_state != CircuitState.CLOSED:
            try:
                self._on_state_change(self.name, old_state, CircuitState.CLOSED)
            except Exception as e:
                self._logger.error(f"Force close callback failed: {e}")


def _transition_to(self: CircuitBreaker, new_state: CircuitState) -> None:
    """Transition to a new state.

    Args:
        new_state: State to transition to
    """
    old_state = self._state
    self._state = new_state

    with self._stats_lock:
        self._stats.state_changes += 1
        self._stats.last_state_change = time.time()

    self._logger.info(
        f"Circuit breaker '{self.name}' transitioned from {old_state.value} to {new_state.value}"
    )

    if self._on_state_change:
        try:
            self._on_state_change(self.name, old_state, new_state)
        except Exception as e:
            self._logger.error(f"State change callback failed: {e}")
