# Asyncio Examples

A comprehensive collection of asyncio examples demonstrating asynchronous programming concepts in Python.

## 📚 Overview

This module provides hands-on examples covering:

- **Basic Asyncio**: Coroutines, event loops, tasks, futures
- **Context Managers**: Async resource management and cleanup
- **Generators**: Async iteration and streaming
- **Concurrency Patterns**: Producer-consumer, pipelines, pub-sub
- **I/O Operations**: File and network operations
- **Synchronization**: Locks, semaphores, events, conditions
- **Task Management**: Creation, cancellation, groups
- **Web Applications**: HTTP servers and clients
- **Real-world Demo**: Complete async application

## 🚀 Quick Start

### Run All Examples
```bash
python run_examples.py
```

### Run Specific Examples
```bash
# Basic coroutines and tasks
python run_examples.py basic

# Async context managers
python run_examples.py context

# Async generators and iteration
python run_examples.py generators

# Concurrency patterns
python run_examples.py patterns

# Async I/O operations
python run_examples.py io

# Synchronization primitives
python run_examples.py primitives

# Task management
python run_examples.py tasks

# Web applications (requires aiohttp)
python run_examples.py web

# Comprehensive demo
python run_examples.py demo

# Performance benchmark
python run_examples.py benchmark
```

### Run Individual Modules
```bash
# Basic asyncio
python -m basic_asyncio

# Async context managers
python -m async_context_managers

# And so on...
```

## 📁 Module Structure

```
asyncio/
├── __init__.py                   # Package initialization and exports
├── basic_asyncio.py             # Coroutines, tasks, event loops
├── async_context_managers.py    # Resource management with async with
├── async_generators.py          # Async iteration and streaming
├── concurrency_patterns.py      # Advanced concurrent patterns
├── async_io.py                  # File and network I/O
├── async_primitives.py          # Locks, semaphores, events
├── task_management.py           # Task lifecycle and groups
├── web_asyncio.py               # HTTP servers and clients
├── asyncio_demo.py              # Complete application demo
├── run_examples.py              # Runner script for all examples
└── README.md                   # This file
```

## 🔧 Key Concepts Covered

### Basic Asyncio
- `async def` for defining coroutines
- `await` for calling async functions
- `asyncio.create_task()` for concurrent execution
- `asyncio.gather()` and `asyncio.wait()` for coordination
- Exception handling in async code

### Context Managers
- `async with` syntax for resource management
- `__aenter__` and `__aexit__` methods
- Automatic cleanup and exception handling
- Stacking multiple context managers

### Generators
- `async def` with `yield` for async generators
- `async for` loops for iteration
- `aiter()` and `anext()` functions
- Streaming data processing

### Concurrency Patterns
- Producer-consumer with queues
- Data processing pipelines
- Publish-subscribe messaging
- Circuit breaker for fault tolerance
- Rate limiting and request batching

### I/O Operations
- Async file operations
- TCP/UDP network operations
- HTTP client/server with aiohttp
- Concurrent I/O patterns
- Error handling in async I/O

### Synchronization
- `asyncio.Lock` for mutual exclusion
- `asyncio.Semaphore` for resource limiting
- `asyncio.Event` for coordination
- `asyncio.Condition` for complex sync
- Reader-writer patterns

### Task Management
- Task creation and lifecycle
- Cancellation and timeouts
- Exception handling
- Monitoring and metrics
- Resource cleanup

## 🎯 Real-World Demo

The comprehensive demo (`asyncio_demo.py`) showcases:

### Features
- **REST API Server**: Full HTTP API with endpoints for CRUD operations
- **Background Processing**: Continuous data processing pipeline
- **Monitoring**: Real-time metrics and status tracking
- **Concurrent Operations**: Multiple tasks running simultaneously
- **Graceful Shutdown**: Proper cleanup on termination
- **Performance Benchmarking**: Asyncio vs sequential execution

### API Endpoints
- `GET /` - API information
- `GET /api/items` - List items with filtering/pagination
- `GET /api/items/{id}` - Get single item
- `POST /api/items` - Create new item
- `GET /api/stats` - Application statistics
- `POST /api/batch` - Process multiple items concurrently

### Usage
```bash
# Start the demo
python run_examples.py demo

# API available at http://localhost:8080
curl http://localhost:8080/api/stats
```

## ⚡ Performance Insights

### Benchmark Results
```
CPU-bound tasks: Limited benefit from asyncio (GIL limitation)
I/O-bound tasks: Significant speedup (2-10x improvement)
```

### When to Use Asyncio
- **I/O-bound operations**: Network requests, file I/O, database queries
- **Concurrent connections**: Web servers, chat applications, APIs
- **Streaming data**: Real-time data processing, WebSockets
- **Resource efficiency**: Handling many concurrent operations

### Best Practices
- Use asyncio for I/O concurrency, threading/multiprocessing for CPU parallelism
- Avoid blocking operations in async code
- Handle exceptions properly in async contexts
- Use appropriate synchronization primitives
- Implement proper resource cleanup

## 🔧 Platform Notes

### Event Loop Policies
```python
# Default selector event loop
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# Windows-specific (if needed)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Debugging
```python
# Enable debug mode
asyncio.get_event_loop().set_debug(True)

# Log slow tasks
asyncio.get_event_loop().slow_callback_duration = 0.1
```

## 📊 Example Output

```
=== Basic Coroutine Execution ===
Coroutine A starting...
Coroutine A completed after 0.5s
Coroutine B starting...
Coroutine B completed after 0.3s

=== Concurrent Execution ===
Task A: starting work
Task B: starting work
Task C: starting work
Task A: completed
Task B: completed
Task C: completed
Concurrent time: 0.8s (was 1.1s sequential)
```

## 🛠️ Dependencies

- **Python 3.7+** (for asyncio features)
- **aiohttp** (optional, for web examples): `pip install aiohttp`
- Standard library modules only otherwise

## 📖 References

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [aiohttp documentation](https://docs.aiohttp.org/)
- [Asyncio best practices](https://asyncio.readthedocs.io/)

## 🎓 Learning Path

1. **Start here**: `basic_asyncio.py` - Learn async/await syntax
2. **Resource management**: `async_context_managers.py` - Cleanup patterns
3. **Streaming**: `async_generators.py` - Async iteration
4. **Synchronization**: `async_primitives.py` - Locks and coordination
5. **Patterns**: `concurrency_patterns.py` - Real-world architectures
6. **I/O**: `async_io.py` - Network and file operations
7. **Tasks**: `task_management.py` - Advanced task control
8. **Web**: `web_asyncio.py` - HTTP servers and clients
9. **Demo**: `asyncio_demo.py` - Complete application

## 🤝 Contributing

Add more examples following the established patterns:
- Clear, well-documented async code
- Error handling and edge cases
- Real-world applicability
- Performance considerations
- Cross-platform compatibility

---

**Happy async programming! 🚀**
