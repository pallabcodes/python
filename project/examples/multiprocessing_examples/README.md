# Multiprocessing Examples

A comprehensive collection of Python multiprocessing examples demonstrating various parallel processing concepts and patterns.

## 📚 Overview

This module provides hands-on examples covering:

- **Basic Process Management**: Creating, starting, and managing processes
- **Process Pools**: Using `concurrent.futures.ProcessPoolExecutor` and `multiprocessing.Pool`
- **Shared Memory**: `Value`, `Array`, and `Manager` for inter-process communication
- **Queues & Pipes**: Message passing between processes
- **Synchronization**: Locks, semaphores, events, and condition variables
- **Advanced Patterns**: Map-reduce, pipelines, work stealing, and monitoring
- **Real-world Demo**: Complete data processing pipeline

## 🚀 Quick Start

### Run All Examples
```bash
python run_examples.py
```

### Run Specific Examples
```bash
# Basic process examples
python run_examples.py basic

# Process pool examples
python run_examples.py pool

# Shared memory examples
python run_examples.py shared

# Queues and pipes examples
python run_examples.py queues

# Synchronization examples
python run_examples.py sync

# Advanced patterns examples
python run_examples.py advanced

# Comprehensive demo
python run_examples.py demo
```

### Run Individual Modules
```bash
# Basic processes
python -m basic_processes

# Process pools
python -m process_pool

# Shared memory
python -m shared_memory

# And so on...
```

## 📁 Module Structure

```
multiprocessing/
├── __init__.py              # Package initialization and exports
├── basic_processes.py       # Basic process creation and management
├── process_pool.py          # ProcessPoolExecutor and Pool examples
├── shared_memory.py         # Shared memory and synchronization
├── queues_pipes.py          # Inter-process communication
├── synchronization.py       # Advanced synchronization primitives
├── advanced_patterns.py     # Complex patterns and real-world usage
├── multiprocessing_demo.py  # Comprehensive pipeline demo
├── run_examples.py          # Runner script for all examples
└── README.md               # This file
```

## 🔧 Key Concepts Covered

### Basic Process Management
- Creating and starting processes with `multiprocessing.Process`
- Process termination with `join()` and `terminate()`
- Daemon processes
- Process identification and properties
- Parallel computation basics

### Process Pools
- `concurrent.futures.ProcessPoolExecutor` for high-level parallelism
- `multiprocessing.Pool` for lower-level control
- Asynchronous task submission with callbacks
- Map/reduce operations
- Error handling in pools

### Shared Memory & Synchronization
- `Value` and `Array` for shared memory
- `Lock`, `RLock`, `Semaphore`, `Event`, `Condition`
- Atomic operations
- Reader-writer patterns
- Deadlock prevention

### Communication
- `Queue` for process-safe communication
- `Pipe` for direct process-to-process communication
- Message passing patterns
- Timeout handling
- Producer-consumer patterns

### Advanced Patterns
- Custom worker initialization
- Map-reduce pipelines
- Data processing pipelines
- Work stealing algorithms
- Process monitoring and health checks
- Graceful shutdown patterns
- Resource management and cleanup

## 🎯 Real-World Demo

The comprehensive demo (`multiprocessing_demo.py`) showcases a complete data processing pipeline:

1. **Data Generation**: Creates synthetic datasets
2. **Parallel Processing**: Multi-stage pipeline with queues
3. **Load Balancing**: Distributes work across worker processes
4. **Result Aggregation**: Combines results from multiple workers
5. **Monitoring**: Real-time status tracking
6. **Performance Benchmarking**: Compares sequential vs parallel execution

### Demo Features
- **3-stage processing pipeline**: Cleaning → Analysis → Aggregation
- **Dynamic load balancing**: Work distributed across available cores
- **Progress monitoring**: Real-time status updates
- **Resource management**: Proper cleanup and error handling
- **Performance metrics**: Speedup calculations and benchmarking

## ⚡ Performance Considerations

### When to Use Multiprocessing
- **CPU-bound tasks**: Computation-heavy operations
- **Independent subtasks**: Work that can be parallelized
- **Large datasets**: Processing that benefits from multiple cores
- **I/O bound with computation**: Mixed workloads

### Best Practices
- **Avoid shared state**: Use message passing instead of shared memory when possible
- **Minimize synchronization**: Reduce lock contention
- **Handle exceptions**: Proper error handling in worker processes
- **Resource cleanup**: Always clean up resources properly
- **Platform considerations**: Different start methods for different OSes

### Common Pitfalls
- **Global interpreter lock (GIL)**: Doesn't apply to multiprocessing
- **Pickling limitations**: Objects must be serializable
- **Memory overhead**: Each process has its own memory space
- **Inter-process communication**: More complex than threads

## 🔧 Platform-Specific Notes

### macOS/Linux (fork)
```python
multiprocessing.set_start_method('fork', force=True)
```
- Fast process creation
- Shared memory efficient
- Best for most use cases

### Windows (spawn)
```python
multiprocessing.set_start_method('spawn', force=True)
```
- Slower process creation
- More memory usage
- Required for Windows compatibility

## 📊 Example Output

```
Multiprocessing Basic Examples
====================================
=== Basic Process Creation ===
Created 3 processes
Starting Worker-1...
Starting Worker-2...
Starting Worker-3...
Worker Process-1 (PID: 12345) starting work...
Worker Process-2 (PID: 12346) starting work...
Worker Process-3 (PID: 12347) starting work...
...
Final counter value: 1500
Expected: 1000 + 1000 - 500 = 1500
```

## 🎓 Learning Path

1. **Start with basics**: `basic_processes.py` - Learn process lifecycle
2. **Process pools**: `process_pool.py` - High-level parallelism
3. **Communication**: `queues_pipes.py` - Message passing
4. **Synchronization**: `shared_memory.py` - Shared state management
5. **Advanced patterns**: `advanced_patterns.py` - Complex scenarios
6. **Real demo**: `multiprocessing_demo.py` - Complete application

## 🛠️ Dependencies

- Python 3.6+
- NumPy (optional, for enhanced demo data generation)
- Standard library modules only

## 📖 References

- [Python multiprocessing documentation](https://docs.python.org/3/library/multiprocessing.html)
- [concurrent.futures documentation](https://docs.python.org/3/library/concurrent.futures.html)
- [Multiprocessing best practices](https://pymotw.com/3/multiprocessing/index.html)

## 🤝 Contributing

Feel free to add more examples or improve existing ones! Focus on:
- Clear, well-documented code
- Real-world applicability
- Performance considerations
- Error handling
- Cross-platform compatibility

---

**Happy multiprocessing! 🚀**
