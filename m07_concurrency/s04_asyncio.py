"""
Module: asyncio — Single-threaded Cooperative Multitasking
Target: L5+ Systems Engineers

Key Insights:
1. 'asyncio' is an event loop running in a single thread.
2. It is NOT multi-threading; it is cooperative multitasking via coroutines.
3. Use for high-concurrency IO (web servers, proxies, crawlers).
4. 'TaskGroup' (3.11+) is the modern way to manage concurrent tasks (Structured Concurrency).
"""

import asyncio
import time

async def fetch_data(id: int, delay: int):
    print(f"Task {id}: Fetching data (delay {delay}s)...")
    await asyncio.sleep(delay)  # Yields control back to the event loop
    print(f"Task {id}: Data fetched.")
    return f"Result {id}"

async def main():
    start = time.perf_counter()

    # 1. Running tasks concurrently with gather() (Standard 3.10 way)
    # Equivalent to C++20 coroutines or Javascript's Promise.all
    # In 3.11+, 'asyncio.TaskGroup' is preferred for Structured Concurrency.
    results = await asyncio.gather(
        fetch_data(1, 2),
        fetch_data(2, 1),
        fetch_data(3, 3)
    )

    # All tasks are finished here
    print(f"Results: {results}")

    # 2. Sequential vs Concurrent comparison
    # await fetch_data(4, 1)
    # await fetch_data(5, 1)  # This would take 2 seconds total

    elapsed = time.perf_counter() - start
    print(f"Total time: {elapsed:.2f}s")

if __name__ == "__main__":
    # The entry point for the event loop
    asyncio.run(main())

# Why asyncio?
# Unlike threads which have a stack (approx 1MB - 8MB each), 
# coroutines are extremely lightweight (few KBs), allowing 
# for 100,000+ concurrent connections on a single thread.
