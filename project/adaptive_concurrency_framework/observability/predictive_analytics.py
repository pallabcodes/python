"""
Predictive analytics for strategy selection.

Uses historical optimization data to predict optimal strategies
for new workloads.
"""

import logging
import statistics
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """Prediction for optimal strategy."""
    
    strategy: str
    confidence: float
    expected_improvement: float
    reasoning: str


class PredictiveAnalytics:
    """
    Predictive analytics for strategy selection.
    
    Uses historical data to predict optimal strategies:
    - Pattern matching on workload characteristics
    - Statistical analysis of past optimizations
    - Machine learning (optional)
    """
    
    def __init__(self, optimization_history: Any):
        """
        Initialize predictive analytics.
        
        Args:
            optimization_history: OptimizationHistory instance
        """
        self.optimization_history = optimization_history
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def predict_optimal_strategy(
        self,
        workload_characteristics: Any
    ) -> Optional[Prediction]:
        """
        Predict optimal strategy for a workload.
        
        Args:
            workload_characteristics: Workload characteristics
            
        Returns:
            Prediction with recommended strategy
        """
        # Get historical data
        history = self.optimization_history.get_history()
        
        if not history:
            return None
        
        # Find similar workloads
        similar_records = self._find_similar_workloads(workload_characteristics, history)
        
        if not similar_records:
            return None
        
        # Analyze which strategies worked best
        strategy_scores = {}
        for record in similar_records:
            if record.success is True and record.actual_improvement is not None:
                strategy = record.strategy_selected
                if strategy not in strategy_scores:
                    strategy_scores[strategy] = []
                strategy_scores[strategy].append(record.actual_improvement)
        
        if not strategy_scores:
            return None
        
        # Calculate average improvement per strategy
        strategy_averages = {
            strategy: statistics.mean(improvements)
            for strategy, improvements in strategy_scores.items()
        }
        
        # Select best strategy
        best_strategy = max(strategy_averages, key=strategy_averages.get)
        best_improvement = strategy_averages[best_strategy]
        
        # Calculate confidence based on number of similar cases
        confidence = min(len(similar_records) / 10.0, 1.0)
        
        reasoning = f"Based on {len(similar_records)} similar workloads, {best_strategy} showed average improvement of {best_improvement:.2f}%"
        
        return Prediction(
            strategy=best_strategy,
            confidence=confidence,
            expected_improvement=best_improvement,
            reasoning=reasoning
        )
    
    def _find_similar_workloads(
        self,
        workload_characteristics: Any,
        history: List[Any]
    ) -> List[Any]:
        """Find similar workloads in history."""
        similar = []
        
        for record in history:
            similarity = self._calculate_similarity(
                workload_characteristics,
                record.workload_characteristics
            )
            
            if similarity > 0.7:  # 70% similarity threshold
                similar.append(record)
        
        return similar
    
    def _calculate_similarity(
        self,
        char1: Any,
        char2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between workload characteristics."""
        # Simple similarity calculation
        # In production, would use more sophisticated methods
        
        similarity = 0.0
        
        if hasattr(char1, 'is_cpu_bound') and 'is_cpu_bound' in char2:
            if char1.is_cpu_bound == char2['is_cpu_bound']:
                similarity += 0.3
        
        if hasattr(char1, 'is_io_bound') and 'is_io_bound' in char2:
            if char1.is_io_bound == char2['is_io_bound']:
                similarity += 0.3
        
        if hasattr(char1, 'recommended_strategy') and 'recommended_strategy' in char2:
            if char1.recommended_strategy == char2['recommended_strategy']:
                similarity += 0.4
        
        return similarity

