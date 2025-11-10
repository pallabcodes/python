# Producer-Consumer Queue

A production-grade implementation of the producer-consumer pattern using Python's threading and queue modules.

## Overview

This mini-project demonstrates the classic producer-consumer concurrency pattern. It shows how to coordinate multiple producer and consumer threads using `queue.Queue`, implement graceful shutdown with DONE sentinels, and handle backpressure with bounded queues.

## Key Concepts Demonstrated

### 1. Producer-Consumer Pattern
- **Producers**: Generate and enqueue items
- **Consumers**: Dequeue and process items
- **Queue**: Thread-safe communication channel
- **Coordination**: Thread lifecycle management

### 2. DONE Sentinels
- **Graceful Shutdown**: Sentinel objects to signal completion
- **Multiple Consumers**: One sentinel per consumer
- **Clean Termination**: No hanging threads or resource leaks

### 3. Backpressure Handling
- **Bounded Queues**: `Queue(maxsize=N)` limits queue growth
- **Natural Backpressure**: Producers block when queue is full
- **Flow Control**: Prevents memory exhaustion

### 4. Thread Coordination
- **Lifecycle Management**: Proper start/join patterns
- **Daemon Threads**: Background thread cleanup
- **Timeout Handling**: Prevent infinite waits

## Files Structure

```
producer_consumer/
├── __init__.py           # Module documentation
├── queue.py              # Core queue and sentinel classes
├── producer_thread.py    # Producer thread implementation
├── consumer_thread.py    # Consumer thread implementation
├── queue_core.py         # Core ProducerConsumerQueue class
├── queue_lifecycle.py    # Lifecycle management methods
├── queue_monitor.py      # Monitoring and statistics
├── queue_manager.py      # Queue management utilities
├── context.py            # Context managers and factories
├── demo_basic.py         # Basic demonstrations
├── demo_advanced.py      # Advanced demonstrations
├── test_basic.py         # Basic unit tests
├── test_stress.py        # Stress and performance tests
└── README.md            # This documentation
```

## Usage Examples

### Basic Usage
```python
from producer_consumer import ProducerConsumerQueue

# Create unbounded queue
queue = ProducerConsumerQueue()

# Add producer
def number_producer():
    for i in range(10):
        yield i

queue.add_producer(lambda: next(number_producer().__iter__(), None))

# Add consumer
def number_consumer(item):
    print(f"Processed: {item}")

queue.add_consumer(number_consumer)

# Start and wait
queue.start()
queue.wait_for_completion()
```

### Bounded Queue with Backpressure
```python
# Create bounded queue (backpressure when full)
queue = ProducerConsumerQueue(maxsize=5)

# Fast producer, slow consumer = backpressure
queue.add_producer(fast_producer_func)
queue.add_consumer(slow_consumer_func)

queue.start()
queue.wait_for_completion()
```

### Context Manager (Automatic Cleanup)
```python
from producer_consumer import create_producer_consumer_context

with create_producer_consumer_context(maxsize=10) as queue:
    queue.add_producer(producer_func)
    queue.add_consumer(consumer_func)
    queue.start()
    queue.wait_for_completion()
# Automatic shutdown and cleanup
```

### Multiple Producers and Consumers
```python
queue = ProducerConsumerQueue()

# Multiple producers generating different data
queue.add_producer(text_producer, name="TextProducer")
queue.add_producer(number_producer, name="NumberProducer")

# Multiple consumers processing in parallel
queue.add_consumer(text_consumer, name="TextConsumer1")
queue.add_consumer(text_consumer, name="TextConsumer2")
queue.add_consumer(number_consumer, name="NumberConsumer")

queue.start()
queue.wait_for_completion()
```

## Running the Examples

### Demonstrations
```bash
cd examples/threading/producer_consumer
python demo_basic.py
python demo_advanced.py
```

This runs several demonstrations:
- Basic producer-consumer patterns
- Multiple producers/consumers coordination
- Backpressure handling with bounded queues
- Graceful shutdown mechanisms
- Error handling and recovery

### Tests
```bash
cd examples/threading/producer_consumer
python -m pytest test_basic.py test_stress.py -v
```

## Key Implementation Details

### ProducerConsumerQueue Class
- **Thread Management**: Proper thread lifecycle with start/join
- **DONE Sentinels**: Graceful shutdown signaling
- **Bounded Queues**: Backpressure via `Queue(maxsize)`
- **Statistics**: Real-time monitoring of queue state
- **Logging**: Structured logging with correlation context

