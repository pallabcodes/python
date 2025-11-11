"""
Simple event system for demonstration.
"""

import asyncio
from typing import Dict, List, Any, Callable, Union, Awaitable


class EventSystem:
    """Simple event system for demonstration."""

    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    async def publish(self, event_type: str, data: Any):
        """Publish event to subscribers."""
        if event_type in self.listeners:
            tasks = []
            for callback in self.listeners[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(data))
                else:
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, callback, data))
            await asyncio.gather(*tasks, return_exceptions=True)
