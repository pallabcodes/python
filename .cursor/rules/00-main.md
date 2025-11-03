# Python Concurrency & Parallelism Project - Coding Standards

## Overview
This project follows strict coding standards for SDE-3 level backend engineers, AI engineers, low-level system engineers, and DevOps automation engineers. Code must be crystal clear, easy to understand, and maintainable.

## ⚠️⚠️⚠️ CRITICAL: Google Production Standards ⚠️⚠️⚠️
**BEFORE WRITING ANY CODE, READ: `00-google-production-standards.md`**

### Principal Engineer Review Standards
- **Every line** will be scrutinized by Principal Engineers
- **Production-grade code** is mandatory
- **Debuggability**: Bugs must be detectable in **5 minutes** (standard), **20 minutes** (maximum)
- **Code must be worthy** of production codebase acceptance

## ⚠️ CRITICAL: File Size Enforcement
**BEFORE WRITING ANY CODE, READ: `01-file-size-enforcement.md`**

### Absolute Maximums (NO EXCEPTIONS):
- **File: 200 lines maximum**
- **Function: 50 lines maximum**
- **Class: 200 lines maximum**

If you're about to write code that would exceed these limits, **STOP** and refactor first.

## Rule Files Structure
This directory contains focused rule files:

### ⚠️ CRITICAL: Read These First
- `00-google-production-standards.md` - **READ THIS FIRST** - Google SDE-3 production standards, Principal Engineer review criteria, debuggability requirements (5-20 min), production readiness
- `01-file-size-enforcement.md` - **READ THIS SECOND** - File and function size limits

### Core Standards
- `02-oop-principles.md` - Object-oriented programming requirements
- `03-naming-conventions.md` - Naming standards
- `04-type-hints.md` - Type hinting requirements
- `05-documentation.md` - Documentation standards
- `06-error-handling.md` - Error handling patterns
- `07-concurrency-guidelines.md` - Concurrency-specific guidelines

### Additional Guidelines
- `08-conventional-commits.md` - Commit message standards
- `09-fastapi-guidelines.md` - FastAPI-specific guidelines (when using FastAPI)

## Core Principles

### 1. Object-Oriented Programming (OOP)
- **MANDATORY**: All code must follow proper OOP principles
- Use classes for grouping related functionality
- Prefer composition over inheritance
- Implement proper encapsulation (private/public attributes)
- Use abstract base classes for interfaces
- Follow SOLID principles strictly:
  - **S**ingle Responsibility Principle: Each class has one reason to change
  - **O**pen/Closed Principle: Open for extension, closed for modification
  - **L**iskov Substitution Principle: Subtypes must be substitutable
  - **I**nterface Segregation Principle: No client should depend on unused methods
  - **D**ependency Inversion Principle: Depend on abstractions, not concretions

### 2. File Size Limits
- **MAXIMUM**: 150-200 lines per file
- If a file exceeds this limit, split into multiple files
- Each file should have a single, clear purpose
- Use modules to organize related functionality

### 3. Function Size Limits
- **MAXIMUM**: 50 lines per function
- If a function exceeds this limit, refactor into smaller functions
- Functions should do one thing well
- Extract complex logic into helper methods

### 4. Code Readability
- Code must be self-documenting
- Use meaningful names for classes, functions, and variables
- Avoid abbreviations unless they are well-known (e.g., `id`, `http`, `api`)
- Use descriptive variable names that explain intent

### 5. Class Structure
- Keep classes focused and cohesive
- Maximum 5-7 methods per class (excluding getters/setters)
- Use properties instead of getters/setters when appropriate
- Group related methods together
- Use type hints for all method signatures

## Code Organization

### File Structure Template
```python
"""
Module docstring explaining the module's purpose.
"""
from typing import Optional, List, Dict, Any
import logging

# Constants
MAX_SIZE = 100
DEFAULT_TIMEOUT = 30

# Type aliases
Result = Dict[str, Any]

# Classes
class ClassName:
    """Class docstring explaining purpose and usage."""
    
    def __init__(self, param: str):
        """Initialize with clear parameter description."""
        self._private_attr = param
        self._logger = logging.getLogger(__name__)
    
    def public_method(self, arg: int) -> bool:
        """Method docstring with clear description."""
        # Implementation
        pass

# Helper functions (if needed)
def helper_function(data: str) -> Optional[str]:
    """Helper function docstring."""
    pass
```

