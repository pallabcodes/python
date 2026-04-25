"""
Module: Advanced Backpressure and Streaming
Target: L7 Systems Engineers (Google/Discord Scale)

Key Patterns:
1. Bounded vs Unbounded Buffers: Managing memory vs. latency.
2. Backpressure (Load Shedding): Dropping tasks when the buffer is full.
3. Batching: Reducing IO overhead by grouping requests.
4. Pausable Streams: Using Events to throttle ingestion.
"""

import asyncio
import time
import logging
import random
from typing import List, Any

logger = logging.getLogger(__name__)

class BoundedStream:
    """
    Implements Backpressure via Bounded Buffers.
    If the consumer is slower than the producer, the producer is forced to wait (backpressure).
    """
    def __init__(self, capacity: int = 10):
        self.queue = asyncio.Queue(maxsize=capacity)
        self.is_paused = asyncio.Event()
        self.is_paused.set() # Start unpaused

    async def produce(self, item: Any):
        await self.is_paused.wait()
        # This will 'await' if the queue is full, applying backpressure
        await self.queue.put(item)
        logger.debug(f"Produced: {item}")

    async def consume(self):
        while True:
            item = await self.queue.get()
            # Simulate heavy processing
            await asyncio.sleep(random.uniform(0.1, 0.5))
            logger.info(f"Consumed: {item}")
            self.queue.task_done()

class BatchingBuffer:
    """
    Optimizes IO by batching multiple items before processing.
    Essential for 1M+ ingestion scenarios (Discord/Google standard).
    """
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []
        self._lock = asyncio.Lock()
        self._last_flush = time.time()

    async def add(self, item: Any):
        async with self._lock:
            self.buffer.append(item)
            if len(self.buffer) >= self.batch_size:
                await self.flush()

    async def flush(self):
        if not self.buffer:
            return
        async with self._lock:
            logger.info(f"FLUSHING BATCH of {len(self.buffer)} items to storage...")
            # In real system: await redis.mset(self.buffer)
            self.buffer = []
            self._last_heartbeat = time.time()

async def run_backpressure_demo():
    stream = BoundedStream(capacity=5)
    
    # Start consumer
    consumer_task = asyncio.create_task(stream.consume())
    
    # Produce rapidly
    logger.info("Starting rapid production...")
    for i in range(20):
        if i == 10:
            logger.warning("PAUSING STREAM manually for 2 seconds...")
            stream.is_paused.clear()
            await asyncio.sleep(2)
            stream.is_paused.set()
        
        await stream.produce(f"Data-{i}")

    await stream.queue.join()
    consumer_task.cancel()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(run_backpressure_demo())
    except KeyboardInterrupt:
        pass
