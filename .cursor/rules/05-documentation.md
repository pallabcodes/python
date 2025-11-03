# Documentation Standards

## MANDATORY: All classes and functions MUST have docstrings

### Docstring Format

#### Google-Style Docstrings (Required)
```python
class ExampleClass:
    """Short description of the class.
    
    Longer description if needed. This can span multiple lines
    and explain the class purpose, usage, and important details.
    
    Attributes:
        attribute1: Description of attribute1.
        attribute2: Description of attribute2.
    
    Example:
        >>> obj = ExampleClass(param1, param2)
        >>> obj.method()
        result
    """
    
    def method(self, param: str) -> bool:
        """Short description of the method.
        
        Longer description if needed. This explains what the method
        does, how it works, and any important details.
        
        Args:
            param: Description of the parameter.
        
        Returns:
            Description of the return value.
        
        Raises:
            ValueError: Description of when this exception is raised.
            TypeError: Description of when this exception is raised.
        
        Example:
            >>> obj = ExampleClass()
            >>> result = obj.method("example")
            True
        """
        pass
```

### Class Docstrings

#### Required Elements
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
        >>> future = pool.submit(task_function, arg1, arg2)
        >>> result = future.result(timeout=10.0)
        >>> pool.shutdown()
    """
```

### Function Docstrings

#### Required Elements
```python
def process_data(
    items: List[str],
    max_workers: int = 4,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """Process data items concurrently.
    
    This function processes a list of data items using multiple
    worker threads. It validates, transforms, and aggregates results.
    
    Args:
        items: List of data items to process.
        max_workers: Maximum number of worker threads to use.
        timeout: Optional timeout in seconds for processing.
    
    Returns:
        Dictionary containing:
            - 'results': List of processed items.
            - 'count': Number of items processed.
            - 'errors': List of errors encountered.
    
    Raises:
        ValueError: If items list is empty.
        TimeoutError: If processing exceeds timeout.
    
    Example:
        >>> items = ["item1", "item2", "item3"]
        >>> result = process_data(items, max_workers=2)
        >>> print(result['count'])
        3
    """
    pass
```

### Module Docstrings

#### Module-Level Documentation
```python
"""
Thread pool implementation for concurrent task execution.

This module provides a thread pool implementation that manages
worker threads and handles task submission and execution.

Classes:
    ThreadPool: Main thread pool class.
    Task: Task representation class.
    Future: Future result class.

Example:
    >>> from thread_pool import ThreadPool
    >>> pool = ThreadPool(max_workers=4)
    >>> future = pool.submit(lambda x: x * 2, 5)
    >>> result = future.result()
    10
"""
```

### Documentation Best Practices

#### Be Clear and Concise
```python
# ✅ Good
def calculate_total(items: List[int]) -> int:
    """Calculate the sum of all items in the list.
    
    Args:
        items: List of integers to sum.
    
    Returns:
        Sum of all items in the list.
    """
    return sum(items)

# ❌ Bad (too vague)
def calc(items):
    """Calculate stuff."""
    return sum(items)
```

#### Include Examples for Complex Functions
```python
# ✅ Good
def process_nested_data(data: Dict[str, List[Dict]]) -> Dict[str, int]:
    """Process nested data structure and count items.
    
    This function processes a nested dictionary structure where
    each value is a list of dictionaries. It counts items in each
    category.
    
    Args:
        data: Dictionary mapping category names to lists of items.
    
    Returns:
        Dictionary mapping category names to item counts.
    
    Example:
        >>> data = {
        ...     'category1': [{'id': 1}, {'id': 2}],
        ...     'category2': [{'id': 3}]
        ... }
        >>> result = process_nested_data(data)
        >>> print(result)
        {'category1': 2, 'category2': 1}
    """
    pass
```

#### Document Edge Cases
```python
# ✅ Good
def divide(a: float, b: float) -> float:
    """Divide two numbers.
    
    Args:
        a: Dividend.
        b: Divisor.
    
    Returns:
        Result of division.
    
    Raises:
        ZeroDivisionError: If divisor is zero.
    
    Note:
        This function does not handle floating point precision
        issues. For precise calculations, use Decimal.
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
```

### Private Method Documentation

#### Document Private Methods
```python
class Worker:
    def _process_item(self, item: Item) -> Result:
        """Process a single item internally.
        
        This is a private method used internally by the public
        process method. It handles the actual processing logic.
        
        Args:
            item: Item to process.
        
        Returns:
            Processing result.
        
        Note:
            This method should not be called directly. Use the
            public process method instead.
        """
        pass
```

### Type Documentation

#### When Type Hints Are Not Enough
```python
# ✅ Good
def process_data(
    items: List[Dict[str, Union[str, int]]],
    config: Dict[str, Any]
) -> Dict[str, List[Any]]:
    """Process data items with configuration.
    
    Args:
        items: List of dictionaries where each dict contains:
            - 'name': String identifier.
            - 'value': Integer or string value.
        config: Configuration dictionary with:
            - 'max_items': Maximum items to process.
            - 'timeout': Processing timeout in seconds.
    
    Returns:
        Dictionary with:
            - 'results': List of processed items.
            - 'errors': List of error messages.
    """
    pass
```

