# memory_locality_demo.py
# Demonstrates the CPU cache penalty of PyObject pointer chasing 
# vs contiguous memory arrays.

import time
import sys
import array

def run_demo():
    N = 10_000_000
    
    print(f"Allocating {N} integers...")
    
    # 1. Standard Python List (Array of Pointers to PyObjects)
    py_list = list(range(N))
    
    # 2. C-Style Array (Contiguous block of 8-byte integers)
    # The 'array' module is part of the standard library and bypasses 
    # PyObject for its internal storage.
    c_array = array.array('q', range(N)) # 'q' is signed 8-byte int
    
    # Analyze Memory Footprint
    list_mem = sys.getsizeof(py_list) + sum(sys.getsizeof(i) for i in py_list[:100]) * (N/100)
    arr_mem = sys.getsizeof(c_array)
    
    print("\n--- Memory Layout ---")
    print(f"Python List (Pointers + PyObjects): ~{list_mem / 1024 / 1024:.2f} MB")
    print(f"Contiguous C Array: ~{arr_mem / 1024 / 1024:.2f} MB")
    
    print("\n--- CPU Cache & Iteration Performance ---")
    
    # Test List (Pointer Chasing = CPU Cache Misses)
    start = time.perf_counter()
    sum_list = sum(py_list)
    end = time.perf_counter()
    list_time = end - start
    print(f"Python List Sum Time: {list_time:.4f} seconds")
    
    # Test Array (Cache Pre-fetching = CPU Cache Hits)
    start = time.perf_counter()
    sum_arr = sum(c_array)
    end = time.perf_counter()
    arr_time = end - start
    print(f"Contiguous Array Sum Time: {arr_time:.4f} seconds")
    
    print(f"\nSpeedup from avoiding pointer-chasing: {list_time / arr_time:.2f}x")

if __name__ == "__main__":
    run_demo()

# SYSTEMS ENGINEERING INSIGHT:
# If you run this script, the math is exactly the same. But the C-array will be 
# significantly faster (and use vastly less RAM).
# Why? Because the CPU can load 64 bytes (8 integers) into its L1 cache in a single 
# memory fetch. With the Python list, every integer requires a separate, unpredictable 
# jump into heap memory, stalling the CPU.
# This is the "Physics" of why Python is slow, and why NumPy is fast.
