"""
Module: Multi-processing for CPU-Bound Tasks

Key Insights for C/C++ Engineers:
1. Each process is a separate OS process with its own memory space.
2. Inter-Process Communication (IPC): Pipes, Queues, Shared Memory.
3. Use 'multiprocessing' to bypass the GIL for heavy calculations.
"""

from multiprocessing import Process, Value, Array, Lock, Pool
import os

# 1. Basic Process
def info(title):
    print(f"{title}")
    print(f"module name: {__name__}")
    print(f"parent process: {os.getppid()}")
    print(f"process id: {os.getpid()}")

# 2. Shared Memory (Low-level primitives)
# Similar to shm_open / mmap in C.
def f(n, a, lock):
    with lock:
        n.value = 3.1415927
        for i in range(len(a)):
            a[i] = -a[i]

# 3. Process Pool (The workhorse)
def square(n):
    return n * n

if __name__ == "__main__":
    # Standard boilerplate for multiprocessing on Windows/macOS (spawn)
    # but also good practice on Linux (fork).
    
    # Shared memory example
    num = Value('d', 0.0)
    arr = Array('i', range(10))
    lock = Lock()

    p = Process(target=f, args=(num, arr, lock))
    p.start()
    p.join()

    print(f"Shared value: {num.value}")
    print(f"Shared array: {arr[:]}")

    # Pool example
    with Pool(processes=4) as pool:
        results = pool.map(square, range(10))
        print(f"Pool results: {results}")
