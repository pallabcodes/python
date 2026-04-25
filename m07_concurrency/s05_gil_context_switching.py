"""
Module: GIL Mechanics & Thread Context Switching

Demonstrates sys.setswitchinterval, OS-level thread preemption overhead, 
and bytecode atomicity.
"""
import sys
import threading
import time
import dis

def thread_safe_vs_unsafe():
    print("=== Bytecode Atomicity ===")
    
    def non_atomic_add(a):
        a += 1
    
    print("Bytecode for `a += 1` (Notice INPLACE_ADD is not atomic):")
    dis.dis(non_atomic_add)

    def atomic_append(lst):
        lst.append(1)
        
    print("\nBytecode for `lst.append(1)` (C function call, thread-safe via GIL):")
    dis.dis(atomic_append)

def gil_switch_interval_demo():
    print("\n=== GIL Switch Interval ===")
    print(f"Current GIL switch interval: {sys.getswitchinterval()} seconds")
    print("A smaller interval = fairer but more context switching overhead.")
    print("A larger interval = better for CPU-heavy tasks but worse latency for I/O tasks.")
    
if __name__ == "__main__":
    thread_safe_vs_unsafe()
    gil_switch_interval_demo()
