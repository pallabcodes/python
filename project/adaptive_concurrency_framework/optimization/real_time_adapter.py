"""
Real-time adaptation mechanism for concurrency parameters.

This module adjusts concurrency parameters in real-time as workload changes:
- Thread/process pool sizes
- Async concurrency limits
- Subprocess usage
- Resource allocation
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AdaptationConfig:
    """Configuration for real-time adaptation."""
    
    min_thread_workers: int = 1
    max_thread_workers: int = 10
    min_process_workers: int = 1
    max_process_workers: int = 4
    min_async_concurrency: int = 10
    max_async_concurrency: int = 1000
    adaptation_interval: float = 5.0
    adaptation_threshold: float = 0.2  # 20% change triggers adaptation


@dataclass
class AdaptationMetrics:
    """Metrics for adaptation decisions."""
    
    current_throughput: float
    target_throughput: float
    current_latency: float
    target_latency: float
    resource_usage: Dict[str, float]
    timestamp: float = field(default_factory=time.time)


class RealTimeAdapter:
    """
    Real-time adapter that adjusts concurrency parameters.
    
    Monitors performance metrics and adapts:
    - Thread pool sizes
    - Process pool sizes
    - Async concurrency limits
    - Resource allocation
    """
    
    def __init__(self, config: Any):
        """Initialize real-time adapter."""
        self.config = config
        self._adapter_config = AdaptationConfig()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._current_thread_workers = self.config.max_workers_threading
        self._current_process_workers = self.config.max_workers_multiprocessing
        self._current_async_concurrency = self.config.max_concurrent_tasks_asyncio
        
        self._metrics_history: List[AdaptationMetrics] = []
        self._adaptation_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self) -> None:
        """Start real-time adaptation."""
        if self._running:
            return
        
        self._running = True
        self._adaptation_task = asyncio.create_task(self._adaptation_loop())
        self._logger.info("Real-time adapter started")
    
    async def stop(self) -> None:
        """Stop real-time adaptation."""
        self._running = False
        if self._adaptation_task:
            self._adaptation_task.cancel()
            try:
                await self._adaptation_task
            except asyncio.CancelledError:
                pass
        self._logger.info("Real-time adapter stopped")
    
    async def _adaptation_loop(self) -> None:
        """Background task for real-time adaptation."""
        while self._running:
            try:
                await asyncio.sleep(self._adapter_config.adaptation_interval)
                await self._adapt()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Adaptation loop error: {e}")
    
    async def _adapt(self) -> None:
        """Perform adaptation based on current metrics."""
        if len(self._metrics_history) < 2:
            return
        
        current = self._metrics_history[-1]
        previous = self._metrics_history[-2]
        
        # Calculate changes
        throughput_change = (current.current_throughput - previous.current_throughput) / previous.current_throughput if previous.current_throughput > 0 else 0
        latency_change = (current.current_latency - previous.current_latency) / previous.current_latency if previous.current_latency > 0 else 0
        
        # Adapt thread workers
        if abs(throughput_change) > self._adapter_config.adaptation_threshold:
            if throughput_change < 0:  # Throughput decreased
                if self._current_thread_workers < self._adapter_config.max_thread_workers:
                    self._current_thread_workers += 1
                    self._logger.info(f"Increased thread workers to {self._current_thread_workers}")
            else:  # Throughput increased
                if self._current_thread_workers > self._adapter_config.min_thread_workers:
                    self._current_thread_workers -= 1
                    self._logger.info(f"Decreased thread workers to {self._current_thread_workers}")
        
        # Adapt process workers
        if abs(throughput_change) > self._adapter_config.adaptation_threshold:
            if throughput_change < 0:  # Throughput decreased
                if self._current_process_workers < self._adapter_config.max_process_workers:
                    self._current_process_workers += 1
                    self._logger.info(f"Increased process workers to {self._current_process_workers}")
            else:  # Throughput increased
                if self._current_process_workers > self._adapter_config.min_process_workers:
                    self._current_process_workers -= 1
                    self._logger.info(f"Decreased process workers to {self._current_process_workers}")
        
        # Adapt async concurrency
        if abs(latency_change) > self._adapter_config.adaptation_threshold:
            if latency_change > 0:  # Latency increased
                if self._current_async_concurrency > self._adapter_config.min_async_concurrency:
                    self._current_async_concurrency = int(self._current_async_concurrency * 0.9)
                    self._logger.info(f"Decreased async concurrency to {self._current_async_concurrency}")
            else:  # Latency decreased
                if self._current_async_concurrency < self._adapter_config.max_async_concurrency:
                    self._current_async_concurrency = int(self._current_async_concurrency * 1.1)
                    self._logger.info(f"Increased async concurrency to {self._current_async_concurrency}")
    
    async def record_metrics(self, metrics: AdaptationMetrics) -> None:
        """Record metrics for adaptation."""
        self._metrics_history.append(metrics)
        
        # Keep only recent history
        if len(self._metrics_history) > 100:
            self._metrics_history = self._metrics_history[-100:]
    
    def get_current_config(self) -> Dict[str, int]:
        """Get current concurrency configuration."""
        return {
            "thread_workers": self._current_thread_workers,
            "process_workers": self._current_process_workers,
            "async_concurrency": self._current_async_concurrency,
        }

