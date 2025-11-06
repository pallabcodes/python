"""
Distributed tracing manager for request tracing and observability.

Provides OpenTelemetry-compatible distributed tracing across all
platform components and operations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, ContextManager

from ..core.config import PlatformConfig


class TracingManager:
    """
    OpenTelemetry-compatible distributed tracing manager.

    Features:
    - Request tracing across components
    - Span creation and management
    - Context propagation
    - Trace export and visualization
    - Performance monitoring integration
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize tracing manager.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.TracingManager")

        # Tracing state
        self._active_traces: Dict[str, Dict[str, Any]] = {}
        self._trace_count = 0

        # Tracing settings
        self._enabled = self.config.monitoring.enable_tracing
        self._service_name = self.config.project_name

    async def initialize(self) -> None:
        """Initialize tracing manager."""
        self.logger.info("Initializing tracing manager...")

        if not self._enabled:
            self.logger.info("Tracing is disabled")
            return

        # Initialize OpenTelemetry if available
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

            # Setup tracer provider
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()

            # Add console exporter for development
            console_exporter = ConsoleSpanExporter()
            span_processor = SimpleSpanProcessor(console_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Get tracer
            self._tracer = trace.get_tracer(__name__)

            self.logger.info("OpenTelemetry tracing initialized")

        except ImportError:
            self.logger.warning("OpenTelemetry not available, using mock tracing")
            self._tracer = None

    def start_trace(
        self,
        operation: str,
        trace_id: Optional[str] = None,
        parent_span: Optional[Any] = None
    ) -> ContextManager:
        """
        Start a new trace or span.

        Args:
            operation: Operation name
            trace_id: Optional trace ID
            parent_span: Optional parent span

        Returns:
            Context manager for span
        """
        if not self._enabled:
            return self._mock_span()

        if self._tracer:
            # Real OpenTelemetry span
            return self._tracer.start_as_span(operation)

        else:
            # Mock span for development
            return self._mock_span(operation, trace_id)

    def _mock_span(self, operation: str = "mock_operation", trace_id: Optional[str] = None) -> ContextManager:
        """Create a mock span for development."""
        class MockSpan:
            def __init__(self, operation, trace_id):
                self.operation = operation
                self.trace_id = trace_id or f"trace_{int(asyncio.get_event_loop().time() * 1000000)}"
                self.start_time = asyncio.get_event_loop().time()

            def __enter__(self):
                self._active_traces[self.trace_id] = {
                    "operation": self.operation,
                    "start_time": self.start_time,
                    "spans": []
                }
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.trace_id in self._active_traces:
                    trace_info = self._active_traces[self.trace_id]
                    trace_info["end_time"] = asyncio.get_event_loop().time()
                    trace_info["duration"] = trace_info["end_time"] - trace_info["start_time"]

                    if exc_type:
                        trace_info["error"] = str(exc_val)

                    self.logger.debug(f"Trace {self.trace_id} completed: {trace_info}")

        return MockSpan(operation, trace_id)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        # In a real implementation, this would set attributes on the current span
        pass

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the current span."""
        # In a real implementation, this would add events to the current span
        pass

    def set_status(self, status: str, description: Optional[str] = None) -> None:
        """Set span status."""
        # In a real implementation, this would set status on the current span
        pass

    def get_active_traces(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active traces."""
        return self._active_traces.copy()

    def get_trace_info(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific trace."""
        return self._active_traces.get(trace_id)

    def clear_completed_traces(self, max_age: float = 3600) -> int:
        """
        Clear completed traces older than max_age.

        Args:
            max_age: Maximum age in seconds

        Returns:
            Number of traces cleared
        """
        current_time = asyncio.get_event_loop().time()
        to_remove = []

        for trace_id, trace_info in self._active_traces.items():
            if "end_time" in trace_info and (current_time - trace_info["end_time"]) > max_age:
                to_remove.append(trace_id)

        for trace_id in to_remove:
            del self._active_traces[trace_id]

        if to_remove:
            self.logger.debug(f"Cleared {len(to_remove)} old traces")

        return len(to_remove)

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """
        Inject current trace context into carrier.

        Args:
            carrier: Context carrier (headers, etc.)
        """
        # In a real implementation, this would inject trace context
        # for propagation across service boundaries
        pass

    def extract_context(self, carrier: Dict[str, str]) -> Optional[Any]:
        """
        Extract trace context from carrier.

        Args:
            carrier: Context carrier (headers, etc.)

        Returns:
            Extracted context or None
        """
        # In a real implementation, this would extract trace context
        # for continuing traces across service boundaries
        return None

    async def export_traces(self, format: str = "json") -> str:
        """
        Export traces in specified format.

        Args:
            format: Export format ("json", "jaeger", etc.)

        Returns:
            Exported trace data
        """
        if format == "json":
            import json
            return json.dumps(self._active_traces, indent=2, default=str)
        else:
            return f"Trace export in {format} format not implemented"

    def get_tracing_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        active_traces = len(self._active_traces)
        completed_traces = sum(1 for t in self._active_traces.values() if "end_time" in t)

        return {
            "enabled": self._enabled,
            "active_traces": active_traces,
            "completed_traces": completed_traces,
            "total_traces_created": self._trace_count,
            "service_name": self._service_name
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "healthy": True,
            "tracing_enabled": self._enabled,
            "active_traces": len(self._active_traces),
            "opentelemetry_available": self._tracer is not None
        }

    async def shutdown(self) -> None:
        """Shutdown tracing manager."""
        self.logger.info("Shutting down tracing manager...")

        # Clear all active traces
        self._active_traces.clear()

        self.logger.info("Tracing manager shutdown complete")