### Class Design Patterns
- Use factory pattern for object creation
- Use strategy pattern for algorithm selection
- Use observer pattern for event handling
- Use singleton pattern sparingly (only when truly needed)
- Use dependency injection for testability

## Naming Conventions

### Classes
- Use PascalCase: `ThreadPool`, `ProcessManager`, `AsyncExecutor`
- Be descriptive: `WorkerPool` not `Pool`, `ThreadSynchronizer` not `Sync`

### Functions and Methods
- Use snake_case: `create_thread`, `process_data`, `handle_request`
- Use verbs: `start`, `stop`, `process`, `validate`, `execute`
- Be specific: `calculate_total_time` not `calc`, `process_user_data` not `proc`

### Variables
- Use snake_case: `thread_count`, `max_workers`, `result_data`
- Avoid single letters except for loop counters: `i`, `j`, `k` in loops only
- Use descriptive names: `worker_thread` not `wt`, `execution_time` not `et`

### Private Attributes
- Prefix with single underscore: `_private_attr`, `_internal_state`
- Use double underscore sparingly (name mangling only when necessary)

### Constants
- Use UPPER_SNAKE_CASE: `MAX_THREADS`, `DEFAULT_TIMEOUT`, `API_BASE_URL`

## Type Hints

### Mandatory Type Hints
- All function signatures must have type hints
- All class attributes should have type hints
- Use `typing` module for complex types
- Use `Optional[T]` for nullable types
- Use `Union[T1, T2]` for multiple types
- Use `List[T]`, `Dict[K, V]`, `Tuple[T, ...]` for collections

### Examples
```python
def process_data(
    items: List[str],
    max_workers: int = 4,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """Process data with proper type hints."""
    pass

class WorkerPool:
    def __init__(self, max_workers: int, timeout: float = 30.0):
        self._max_workers: int = max_workers
        self._timeout: float = timeout
        self._workers: List[Worker] = []
```

## Documentation Standards

### Docstrings
- Use Google-style docstrings for all classes and functions
- Include parameter descriptions
- Include return value descriptions
- Include exception descriptions
- Include usage examples for complex functions

### Example Docstring
```python
class ThreadPool:
    """Thread pool for managing concurrent thread execution.
    
    This class provides a pool of worker threads that can execute
    tasks concurrently. It automatically manages thread lifecycle
    and provides synchronization mechanisms.
    
    Attributes:
        max_workers: Maximum number of worker threads in the pool.
        timeout: Default timeout for task execution in seconds.
    
    Example:
        >>> pool = ThreadPool(max_workers=4)
        >>> pool.submit(task_function, arg1, arg2)
        >>> pool.shutdown()
    """
    
    def submit(self, func: Callable, *args: Any, **kwargs: Any) -> Future:
        """Submit a task to the thread pool.
        
        Args:
            func: Callable function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        
        Returns:
            Future object representing the task result.
        
        Raises:
            RuntimeError: If pool is already shut down.
            ValueError: If function is not callable.
        """
        pass
```

## Error Handling

### Exception Handling
- Use specific exception types, not bare `except:`
- Create custom exceptions when needed
- Include context in error messages
- Log errors appropriately
- Use exception chaining when appropriate

### Example
```python
class TaskExecutionError(Exception):
    """Raised when task execution fails."""
    pass

def execute_task(self, task: Task) -> Result:
    try:
        return self._run_task(task)
    except TimeoutError as e:
        self._logger.error(f"Task {task.id} timed out: {e}")
        raise TaskExecutionError(f"Task {task.id} execution failed") from e
    except Exception as e:
        self._logger.error(f"Unexpected error in task {task.id}: {e}")
        raise TaskExecutionError(f"Task {task.id} execution failed") from e
```

## Logging

### Logging Standards
- Use module-level logger: `self._logger = logging.getLogger(__name__)`
- Use appropriate log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context in log messages
- Use structured logging when possible

### Example
```python
class Worker:
    def __init__(self, worker_id: str):
        self._worker_id = worker_id
        self._logger = logging.getLogger(__name__)
    
    def process(self, item: Any) -> Result:
        self._logger.info(f"Worker {self._worker_id} processing item")
        try:
            result = self._do_work(item)
            self._logger.debug(f"Worker {self._worker_id} completed successfully")
            return result
        except Exception as e:
            self._logger.error(f"Worker {self._worker_id} failed: {e}", exc_info=True)
            raise
```

