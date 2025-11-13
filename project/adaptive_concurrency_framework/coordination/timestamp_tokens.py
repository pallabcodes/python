"""
Timestamp token implementation based on Lattuada & McSherry paper.

Implements timestamp tokens as a coordination primitive that minimizes
coordination overhead while maintaining concurrency precision.
"""

import time
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TimestampToken:
    """Timestamp token for task coordination."""
    
    timestamp: float
    task_id: str
    sequence: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TimestampTokenCoordinator:
    """
    Coordinator using timestamp tokens for task ordering and synchronization.
    
    Based on: "Timestamp Tokens: A Better Coordination Primitive for Data-Processing Systems"
    Authors: Andrea Lattuada, Frank McSherry
    ArXiv: 2210.06113
    
    Key features:
    - Minimal coordination overhead
    - Precise concurrency control
    - Efficient task ordering
    - Reduced information sharing
    """
    
    def __init__(self):
        """Initialize timestamp token coordinator."""
        self._sequence_counter = 0
        self._lock = asyncio.Lock()
        self._tokens: Dict[str, TimestampToken] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def generate_token(self, task_id: str, metadata: Optional[Dict[str, Any]] = None) -> TimestampToken:
        """
        Generate a timestamp token for a task.
        
        Args:
            task_id: Unique identifier for the task
            metadata: Optional metadata to attach
            
        Returns:
            TimestampToken with timestamp and sequence
        """
        async with self._lock:
            self._sequence_counter += 1
            token = TimestampToken(
                timestamp=time.time(),
                task_id=task_id,
                sequence=self._sequence_counter,
                metadata=metadata or {}
            )
            self._tokens[task_id] = token
            
        self._logger.debug(f"Generated token for task {task_id}: sequence={token.sequence}")
        
        return token
    
    async def get_token(self, task_id: str) -> Optional[TimestampToken]:
        """Get token for a task."""
        return self._tokens.get(task_id)
    
    async def compare_tokens(self, token1: TimestampToken, token2: TimestampToken) -> int:
        """
        Compare two tokens for ordering.
        
        Returns:
            -1 if token1 < token2, 0 if equal, 1 if token1 > token2
        """
        if token1.sequence < token2.sequence:
            return -1
        elif token1.sequence > token2.sequence:
            return 1
        else:
            return 0
    
    async def order_tasks(self, task_ids: List[str]) -> List[str]:
        """
        Order tasks by their timestamp tokens.
        
        Args:
            task_ids: List of task IDs to order
            
        Returns:
            Ordered list of task IDs
        """
        tokens = []
        for task_id in task_ids:
            token = self._tokens.get(task_id)
            if token:
                tokens.append((token, task_id))
        
        tokens.sort(key=lambda x: (x[0].sequence, x[0].timestamp))
        
        return [task_id for _, task_id in tokens]
    
    async def synchronize_tasks(self, task_ids: List[str]) -> Dict[str, TimestampToken]:
        """
        Synchronize multiple tasks using timestamp tokens.
        
        Args:
            task_ids: List of task IDs to synchronize
            
        Returns:
            Dictionary mapping task IDs to their tokens
        """
        tokens = {}
        async with self._lock:
            for task_id in task_ids:
                if task_id not in self._tokens:
                    await self.generate_token(task_id)
                tokens[task_id] = self._tokens[task_id]
        
        return tokens

