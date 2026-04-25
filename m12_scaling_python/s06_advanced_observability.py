"""
Module: Advanced Observability and Tracing

How to debug production memory leaks and profile CPU constraints 
without using heavy tracing (like cProfile or sys.settrace) in production.
"""
import tracemalloc
import time
import sys

def simulate_memory_leak():
    leaky_list = []
    # Simulating a leak by holding references
    for _ in range(50_000):
        leaky_list.append(dict(a=1, b=2, c="some data that takes up space"))
    return leaky_list

def trace_allocations():
    print("=== tracemalloc Memory Profiling ===")
    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()
    
    _ = simulate_memory_leak()
    
    snap2 = tracemalloc.take_snapshot()
    stats = snap2.compare_to(snap1, 'lineno')
    
    print("[Top 3 Memory Allocations/Leaks]")
    for stat in stats[:3]:
        print(stat)
    tracemalloc.stop()

def production_profiling_strategies():
    print("\n=== Production CPU Profiling (L7 Strategy) ===")
    print("1. py-spy: A sampling profiler that works WITHOUT modifying your code.")
    print("   Usage: `py-spy record -o profile.svg --pid 1234`")
    print("2. Flame Graphs: Essential for visualizing 'Hot Paths' in large systems.")
    print("3. OpenTelemetry: Use for distributed tracing in microservices (Discord/Uber scale).")
    print("   Tip: Be careful with 'auto-instrumentation' overhead in Python.")

if __name__ == "__main__":
    trace_allocations()
    production_profiling_strategies()
