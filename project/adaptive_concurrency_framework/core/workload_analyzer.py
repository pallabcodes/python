"""
Refactored Workload Analyzer (L7 Standard)
Patterns: Strategy, Factory, Context Manager, Observer (Tracing)
"""

import asyncio
import threading
import multiprocessing
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from project.adaptive_concurrency_framework.observability.tracing_manager import tracer

logger = logging.getLogger(__name__)

class BaseWorkloadAnalyzer(ABC):
    """Abstract Strategy: Define the interface for all analyzers."""
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, task: Callable) -> Dict[str, Any]:
        pass

    def benchmark(self, task: Callable, iterations: int = 10) -> float:
        """High-precision benchmarking."""
        start = time.perf_counter()
        for _ in range(iterations):
            task()
        return (time.perf_counter() - start) / iterations

class ThreadingAnalyzer(BaseWorkloadAnalyzer):
    def __init__(self, max_workers: int = 4):
        super().__init__("Threading")
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def analyze(self, task: Callable) -> Dict[str, Any]:
        with tracer.trace(f"{self.name}_Analysis"):
            start = time.perf_counter()
            future = self.executor.submit(task)
            future.result()
            duration = time.perf_counter() - start
            return {"type": "threading", "duration": duration, "overhead": "low"}

    def __enter__(self): return self
    def __exit__(self, *args): self.executor.shutdown()

class ProcessAnalyzer(BaseWorkloadAnalyzer):
    def __init__(self, max_workers: int = 4):
        super().__init__("Multiprocessing")
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

    def analyze(self, task: Callable) -> Dict[str, Any]:
        with tracer.trace(f"{self.name}_Analysis"):
            start = time.perf_counter()
            future = self.executor.submit(task)
            future.result()
            duration = time.perf_counter() - start
            return {"type": "multiprocessing", "duration": duration, "overhead": "high"}

    def __enter__(self): return self
    def __exit__(self, *args): self.executor.shutdown()

class AsyncioAnalyzer(BaseWorkloadAnalyzer):
    def __init__(self):
        super().__init__("Asyncio")

    def analyze(self, task: Callable) -> Dict[str, Any]:
        """Analyze using asyncio task patterns."""
        with tracer.trace(f"{self.name}_Analysis"):
            start = time.perf_counter()
            if asyncio.iscoroutinefunction(task):
                asyncio.run(task())
            else:
                # Bridge for synchronous tasks in an async context
                asyncio.run(self._run_sync_task(task))
            duration = time.perf_counter() - start
            return {"type": "asyncio", "duration": duration, "overhead": "medium"}

    async def _run_sync_task(self, task: Callable):
        return await asyncio.to_thread(task)

class AnalyzerFactory:
    """
    Factory + Registry Pattern: Decouples analyzer selection from implementation.
    Allows for L7-standard extensibility without modifying core factory logic.
    """
    _registry: Dict[str, BaseWorkloadAnalyzer] = {
        "cpu": ProcessAnalyzer(),
        "io": ThreadingAnalyzer(),
        "async": AsyncioAnalyzer()
    }

    @classmethod
    def get_analyzer(cls, workload_type: str) -> BaseWorkloadAnalyzer:
        analyzer = cls._registry.get(workload_type.lower())
        if not analyzer:
            raise ValueError(f"No analyzer registered for type: {workload_type}")
        return analyzer

    @classmethod
    def register_analyzer(cls, workload_type: str, analyzer: BaseWorkloadAnalyzer):
        cls._registry[workload_type.lower()] = analyzer

# Main entry point for demonstration
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    def cpu_task():
        # High-precision L7 benchmark task
        return sum(i*i for i in range(10**6))

    # Using the Factory to get the correct L7-hardened engine
    analyzer = AnalyzerFactory.get_analyzer("cpu")
    
    # Using Context Manager for guaranteed resource cleanup
    with analyzer:
        results = analyzer.analyze(cpu_task)
        logger.info(f"Final Report: {results}")
