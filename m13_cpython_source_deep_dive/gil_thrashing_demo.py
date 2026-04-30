# gil_thrashing_demo.py
# Empirically demonstrates how the GIL causes multithreaded Python to run 
# SLOWER than single-threaded Python on CPU-bound workloads.

import time
import threading

def heavy_math(n):
    """A useless but CPU-intensive loop."""
    count = 0
    for i in range(n):
        count += 1
    return count

def run_single_thread(n):
    print("Running Single Thread...")
    start = time.perf_counter()
    heavy_math(n * 2) # Do 2x the work on 1 thread
    end = time.perf_counter()
    print(f"Single Thread Time: {end - start:.4f} seconds")

def run_multi_thread(n):
    print("\nRunning Two Threads (Same total work)...")
    start = time.perf_counter()
    
    # We split the exact same amount of work across 2 threads
    t1 = threading.Thread(target=heavy_math, args=(n,))
    t2 = threading.Thread(target=heavy_math, args=(n,))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    end = time.perf_counter()
    print(f"Two Threads Time: {end - start:.4f} seconds")

if __name__ == "__main__":
    workload = 50_000_000
    print(f"Total Workload: {workload * 2} iterations\n")
    
    run_single_thread(workload)
    run_multi_thread(workload)

# SYSTEMS ENGINEERING INSIGHT:
# If you run this on a multi-core machine, the "Two Threads" version will almost 
# certainly take 1.2x to 1.5x LONGER than the single thread version.
# 
# Why? The OS Kernel sees two active threads and puts them on two separate CPU cores.
# But because of the Python GIL (a C-level Mutex), only one thread can execute at a time.
# The OS Kernel is forced to constantly pause and wake up the threads as they fight for 
# the lock across different CPU cores. This Kernel-level "Context Thrashing" destroys 
# performance.
