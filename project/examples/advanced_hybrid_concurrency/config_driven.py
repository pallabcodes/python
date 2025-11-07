"""
Configuration-Driven Concurrency Approaches.

This module provides runtime-configurable concurrency that can switch between
different models and strategies based on configuration files or runtime conditions.

Features:
- YAML/JSON configuration for concurrency strategies
- Runtime switching between concurrency models
- Adaptive concurrency based on system load
- Configuration validation and hot-reloading
"""

import asyncio
import threading
import time
import logging
import yaml
import json
from typing import Any, Callable, List, Dict, Optional, Union, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import weakref

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


class ConcurrencyModel(Enum):
    """Available concurrency models."""
    ASYNCIO = "asyncio"
    THREADING = "threading"
    MULTIPROCESSING = "multiprocessing"
    HYBRID = "hybrid"


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrency behavior."""
    default_model: ConcurrencyModel = ConcurrencyModel.THREADING
    max_threads: int = 8
    max_processes: Optional[int] = None
    enable_asyncio: bool = True

    # Adaptive settings
    adaptive_enabled: bool = True
    cpu_high_threshold: float = 80.0
    memory_high_threshold: float = 85.0

    # Model-specific configs
    thread_pool_config: Dict[str, Any] = field(default_factory=dict)
    process_pool_config: Dict[str, Any] = field(default_factory=dict)
    asyncio_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'ConcurrencyConfig':
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_json(cls, json_path: str) -> 'ConcurrencyConfig':
        """Load configuration from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConcurrencyConfig':
        """Load configuration from dictionary."""
        return cls(**data)


