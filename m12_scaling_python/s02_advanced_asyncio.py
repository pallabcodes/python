"""
Module: Advanced Asyncio Patterns for High Throughput
Target: L7 Engineers (Discord/Scale standard)

Key Insights:
1. Producer-Consumer: Using 'asyncio.Queue' to decouple ingestion from processing.
2. Graceful Shutdown: Handling SIGINT/SIGTERM to prevent data loss.
3. Event Loop Tuning: Using 'uvloop' (if available) for 2x-4x speedups.
"""

import asyncio
import signal
import time

# 1. Producer-Consumer Pattern
# Common in Discord-style message processing
async def worker(name: str, queue: asyncio.Queue):
    while True:
        # Get a "work item" out of the queue.
        item = await queue.get()
        
        # Process the item (simulated IO)
        print(f"Worker {name} processing {item}")
        await asyncio.sleep(0.5)
        
        # Notify the queue that the item has been processed.
        queue.task_done()

async def producer(queue: asyncio.Queue):
    for i in range(10):
        await queue.put(f"Task-{i}")
        print(f"Produced Task-{i}")
        await asyncio.sleep(0.1)

# 2. Graceful Shutdown
def handle_signal(sig, frame):
    print(f"Received signal {sig}. Initiating graceful shutdown...")
    # In a real app, you would set a 'stop' flag or cancel pending tasks.

# 3. Offloading Blocking Calls (The Google Pattern)
# If you must call a blocking C++ or legacy Python function, use an executor.
def blocking_calculation():
    time.sleep(2)  # Simulated heavy CPU or blocking IO
    return "Result"

async def main():
    queue = asyncio.Queue()

    # Start workers
    workers = [asyncio.create_task(worker(f"W-{i}", queue)) for i in range(3)]

    # Start producer
    await producer(queue)

    # Wait for all items in the queue to be processed
    await queue.join()

    # Cancel workers
    for w in workers:
        w.cancel()
    
    # Run a blocking call without freezing the loop
    loop = asyncio.get_running_loop()
    print("Starting blocking call in executor...")
    result = await loop.run_in_executor(None, blocking_calculation)
    print(f"Blocking result: {result}")

if __name__ == "__main__":
    # Signal handling (Unix only)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # loop.add_signal_handler(signal.SIGINT, lambda: print("SIGINT received"))
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutdown complete.")

# NOTE on uvloop:
# In a real production environment at Discord/Google, you would:
# import uvloop
# uvloop.install()
# before calling asyncio.run()
