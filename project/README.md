# Python Concurrency & Parallelism Learning Project

A comprehensive guide to mastering concurrency and parallelism in Python, designed for SDE-3, DevOps, and Low-Level Systems Engineers.

## Learning Path

This project is organized to take you from fundamentals to advanced concepts:

1. **Core Concepts** (`core/`) - Start here for theoretical understanding
2. **Examples** (`examples/`) - Working implementations of each concept
3. **Exercises** (`exercises/`) - Hands-on practice at different levels
4. **Benchmarks** (`benchmarks/`) - Performance analysis and comparisons
5. **Real World** (`real_world/`) - Practical applications and patterns

## Project Structure

```
project/
├── core/                    # Core concepts and theory
│   ├── threading/          # Threading fundamentals
│   ├── multiprocessing/    # Multiprocessing and IPC
│   ├── asyncio/            # Async/await patterns
│   ├── concurrent_futures/ # Executor patterns
│   ├── gil/                # GIL deep dive
│   └── synchronization/    # Locks, semaphores, barriers
├── examples/               # Working examples
│   ├── threading/
│   ├── multiprocessing/
│   ├── asyncio/
│   ├── concurrent_futures/
│   └── patterns/           # Common patterns
├── exercises/              # Progressive exercises
│   ├── beginner/
│   ├── intermediate/
│   └── advanced/
├── benchmarks/             # Performance analysis
│   ├── profiling/          # Profiling tools
│   └── comparisons/        # Approach comparisons
├── real_world/             # Practical applications
│   ├── web_scraping/
│   ├── api_clients/
│   ├── data_processing/
│   └── distributed_tasks/
├── utilities/              # Helper utilities
│   ├── profilers/
│   ├── decorators/
│   └── helpers/
└── tests/                  # Test suites
    ├── unit/
    └── integration/
```

## Topics Covered

### Threading
- Thread creation and management
- Thread synchronization (locks, RLock, semaphores)
- Thread-safe data structures
- Thread pools and executors
- Common pitfalls and race conditions

### Multiprocessing
- Process creation and management
- Inter-process communication (pipes, queues, shared memory)
- Process pools
- Synchronization across processes
- Process vs thread trade-offs

### Asyncio
- Coroutines and async/await syntax
- Event loops and task scheduling
- Tasks and futures
- Async context managers and generators
- aiohttp and aiofiles patterns

### Concurrent.futures
- ThreadPoolExecutor
- ProcessPoolExecutor
- Future objects and callbacks
- Executor patterns and best practices

### Advanced Topics
- GIL (Global Interpreter Lock) deep dive
- Lock-free programming concepts
- Distributed systems (Celery, Ray, Dask)
- Performance profiling and optimization
- Debugging concurrent code

### Real-world Patterns
- Producer-consumer patterns
- Worker pool patterns
- Pipeline patterns
- Rate limiting
- Circuit breakers
- Backpressure handling

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start with core concepts:
   ```bash
   cd core/threading
   # Read the README.md and explore examples
   ```

3. Run examples:
   ```bash
   cd examples/threading
   python basic_threading.py
   ```

4. Practice with exercises:
   ```bash
   cd exercises/beginner
   # Follow exercise instructions
   ```

## Usage Guidelines

- **Core/**: Read the README.md in each topic folder for theory and concepts
- **Examples/**: Run and modify examples to understand implementations
- **Exercises/**: Complete exercises to reinforce learning
- **Benchmarks/**: Use profiling tools to understand performance characteristics
- **Real World/**: Study practical applications and patterns

## Contributing

This is a learning project. Feel free to:
- Add more examples
- Create additional exercises
- Share performance insights
- Document patterns and best practices

