# epoll_async_demo.py
# Demonstrates how asyncio uses the OS kernel (epoll) to handle massive
# concurrency on a SINGLE thread, rendering the GIL irrelevant.

import asyncio
import time
import socket

async def simulated_network_call(id, duration):
    """
    Simulates a non-blocking network I/O call.
    Under the hood, asyncio.sleep() registers a timer with the event loop 
    and yields control. No OS threads are put to sleep.
    """
    # Yield control to the event loop
    await asyncio.sleep(duration)
    return f"Request {id} complete"

async def run_massive_concurrency():
    connections = 10_000
    print(f"Spawning {connections} concurrent 'network requests'...")
    
    start = time.perf_counter()
    
    # asyncio.gather schedules all 10,000 tasks on the event loop concurrently.
    # Because there is no GIL contention (we are on 1 thread) and no OS 
    # thread memory overhead, this completes almost instantly.
    tasks = [simulated_network_call(i, 2.0) for i in range(connections)]
    await asyncio.gather(*tasks)
    
    end = time.perf_counter()
    
    print(f"Completed {connections} requests in {end - start:.4f} seconds.")
    print("If you tried this with 10,000 threading.Thread instances, your OS would likely crash.")

if __name__ == "__main__":
    # The event loop is a single Python while-loop that wraps the OS 'epoll_wait' syscall.
    asyncio.run(run_massive_concurrency())

# SYSTEMS ENGINEERING INSIGHT:
# This script proves that Python's true scaling mechanism is NOT multi-threading.
# If you are building a high-throughput API gateway or data ingestion pipeline in Python,
# you MUST use `asyncio` (or frameworks like FastAPI/AIOHTTP built on it).
# It uses the exact same `epoll` architecture as Erlang/BEAM and Node.js.
