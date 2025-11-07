"""
Hybrid Concurrency Patterns for Python.

This module demonstrates advanced concurrency techniques that combine multiple
concurrency models (asyncio, threading, multiprocessing) to solve complex,
real-world problems that cannot be adequately addressed by any single approach.

Key concepts:
- Hybrid executors combining different concurrency models
- Situation-specific concurrency patterns
- Performance optimization across mixed workloads
- Advanced synchronization in hybrid environments
"""

from .asyncio_threading import AsyncioThreadingHybrid
from .asyncio_multiprocessing import AsyncioMultiprocessingHybrid
from .threading_multiprocessing import ThreadingMultiprocessingHybrid
from .custom_executor import CustomHybridExecutor
from .situation_specific import (
    HighThroughputProcessor,
    LowLatencyProcessor,
    MixedWorkloadProcessor
)
from .real_world_hybrids import (
    WebServerHybrid,
    DataPipelineHybrid,
    DatabaseHybrid
)

__all__ = [
    "AsyncioThreadingHybrid",
    "AsyncioMultiprocessingHybrid",
    "ThreadingMultiprocessingHybrid",
    "CustomHybridExecutor",
    "HighThroughputProcessor",
    "LowLatencyProcessor",
    "MixedWorkloadProcessor",
    "WebServerHybrid",
    "DataPipelineHybrid",
    "DatabaseHybrid"
]
