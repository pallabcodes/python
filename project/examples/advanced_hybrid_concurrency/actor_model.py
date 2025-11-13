"""
Actor Model Patterns for Hybrid Concurrency.

This module implements actor model patterns using message passing
for concurrent computation, inspired by Erlang/Elixir.

Features:
- Actor system with message passing
- Pykka actor framework integration
- Supervisor hierarchies for fault tolerance
- Message queues and routing
"""

import asyncio
import threading
import time
import logging
import queue
import uuid
from typing import Any, Callable, List, Dict, Optional, Union, Protocol
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)

# Optional Pykka import
try:
    import pykka
    PYKKA_AVAILABLE = True
except ImportError:
    pykka = None
    PYKKA_AVAILABLE = False


@dataclass
class Message:
    """Message sent between actors."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: Optional[str] = None
    receiver: Optional[str] = None
    message_type: str = "default"
    payload: Any = None
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None


class Actor(ABC):
    """
    Base actor class.

    When to Use:
        - Message-passing concurrency
        - Actor model patterns
        - Isolated state management
        - Fault-tolerant systems

    Real-World Examples:
        - Chat systems: User actors
        - Game servers: Player actors
        - Distributed systems: Service actors
        - Event-driven systems: Event actors

    Gotchas:
        - Message passing overhead
        - Actor lifecycle management
        - Dead letter handling
        - Supervisor hierarchies
        - State isolation

    Performance Notes:
        - Message passing overhead
        - Optimal for isolated state
        - Scales with actor count
        - Balance actors vs overhead
    """

    def __init__(self, actor_id: Optional[str] = None):
        self.actor_id = actor_id or str(uuid.uuid4())
        self._mailbox: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._supervisor: Optional['SupervisorActor'] = None

    @abstractmethod
    async def receive(self, message: Message) -> None:
        """Handle incoming message."""
        pass

    async def send(self, target: 'Actor', message: Message) -> None:
        """Send message to another actor."""
        message.sender = self.actor_id
        message.receiver = target.actor_id
        await target._mailbox.put(message)

    async def run(self):
        """Run actor message loop."""
        self._running = True
        try:
            while self._running:
                try:
                    message = await asyncio.wait_for(self._mailbox.get(), timeout=1.0)
                    await self.receive(message)
                    self._mailbox.task_done()
                except asyncio.TimeoutError:
                    await self.idle()
        except Exception as e:
            logger.error(f"Actor {self.actor_id} error: {e}")
            if self._supervisor:
                await self._supervisor.report_failure(self, e)

    async def idle(self):
        """Called when no messages are available."""
        pass

    def stop(self):
        """Stop the actor."""
        self._running = False


class WorkerActor(Actor):
    """Worker actor that processes tasks."""

    def __init__(self, worker_func: Callable):
        super().__init__()
        self.worker_func = worker_func
        self.processed_count = 0

    async def receive(self, message: Message):
        """Handle work messages."""
        if message.message_type == "work":
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.worker_func, *message.payload.get('args', []),
                    **message.payload.get('kwargs', {})
                )
                self.processed_count += 1

                # Send result back if reply_to specified
                reply_to = message.payload.get('reply_to')
                if reply_to:
                    response = Message(
                        message_type="result",
                        payload={"original_message": message.message_id, "result": result}
                    )
                    await self.send(reply_to, response)

            except Exception as e:
                logger.error(f"Worker actor error: {e}")


class RouterActor(Actor):
    """Router actor that distributes work to worker actors."""

    def __init__(self):
        super().__init__()
        self.workers: List[WorkerActor] = []
        self.next_worker = 0

    def add_worker(self, worker: WorkerActor):
        """Add worker to the pool."""
        self.workers.append(worker)

    async def receive(self, message: Message):
        """Route work messages to workers."""
        if message.message_type == "work" and self.workers:
            # Round-robin distribution
            worker = self.workers[self.next_worker % len(self.workers)]
            self.next_worker += 1

            # Add reply_to for result routing
            message.payload['reply_to'] = self

            await self.send(worker, message)


class SupervisorActor(Actor):
    """Supervisor actor that monitors and restarts child actors."""

    def __init__(self, strategy: str = "one_for_one"):
        super().__init__()
        self.strategy = strategy  # one_for_one, one_for_all, rest_for_one
        self.children: Dict[str, Actor] = {}
        self.failure_counts: Dict[str, int] = {}

    def supervise(self, actor: Actor):
        """Add actor to supervision."""
        self.children[actor.actor_id] = actor
        actor._supervisor = self

    async def receive(self, message: Message):
        """Handle supervision messages."""
        if message.message_type == "failure_report":
            await self.handle_failure(
                message.payload['actor'],
                message.payload['error']
            )

    async def report_failure(self, actor: Actor, error: Exception):
        """Report actor failure."""
        message = Message(
            message_type="failure_report",
            payload={"actor": actor, "error": error}
        )
        await self.send(self, message)

    async def handle_failure(self, actor: Actor, error: Exception):
        """Handle actor failure based on strategy."""
        actor_id = actor.actor_id
        self.failure_counts[actor_id] = self.failure_counts.get(actor_id, 0) + 1

        if self.strategy == "one_for_one":
            await self.restart_actor(actor)
        elif self.strategy == "one_for_all":
            await self.restart_all_actors()
        elif self.strategy == "rest_for_one":
            await self.restart_rest_actors(actor_id)

    async def restart_actor(self, actor: Actor):
        """Restart a single actor."""
        logger.info(f"Restarting actor {actor.actor_id}")
        actor.stop()
        # In production, create new instance
        await actor.run()

    async def restart_all_actors(self):
        """Restart all actors."""
        logger.info("Restarting all actors")
        for actor in self.children.values():
            actor.stop()
        # Restart all
        for actor in self.children.values():
            await actor.run()

    async def restart_rest_actors(self, failed_actor_id: str):
        """Restart actors after the failed one."""
        logger.info(f"Restarting actors after {failed_actor_id}")
        restart_from = False
        for actor_id, actor in self.children.items():
            if restart_from:
                actor.stop()
                await actor.run()
            if actor_id == failed_actor_id:
                restart_from = True
                actor.stop()
                await actor.run()


class MessageQueue:
    """Message queue for inter-actor communication."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=capacity)
        self._subscribers: Dict[str, Actor] = {}

    def subscribe(self, topic: str, actor: Actor):
        """Subscribe actor to topic."""
        self._subscribers[topic] = actor

    def unsubscribe(self, topic: str):
        """Unsubscribe from topic."""
        self._subscribers.pop(topic, None)

    async def publish(self, topic: str, message: Message):
        """Publish message to topic subscribers."""
        if topic in self._subscribers:
            await self._subscribers[topic]._mailbox.put(message)

    async def broadcast(self, message: Message):
        """Broadcast message to all subscribers."""
        for actor in self._subscribers.values():
            await actor._mailbox.put(message)


