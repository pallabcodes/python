"""
Optimization history tracking.

Tracks optimization decisions, performance improvements, and maintains
a log of what worked and why.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRecord:
    """Record of an optimization decision."""
    
    timestamp: float
    strategy_selected: str
    confidence: float
    expected_improvement: float
    actual_improvement: Optional[float] = None
    workload_characteristics: Dict[str, Any] = field(default_factory=dict)
    benchmark_results: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    success: Optional[bool] = None


class OptimizationHistory:
    """
    Tracks optimization history and learns from past decisions.
    
    Features:
    - Records all optimization decisions
    - Tracks actual vs expected improvements
    - Learns which strategies work best
    - Provides recommendations based on history
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize optimization history.
        
        Args:
            max_history: Maximum number of records to keep
        """
        self.max_history = max_history
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._history: deque = deque(maxlen=max_history)
        
    def record_optimization(
        self,
        strategy_selected: str,
        confidence: float,
        expected_improvement: float,
        workload_characteristics: Dict[str, Any],
        benchmark_results: Dict[str, Any],
        reasoning: str
    ) -> OptimizationRecord:
        """
        Record an optimization decision.
        
        Args:
            strategy_selected: Selected strategy
            confidence: Confidence in selection
            expected_improvement: Expected performance improvement
            workload_characteristics: Workload characteristics
            benchmark_results: Benchmark results
            reasoning: Reasoning for the decision
            
        Returns:
            OptimizationRecord
        """
        record = OptimizationRecord(
            timestamp=time.time(),
            strategy_selected=strategy_selected,
            confidence=confidence,
            expected_improvement=expected_improvement,
            workload_characteristics=workload_characteristics,
            benchmark_results=benchmark_results,
            reasoning=reasoning
        )
        
        self._history.append(record)
        self._logger.info(f"Recorded optimization: {strategy_selected} (confidence={confidence:.2f})")
        
        return record
    
    def update_optimization_result(
        self,
        record: OptimizationRecord,
        actual_improvement: float,
        success: bool
    ) -> None:
        """
        Update optimization record with actual results.
        
        Args:
            record: Optimization record to update
            actual_improvement: Actual performance improvement
            success: Whether optimization was successful
        """
        record.actual_improvement = actual_improvement
        record.success = success
        
        self._logger.info(
            f"Updated optimization result: {record.strategy_selected} "
            f"(expected={record.expected_improvement:.2f}%, "
            f"actual={actual_improvement:.2f}%, success={success})"
        )
    
    def get_strategy_success_rate(self, strategy: str) -> float:
        """
        Get success rate for a strategy.
        
        Args:
            strategy: Strategy name
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        strategy_records = [r for r in self._history if r.strategy_selected == strategy]
        
        if not strategy_records:
            return 0.0
        
        successful = sum(1 for r in strategy_records if r.success is True)
        return successful / len(strategy_records)
    
    def get_best_strategy_for_workload(self, workload_type: str) -> Optional[str]:
        """
        Get best strategy for a workload type based on history.
        
        Args:
            workload_type: Type of workload (e.g., "cpu_bound", "io_bound")
            
        Returns:
            Best strategy name or None
        """
        relevant_records = [
            r for r in self._history
            if workload_type in str(r.workload_characteristics) and r.success is True
        ]
        
        if not relevant_records:
            return None
        
        # Count strategy usage
        strategy_counts = {}
        for record in relevant_records:
            strategy = record.strategy_selected
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        if strategy_counts:
            return max(strategy_counts, key=strategy_counts.get)
        
        return None
    
    def get_history(self, limit: Optional[int] = None) -> List[OptimizationRecord]:
        """
        Get optimization history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of optimization records
        """
        history = list(self._history)
        if limit:
            return history[-limit:]
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about optimization history."""
        if not self._history:
            return {}
        
        total_optimizations = len(self._history)
        successful = sum(1 for r in self._history if r.success is True)
        failed = sum(1 for r in self._history if r.success is False)
        unknown = total_optimizations - successful - failed
        
        strategies = {}
        for record in self._history:
            strategy = record.strategy_selected
            if strategy not in strategies:
                strategies[strategy] = {"count": 0, "success": 0, "failed": 0}
            strategies[strategy]["count"] += 1
            if record.success is True:
                strategies[strategy]["success"] += 1
            elif record.success is False:
                strategies[strategy]["failed"] += 1
        
        return {
            "total_optimizations": total_optimizations,
            "successful": successful,
            "failed": failed,
            "unknown": unknown,
            "success_rate": successful / total_optimizations if total_optimizations > 0 else 0,
            "strategies": strategies,
        }

