"""
Core adaptive engine for the concurrency optimization framework.

This module orchestrates all components of the adaptive concurrency framework,
managing the lifecycle and coordination of workload analysis, benchmarking,
and optimization.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FrameworkConfig:
    """Configuration for the adaptive concurrency framework."""
    
    enable_benchmarking: bool = True
    enable_optimization: bool = True
    enable_distributed_coordination: bool = False
    enable_ml_selector: bool = False
    benchmark_interval: float = 60.0
    optimization_interval: float = 30.0
    max_workers_threading: int = 4
    max_workers_multiprocessing: int = 4
    max_concurrent_tasks_asyncio: int = 100


@dataclass
class OptimizationResult:
    """Result of an optimization decision."""
    
    selected_strategy: str
    performance_improvement: float
    metrics: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0


class AdaptiveConcurrencyEngine:
    """
    Core adaptive engine orchestrating the concurrency optimization framework.
    
    This engine coordinates all components:
    - Workload analysis using all concurrency models
    - Comprehensive benchmarking of all techniques
    - Adaptive optimization and strategy selection
    - Distributed coordination (if enabled)
    - Observability and metrics collection
    """
    
    def __init__(self, config: Optional[FrameworkConfig] = None):
        """
        Initialize the adaptive concurrency engine.
        
        Args:
            config: Framework configuration. If None, uses default config.
        """
        self.config = config or FrameworkConfig()
        self.running = False
        self._workload_analyzer = None
        self._benchmark_runner = None
        self._adaptive_optimizer = None
        self._distributed_coordinator = None
        self._observability_layer = None
        self._optimization_history = None
        self._optimization_history_list: List[OptimizationResult] = []
        self._real_time_adapter = None
        self._performance_profiler = None
        self._metrics_collector = None
        self._predictive_analytics = None
        self._ml_selector = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def initialize(self) -> None:
        """Initialize all framework components."""
        self._logger.info("Initializing adaptive concurrency framework")
        
        # Import components lazily to avoid circular dependencies
        from .workload_analyzer import WorkloadAnalyzer
        from ..benchmarking.benchmark_runner import BenchmarkRunner
        from ..optimization.adaptive_optimizer import AdaptiveOptimizer
        from ..optimization.real_time_adapter import RealTimeAdapter
        from ..observability.performance_profiler import PerformanceProfiler
        from ..observability.metrics_collector import MetricsCollector
        from ..observability.optimization_history import OptimizationHistory
        from ..observability.predictive_analytics import PredictiveAnalytics
        
        # Initialize components
        self._workload_analyzer = WorkloadAnalyzer(self.config)
        self._benchmark_runner = BenchmarkRunner(self.config) if self.config.enable_benchmarking else None
        self._adaptive_optimizer = AdaptiveOptimizer(self.config) if self.config.enable_optimization else None
        self._real_time_adapter = RealTimeAdapter(self.config) if self.config.enable_optimization else None
        
        if self.config.enable_distributed_coordination:
            from ..coordination.distributed_coordinator import DistributedCoordinator
            self._distributed_coordinator = DistributedCoordinator()
            await self._distributed_coordinator.initialize()
        
        self._performance_profiler = PerformanceProfiler()
        self._metrics_collector = MetricsCollector()
        self._optimization_history = OptimizationHistory()
        self._predictive_analytics = PredictiveAnalytics(self._optimization_history)
        
        if self.config.enable_ml_selector:
            from ..optimization.ml_selector import MLPatternSelector
            self._ml_selector = MLPatternSelector(self._optimization_history, enable_ml=True)
        else:
            self._ml_selector = None
        
        self._logger.info("Framework initialization complete")
    
    async def start(self) -> None:
        """Start the adaptive concurrency framework."""
        if self.running:
            self._logger.warning("Framework is already running")
            return
        
        await self.initialize()
        self.running = True
        
        self._logger.info("Starting adaptive concurrency framework")
        
        # Start background tasks
        if self.config.enable_benchmarking and self._benchmark_runner:
            asyncio.create_task(self._benchmark_loop())
        
        if self.config.enable_optimization and self._adaptive_optimizer:
            asyncio.create_task(self._optimization_loop())
        
        if self._real_time_adapter:
            await self._real_time_adapter.start()
        
        if self._performance_profiler:
            self._performance_profiler.start()
        
        self._logger.info("Framework started successfully")
    
    async def stop(self) -> None:
        """Stop the adaptive concurrency framework."""
        if not self.running:
            return
        
        self._logger.info("Stopping adaptive concurrency framework")
        self.running = False
        
        # Stop all components
        if self._real_time_adapter:
            await self._real_time_adapter.stop()
        
        if self._performance_profiler:
            self._performance_profiler.stop()
        
        if self._distributed_coordinator:
            await self._distributed_coordinator.shutdown()
        
        self._logger.info("Framework stopped")
    
    async def analyze_workload(self, task: Any) -> Dict[str, Any]:
        """
        Analyze a workload to determine its characteristics.
        
        Args:
            task: The task to analyze (function, coroutine, or callable)
            
        Returns:
            Dictionary containing workload characteristics
        """
        if not self._workload_analyzer:
            await self.initialize()
        
        return await self._workload_analyzer.analyze(task)
    
    async def benchmark_strategies(self, workload: Any) -> Dict[str, Any]:
        """
        Benchmark different concurrency strategies for a workload.
        
        Args:
            workload: The workload to benchmark
            
        Returns:
            Dictionary containing benchmark results for all strategies
        """
        if not self._benchmark_runner:
            raise RuntimeError("Benchmarking is not enabled")
        
        return await self._benchmark_runner.run_comprehensive_benchmark(workload)
    
    async def optimize_strategy(self, workload: Any) -> OptimizationResult:
        """
        Optimize concurrency strategy for a workload.
        
        Args:
            workload: The workload to optimize
            
        Returns:
            OptimizationResult with selected strategy and metrics
        """
        if not self._adaptive_optimizer:
            raise RuntimeError("Optimization is not enabled")
        
        # Analyze workload
        workload_characteristics = await self.analyze_workload(workload)
        
        # Benchmark strategies
        benchmark_results = await self.benchmark_strategies(workload)
        
        # Optimize
        decision = await self._adaptive_optimizer.optimize(
            workload_characteristics,
            benchmark_results
        )
        
        # Record optimization in history
        if self._optimization_history:
            record = self._optimization_history.record_optimization(
                strategy_selected=decision.selected_strategy,
                confidence=decision.confidence,
                expected_improvement=decision.expected_improvement,
                workload_characteristics=workload_characteristics.profiling_metrics,
                benchmark_results={k: v.__dict__ if hasattr(v, '__dict__') else str(v) for k, v in benchmark_results.items()},
                reasoning=decision.reasoning
            )
        
        # Convert to OptimizationResult for return
        result = OptimizationResult(
            selected_strategy=decision.selected_strategy,
            performance_improvement=decision.expected_improvement,
            metrics=decision.metrics,
            confidence=decision.confidence
        )
        
        # Store in internal history
        self._optimization_history_list.append(result)
        
        return result
    
    async def _benchmark_loop(self) -> None:
        """Background task for periodic benchmarking."""
        while self.running:
            try:
                await asyncio.sleep(self.config.benchmark_interval)
                # Periodic benchmarking logic here
                self._logger.debug("Running periodic benchmark")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in benchmark loop: {e}", exc_info=True)
    
    async def _optimization_loop(self) -> None:
        """Background task for periodic optimization."""
        while self.running:
            try:
                await asyncio.sleep(self.config.optimization_interval)
                # Periodic optimization logic here
                self._logger.debug("Running periodic optimization")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in optimization loop: {e}", exc_info=True)
    
    def get_optimization_history(self) -> List[OptimizationResult]:
        """Get the history of optimization decisions."""
        return self._optimization_history_list.copy()
    
    def get_optimization_history_records(self):
        """Get detailed optimization history records."""
        if self._optimization_history:
            return self._optimization_history.get_history()
        return []
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current framework metrics."""
        metrics = {
            "running": self.running,
            "optimization_count": len(self._optimization_history_list),
        }
        
        if self._performance_profiler:
            metrics.update(await self._performance_profiler.get_metrics())
        
        if self._metrics_collector:
            summaries = await self._metrics_collector.get_all_summaries()
            metrics["metric_summaries"] = summaries
        
        if self._optimization_history:
            stats = self._optimization_history.get_statistics()
            metrics["optimization_stats"] = stats
        
        return metrics