class ConcurrencyStrategy(ABC):
    """Abstract base class for concurrency strategies."""

    @abstractmethod
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function using this strategy."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics."""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up strategy resources."""
        pass


class ThreadingStrategy(ConcurrencyStrategy):
    """Threading-based concurrency strategy."""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._executor = ThreadPoolExecutor(
            max_workers=config.max_threads,
            **config.thread_pool_config
        )
        self._execution_count = 0
        self._total_time = 0.0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function using thread pool."""
        loop = asyncio.get_event_loop()
        start_time = time.time()

        result = await loop.run_in_executor(
            self._executor, func, *args, **kwargs
        )

        execution_time = time.time() - start_time
        self._execution_count += 1
        self._total_time += execution_time

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get threading strategy stats."""
        return {
            "strategy": "threading",
            "executions": self._execution_count,
            "total_time": self._total_time,
            "avg_time": self._total_time / self._execution_count if self._execution_count > 0 else 0,
            "active_threads": threading.active_count()
        }

    def cleanup(self):
        """Clean up thread executor."""
        self._executor.shutdown(wait=True)


class MultiprocessingStrategy(ConcurrencyStrategy):
    """Multiprocessing-based concurrency strategy."""

    def __init__(self, config: ConcurrencyConfig):
        max_processes = config.max_processes or multiprocessing.cpu_count()
        self._executor = ProcessPoolExecutor(
            max_workers=max_processes,
            **config.process_pool_config
        )
        self._execution_count = 0
        self._total_time = 0.0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function using process pool."""
        loop = asyncio.get_event_loop()
        start_time = time.time()

        result = await loop.run_in_executor(
            self._executor, func, *args, **kwargs
        )

        execution_time = time.time() - start_time
        self._execution_count += 1
        self._total_time += execution_time

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get multiprocessing strategy stats."""
        return {
            "strategy": "multiprocessing",
            "executions": self._execution_count,
            "total_time": self._total_time,
            "avg_time": self._total_time / self._execution_count if self._execution_count > 0 else 0
        }

    def cleanup(self):
        """Clean up process executor."""
        self._executor.shutdown(wait=True)


class AsyncioStrategy(ConcurrencyStrategy):
    """AsyncIO-based concurrency strategy."""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._execution_count = 0
        self._total_time = 0.0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function directly (assuming it's async)."""
        start_time = time.time()

        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            # For sync functions, run in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, *args, **kwargs)

        execution_time = time.time() - start_time
        self._execution_count += 1
        self._total_time += execution_time

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get asyncio strategy stats."""
        return {
            "strategy": "asyncio",
            "executions": self._execution_count,
            "total_time": self._total_time,
            "avg_time": self._total_time / self._execution_count if self._execution_count > 0 else 0
        }

    def cleanup(self):
        """No cleanup needed for asyncio."""
        pass


class HybridStrategy(ConcurrencyStrategy):
    """Hybrid strategy combining multiple approaches."""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._thread_strategy = ThreadingStrategy(config)
        self._process_strategy = MultiprocessingStrategy(config)
        self._asyncio_strategy = AsyncioStrategy(config)
        self._execution_count = 0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function using hybrid approach."""
        # Analyze function characteristics
        func_name = getattr(func, '__name__', '').lower()

        # Choose strategy based on function characteristics
        if 'cpu' in func_name or 'compute' in func_name:
            strategy = self._process_strategy
        elif asyncio.iscoroutinefunction(func) and self.config.enable_asyncio:
            strategy = self._asyncio_strategy
        else:
            strategy = self._thread_strategy

        result = await strategy.execute(func, *args, **kwargs)
        self._execution_count += 1

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get hybrid strategy stats."""
        return {
            "strategy": "hybrid",
            "total_executions": self._execution_count,
            "threading": self._thread_strategy.get_stats(),
            "multiprocessing": self._process_strategy.get_stats(),
            "asyncio": self._asyncio_strategy.get_stats()
        }

    def cleanup(self):
        """Clean up all strategies."""
        self._thread_strategy.cleanup()
        self._process_strategy.cleanup()
        self._asyncio_strategy.cleanup()


class SystemMetrics:
    """System performance metrics for adaptive decisions."""

    @staticmethod
    def get_current() -> Dict[str, float]:
        """Get current system metrics."""
        if not PSUTIL_AVAILABLE:
            return {
                "cpu_percent": 50.0,  # Default values
                "memory_percent": 50.0,
                "load_average": 1.0
            }

        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 1.0
        }


class AdaptiveExecutor:
    """
    Adaptive executor that switches strategies based on system load and task characteristics.

    Features:
    - Automatic strategy selection based on system metrics
    - Runtime adaptation to changing conditions
    - Performance monitoring and optimization
    - Graceful fallback on failures
    """

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._strategies: Dict[ConcurrencyModel, ConcurrencyStrategy] = {}
        self._current_strategy: Optional[ConcurrencyStrategy] = None
        self._adaptation_count = 0
        self._last_adaptation = time.time()

    async def initialize(self):
        """Initialize adaptive executor."""
        # Create all strategies
        self._strategies = {
            ConcurrencyModel.THREADING: ThreadingStrategy(self.config),
            ConcurrencyModel.MULTIPROCESSING: MultiprocessingStrategy(self.config),
            ConcurrencyModel.ASYNCIO: AsyncioStrategy(self.config),
            ConcurrencyModel.HYBRID: HybridStrategy(self.config)
        }

        # Start with default strategy
        self._current_strategy = self._strategies[self.config.default_model]

    async def execute(self, func: Callable, *args, strategy: Optional[ConcurrencyModel] = None, **kwargs) -> Any:
        """Execute function with adaptive strategy selection."""
        if not self._current_strategy:
            await self.initialize()

        # Choose strategy
        if strategy:
            # Explicit strategy requested
            target_strategy = self._strategies[strategy]
        elif self.config.adaptive_enabled:
            # Adaptive selection
            target_strategy = await self._select_adaptive_strategy(func, *args, **kwargs)
        else:
            # Use current/default strategy
            target_strategy = self._current_strategy

        # Switch strategy if needed
        if target_strategy != self._current_strategy:
            logger.info(f"Switching strategy to {target_strategy.__class__.__name__}")
            self._current_strategy = target_strategy
            self._adaptation_count += 1
            self._last_adaptation = time.time()

        # Execute with selected strategy
        try:
            return await target_strategy.execute(func, *args, **kwargs)
        except Exception as e:
            # Fallback to threading on failure
            logger.warning(f"Strategy failed, falling back to threading: {e}")
            fallback_strategy = self._strategies[ConcurrencyModel.THREADING]
            return await fallback_strategy.execute(func, *args, **kwargs)

    async def _select_adaptive_strategy(self, func: Callable, *args, **kwargs) -> ConcurrencyStrategy:
        """Select optimal strategy based on system metrics and task characteristics."""
        metrics = SystemMetrics.get_current()

        # Analyze function
        func_name = getattr(func, '__name__', '').lower()
        is_cpu_intensive = any(keyword in func_name for keyword in ['cpu', 'compute', 'process'])
        is_async = asyncio.iscoroutinefunction(func)

        # Decision logic
        if is_async and self.config.enable_asyncio and metrics['cpu_percent'] < self.config.cpu_high_threshold:
            return self._strategies[ConcurrencyModel.ASYNCIO]
        elif is_cpu_intensive and metrics['cpu_percent'] < self.config.cpu_high_threshold:
            return self._strategies[ConcurrencyModel.MULTIPROCESSING]
        elif metrics['memory_percent'] > self.config.memory_high_threshold:
            # High memory usage, use fewer processes
            return self._strategies[ConcurrencyModel.THREADING]
        else:
            return self._strategies[ConcurrencyModel.HYBRID]

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive executor statistics."""
        if not self._strategies:
            return {"message": "Executor not initialized"}

        strategy_stats = {}
        for model, strategy in self._strategies.items():
            strategy_stats[model.value] = strategy.get_stats()

        return {
            "adaptive_enabled": self.config.adaptive_enabled,
            "current_strategy": self._current_strategy.__class__.__name__ if self._current_strategy else None,
            "adaptation_count": self._adaptation_count,
            "last_adaptation": self._last_adaptation,
            "strategy_stats": strategy_stats,
            "system_metrics": SystemMetrics.get_current()
        }

    async def cleanup(self):
        """Clean up all strategies."""
        for strategy in self._strategies.values():
            strategy.cleanup()
        self._strategies.clear()


