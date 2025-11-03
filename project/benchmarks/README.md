# Benchmarks

Performance benchmarks and profiling tools for analyzing Python concurrency and parallelism.

## Organization

Benchmarks are organized by type:

- **profiling/** - Profiling tools and scripts
- **comparisons/** - Comparison scripts for different approaches

## Profiling Tools

### cProfile
- Built-in Python profiler
- Function-level profiling
- Call graph analysis

### line_profiler
- Line-by-line profiling
- Identifying bottlenecks
- Memory usage analysis

### memory_profiler
- Memory usage tracking
- Memory leak detection
- Peak memory analysis

### py-spy
- Sampling profiler
- Low-overhead profiling
- Production-safe profiling

## Comparison Scripts

Compare different approaches:
- Threading vs Multiprocessing vs Asyncio
- Synchronization primitives
- Pool sizes and configurations
- Different algorithms and patterns

## Usage

### Profiling a Script

```bash
cd benchmarks/profiling
python profile_script.py your_script.py
```

### Running Comparisons

```bash
cd benchmarks/comparisons
python compare_threading_multiprocessing.py
```

## Best Practices

- Profile before optimizing
- Compare multiple approaches
- Run benchmarks multiple times
- Consider system load
- Document your findings

