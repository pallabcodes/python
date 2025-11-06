"""
ThreadPoolExecutor wrapper with enhanced features.

Demonstrates:
- Typed executor wrapper
- Task submission and futures management
- Cancellation and timeout handling
- Error aggregation and recovery
- Performance monitoring
"""

# Import all modules to ensure class methods are registered
from .executor_core import TypedThreadPoolExecutor
from .task_result import TaskResult, TaskBatchResult

# Make key classes available at package level
__all__ = ['TypedThreadPoolExecutor', 'TaskResult', 'TaskBatchResult']