class RuntimeSwitcher:
    """
    Runtime switcher for changing concurrency configurations on the fly.

    Features:
    - Hot configuration reloading
    - Gradual strategy transitions
    - Configuration validation
    - Rollback on failures
    """

    def __init__(self, initial_config: ConcurrencyConfig):
        self._current_config = initial_config
        self._executor: Optional[AdaptiveExecutor] = None
        self._config_history: List[ConcurrencyConfig] = [initial_config]
        self._switch_count = 0

    async def initialize(self):
        """Initialize with current configuration."""
        self._executor = AdaptiveExecutor(self._current_config)
        await self._executor.initialize()

    async def switch_config(self, new_config: ConcurrencyConfig) -> bool:
        """
        Switch to new configuration at runtime.

        Returns:
            True if successful, False if failed (rollback performed)
        """
        if not self._executor:
            await self.initialize()

        # Validate new configuration
        if not await self._validate_config(new_config):
            logger.error("Invalid configuration, aborting switch")
            return False

        # Store old config for rollback
        old_config = self._current_config
        old_executor = self._executor

        try:
            # Create new executor with new config
            new_executor = AdaptiveExecutor(new_config)
            await new_executor.initialize()

            # Switch executors
            self._executor = new_executor
            self._current_config = new_config
            self._config_history.append(new_config)
            self._switch_count += 1

            # Clean up old executor
            await old_executor.cleanup()

            logger.info("Configuration switched successfully")
            return True

        except Exception as e:
            logger.error(f"Configuration switch failed: {e}")

            # Rollback
            self._executor = old_executor
            self._current_config = old_config

            return False

    async def _validate_config(self, config: ConcurrencyConfig) -> bool:
        """Validate configuration."""
        try:
            # Basic validation
            if config.max_threads < 1:
                return False
            if config.max_processes is not None and config.max_processes < 1:
                return False
            if config.cpu_high_threshold < 0 or config.cpu_high_threshold > 100:
                return False
            if config.memory_high_threshold < 0 or config.memory_high_threshold > 100:
                return False

            return True
        except Exception:
            return False

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with current configuration."""
        if not self._executor:
            await self.initialize()
        return await self._executor.execute(func, *args, **kwargs)

    def get_current_config(self) -> ConcurrencyConfig:
        """Get current configuration."""
        return self._current_config

    def get_switch_history(self) -> List[ConcurrencyConfig]:
        """Get configuration switch history."""
        return self._config_history.copy()

    async def get_stats(self) -> Dict[str, Any]:
        """Get runtime switcher statistics."""
        executor_stats = await self._executor.get_stats() if self._executor else {}

        return {
            "switch_count": self._switch_count,
            "config_history_length": len(self._config_history),
            "current_config": self._current_config.__dict__,
            "executor_stats": executor_stats
        }


# Example usage and demonstrations
def cpu_intensive_task(data: str, iterations: int = 10000) -> str:
    """CPU-intensive task."""
    import math
    result = sum(math.sin(i) * math.cos(i) for i in range(iterations))
    return f"CPU result for {data}: {result:.2f}"

def io_task(data: str, delay: float = 0.1) -> str:
    """I/O task."""
    time.sleep(delay)
    return f"I/O result for {data}"

async def async_task(data: str) -> str:
    """Async task."""
    await asyncio.sleep(0.05)
    return f"Async result for {data}"


async def demonstrate_adaptive_executor():
    """Demonstrate adaptive executor."""
    print("🎯 Adaptive Executor Demo:")

    config = ConcurrencyConfig(
        default_model=ConcurrencyModel.HYBRID,
        adaptive_enabled=True,
        max_threads=4,
        max_processes=2
    )

    executor = AdaptiveExecutor(config)
    await executor.initialize()

    # Execute different types of tasks
    tasks = [
        (cpu_intensive_task, ("cpu_data", 5000), {}),
        (io_task, ("io_data", 0.1), {}),
        (async_task, ("async_data",), {}),
    ]

    results = []
    for func, args, kwargs in tasks:
        result = await executor.execute(func, *args, **kwargs)
        results.append(result)
        print(f"Result: {result}")

    stats = await executor.get_stats()
    print(f"Strategy adaptations: {stats['adaptation_count']}")

    await executor.cleanup()


async def demonstrate_runtime_switcher():
    """Demonstrate runtime configuration switching."""
    print("\n🔄 Runtime Switcher Demo:")

    # Initial config
    initial_config = ConcurrencyConfig(
        default_model=ConcurrencyModel.THREADING,
        max_threads=2
    )

    switcher = RuntimeSwitcher(initial_config)
    await switcher.initialize()

    # Execute with initial config
    result1 = await switcher.execute(cpu_intensive_task, "initial", 3000)
    print(f"Initial config result: {result1}")

    # Switch to multiprocessing-heavy config
    new_config = ConcurrencyConfig(
        default_model=ConcurrencyModel.MULTIPROCESSING,
        max_processes=multiprocessing.cpu_count()
    )

    success = await switcher.switch_config(new_config)
    print(f"Config switch successful: {success}")

    # Execute with new config
    result2 = await switcher.execute(cpu_intensive_task, "switched", 3000)
    print(f"Switched config result: {result2}")

    stats = await switcher.get_stats()
    print(f"Total switches: {stats['switch_count']}")


def create_sample_config() -> ConcurrencyConfig:
    """Create a sample configuration."""
    return ConcurrencyConfig(
        default_model=ConcurrencyModel.HYBRID,
        max_threads=8,
        max_processes=4,
        adaptive_enabled=True,
        cpu_high_threshold=75.0,
        memory_high_threshold=80.0,
        thread_pool_config={"thread_name_prefix": "config-thread"},
        process_pool_config={"mp_context": multiprocessing.get_context('spawn')}
    )


if __name__ == "__main__":
    # Run demonstrations
    logging.basicConfig(level=logging.INFO)

    asyncio.run(demonstrate_adaptive_executor())
    asyncio.run(demonstrate_runtime_switcher())