class FaultTolerantActor(Actor):
    """Fault-tolerant actor with automatic recovery."""

    def __init__(self, max_failures: int = 3, recovery_time: float = 5.0):
        super().__init__()
        self.max_failures = max_failures
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure = 0
        self.state = "active"

    async def receive(self, message: Message):
        """Handle messages with fault tolerance."""
        try:
            if self.state == "recovering":
                # Queue message for later processing
                await self.handle_during_recovery(message)
            else:
                await self.process_message(message)

        except Exception as e:
            await self.handle_error(e, message)

    async def process_message(self, message: Message):
        """Process normal messages (to be overridden)."""
        pass

    async def handle_during_recovery(self, message: Message):
        """Handle messages during recovery."""
        # Default: ignore during recovery
        pass

    async def handle_error(self, error: Exception, message: Message):
        """Handle processing errors."""
        self.failure_count += 1
        self.last_failure = time.time()

        if self.failure_count >= self.max_failures:
            logger.error(f"Actor {self.actor_id} exceeded max failures")
            self.state = "failed"
        else:
            logger.warning(f"Actor {self.actor_id} failure {self.failure_count}: {error}")
            self.state = "recovering"
            # Schedule recovery
            asyncio.create_task(self.recover())

    async def recover(self):
        """Recover from failure."""
        await asyncio.sleep(self.recovery_time)
        self.state = "active"
        logger.info(f"Actor {self.actor_id} recovered")


