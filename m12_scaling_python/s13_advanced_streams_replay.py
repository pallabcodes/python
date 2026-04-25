"""
Module: Replayable and Interruptible Streams
Target: L7 Architects (Kafka-lite/Google standard)

Key Patterns:
1. Replayable Logs: Consumers track an 'offset' to replay historical data.
2. Graceful Interruption: Ensuring 'Exactly-Once' or 'At-Least-Once' semantics during cancellation.
3. Cursor Pattern: Decoupling stream ingestion from processing state.
"""

import asyncio
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ReplayableLog:
    """
    A simple in-memory Log-based stream (Kafka-style).
    Data is never removed; consumers use offsets to read.
    """
    def __init__(self):
        self._log: List[str] = []
        self._new_data_event = asyncio.Event()

    def append(self, data: str):
        self._log.append(data)
        self._new_data_event.set()
        self._new_data_event.clear()

    async def get_stream(self, offset: int = 0):
        """Yields data from the log starting at 'offset'."""
        current_offset = offset
        while True:
            # Catch up with existing log
            while current_offset < len(self._log):
                yield current_offset, self._log[current_offset]
                current_offset += 1
            
            # Wait for new data
            await self._new_data_event.wait()

class InterruptibleConsumer:
    """
    Handles graceful interruption and state persistence.
    Essential for systems that cannot lose data during deployment/shutdown.
    """
    def __init__(self, log: ReplayableLog):
        self.log = log
        self.last_processed_offset = -1

    async def run(self):
        try:
            async for offset, data in self.log.get_stream(self.last_processed_offset + 1):
                logger.info(f"Processing: {data} (Offset: {offset})")
                
                # Simulate processing
                await asyncio.sleep(0.5)
                
                # ATOMIC COMMIT: Update offset only after successful processing
                self.last_processed_offset = offset
                
        except asyncio.CancelledError:
            logger.warning(f"Consumer interrupted! Saving offset {self.last_processed_offset} for replay.")
            # In real system: await db.save_offset(self.last_processed_offset)
            raise

async def replay_demo():
    log = ReplayableLog()
    consumer = InterruptibleConsumer(log)
    
    # 1. Pre-fill log
    for i in range(5): log.append(f"Initial-{i}")

    # 2. Start consumer
    task = asyncio.create_task(consumer.run())
    await asyncio.sleep(1) # Let it process some

    # 3. Simulate Interrupt
    logger.error("SYSTEM INTERRUPT DETECTED!")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # 4. REPLAY: Start a new consumer from the last offset
    logger.info(f"RESTARTING consumer from offset {consumer.last_processed_offset + 1}...")
    for i in range(5, 10): log.append(f"New-{i}")
    
    # New task will pick up exactly where it left off
    new_task = asyncio.create_task(consumer.run())
    await asyncio.sleep(2)
    new_task.cancel()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(replay_demo())
    except KeyboardInterrupt:
        pass
