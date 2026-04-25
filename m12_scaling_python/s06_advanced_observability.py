"""
Module: Advanced Observability and Tracing
Target: L5/L7 Engineers

How to debug production memory leaks and profile CPU constraints 
without using heavy tracing (like cProfile or sys.settrace) in production.
"""
import tracemalloc
import time

def simulate_memory_leak():
    leaky_list = []
    # Simulating a leak by holding references
    for _ in range(50_000):
        leaky_list.append(dict(a=1, b=2, c="some data that takes up space"))
    return leaky_list

def trace_allocations():
    print("=== tracemalloc Memory Profiling ===")
    # Start tracing Python memory allocations
    tracemalloc.start()
    
    snap1 = tracemalloc.take_snapshot()
    
    # Run the leaky function
    _ = simulate_memory_leak()
    
    snap2 = tracemalloc.take_snapshot()
    
    # Compare snapshots to find memory leaks
    stats = snap2.compare_to(snap1, 'lineno')
    
    print("[Top 3 Memory Allocations/Leaks]")
    for stat in stats[:3]:
        print(stat)
        
    tracemalloc.stop()

if __name__ == "__main__":
    trace_allocations()
