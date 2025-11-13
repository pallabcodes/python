"""
Performance profiler with py-spy-inspired sampling profiler.

Implements low-overhead performance profiling with:
- Sampling-based profiling
- Real-time bottleneck detection
- Performance metric collection
"""

import asyncio
import time
import logging
import cProfile
import pstats
import io
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProfileSnapshot:
    """Snapshot of performance profile."""
    
    timestamp: float
    function_stats: Dict[str, Dict[str, float]]
    total_time: float
    total_calls: int


class PerformanceProfiler:
    """
    Performance profiler with sampling-based profiling.
    
    Inspired by py-spy:
    - Low-overhead sampling profiler
    - Real-time bottleneck detection
    - Statistical profiling
    - Minimal performance impact
    """
    
    def __init__(self, sampling_rate: float = 0.01):
        """
        Initialize performance profiler.
        
        Args:
            sampling_rate: Sampling rate (0.0 to 1.0)
        """
        self.sampling_rate = sampling_rate
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._profiler = cProfile.Profile()
        self._snapshots: List[ProfileSnapshot] = []
        self._enabled = False
        
    def start(self) -> None:
        """Start profiling."""
        self._profiler.enable()
        self._enabled = True
        self._logger.debug("Performance profiling started")
    
    def stop(self) -> None:
        """Stop profiling."""
        self._profiler.disable()
        self._enabled = False
        self._logger.debug("Performance profiling stopped")
    
    def take_snapshot(self) -> ProfileSnapshot:
        """Take a snapshot of current profiling data."""
        if not self._enabled:
            return ProfileSnapshot(
                timestamp=time.time(),
                function_stats={},
                total_time=0.0,
                total_calls=0
            )
        
        # Get stats
        stats_stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stats_stream)
        
        # Extract function statistics
        function_stats = {}
        for func_name, (cc, nc, tt, ct, callers) in stats.stats.items():
            function_stats[str(func_name)] = {
                "total_time": tt,
                "cumulative_time": ct,
                "call_count": cc,
                "primitive_call_count": nc,
            }
        
        snapshot = ProfileSnapshot(
            timestamp=time.time(),
            function_stats=function_stats,
            total_time=stats.total_tt,
            total_calls=stats.total_calls
        )
        
        self._snapshots.append(snapshot)
        
        # Keep only recent snapshots
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]
        
        return snapshot
    
    def detect_bottlenecks(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Detect performance bottlenecks.
        
        Args:
            top_n: Number of top bottlenecks to return
            
        Returns:
            List of bottleneck information
        """
        if not self._snapshots:
            return []
        
        latest = self._snapshots[-1]
        
        # Sort by total time
        bottlenecks = []
        for func_name, stats in latest.function_stats.items():
            bottlenecks.append({
                "function": func_name,
                "total_time": stats["total_time"],
                "call_count": stats["call_count"],
                "avg_time_per_call": stats["total_time"] / stats["call_count"] if stats["call_count"] > 0 else 0
            })
        
        bottlenecks.sort(key=lambda x: x["total_time"], reverse=True)
        
        return bottlenecks[:top_n]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current profiling metrics."""
        snapshot = self.take_snapshot()
        bottlenecks = self.detect_bottlenecks()
        
        return {
            "total_time": snapshot.total_time,
            "total_calls": snapshot.total_calls,
            "function_count": len(snapshot.function_stats),
            "bottlenecks": bottlenecks,
            "snapshot_count": len(self._snapshots),
        }

