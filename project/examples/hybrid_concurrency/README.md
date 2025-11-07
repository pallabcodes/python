# Hybrid Concurrency Patterns

This module demonstrates **advanced concurrency techniques** that combine multiple concurrency models (asyncio, threading, multiprocessing) to solve complex, real-world problems that cannot be adequately addressed by any single approach.

## 🎯 Why Hybrid Approaches?

While individual concurrency models are powerful, real-world applications often need **customized solutions** that:

- **Combine strengths** of different models (I/O efficiency + CPU parallelism)
- **Adapt to workload characteristics** (route tasks to optimal executors)
- **Handle mixed requirements** (throughput vs latency trade-offs)
- **Scale dynamically** based on system conditions and load
- **Provide QoS guarantees** through intelligent resource allocation

## 📁 Module Structure

### Core Hybrid Patterns
- **`asyncio_threading.py`** - AsyncIO + Threading for I/O + moderate CPU work
- **`asyncio_multiprocessing.py`** - AsyncIO + Multiprocessing for I/O + heavy CPU work
- **`threading_multiprocessing.py`** - Threading + Multiprocessing for complex workflows

### Advanced Components
- **`custom_executor.py`** - Intelligent executor that auto-selects optimal concurrency model
- **`situation_specific.py`** - Specialized processors for throughput vs latency optimization
- **`real_world_hybrids.py`** - Complete hybrid applications (web server, data pipeline, database)

## 🚀 Key Concepts Demonstrated

### 1. Workload-Aware Task Routing
```python
# Tasks automatically routed based on characteristics
cpu_task -> ProcessPoolExecutor  # True parallelism
io_task -> asyncio               # Efficient I/O handling
mixed_task -> ThreadPoolExecutor # Balanced approach
```

### 2. Hybrid Application Architecture
```python
# Web server with intelligent routing
I/O requests -> asyncio (10k+ concurrent connections)
CPU calculations -> process pools (GIL bypass)
Data validation -> thread pools (lightweight)
```

### 3. Quality of Service (QoS)
```python
# Multi-level service guarantees
high_priority -> dedicated resources + low latency
normal_priority -> shared resources + balanced performance
background -> batch processing + high throughput
```

### 4. Adaptive Scaling
```python
# Dynamic resource allocation based on load
high_load -> increase process workers for CPU work
low_load -> optimize for memory efficiency
mixed_load -> balance thread/process allocation
```

## 🎯 Real-World Use Cases

### Web Server with Mixed Workloads
```python
# Handle different request types optimally
API queries -> asyncio (fast I/O)
ML inference -> process pools (CPU intensive)
Data processing -> thread pools (moderate CPU)
File uploads -> asyncio (streaming I/O)
```

### Data Processing Pipeline
```python
# Multi-stage processing with different concurrency needs
Ingestion -> asyncio (handle many concurrent streams)
Validation -> threading (light CPU, many concurrent)
Processing -> multiprocessing (heavy CPU, true parallelism)
Aggregation -> threading (combine results)
Storage -> asyncio (efficient I/O writes)
```

### Database with Analytics
```python
# Handle both fast queries and heavy analytics
Simple queries -> asyncio (low latency I/O)
Complex queries -> threading (cached operations)
Analytics -> multiprocessing (heavy computation)
Reporting -> asyncio (result streaming)
```

## 📊 Performance Characteristics

| Pattern | Throughput | Latency | Scalability | Use Case |
|---------|------------|---------|-------------|----------|
| AsyncIO Only | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | I/O bound applications |
| Threading Only | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Moderate CPU + I/O |
| Multiprocessing Only | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | CPU intensive |
| **AsyncIO + Threading** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Mixed workloads** |
| **AsyncIO + Multiprocessing** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Heavy CPU + I/O** |
| **Threading + Multiprocessing** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Complex pipelines** |

## 🛠 Usage Examples

### Basic Hybrid Pattern
```python
from hybrid_concurrency import AsyncioThreadingHybrid

async with AsyncioThreadingHybrid() as hybrid:
    # I/O task runs in asyncio
    io_result = await hybrid.run_io_task(fetch_data_async)

    # CPU task runs in thread pool
    cpu_result = await hybrid.run_cpu_task(process_data_sync)

    # Run both concurrently
    results = await hybrid.run_mixed_tasks([io_task], [(cpu_task, args)])
```

