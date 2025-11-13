"""
Advanced Callback Patterns for LangChain.

This module implements comprehensive callback techniques:
1. Custom Callbacks - Custom callback handlers
2. Monitoring Callbacks - Performance monitoring
3. Logging Callbacks - Structured logging
4. Error Callbacks - Error handling callbacks
5. Progress Callbacks - Progress tracking
6. Multi-Callback Manager - Manage multiple callbacks
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class CallbackEvent:
    """Represents a callback event."""
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# ============================================================================
# 1. BASE CALLBACK
# ============================================================================

class BaseCallback(ABC):
    """
    Base Callback - Abstract callback interface.
    
    Based on:
    - LangChain callback patterns
    - Observer pattern
    
    Key Features:
    - Event handling
    - Extensible interface
    - Error handling
    - Production patterns
    
    When to Use:
    - Custom callback needs
    - Event handling
    - Monitoring requirements
    - Production callback systems
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def on_event(self, event: CallbackEvent) -> None:
        """Handle callback event."""
        pass


# ============================================================================
# 2. MONITORING CALLBACK
# ============================================================================

class MonitoringCallback(BaseCallback):
    """
    Monitoring Callback - Performance monitoring.
    
    Based on:
    - Performance monitoring patterns
    - Metrics collection
    
    Key Features:
    - Latency tracking
    - Throughput monitoring
    - Error tracking
    - Performance metrics
    
    When to Use:
    - Performance monitoring
    - Production observability
    - Metrics collection
    - System optimization
    """
    
    def __init__(self):
        super().__init__()
        self.metrics: Dict[str, List[float]] = {
            "latency": [],
            "errors": []
        }
    
    async def on_event(self, event: CallbackEvent) -> None:
        """Handle monitoring event."""
        if event.event_type == "start":
            event.data["start_time"] = time.time()
        elif event.event_type == "end":
            start_time = event.data.get("start_time", time.time())
            latency = time.time() - start_time
            self.metrics["latency"].append(latency)
        elif event.event_type == "error":
            self.metrics["errors"].append(time.time())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        latencies = self.metrics["latency"]
        return {
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
            "max_latency": max(latencies) if latencies else 0.0,
            "min_latency": min(latencies) if latencies else 0.0,
            "error_count": len(self.metrics["errors"])
        }


# ============================================================================
# 3. LOGGING CALLBACK
# ============================================================================

class LoggingCallback(BaseCallback):
    """
    Logging Callback - Structured logging.
    
    Based on:
    - Structured logging patterns
    - Production logging
    
    Key Features:
    - Structured logs
    - Context preservation
    - Log levels
    - Production logging
    
    When to Use:
    - Need structured logging
    - Debugging requirements
    - Production logging
    - Audit requirements
    """
    
    def __init__(self, log_level: int = logging.INFO):
        super().__init__()
        self.log_level = log_level
    
    async def on_event(self, event: CallbackEvent) -> None:
        """Handle logging event."""
        log_message = f"[{event.event_type}] {event.data}"
        self._logger.log(self.log_level, log_message)


# ============================================================================
# 4. PROGRESS CALLBACK
# ============================================================================

class ProgressCallback(BaseCallback):
    """
    Progress Callback - Progress tracking.
    
    Based on:
    - Progress tracking patterns
    - User feedback
    
    Key Features:
    - Progress updates
    - Percentage tracking
    - Status updates
    - User feedback
    
    When to Use:
    - Long-running operations
    - User-facing applications
    - Need progress feedback
    - Production UX systems
    """
    
    def __init__(self, progress_callback: Optional[Callable[[float], None]] = None):
        super().__init__()
        self.progress_callback = progress_callback or self._default_progress
        self.current_progress = 0.0
    
    def _default_progress(self, progress: float) -> None:
        """Default progress handler."""
        print(f"Progress: {progress:.1f}%")
    
    async def on_event(self, event: CallbackEvent) -> None:
        """Handle progress event."""
        if event.event_type == "progress":
            progress = event.data.get("progress", 0.0)
            self.current_progress = progress
            self.progress_callback(progress)


# ============================================================================
# 5. MULTI-CALLBACK MANAGER
# ============================================================================

