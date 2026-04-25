"""
Module: Distributed Actor Pattern
Target: L7 Systems Engineers (Discord/Erlang standard)

Key Concept: "Do not communicate by sharing memory; instead, share memory by communicating."
- Each Actor owns its state.
- External callers send messages to the Actor's mailbox (Queue).
- The Actor processes messages sequentially, eliminating locks.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)

class Actor:
    def __init__(self, name: str):
        self.name = name
        self.mailbox = asyncio.Queue()
        self._state: Dict[str, Any] = {}
        self._active = False
        self._task = None

    async def start(self):
        self._active = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Actor {self.name} started.")

    async def _run(self):
        while self._active:
            # Wait for the next message
            msg_type, payload, future = await self.mailbox.get()
            
            try:
                # Dispatch message to internal handler
                handler = getattr(self, f"handle_{msg_type}", self.handle_unknown)
                result = await handler(payload)
                if future:
                    future.set_result(result)
            except Exception as e:
                if future:
                    future.set_exception(e)
            finally:
                self.mailbox.task_done()

    async def ask(self, msg_type: str, payload: Any = None):
        """Sends a message and waits for a response (synchronous)."""
        future = asyncio.get_running_loop().create_future()
        await self.mailbox.put((msg_type, payload, future))
        return await future

    async def tell(self, msg_type: str, payload: Any = None):
        """Sends a message and continues (asynchronous)."""
        await self.mailbox.put((msg_type, payload, None))

    async def handle_unknown(self, payload):
        logger.warning(f"Actor {self.name} received unknown message.")

class UserProfileActor(Actor):
    """Concrete Actor managing a specific user's state."""
    
    async def handle_update_score(self, score: int):
        current = self._state.get("score", 0)
        self._state["score"] = current + score
        return self._state["score"]

    async def handle_get_profile(self, _):
        return self._state

async def actor_demo():
    # Instantiate an Actor
    user_actor = UserProfileActor("User-123")
    await user_actor.start()

    # Tell (Fire and forget)
    await user_actor.tell("update_score", 10)
    
    # Ask (Request-Response)
    new_score = await user_actor.ask("update_score", 5)
    print(f"New score: {new_score}")
    
    profile = await user_actor.ask("get_profile")
    print(f"Final Profile: {profile}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(actor_demo())
    except KeyboardInterrupt:
        pass
