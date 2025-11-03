# Profiling Tools

Profiling tools and scripts for analyzing performance of concurrent Python code.

## Available Tools

### cProfile Wrapper
- Function-level profiling
- Call graph analysis
- Performance reports

### Line Profiler
- Line-by-line profiling
- Bottleneck identification
- Time per line analysis

### Memory Profiler
- Memory usage tracking
- Memory leak detection
- Peak memory analysis

### Custom Profilers
- Thread profiling
- Process profiling
- Async profiling
- Custom metrics

## Usage Examples

### Profile with cProfile

```python
from utilities.profilers.cprofile_wrapper import profile

@profile
def your_function():
    # Your code here
    pass
```

### Profile with line_profiler

```python
from line_profiler import LineProfiler

profiler = LineProfiler()
profiler.add_function(your_function)
profiler.enable()
your_function()
profiler.disable()
profiler.print_stats()
```

### Profile memory usage

```python
from memory_profiler import profile

@profile
def your_function():
    # Your code here
    pass
```

## Best Practices

- Profile representative workloads
- Run multiple times for consistency
- Profile both CPU and memory
- Compare different implementations
- Document profiling results