### Custom Intelligent Executor
```python
from hybrid_concurrency import CustomHybridExecutor

async with CustomHybridExecutor() as executor:
    # Automatically selects optimal concurrency model
    result1 = await executor.execute_task(cpu_intensive_func)
    result2 = await executor.execute_task(io_intensive_func)

    # Force specific model if needed
    result3 = await executor.execute_task(
        mixed_func, force_model=ConcurrencyModel.THREADING
    )
```

### Situation-Specific Processing
```python
from hybrid_concurrency import HighThroughputProcessor, LowLatencyProcessor

# For maximum throughput (batch processing)
async with HighThroughputProcessor() as processor:
    results = await processor.process_batch(cpu_tasks)

# For minimum latency (real-time responses)
async with LowLatencyProcessor() as processor:
    result = await processor.submit_task(urgent_task, priority=Priority.HIGH)
```

## 🎯 When to Use Hybrid Approaches

### ✅ Use Hybrid When:
- **Mixed workloads** (some I/O, some CPU intensive)
- **Performance requirements** vary across tasks
- **Need both throughput AND latency** optimization
- **Complex pipelines** with different processing stages
- **Real-time systems** with QoS requirements
- **Resource constraints** require intelligent allocation

### ❌ Avoid Hybrid When:
- **Simple workloads** (single concurrency model sufficient)
- **Homogeneous tasks** (all similar characteristics)
- **Development complexity** is a major concern
- **Debugging difficulty** would impact maintenance

## 🚀 Running Examples

### Interactive Mode
```bash
cd /Users/picon/Learning/python/project/examples
python -m hybrid_concurrency.run_examples
```

### Command Line Mode
```bash
# Run specific example
python -m hybrid_concurrency.run_examples asyncio_threading
python -m hybrid_concurrency.run_examples custom_executor
python -m hybrid_concurrency.run_examples real_world

# Run all examples
python -m hybrid_concurrency.run_examples all
```

### Programmatic Usage
```python
from hybrid_concurrency import AsyncioThreadingHybrid, CustomHybridExecutor

# Direct import and use
async with AsyncioThreadingHybrid() as hybrid:
    # Use hybrid patterns directly
    pass
```

## 📈 Performance Monitoring

All hybrid components include built-in performance monitoring:

```python
# Get execution statistics
stats = executor.get_performance_stats()
print(f"Tasks/sec: {stats['tasks_per_second']}")
print(f"Model usage: {stats['model_usage']}")

# Monitor system resources
status = executor.get_system_status()
print(f"CPU: {status['cpu_percent']}%, Memory: {status['memory_percent']}%")
```

## 🔧 Customization Guidelines

### Choosing the Right Hybrid Pattern

1. **I/O Heavy + Light CPU** → AsyncIO + Threading
2. **I/O Heavy + Heavy CPU** → AsyncIO + Multiprocessing
3. **Complex Workflows** → Threading + Multiprocessing
4. **Intelligent Routing** → Custom Hybrid Executor
5. **QoS Requirements** → Situation-Specific Processors

### Configuration Best Practices

```python
# Match worker counts to workload
hybrid = AsyncioThreadingHybrid(
    max_threads=2 * multiprocessing.cpu_count(),  # I/O threads
    thread_name_prefix="my-app"
)

# Use resource monitoring for dynamic scaling
if system_load > 0.8:
    # Scale up CPU workers
    pass
elif memory_usage > 0.9:
    # Scale down to prevent OOM
    pass
```

## 🎉 Summary

Hybrid concurrency patterns provide the **flexibility and performance** needed for complex, real-world applications. By intelligently combining different concurrency models, you can:

- **Optimize resource utilization** across mixed workloads
- **Achieve both high throughput AND low latency**
- **Scale dynamically** based on system conditions
- **Provide QoS guarantees** for different task types
- **Build more efficient and responsive applications**

The examples in this module demonstrate practical implementations of these advanced patterns, showing how to build sophisticated concurrency architectures that go beyond single-model approaches.