### ProducerThread
- **Item Generation**: Calls producer function to generate items
- **Queue Insertion**: Handles full queue blocking/retry
- **Graceful Shutdown**: Responds to shutdown events
- **Error Handling**: Logs errors without crashing

### ConsumerThread
- **Item Processing**: Dequeues and processes items
- **DONE Detection**: Recognizes shutdown sentinels
- **Task Completion**: Calls `task_done()` for queue coordination
- **Timeout Handling**: Uses timeouts to prevent blocking

### Thread Safety
- **Queue Operations**: Uses thread-safe `queue.Queue`
- **Shutdown Coordination**: Uses `threading.Event` for signaling
- **Statistics Access**: Thread-safe stats reporting

## Performance Characteristics

### Throughput Scaling
- **Single Producer/Consumer**: Baseline performance
- **Multiple Consumers**: Scales nearly linearly
- **Bounded Queues**: May reduce throughput due to blocking
- **Backpressure**: Prevents memory issues but may slow producers

### Memory Usage
- **Unbounded Queues**: Risk of memory exhaustion
- **Bounded Queues**: Predictable memory usage
- **Thread Overhead**: Each thread uses ~8MB stack space

### Latency
- **Queue Operations**: Microsecond-level enqueue/dequeue
- **Context Switching**: Millisecond-level thread switching
- **Lock Contention**: May increase latency with many threads

## Error Handling Patterns

### Producer Errors
```python
# Producer handles its own errors
def robust_producer():
    try:
        item = generate_item()
        return item
    except Exception as e:
        logger.error(f"Producer error: {e}")
        return None  # Signal completion
```

### Consumer Errors
```python
# Consumer errors are logged but don't crash the system
def robust_consumer(item):
    try:
        process_item(item)
    except Exception as e:
        logger.error(f"Consumer error processing {item}: {e}")
        # Continue processing other items
```

### Queue Errors
- **Full Queue**: Producers block/retry automatically
- **Empty Queue**: Consumers wait with timeout
- **Shutdown**: Graceful termination with DONE sentinels

## Common Patterns and Variations

### Work Distribution
```python
# One producer, multiple consumers (fan-out)
queue.add_producer(single_producer)
queue.add_consumer(worker_consumer)  # Multiple instances
queue.add_consumer(worker_consumer)
```

### Result Aggregation
```python
# Multiple producers, one consumer (fan-in)
queue.add_producer(producer1)
queue.add_producer(producer2)
queue.add_consumer(result_aggregator)
```

### Pipeline Stages
```python
# Multi-stage pipeline
stage1_queue.add_producer(raw_data_producer)
stage1_queue.add_consumer(stage1_processor)

stage2_queue.add_producer(lambda: stage1_queue.get())
stage2_queue.add_consumer(stage2_processor)
```

## Debuggability Assessment

✅ **5-20 minute rule compliance**:
- Structured logging with thread names and correlation
- Queue statistics for monitoring state
- Error context with full stack traces
- Thread lifecycle logging
- Timeout handling prevents hanging
- DONE sentinel tracking

## Next Steps

This mini-project provides the foundation for more complex patterns:

1. **Pipeline Framework**: Multi-stage processing pipelines
2. **YAML Configuration**: Declarative pipeline setup
3. **HTTP Fetcher**: Threaded HTTP client with retries
4. **Datastore Writer**: Pluggable data persistence
5. **Observability**: Metrics and tracing
6. **Resilience**: Circuit breakers and bulkheads

## Real-World Applications

- **Web Scraping**: Producer generates URLs, consumers fetch/process
- **Data Processing**: Producer reads files, consumers transform data
- **API Processing**: Producer receives requests, consumers handle them
- **Log Processing**: Producer tails logs, consumers parse/index
- **Task Distribution**: Producer creates tasks, consumers execute them

## Production Considerations

### Scaling
- Monitor queue sizes and thread utilization
- Adjust producer/consumer ratios based on workload
- Use bounded queues to prevent memory issues
- Consider process-based alternatives for CPU-bound work

### Monitoring
- Track queue depth, processing rates, error rates
- Monitor thread health and resource usage
- Alert on queue full/empty conditions
- Log processing latencies and throughput

### Reliability
- Implement proper error handling and recovery
- Use timeouts to prevent hanging operations
- Implement graceful degradation under load
- Test failure scenarios thoroughly