## Testing Standards

### Test Organization
- One test file per module
- Test classes should mirror production classes
- Use descriptive test names: `test_thread_pool_submit_task_success`
- Follow Arrange-Act-Assert pattern
- Use fixtures for common setup

### Example
```python
class TestThreadPool:
    """Tests for ThreadPool class."""
    
    def test_submit_task_success(self):
        """Test successful task submission."""
        # Arrange
        pool = ThreadPool(max_workers=2)
        task = MockTask()
        
        # Act
        future = pool.submit(task.execute)
        result = future.result(timeout=5.0)
        
        # Assert
        assert result is not None
        assert task.executed is True
```

## Concurrency-Specific Guidelines

### Thread Safety
- Document thread-safety guarantees
- Use locks explicitly when needed
- Prefer thread-safe data structures from `queue` module
- Avoid shared mutable state when possible

### Resource Management
- Use context managers for resource cleanup
- Implement `__enter__` and `__exit__` for custom resources
- Always close resources properly
- Use `with` statements for resource management

### Example
```python
class ThreadPool:
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup."""
        self.shutdown(wait=True)
        return False
```

## Code Review Checklist

Before submitting code, ensure:
- [ ] All classes follow OOP principles
- [ ] File size is under 200 lines
- [ ] All functions are under 50 lines
- [ ] Type hints are present for all functions
- [ ] Docstrings are complete and accurate
- [ ] Code is self-documenting
- [ ] Error handling is appropriate
- [ ] Logging is properly implemented
- [ ] Thread safety is documented
- [ ] Resource management is correct
- [ ] Tests are written and passing
- [ ] No hardcoded values (use constants)
- [ ] No magic numbers (use named constants)
- [ ] No code duplication (use functions/classes)

## Refactoring Guidelines

### When to Refactor
- File exceeds 200 lines → Split into multiple files
- Function exceeds 50 lines → Extract into smaller functions
- Class has too many methods → Split into multiple classes
- Code duplication → Extract common functionality
- Complex conditional logic → Extract into methods
- Long parameter lists → Use dataclasses or config objects

### Refactoring Patterns
- Extract Method: Long method → Multiple smaller methods
- Extract Class: Large class → Multiple focused classes
- Extract Module: Large file → Multiple related files
- Replace Magic Number: Hardcoded value → Named constant
- Introduce Parameter Object: Long parameter list → Config object

## Examples of Good vs Bad Code

### Bad Example (Too Long, Not OOP)
```python
def process_data(data):
    results = []
    for item in data:
        if item['status'] == 'pending':
            item['processed'] = True
            item['timestamp'] = time.time()
            if item['priority'] > 5:
                item['priority'] = item['priority'] * 2
            results.append(item)
    return results
```

### Good Example (OOP, Small Functions)
```python
class DataProcessor:
    """Processes data items with proper validation."""
    
    HIGH_PRIORITY_THRESHOLD = 5
    PRIORITY_MULTIPLIER = 2
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process list of data items."""
        results = []
        for item in data:
            if self._is_pending(item):
                processed_item = self._process_item(item)
                results.append(processed_item)
        return results
    
    def _is_pending(self, item: Dict[str, Any]) -> bool:
        """Check if item is pending."""
        return item.get('status') == 'pending'
    
    def _process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single item."""
        item['processed'] = True
        item['timestamp'] = time.time()
        item['priority'] = self._adjust_priority(item)
        return item
    
    def _adjust_priority(self, item: Dict[str, Any]) -> int:
        """Adjust priority for high-priority items."""
        priority = item.get('priority', 0)
        if priority > self.HIGH_PRIORITY_THRESHOLD:
            return priority * self.PRIORITY_MULTIPLIER
        return priority
```

## Final Notes

- **Code is read more than it's written** - Prioritize readability
- **Small is beautiful** - Smaller functions and classes are easier to understand
- **OOP is mandatory** - Always use proper object-oriented design
- **Documentation is code** - Docstrings are as important as implementation
- **Testability matters** - Code should be easy to test
- **Maintainability is key** - Future you will thank present you

Remember: As an SDE-3 engineer, you're writing code that will be maintained by others. Make it crystal clear, easy to understand, and easy to debug.

