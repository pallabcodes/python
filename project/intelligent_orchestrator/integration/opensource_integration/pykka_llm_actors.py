"""Pykka actor model for LLM agents."""

from typing import Any, Dict, Optional
import logging


class PykkaLLMActor:
    """Pykka-based actor model for LLM agents."""

    def __init__(
        self,
        actor_id: str,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize Pykka actor.

        Args:
            actor_id: Actor identifier
            logger: Optional logger instance
        """
        self._actor_id = actor_id
        self._logger = logger or logging.getLogger(__name__)
        self._messages: list = []
        self._logger.info(f"Pykka LLM actor {actor_id} initialized")

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to actor.

        Args:
            message: Message dictionary
        """
        self._messages.append(message)
        self._logger.debug(f"Actor {self._actor_id} received message")

