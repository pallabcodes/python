import asyncio
import time
import uuid
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class Span:
    def __init__(self, name: str, parent_id: Optional[str] = None):
        self.span_id = str(uuid.uuid4())[:8]
        self.parent_id = parent_id
        self.name = name
        self.start_time = time.perf_counter()
        self.end_time = None
        self.metadata: Dict[str, Any] = {}

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return time.perf_counter() - self.start_time

class TracingManager:
    """
    Observer-based Tracing for 'Instant Debuggability'.
    Captures async execution flow to identify bottlenecks in real-time.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._spans = {}
            cls._instance._active_span_id = asyncio.ContextVar("active_span_id", default=None)
        return cls._instance

    @asynccontextmanager
    async def trace(self, name: str, **metadata):
        parent_id = self._active_span_id.get()
        span = Span(name, parent_id)
        span.metadata.update(metadata)
        
        self._spans[span.span_id] = span
        token = self._active_span_id.set(span.span_id)
        
        logger.debug(f"DEBUG [START]: {span.name} (id={span.span_id}, parent={span.parent_id})")
        
        try:
            yield span
        finally:
            span.finish()
            logger.info(f"DEBUG [END]: {span.name} took {span.duration:.4f}s")
            self._active_span_id.reset(token)

    def get_trace_summary(self):
        """Returns a tree of spans for debugging."""
        return self._spans

# Global instance for easy access
tracer = TracingManager()
