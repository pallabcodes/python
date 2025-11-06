# Basic Threading Locking

A production-grade implementation demonstrating thread synchronization fundamentals using locks.

## Overview

This mini-project demonstrates the core concept of thread synchronization by implementing a thread-safe counter. It shows how race conditions occur without proper locking and how explicit locking prevents data corruption under concurrent access.

## Key Concepts Demonstrated

### 1. Race Conditions
- **What**: When multiple threads access shared mutable state simultaneously
- **Impact**: Data corruption, incorrect results, non-deterministic behavior
- **Detection**: Statistical testing with multiple runs

### 2. Thread Synchronization
- **Lock**: `threading.Lock()` for mutual exclusion
- **Critical Sections**: Code that must execute atomically
- **Explicit Locking**: Manual acquire/release vs context managers

### 3. Thread-Safe Design
- **Encapsulation**: Private attributes with public methods
- **Atomic Operations**: Ensuring operations complete entirely or not at all
- **Consistency**: Maintaining invariants under concurrent access

## Files Structure

```
basic_locking/
├── __init__.py          # Module documentation
├── counter.py           # ThreadSafeCounter and UnsafeCounter implementations
├── race_test.py         # Race condition detection and statistical testing
├── benchmark.py         # Performance comparison and analysis
└── README.md           # This documentation
```

## Usage Examples

### Basic Usage
```python
from basic_locking.counter import ThreadSafeCounter

# Create thread-safe counter
counter = ThreadSafeCounter()

# Use from multiple threads safely
counter.increment()
value = counter.get_value()  # Always correct
```

### Race Condition Testing
```python
from basic_locking.race_test import RaceConditionDetector

detector = RaceConditionDetector()
results = detector.test_counter_implementation(
    ThreadSafeCounter,  # or UnsafeCounter
    thread_count=4,
    iterations_per_thread=1000,
    test_runs=10
)

analysis = detector.analyze_results(results)
print(f"Race conditions detected: {analysis['race_condition_detected']}")
```

### Performance Benchmarking
```python
from basic_locking.benchmark import CounterBenchmark

benchmark = CounterBenchmark()
result = benchmark.benchmark_implementation(
    ThreadSafeCounter,
    thread_count=4,
    operations_per_thread=10000
)

print(f"Throughput: {result.throughput:.0f} ops/sec")
print(f"Average latency: {result.avg_latency*1000:.2f} ms/op")
```

## Running the Examples

### Race Condition Detection
```bash
cd examples/threading/basic_locking
python race_test.py
```

### Performance Benchmark
```bash
cd examples/threading/basic_locking
python benchmark.py
```

### Interactive Demo
```bash
cd examples/threading/basic_locking
python counter.py
```

## Key Implementation Details

### ThreadSafeCounter Class
- **Private Attributes**: `_value`, `_lock`, `_logger`
- **Public Interface**: `increment()`, `decrement()`, `get_value()`, `reset()`
- **Lock Usage**: Context manager (`with self._lock:`) for all operations
- **Error Handling**: Validation and meaningful error messages
- **Logging**: Structured logging with context

### Race Condition Detection
- **Statistical Testing**: Multiple runs to detect non-deterministic behavior
- **Thread Coordination**: Proper thread creation, starting, and joining
- **Result Analysis**: Success rates, error patterns, timing analysis
- **Comprehensive Reporting**: Detailed logs and structured results

### Performance Analysis
- **Throughput Measurement**: Operations per second
- **Latency Analysis**: Average time per operation
- **Scaling Analysis**: How performance changes with thread count
- **Comparison**: Thread-safe vs unsafe implementations

## Learning Outcomes

After studying this mini-project, you should understand:

1. **Why synchronization matters**: Race conditions can silently corrupt data
2. **How locks work**: Mutual exclusion prevents concurrent access
3. **Performance impact**: Synchronization has overhead but ensures correctness
4. **Testing concurrency**: Statistical methods to detect race conditions
5. **Production patterns**: Logging, error handling, validation in concurrent code

## Common Pitfalls Avoided

### ❌ Incorrect Lock Usage
```python
# DON'T: Forget to acquire lock
def increment(self):
    self._value += 1  # Race condition!
```

### ❌ Lock Scope Issues
```python
# DON'T: Lock too much or too little
def get_and_increment(self):
    with self._lock:
        value = self._value
    # Gap between read and increment - race condition!
    with self._lock:
        self._value = value + 1
```

### ✅ Correct Implementation
```python
# DO: Keep critical sections minimal but complete
def get_and_increment(self):
    with self._lock:
        value = self._value
        self._value = value + 1
    return value
```

## Next Steps

This mini-project provides the foundation for understanding thread synchronization. The next mini-projects will build on these concepts:

1. **Producer-Consumer Queue**: Using `queue.Queue` for thread communication
2. **ThreadPoolExecutor Wrapper**: Building on concurrent.futures patterns
3. **Pipeline Framework**: Composing multiple synchronized components

## Debuggability Assessment

✅ **5-20 minute rule compliance**:
- Structured logging with correlation context
- Race condition tests provide clear failure indicators
- Performance benchmarks show timing and throughput metrics
- Error messages include relevant state information
- Thread coordination is explicit and logged

This implementation can be debugged within the 5-20 minute target for any concurrency issues.

