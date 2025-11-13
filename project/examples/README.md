# Examples

Working examples demonstrating Python concurrency and parallelism concepts.

## Organization

Examples are organized by topic:

- **threading_examples/** - Thread-based concurrency examples
- **multiprocessing_examples/** - Process-based parallelism examples
- **asyncio_examples/** - Async/await programming examples
- **concurrent_futures/** - Executor-based concurrency examples
- **subprocess_examples/** - External process execution examples
- **hybrid_concurrency/** - Advanced hybrid concurrency patterns
- **langchain_examples/** - LangChain framework examples (LLMs, Agents, Chains, RAG)
- **patterns/** - Common concurrency patterns

## Usage

Each example is self-contained and can be run directly:

```bash
cd examples/threading_examples
python basic_threading.py
```

## Example Categories

### Threading Examples
- Basic thread creation
- Thread synchronization
- Thread-safe data structures
- Thread pools
- Producer-consumer patterns

### Multiprocessing Examples
- Basic process creation
- Inter-process communication
- Shared memory
- Process pools
- Parallel processing

### Asyncio Examples
- Basic coroutines
- Event loops
- Tasks and futures
- Async I/O operations
- Async patterns

### Concurrent.futures Examples
- ThreadPoolExecutor usage
- ProcessPoolExecutor usage
- Future management
- Parallel map operations

### Subprocess Examples
- Basic command execution
- Advanced process control
- Inter-process communication
- Error handling and recovery
- Security best practices
- Real-world system administration

### Hybrid Concurrency Examples
- AsyncIO + Threading patterns
- AsyncIO + Multiprocessing patterns
- Threading + Multiprocessing patterns
- Custom intelligent executors
- Situation-specific processors
- Real-world hybrid applications

### Advanced Hybrid Concurrency Examples
- **Advanced Synchronization**: Distributed locks, transactional memory, lock-free structures
- **Distributed Concurrency**: Celery, Dask, Ray integration, Kubernetes-aware concurrency
- **Actor Model**: Message-passing concurrency with supervisors and fault tolerance
- **Reactive Programming**: RxPY streams, backpressure handling, async reactive patterns
- **Custom Primitives**: Priority queues, adaptive rate limiters, smart circuit breakers
- **Performance Profiling**: Real-time monitoring, bottleneck detection, tracing
- **Configuration-Driven**: Runtime switching, adaptive executors, YAML/JSON config
- **Container-Aware**: Docker communication, Kubernetes integration, service discovery
- **ML-Specific**: GPU/TPU concurrency, model inference pipelines, distributed training

### LangChain Examples
- **Core Concepts**: LLMs, Prompts, Output Parsers with production patterns
- **Chains**: Sequential, Router, and Custom Chain implementations
- **Agents**: ReAct, Plan-and-Execute, and Custom Agent patterns
- **Memory**: Conversation Buffer, Summary, and Window Memory management
- **Tools**: Custom Tools and Toolkits for agent integration
- **Retrieval**: RAG pipelines, Vector Stores, Document Loaders
- **LangGraph**: Complex workflow orchestration
- **Evaluation**: Model evaluation and testing patterns
- **Production**: Error handling, Monitoring, Caching for production deployment

### Pattern Examples
- Producer-consumer
- Worker pools
- Pipeline patterns
- Rate limiting
- Circuit breakers

## Learning Path

1. Start with basic examples in each topic
2. Understand the implementation
3. Modify and experiment
4. Compare different approaches
5. Move to exercises for hands-on practice

