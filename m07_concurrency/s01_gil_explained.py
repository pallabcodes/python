"""
Module: The Global Interpreter Lock (GIL) — Reality Check
Target: L5+ Systems Engineers

Key Insights for C/C++ Engineers:
1. The GIL is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes at once.
2. Impact: CPU-bound Python code does NOT scale with multiple threads.
3. IO-bound code: Threads are still useful because the GIL is released during syscalls (socket, file, etc.).
4. Extension modules (C/C++, Rust): Can release the GIL manually for true parallelism.
"""

import time
import threading
from multiprocessing import Process

def cpu_bound_task(n):
    while n > 0:
        n -= 1

COUNT = 50_000_000

# 1. Serial Execution
start = time.time()
cpu_bound_task(COUNT)
cpu_bound_task(COUNT)
print(f"Serial time: {time.time() - start:.2f}s")

# 2. Multi-threaded (The GIL bottleneck)
# Even with 2 threads, it will likely take LONGER than serial due to context switching overhead.
t1 = threading.Thread(target=cpu_bound_task, args=(COUNT,))
t2 = threading.Thread(target=cpu_bound_task, args=(COUNT,))

start = time.time()
t1.start()
t2.start()
t1.join()
t2.join()
print(f"Multi-threaded time (GIL bottleneck): {time.time() - start:.2f}s")

# 3. Multi-processing (True Parallelism)
# Each process has its OWN Interpreter and its OWN GIL.
p1 = Process(target=cpu_bound_task, args=(COUNT,))
p2 = Process(target=cpu_bound_task, args=(COUNT,))

start = time.time()
p1.start()
p2.start()
p1.join()
p2.join()
print(f"Multi-processing time (Parallel): {time.time() - start:.2f}s")

# Future Outlook (Python 3.13+):
# PEP 703: Making the Global Interpreter Lock Optional.
# "Free-threading" builds of Python will allow true parallel threads.

if __name__ == "__main__":
    pass
