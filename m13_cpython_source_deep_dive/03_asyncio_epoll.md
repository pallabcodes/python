# Phase 3: The `asyncio` Event Loop

If the GIL prevents Python from using threads efficiently, how do companies like Instagram and Dropbox handle 1,000,000+ concurrent network connections using Python?

They bypass the GIL entirely using **Non-Blocking I/O and `epoll`**. 

## The Problem: Blocking I/O
When you use `requests.get()` or a standard `socket.recv()`, the Python thread makes a blocking syscall to the OS. The OS puts the thread to sleep. While asleep, that thread *holds the GIL*, meaning no other Python thread can run (unless the C extension explicitly releases the GIL before the syscall, which many do, but context-switching overhead remains).

## The Solution: `asyncio` and the `selectors` module
`asyncio` is not magic. It is simply a Python loop running on a **single OS thread**.

### 1. The Source (Generators as Coroutines)
When you write an `async def` function, Python compiles it into a Generator. When you use `await`, the generator yields control back to the central Event Loop. 
Like Lua Coroutines, this context switch happens entirely in user-space.

### 2. The Kernel (`epoll` / `kqueue`)
When your `async` code awaits a network socket (e.g., `await reader.read(100)`), the Python Event Loop:
1. Sets the file descriptor to `O_NONBLOCK`.
2. Registers the file descriptor with the OS Kernel using `epoll_ctl` (Linux) or `kqueue` (macOS).
3. The event loop then calls `epoll_wait()`. The Kernel returns a list of sockets that have data ready.
4. The event loop finds the specific Python Generator waiting on that socket and resumes it.

### Syscalls & Scale
Because `asyncio` runs on a single thread, **the GIL is completely irrelevant**. There is no thread contention. There is no lock thrashing. 

By using `epoll`, a single Python process can manage 10,000 concurrent sockets using exactly *one* OS thread and *zero* GIL locks, matching the architectural throughput of Node.js and Erlang (though Python's object overhead still makes it slightly slower per request).
