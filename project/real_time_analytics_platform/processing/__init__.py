"""
Reactive event processing layer.

Provides:
- Reactive streams for event processing pipelines
- Backpressure handling
"""

from .reactive_stream import ReactiveStream

__all__ = [
    "ReactiveStream"
]
