"""
Module: CPython Interpreter Tuning
Target: L7 Performance Engineers (Google standard)

Key Techniques:
1. GIL Switch Interval: Tuning how often the GIL is released.
2. RAII Hot-Path GC Control: Exception-safe GC disabling to eliminate GC-pause jitter.
3. GC Freeze: Optimizing memory usage for pre-forked worker processes.
"""

import sys
import gc
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


def tune_gil(interval: float = 0.005) -> float:
    """Tune the Global Interpreter Lock (GIL) switch interval.

    Default is 0.005s (5ms).
    Lower = Better responsiveness for IO-bound apps.
    Higher = Better throughput for CPU-heavy multi-threading (reduces context switching).

    Args:
        interval: Target GIL switch interval in seconds.

    Returns:
        Previous GIL switch interval.
    """
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(interval)
    logger.info(f"GIL Switch Interval tuned from {old_interval}s to {interval}s")
    return old_interval


class HotPathGCContext:
    """RAII Context Manager for Hot-Path Garbage Collector Disabling.

    Guarantees exception safety: cyclic GC is disabled upon entry and reliably
    re-enabled (followed by a manual cold-path collection) upon exit even if
    an exception is raised within the hot path.
    """

    def __init__(self, trigger_manual_collect: bool = True):
        self._trigger_manual_collect = trigger_manual_collect
        self._was_enabled = False

    def __enter__(self) -> "HotPathGCContext":
        self._was_enabled = gc.isenabled()
        if self._was_enabled:
            gc.disable()
            logger.debug("Cyclic GC DISABLED for hot-path execution.")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if self._was_enabled:
                gc.enable()
                logger.debug("Cyclic GC RE-ENABLED following hot-path execution.")
            if self._trigger_manual_collect:
                collected = gc.collect()
                logger.debug(f"Manual cold-path collection reclaimed {collected} objects.")
        finally:
            pass


def gc_snapshot_and_freeze() -> None:
    """GC Freeze (Python 3.7+).

    Freezes objects in the permanent generation.
    Critical for pre-forking servers (Gunicorn/Uvicorn) to maximize Copy-on-Write
    memory sharing across child processes.
    """
    gc.collect()  # Full collection before freeze
    gc.freeze()
    logger.info("GC Permanent Generation FROZEN. Optimized for Copy-on-Write sharing.")


class GCTimer:
    """Diagnostic tool to measure GC overhead."""

    def __enter__(self) -> "GCTimer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        duration = time.perf_counter() - self.start
        logger.info(f"Critical section took {duration:.6f}s")


if __name__ == "__main__":
    # Example tuning for a high-load Google-standard service
    tune_gil(0.1)  # Prioritize throughput
    gc_snapshot_and_freeze()

    with GCTimer():
        # Exception-safe RAII GC suppression on the hot path
        with HotPathGCContext(trigger_manual_collect=True):
            total = sum(i for i in range(10**7))
            logger.info(f"Hot-path execution complete. Total = {total}")
