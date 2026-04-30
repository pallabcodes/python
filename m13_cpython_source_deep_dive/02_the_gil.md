# Phase 2: The Global Interpreter Lock (GIL)

If you spawn 4 Python threads on a 4-core CPU to do heavy math, it will often take *longer* than doing it on 1 thread. This is the infamy of the CPython GIL. But *why* exactly does it exist, and how does it cause this?

## The Problem: Garbage Collection Race Conditions
Recall from Phase 1 that every `PyObject` has an `ob_refcnt` (Reference Count). 
When you assign a variable `x = y`, CPython increments `y`'s reference count. When `x` goes out of scope, it decrements it. If it hits zero, the memory is freed.

If Thread A and Thread B simultaneously try to decrement the same `PyObject`, a race condition occurs. The object might not be freed (memory leak), or freed twice (segfault).

## The Origin of the GIL
To solve this, Guido van Rossum made a simple architectural choice in the 1990s: Instead of putting a lock on *every single object* (which would be slow and prone to deadlocks), he put **one giant lock around the entire CPython interpreter.**
The C source code (`ceval.c`) shows that before any C thread can execute a single Python bytecode instruction, it must acquire this lock.

## Syscalls & Kernel: Thread Thrashing
The GIL is literally implemented using an OS Mutex (like `pthread_mutex_t` on Linux). 

Here is what happens at the Kernel level when you run CPU-bound Python threads:
1. Thread A acquires the GIL and starts running Python bytecode on Core 1.
2. Thread B wakes up on Core 2, tries to acquire the GIL, and immediately goes to sleep (blocking syscall).
3. Every 5 milliseconds (or after a certain number of bytecodes), CPython forces Thread A to voluntarily drop the GIL.
4. The Linux Kernel wakes up Thread B. Thread B acquires the GIL.
5. Thread A immediately tries to re-acquire the GIL and goes to sleep.

**The "Convoy Effect":**
The OS Kernel is constantly putting threads to sleep and waking them up thousands of times a second. This is called **Context Switching**. It flushes the CPU caches and wastes enormous amounts of CPU cycles simply managing the locks, resulting in the app running *slower* than a single thread.

### The Systems Engineering Solution
If you want to use all 32 cores, you have three options:
1. **Multiprocessing:** Span completely separate OS processes (with separate heaps and separate GILs) using IPC (Inter-Process Communication) to share data.
2. **C Extensions:** Libraries like `numpy` or Rust `PyO3` can explicitly drop the GIL (`Py_BEGIN_ALLOW_THREADS`) when they do heavy math in C, allowing other Python threads to run concurrently in the background.
3. **Asyncio:** If the workload is Network I/O (not CPU math), use `epoll` instead of native OS threads.
