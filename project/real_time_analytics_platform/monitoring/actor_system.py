"""
Actor Model Implementation for Fault-Tolerant Monitoring.

Demonstrates:
- Actor model for concurrent, fault-tolerant systems
- Message passing between actors
- Supervisor hierarchies for fault recovery
- Asynchronous message processing
- Actor lifecycle management
"""

import asyncio
import time
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class ActorState(Enum):
    """States for actor lifecycle."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class Message:
    """Message for actor communication."""
    message_type: str
    payload: Dict[str, Any]
    sender: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ActorMetrics:
    """Metrics for actor performance."""
    messages_processed: int = 0
    messages_failed: int = 0
    avg_processing_time: float = 0.0
    total_processing_time: float = 0.0
    uptime_seconds: float = 0.0
    restart_count: int = 0


class Actor(ABC):
    """
    Base Actor class for the actor model implementation.

    Actors are independent units of computation that communicate
    via asynchronous message passing.
    """

    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.state = ActorState.CREATED
        self.metrics = ActorMetrics()
        self.mailbox: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.supervisor: Optional['SupervisorActor'] = None

        # Lifecycle management
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Start time tracking
        self._start_time = time.time()

    @abstractmethod
    async def receive(self, message: Message) -> None:
        """Handle incoming messages. Must be implemented by subclasses."""
        pass

    async def pre_start(self) -> None:
        """Called before actor starts processing messages."""
        pass

    async def post_stop(self) -> None:
        """Called after actor stops."""
        pass

    async def on_failure(self, error: Exception) -> None:
        """Called when actor encounters an error."""
        logger.error(f"Actor {self.actor_id} failed: {error}")

        # Notify supervisor if available
        if self.supervisor:
            await self.supervisor.handle_child_failure(self.actor_id, error)

    def get_metrics(self) -> Dict[str, Any]:
        """Get actor performance metrics."""
        self.metrics.uptime_seconds = time.time() - self._start_time

        return {
            "actor_id": self.actor_id,
            "state": self.state.value,
            "messages_processed": self.metrics.messages_processed,
            "messages_failed": self.metrics.messages_failed,
            "avg_processing_time": self.metrics.avg_processing_time,
            "uptime_seconds": self.metrics.uptime_seconds,
            "restart_count": self.metrics.restart_count,
            "mailbox_size": self.mailbox.qsize()
        }


class ActorSystem:
    """
    Actor System for managing actor lifecycles and communication.

    Features:
    - Actor registration and management
    - Message routing between actors
    - Supervisor hierarchies for fault tolerance
    - Performance monitoring
    - Graceful shutdown
    """

    def __init__(self):
        self.actors: Dict[str, Actor] = {}
        self._system_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()

        logger.info("ActorSystem initialized")

    async def start(self) -> None:
        """Start the actor system."""
        if self._system_task is not None:
            return

        self._system_task = asyncio.create_task(self._system_loop())
        logger.info("ActorSystem started")

    async def stop(self) -> None:
        """Stop the actor system and all actors."""
        if self._system_task is None:
            return

        logger.info("Stopping ActorSystem...")

        # Signal shutdown
        self._shutdown_event.set()

        # Stop all actors
        stop_tasks = []
        for actor in self.actors.values():
            if actor.state == ActorState.RUNNING:
                stop_tasks.append(self._stop_actor(actor))

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        # Cancel system task
        self._system_task.cancel()
        try:
            await self._system_task
        except asyncio.CancelledError:
            pass

        self._system_task = None
        logger.info("ActorSystem stopped")

    async def spawn(self, actor_class: type, *args, **kwargs) -> Actor:
        """
        Create and start a new actor.

        Args:
            actor_class: The actor class to instantiate
            *args, **kwargs: Arguments for actor constructor
        """
        async with self._lock:
            # Generate unique actor ID if not provided
            actor_id = kwargs.get('actor_id', f"{actor_class.__name__}_{uuid.uuid4().hex[:8]}")

            # Create actor instance
            actor = actor_class(actor_id, *args, **kwargs)
            actor.state = ActorState.STARTING

            # Register actor
            self.actors[actor_id] = actor

            # Pre-start hook
            try:
                await actor.pre_start()
            except Exception as e:
                logger.error(f"Actor {actor_id} pre_start failed: {e}")
                actor.state = ActorState.FAILED
                raise

            # Start message processing
            actor._processing_task = asyncio.create_task(self._actor_loop(actor))
            actor.state = ActorState.RUNNING

            logger.info(f"Spawned actor: {actor_id}")
            return actor

    async def send_message(
        self,
        target_actor_id: str,
        message: Union[Message, Dict[str, Any]]
    ) -> bool:
        """
        Send a message to an actor.

        Returns True if message was queued successfully.
        """
        if isinstance(message, dict):
            message = Message(**message)

        if target_actor_id not in self.actors:
            logger.warning(f"Actor {target_actor_id} not found")
            return False

        actor = self.actors[target_actor_id]

        try:
            await asyncio.wait_for(
                actor.mailbox.put(message),
                timeout=1.0  # 1 second timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Mailbox full for actor {target_actor_id}")
            return False

    async def broadcast_message(self, message: Union[Message, Dict[str, Any]]) -> int:
        """
        Send message to all running actors.

        Returns number of actors that received the message.
        """
        if isinstance(message, dict):
            message = Message(**message)

        successful_sends = 0
        send_tasks = []

        for actor in self.actors.values():
            if actor.state == ActorState.RUNNING:
                send_tasks.append(self.send_message(actor.actor_id, message))

        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            successful_sends = sum(1 for r in results if r is True)

        return successful_sends

    async def get_actor_metrics(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific actor."""
        actor = self.actors.get(actor_id)
        if actor:
            return actor.get_metrics()
        return None

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide actor metrics."""
        total_messages = sum(a.metrics.messages_processed for a in self.actors.values())
        total_failed = sum(a.metrics.messages_failed for a in self.actors.values())
        running_actors = sum(1 for a in self.actors.values() if a.state == ActorState.RUNNING)

        return {
            "total_actors": len(self.actors),
            "running_actors": running_actors,
            "total_messages_processed": total_messages,
            "total_messages_failed": total_failed,
            "success_rate": total_messages / max(1, total_messages + total_failed),
            "system_uptime": time.time() - getattr(self, '_system_start_time', time.time())
        }

    async def _system_loop(self):
        """Main system monitoring loop."""
        self._system_start_time = time.time()

        try:
            while not self._shutdown_event.is_set():
                # System health monitoring
                await self._monitor_system_health()

                # Brief pause
                await asyncio.sleep(10)  # Check every 10 seconds

        except asyncio.CancelledError:
            logger.info("System loop cancelled")
        except Exception as e:
            logger.error(f"System loop error: {e}")

    async def _monitor_system_health(self):
        """Monitor overall system health."""
        # Check for dead actors and restart if needed
        dead_actors = []

        for actor_id, actor in self.actors.items():
            if actor.state == ActorState.FAILED:
                dead_actors.append(actor_id)
            elif actor.state == ActorState.RUNNING and actor._processing_task.done():
                # Actor task finished unexpectedly
                try:
                    await actor._processing_task
                except Exception as e:
                    logger.error(f"Actor {actor_id} task failed: {e}")
                    actor.state = ActorState.FAILED
                    dead_actors.append(actor_id)

        # Log system status periodically
        running_count = sum(1 for a in self.actors.values() if a.state == ActorState.RUNNING)
        logger.debug(f"ActorSystem: {running_count}/{len(self.actors)} actors running")

    async def _actor_loop(self, actor: Actor):
        """Message processing loop for an actor."""
        logger.info(f"Starting actor loop for {actor.actor_id}")

        try:
            while not self._shutdown_event.is_set() and actor.state == ActorState.RUNNING:
                try:
                    # Get next message with timeout
                    message = await asyncio.wait_for(
                        actor.mailbox.get(),
                        timeout=1.0
                    )

                    # Process the message
                    await self._process_message(actor, message)

                except asyncio.TimeoutError:
                    # No messages, continue loop
                    continue
                except Exception as e:
                    actor.metrics.messages_failed += 1
                    logger.error(f"Error processing message in {actor.actor_id}: {e}")
                    await actor.on_failure(e)

        except asyncio.CancelledError:
            logger.info(f"Actor loop cancelled for {actor.actor_id}")
        except Exception as e:
            logger.error(f"Fatal error in actor loop for {actor.actor_id}: {e}")
            actor.state = ActorState.FAILED

        # Cleanup
        await self._stop_actor(actor)

    async def _process_message(self, actor: Actor, message: Message):
        """Process a single message for an actor."""
        start_time = time.time()

        try:
            # Add sender info if not present
            if message.sender is None:
                message.sender = "system"

            # Handle the message
            await actor.receive(message)

            # Update metrics
            processing_time = time.time() - start_time
            actor.metrics.messages_processed += 1
            actor.metrics.total_processing_time += processing_time
            actor.metrics.avg_processing_time = (
                actor.metrics.total_processing_time / actor.metrics.messages_processed
            )

        except Exception as e:
            processing_time = time.time() - start_time
            actor.metrics.messages_failed += 1
            logger.error(f"Actor {actor.actor_id} failed to process message: {e}")
            await actor.on_failure(e)

    async def _stop_actor(self, actor: Actor):
        """Stop a single actor."""
        if actor.state in [ActorState.STOPPING, ActorState.STOPPED]:
            return

        actor.state = ActorState.STOPPING

        try:
            # Post-stop hook
            await actor.post_stop()
        except Exception as e:
            logger.error(f"Error in post_stop for {actor.actor_id}: {e}")

        # Cancel processing task if still running
        if actor._processing_task and not actor._processing_task.done():
            actor._processing_task.cancel()
            try:
                await actor._processing_task
            except asyncio.CancelledError:
                pass

        actor.state = ActorState.STOPPED
        logger.info(f"Stopped actor: {actor.actor_id}")


class SupervisorActor(Actor):
    """
    Supervisor actor that monitors and restarts child actors.

    Implements the "let it crash" philosophy with supervisor hierarchies.
    """

    def __init__(self, actor_id: str, max_restarts: int = 3, restart_window: float = 60.0):
        super().__init__(actor_id)
        self.max_restarts = max_restarts
        self.restart_window = restart_window
        self.child_actors: Dict[str, Actor] = {}
        self.restart_times: List[float] = []

    async def supervise(self, actor: Actor) -> None:
        """Add an actor to supervision."""
        actor.supervisor = self
        self.child_actors[actor.actor_id] = actor
        logger.info(f"Supervising actor: {actor.actor_id}")

    async def handle_child_failure(self, child_id: str, error: Exception) -> None:
        """Handle failure of a supervised child actor."""
        logger.warning(f"Child actor {child_id} failed: {error}")

        # Check restart policy
        current_time = time.time()

        # Remove old restart times outside the window
        self.restart_times = [
            t for t in self.restart_times
            if current_time - t < self.restart_window
        ]

        if len(self.restart_times) >= self.max_restarts:
            logger.error(f"Too many restarts for {child_id}, giving up")
            # Could escalate to higher supervisor or alert
            await self.escalate_failure(child_id, error)
            return

        # Record restart attempt
        self.restart_times.append(current_time)

        # Attempt to restart the child
        child_actor = self.child_actors.get(child_id)
        if child_actor:
            try:
                # Create new actor instance (simplified - would need factory pattern)
                logger.info(f"Restarting child actor: {child_id}")

                # For demo, just reset state (real implementation would recreate)
                child_actor.state = ActorState.RUNNING
                child_actor.metrics.restart_count += 1
                child_actor._processing_task = asyncio.create_task(
                    asyncio.get_event_loop().create_task(
                        self._restart_actor_processing(child_actor)
                    )
                )

            except Exception as e:
                logger.error(f"Failed to restart {child_id}: {e}")
                await self.escalate_failure(child_id, error)

    async def _restart_actor_processing(self, actor: Actor):
        """Restart processing for a failed actor."""
        # Simplified restart - in real implementation, would reinitialize state
        actor._shutdown_event.clear()

        # Resume message processing (simplified)
        while not actor._shutdown_event.is_set():
            try:
                message = await asyncio.wait_for(actor.mailbox.get(), timeout=1.0)
                await actor.receive(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Restarted actor {actor.actor_id} failed again: {e}")
                break

    async def escalate_failure(self, child_id: str, error: Exception):
        """Escalate failure to higher level monitoring."""
        # Send alert message
        alert_message = Message(
            message_type="supervisor_alert",
            payload={
                "child_id": child_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "restart_attempts": len(self.restart_times),
                "max_restarts": self.max_restarts
            }
        )

        # Broadcast to alert actors (would be routed in real system)
        logger.error(f"Supervisor escalation: {child_id} failed permanently")

    async def receive(self, message: Message) -> None:
        """Handle supervisor messages."""
        if message.message_type == "child_status_request":
            # Report status of supervised children
            status = {
                child_id: child.get_metrics()
                for child_id, child in self.child_actors.items()
            }

            # Would send response back to requester
            logger.info(f"Supervisor status: {len(self.child_actors)} children")

        elif message.message_type == "shutdown_children":
            # Shutdown all supervised children
            shutdown_tasks = [
                child._shutdown_event.set()
                for child in self.child_actors.values()
            ]
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            logger.info("Shutdown all supervised children")