# Pykka Actor Implementation (if available)
class PykkaActor:
    """Pykka actor wrapper for compatibility."""

    def __init__(self):
        self._pykka_available = PYKKA_AVAILABLE
        self._actor_ref = None

    def start(self):
        """Start Pykka actor."""
        if not self._pykka_available:
            raise ImportError("Pykka not available")

        class PykkaActorImpl(pykka.ThreadingActor):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent

            def on_receive(self, message):
                # Handle message (would delegate to parent)
                return getattr(self.parent, 'handle_message', lambda x: None)(message)

        self._actor_ref = PykkaActorImpl.start(self)

    def stop(self):
        """Stop Pykka actor."""
        if self._actor_ref:
            self._actor_ref.stop()

    def tell(self, message):
        """Send message to Pykka actor."""
        if self._actor_ref:
            self._actor_ref.tell(message)

    def ask(self, message, timeout=None):
        """Ask Pykka actor for response."""
        if self._actor_ref:
            return self._actor_ref.ask(message, timeout=timeout)


class ActorSystem:
    """Actor system that manages multiple actors."""

    def __init__(self):
        self.actors: Dict[str, Actor] = {}
        self._running = False
        self._supervisor = SupervisorActor()

    async def start(self):
        """Start the actor system."""
        if self._running:
            return

        self._running = True
        logger.info("Started ActorSystem")

        # Start supervisor
        asyncio.create_task(self._supervisor.run())

    async def stop(self):
        """Stop the actor system."""
        if not self._running:
            return

        self._running = False

        # Stop all actors
        for actor in self.actors.values():
            actor.stop()

        self._supervisor.stop()
        logger.info("Stopped ActorSystem")

    def spawn(self, actor_class, *args, **kwargs) -> Actor:
        """Create and start new actor."""
        actor = actor_class(*args, **kwargs)
        self.actors[actor.actor_id] = actor

        # Add to supervisor
        self._supervisor.supervise(actor)

        # Start actor
        asyncio.create_task(actor.run())

        return actor

    def get_actor(self, actor_id: str) -> Optional[Actor]:
        """Get actor by ID."""
        return self.actors.get(actor_id)

    async def send_message(self, actor_id: str, message: Message):
        """Send message to actor."""
        actor = self.get_actor(actor_id)
        if actor:
            await self._supervisor.send(actor, message)


# Example worker function
def process_data(data: str, iterations: int = 1000) -> str:
    """Process data (simulates work)."""
    import math
    result = sum(math.sin(i) for i in range(iterations))
    return f"Processed {data}: {result:.2f}"


def demonstrate_actor_system():
    """Demonstrate actor system functionality."""
    print("🎭 Actor System Demonstration")
    print("=" * 35)

    async def run_demo():
        system = ActorSystem()
        await system.start()

        try:
            # Create worker actors
            worker1 = system.spawn(WorkerActor, process_data)
            worker2 = system.spawn(WorkerActor, process_data)

            # Create router
            router = system.spawn(RouterActor)
            router.add_worker(worker1)
            router.add_worker(worker2)

            # Send work messages
            for i in range(5):
                message = Message(
                    message_type="work",
                    payload={"args": [f"task_{i}"], "kwargs": {"iterations": 500}}
                )
                await system.send_message(router.actor_id, message)

            # Wait for processing
            await asyncio.sleep(2.0)

            print(f"✅ Worker 1 processed: {worker1.processed_count} tasks")
            print(f"✅ Worker 2 processed: {worker2.processed_count} tasks")
            print(f"✅ Total tasks processed: {worker1.processed_count + worker2.processed_count}")

        finally:
            await system.stop()

    asyncio.run(run_demo())


if __name__ == "__main__":
    # Run demonstration
    logging.basicConfig(level=logging.INFO)
    demonstrate_actor_system()
