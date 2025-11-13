"""
Adaptive optimizer that selects optimal concurrency strategy.

This module implements intelligent strategy selection based on:
- Workload characteristics from workload analyzer
- Benchmark results from comprehensive benchmarker
- Performance metrics and resource usage
- Historical optimization data
"""

import asyncio
import logging
import statistics
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class OptimizationDecision:
    """Decision made by the adaptive optimizer."""
    
    selected_strategy: str
    confidence: float
    expected_improvement: float
    reasoning: str
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class AdaptiveOptimizer:
    """
    Adaptive optimizer that selects optimal concurrency strategy.
    
    Uses:
    - Workload characteristics from WorkloadAnalyzer
    - Benchmark results from BenchmarkRunner
    - Performance metrics
    - Historical optimization data
    """
    
    def __init__(self, config: Any):
        """Initialize adaptive optimizer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._optimization_history: List[OptimizationDecision] = []
        
    async def optimize(
        self,
        workload_characteristics: Any,
        benchmark_results: Dict[str, Any]
    ) -> OptimizationDecision:
        """
        Optimize concurrency strategy selection.
        
        Args:
            workload_characteristics: Characteristics from WorkloadAnalyzer
            benchmark_results: Results from BenchmarkRunner
            
        Returns:
            OptimizationDecision with selected strategy
        """
        self._logger.info("Starting adaptive optimization")
        
        # Analyze benchmark results
        strategy_scores = self._score_strategies(workload_characteristics, benchmark_results)
        
        # Select optimal strategy
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
        
        # Calculate confidence
        confidence = self._calculate_confidence(strategy_scores, best_strategy)
        
        # Estimate improvement
        improvement = self._estimate_improvement(best_strategy, strategy_scores)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            workload_characteristics,
            best_strategy,
            strategy_scores
        )
        
        decision = OptimizationDecision(
            selected_strategy=best_strategy[0],
            confidence=confidence,
            expected_improvement=improvement,
            reasoning=reasoning,
            alternatives=self._get_alternatives(strategy_scores),
            metrics={"scores": strategy_scores}
        )
        
        self._optimization_history.append(decision)
        self._logger.info(f"Optimization complete: {decision.selected_strategy} (confidence={confidence:.2f})")
        
        return decision
    
    def _score_strategies(
        self,
        workload_characteristics: Any,
        benchmark_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Score all available strategies."""
        scores = {}
        
        # Score based on workload characteristics
        if workload_characteristics.is_cpu_bound:
            scores["multiprocessing"] = 0.9
            scores["threading"] = 0.3
            scores["asyncio"] = 0.2
        elif workload_characteristics.is_io_bound:
            scores["asyncio"] = 0.9
            scores["threading"] = 0.7
            scores["multiprocessing"] = 0.2
        elif workload_characteristics.is_mixed:
            scores["hybrid"] = 0.9
            scores["asyncio"] = 0.6
            scores["threading"] = 0.5
            scores["multiprocessing"] = 0.4
        
        # Adjust scores based on benchmark results
        for strategy_name, result in benchmark_results.items():
            if hasattr(result, 'throughput') and result.throughput > 0:
                # Normalize throughput score
                throughput_score = min(result.throughput / 1000.0, 1.0)  # Normalize to 0-1
                
                # Combine with existing score
                base_strategy = strategy_name.split('_')[0]
                if base_strategy in scores:
                    scores[base_strategy] = (scores[base_strategy] + throughput_score) / 2
                else:
                    scores[strategy_name] = throughput_score
        
        # Use recommended strategy from workload analyzer
        if workload_characteristics.recommended_strategy:
            recommended = workload_characteristics.recommended_strategy
            if recommended in scores:
                scores[recommended] *= 1.2  # Boost recommended strategy
        
        return scores
    
    def _calculate_confidence(
        self,
        strategy_scores: Dict[str, float],
        best_strategy: tuple
    ) -> float:
        """Calculate confidence in the selected strategy."""
        if not strategy_scores:
            return 0.0
        
        best_score = best_strategy[1]
        scores = list(strategy_scores.values())
        scores.sort(reverse=True)
        
        if len(scores) < 2:
            return 0.5
        
        # Confidence based on score difference
        score_diff = best_score - scores[1] if len(scores) > 1 else best_score
        confidence = min(score_diff * 2, 1.0)
        
        # Boost confidence if best score is significantly higher
        if best_score > 0.8:
            confidence = min(confidence + 0.2, 1.0)
        
        return confidence
    
    def _estimate_improvement(
        self,
        best_strategy: tuple,
        strategy_scores: Dict[str, float]
    ) -> float:
        """Estimate performance improvement."""
        if not strategy_scores:
            return 0.0
        
        best_score = best_strategy[1]
        avg_score = statistics.mean(strategy_scores.values())
        
        if avg_score > 0:
            improvement = ((best_score - avg_score) / avg_score) * 100
            return max(improvement, 0.0)
        
        return 0.0
    
    def _generate_reasoning(
        self,
        workload_characteristics: Any,
        best_strategy: tuple,
        strategy_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning for the decision."""
        strategy_name = best_strategy[0]
        score = best_strategy[1]
        
        reasoning_parts = []
        
        if workload_characteristics.is_cpu_bound:
            reasoning_parts.append("Workload is CPU-bound")
        elif workload_characteristics.is_io_bound:
            reasoning_parts.append("Workload is I/O-bound")
        elif workload_characteristics.is_mixed:
            reasoning_parts.append("Workload is mixed (CPU and I/O)")
        
        reasoning_parts.append(f"Selected strategy: {strategy_name} (score: {score:.2f})")
        
        if len(strategy_scores) > 1:
            alternatives = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            if alternatives:
                alt_names = [f"{name} ({score:.2f})" for name, score in alternatives]
                reasoning_parts.append(f"Alternatives: {', '.join(alt_names)}")
        
        return ". ".join(reasoning_parts)
    
    def _get_alternatives(self, strategy_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get alternative strategies."""
        sorted_strategies = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"strategy": name, "score": score} for name, score in sorted_strategies[1:6]]
    
    def get_optimization_history(self) -> List[OptimizationDecision]:
        """Get optimization history."""
        return self._optimization_history.copy()

