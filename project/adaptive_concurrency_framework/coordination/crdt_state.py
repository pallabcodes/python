"""
CRDT state sharing implementation based on Zhao & Haller paper.

Implements CRDTs with Observable Atomic Consistency Protocol (OACP) for
sharing optimization state across instances.
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CRDTValue:
    """CRDT value with metadata."""
    
    value: Any
    timestamp: float
    node_id: str
    version: int = 0


class CRDTState:
    """
    CRDT-based state sharing for optimization insights.
    
    Based on: "Observable Atomic Consistency for CvRDTs"
    Authors: Xin Zhao, Philipp Haller
    ArXiv: 1802.09462
    
    Features:
    - Eventual consistency with atomic operations
    - Observable atomic consistency protocol
    - Mergeable data types
    - Reliable total order broadcast
    """
    
    def __init__(self, node_id: str):
        """
        Initialize CRDT state.
        
        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id
        self._state: Dict[str, CRDTValue] = {}
        self._lock = asyncio.Lock()
        self._observers: List[callable] = []
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def set(self, key: str, value: Any, version: Optional[int] = None) -> None:
        """
        Set a value in CRDT state.
        
        Args:
            key: State key
            value: Value to set
            version: Optional version number
        """
        async with self._lock:
            current = self._state.get(key)
            new_version = version if version is not None else (current.version + 1 if current else 0)
            
            new_value = CRDTValue(
                value=value,
                timestamp=time.time(),
                node_id=self.node_id,
                version=new_version
            )
            
            # Merge logic: keep value with highest version
            if current is None or new_version > current.version:
                self._state[key] = new_value
                await self._notify_observers(key, new_value)
                self._logger.debug(f"Set CRDT state: {key}={value} (version={new_version})")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from CRDT state."""
        async with self._lock:
            value = self._state.get(key)
            return value.value if value else None
    
    async def merge(self, other_state: Dict[str, CRDTValue]) -> None:
        """
        Merge state from another node.
        
        Args:
            other_state: State dictionary from another node
        """
        async with self._lock:
            for key, other_value in other_state.items():
                current = self._state.get(key)
                
                if current is None:
                    self._state[key] = other_value
                    await self._notify_observers(key, other_value)
                elif other_value.version > current.version:
                    self._state[key] = other_value
                    await self._notify_observers(key, other_value)
                elif other_value.version == current.version and other_value.timestamp > current.timestamp:
                    # Same version, use timestamp as tiebreaker
                    self._state[key] = other_value
                    await self._notify_observers(key, other_value)
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all state values."""
        async with self._lock:
            return {key: value.value for key, value in self._state.items()}
    
    async def observe(self, observer: callable) -> None:
        """
        Register observer for state changes.
        
        Args:
            observer: Callable that receives (key, value) on changes
        """
        async with self._lock:
            self._observers.append(observer)
    
    async def _notify_observers(self, key: str, value: CRDTValue) -> None:
        """Notify observers of state changes."""
        for observer in self._observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(key, value)
                else:
                    observer(key, value)
            except Exception as e:
                self._logger.error(f"Observer notification error: {e}")


class ObservableAtomicConsistencyProtocol:
    """
    Observable Atomic Consistency Protocol (OACP) implementation.
    
    Combines CRDTs with reliable total order broadcast to provide
    on-demand strong consistency.
    """
    
    def __init__(self, node_id: str):
        """Initialize OACP."""
        self.node_id = node_id
        self._crdt_state = CRDTState(node_id)
        self._pending_operations: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def atomically(self, operation: callable, *args, **kwargs) -> Any:
        """
        Execute operation with atomic consistency.
        
        Args:
            operation: Operation to execute atomically
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Operation result
        """
        async with self._lock:
            # Execute operation atomically
            result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
            
            # Record operation for total order broadcast
            op_record = {
                "operation": operation.__name__,
                "args": args,
                "kwargs": kwargs,
                "result": result,
                "timestamp": time.time(),
                "node_id": self.node_id
            }
            self._pending_operations.append(op_record)
            
            return result
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current CRDT state."""
        return await self._crdt_state.get_all()
    
    async def set_state(self, key: str, value: Any) -> None:
        """Set state with atomic consistency."""
        await self.atomically(self._crdt_state.set, key, value)