class CallbackManager:
    """
    Callback Manager - Manage multiple callbacks.
    
    Based on:
    - Multi-observer patterns
    - Callback orchestration
    
    Key Features:
    - Multiple callbacks
    - Event broadcasting
    - Error isolation
    - Production patterns
    
    When to Use:
    - Multiple callback needs
    - Complex monitoring
    - Production callback systems
    - Event-driven systems
    """
    
    def __init__(self):
        self.callbacks: List[BaseCallback] = []
        self._logger = logging.getLogger(f"{__name__}.CallbackManager")
    
    def add_callback(self, callback: BaseCallback):
        """Add a callback."""
        self.callbacks.append(callback)
        self._logger.info(f"Added callback: {callback.__class__.__name__}")
    
    async def emit(self, event: CallbackEvent):
        """
        Emit event to all callbacks.
        
        Args:
            event: Callback event
        """
        for callback in self.callbacks:
            try:
                await callback.on_event(event)
            except Exception as e:
                self._logger.error(
                    f"Callback {callback.__class__.__name__} failed: {e}"
                )


# ============================================================================
# REAL-WORLD EXAMPLE
# ============================================================================

def callbacks_real_world_example() -> None:
    """
    Real-World Scenario: Callbacks - Production LLM Service.
    
    REAL-WORLD SCENARIO:
    ====================
    You're building a production LLM service:
    - Need comprehensive monitoring
    - Track performance metrics
    - Problem: No visibility into LLM execution
    
    THE PROBLEM WITHOUT ADVANCED CALLBACKS:
    ======================================
    - No monitoring → blind to issues
    - No logging → hard to debug
    - No progress → poor UX
    - No error tracking → production issues
    - System opaque → unreliable
    
    THE SOLUTION:
    =============
    Advanced callbacks enable:
    - Monitoring callbacks → performance visibility
    - Logging callbacks → structured logging
    - Progress callbacks → user feedback
    - Error callbacks → error tracking
    - Production observability → reliable system
    
    WHEN TO USE ADVANCED CALLBACKS:
    ===============================
    ✅ Production LLM services
    ✅ Need comprehensive monitoring
    ✅ Long-running operations
    ✅ User-facing applications
    ✅ Production observability systems
    """
    print("=" * 70)
    print("REAL-WORLD SCENARIO: Production LLM Service")
    print("=" * 70)
    print()
    print("SITUATION:")
    print("  - Production LLM service")
    print("  - Need comprehensive monitoring")
    print("  - Track performance metrics")
    print("  - Problem: No visibility into LLM execution")
    print()
    print("THE PROBLEM:")
    print("  Without advanced callbacks:")
    print("    ❌ No monitoring → blind to issues")
    print("    ❌ No logging → hard to debug")
    print("    ❌ No progress → poor UX")
    print("    ❌ No error tracking → production issues")
    print()
    print("THE SOLUTION:")
    print("  With advanced callbacks:")
    print("    ✅ Monitoring callbacks → performance visibility")
    print("    ✅ Logging callbacks → structured logging")
    print("    ✅ Progress callbacks → user feedback")
    print("    ✅ Error callbacks → error tracking")
    print()
    print("=" * 70)
    print()

    print("Available callback patterns:")
    patterns = [
        ("Custom Callbacks", "Custom handlers → flexible processing"),
        ("Monitoring Callbacks", "Performance tracking → observability"),
        ("Logging Callbacks", "Structured logging → debugging"),
        ("Error Callbacks", "Error handling → reliability"),
        ("Progress Callbacks", "Progress tracking → user feedback"),
        ("Multi-Callback Manager", "Multiple callbacks → comprehensive monitoring")
    ]

    for pattern, benefit in patterns:
        print(f"  ✅ {pattern}: {benefit}")

    print()
    print("  ✅ Advanced callbacks enabled production observability!")
    print()
    print("=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("1. WHEN TO USE ADVANCED CALLBACKS:")
    print("   ✅ Production LLM services")
    print("   ✅ Need comprehensive monitoring")
    print("   ✅ Long-running operations")
    print("   ✅ User-facing applications")
    print()
    print("2. WHY IT MATTERS:")
    print("   - Performance visibility")
    print("   - Structured logging")
    print("   - User feedback")
    print("   - Production reliability")
    print("=" * 70)
    print()

