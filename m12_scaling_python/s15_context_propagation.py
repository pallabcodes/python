"""
Module: Advanced Context Propagation
Target: L7 Architects (Core Python Standard)

Key Technique: contextvars
- Manages state across concurrent async tasks.
- Eliminates "Context Passing" (threading local for asyncio).
- Essential for Tracing, Logging, and Request-ID tracking.
"""

import asyncio
import contextvars
import uuid
import logging

logger = logging.getLogger(__name__)

# 1. Define Context Variables (Google standard for tracing)
request_id_ctx = contextvars.ContextVar("request_id", default="INTERNAL")
user_id_ctx = contextvars.ContextVar("user_id")

class ContextualLogger:
    """A logger that automatically injects context IDs into every log."""
    @staticmethod
    def info(msg):
        rid = request_id_ctx.get()
        uid = user_id_ctx.get(default="GUEST")
        logger.info(f"[{rid}] [USER:{uid}] {msg}")

async def sub_task_b():
    """Deeply nested task that still has access to the context."""
    ContextualLogger.info("Inside sub_task_b - context is preserved!")

async def sub_task_a():
    ContextualLogger.info("Inside sub_task_a")
    await asyncio.sleep(0.1)
    await sub_task_b()

async def request_handler(user_id: str):
    """Entry point for a request (simulates a web server)."""
    # 2. Set the context for this specific task
    token_rid = request_id_ctx.set(str(uuid.uuid4())[:8])
    token_uid = user_id_ctx.set(user_id)
    
    try:
        ContextualLogger.info("Starting request processing...")
        await sub_task_a()
    finally:
        # 3. Clean up (good practice)
        request_id_ctx.reset(token_rid)
        user_id_ctx.reset(token_uid)

async def context_demo():
    # Simulate concurrent requests
    await asyncio.gather(
        request_handler("Alice"),
        request_handler("Bob"),
        request_handler("Charlie")
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.run(context_demo())
