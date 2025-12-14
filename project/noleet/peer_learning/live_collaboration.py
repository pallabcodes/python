"""
Live Collaboration System - Real-time pair programming and collaborative coding.

This module provides functionality for creating and managing live collaboration
sessions, handling participants, and facilitating real-time communication.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from peer_learning.models import (
    CollaborationSession, SessionParticipant, SessionMessage,
    CollaborationSessionData
)
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


class CollaborationManager:
    """Manager for live collaboration sessions."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager

        # In-memory session tracking (in production, use Redis)
        self.active_sessions: Dict[int, Set[int]] = {}  # session_id -> set of participant user_ids
        self.session_connections: Dict[str, Any] = {}   # connection_id -> connection info

        # Cache TTL settings
        self.CACHE_TTL = {
            'session_data': 1800,      # 30 minutes
            'active_sessions': 300,   # 5 minutes
        }

    async def create_session(self, host_user_id: int, session_data: Dict[str, Any]) -> CollaborationSession:
        """
        Create a new collaboration session.

        Args:
            host_user_id: User creating the session
            session_data: Session configuration

        Returns:
            Created CollaborationSession object
        """
        logger.info(f"User {host_user_id} creating collaboration session")

        # Validate session data
        self._validate_session_data(session_data)

        # Create session
        session = CollaborationSession(
            title=session_data['title'],
            description=session_data.get('description'),
            host_user_id=host_user_id,
            project_id=session_data.get('project_id'),
            session_type=session_data.get('session_type', 'pair_programming'),
            max_participants=session_data.get('max_participants', 2),
            is_public=session_data.get('is_public', True),
            scheduled_start=session_data.get('scheduled_start'),
            topics=session_data.get('topics', []),
            session_metadata={'created_via': 'api', 'version': '1.0'}
        )

        self.db.add(session)
        self.db.flush()  # Get session ID

        # Add host as participant
        host_participant = SessionParticipant(
            session_id=session.id,
            user_id=host_user_id,
            role='host',
            joined_at=datetime.now()
        )
        self.db.add(host_participant)

        self.db.commit()

        # Initialize in-memory tracking
        self.active_sessions[session.id] = {host_user_id}

        # Cache invalidation
        if self.cache:
            await self.cache.delete(f"user_sessions:{host_user_id}")

        logger.info(f"Collaboration session {session.id} created by user {host_user_id}")
        return session

    async def join_session(self, user_id: int, session_id: int) -> SessionParticipant:
        """
        Join an existing collaboration session.

        Args:
            user_id: User joining the session
            session_id: Session ID to join

        Returns:
            SessionParticipant object
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != 'active':
            raise ValueError(f"Session {session_id} is not active")

        # Check capacity
        current_participants = self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.left_at.is_none()
            )
        ).count()

        if current_participants >= session.max_participants:
            raise ValueError(f"Session {session_id} is at capacity ({session.max_participants})")

        # Check if user is already participating
        existing_participant = self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user_id,
                SessionParticipant.left_at.is_none()
            )
        ).first()

        if existing_participant:
            raise ValueError(f"User {user_id} is already participating in session {session_id}")

        # Create new participant
        participant = SessionParticipant(
            session_id=session_id,
            user_id=user_id,
            role='participant',
            joined_at=datetime.now()
        )

        self.db.add(participant)
        self.db.commit()

        # Update in-memory tracking
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = set()
        self.active_sessions[session_id].add(user_id)

        # Broadcast join event (would integrate with WebSocket system)
        await self._broadcast_session_event(session_id, 'participant_joined', {
            'user_id': user_id,
            'joined_at': participant.joined_at.isoformat()
        })

        logger.info(f"User {user_id} joined session {session_id}")
        return participant

    async def leave_session(self, user_id: int, session_id: int) -> bool:
        """
        Leave a collaboration session.

        Args:
            user_id: User leaving the session
            session_id: Session ID to leave

        Returns:
            True if successfully left
        """
        participant = self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user_id,
                SessionParticipant.left_at.is_none()
            )
        ).first()

        if not participant:
            return False

        # Update participant
        participant.left_at = datetime.now()
        self.db.commit()

        # Update in-memory tracking
        if session_id in self.active_sessions:
            self.active_sessions[session_id].discard(user_id)
            if not self.active_sessions[session_id]:
                del self.active_sessions[session_id]

        # Broadcast leave event
        await self._broadcast_session_event(session_id, 'participant_left', {
            'user_id': user_id,
            'left_at': participant.left_at.isoformat()
        })

        # Check if session should end (no participants left)
        remaining_participants = self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.left_at.is_none()
            )
        ).count()

        if remaining_participants == 0:
            await self.end_session(session_id)

        logger.info(f"User {user_id} left session {session_id}")
        return True

    async def start_session(self, session_id: int, host_user_id: int) -> bool:
        """
        Start a scheduled collaboration session.

        Args:
            session_id: Session ID to start
            host_user_id: User starting the session (must be host)

        Returns:
            True if successfully started
        """
        session = self.db.query(CollaborationSession).filter(
            and_(
                CollaborationSession.id == session_id,
                CollaborationSession.host_user_id == host_user_id
            )
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found or user {host_user_id} is not the host")

        if session.status != 'scheduled':
            raise ValueError(f"Session {session_id} cannot be started (status: {session.status})")

        # Start the session
        session.status = 'active'
        session.actual_start = datetime.now()
        self.db.commit()

        # Initialize active session tracking
        self.active_sessions[session_id] = set()

        # Broadcast session start
        await self._broadcast_session_event(session_id, 'session_started', {
            'started_at': session.actual_start.isoformat()
        })

        logger.info(f"Session {session_id} started by host {host_user_id}")
        return True

    async def end_session(self, session_id: int) -> bool:
        """
        End a collaboration session.

        Args:
            session_id: Session ID to end

        Returns:
            True if successfully ended
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status == 'completed':
            return True

        # End the session
        session.status = 'completed'
        session.actual_end = datetime.now()
        self.db.commit()

        # Update all remaining participants
        self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.left_at.is_none()
            )
        ).update({'left_at': session.actual_end})

        self.db.commit()

        # Clean up in-memory tracking
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        # Broadcast session end
        await self._broadcast_session_event(session_id, 'session_ended', {
            'ended_at': session.actual_end.isoformat()
        })

        logger.info(f"Session {session_id} ended")
        return True

    async def send_message(self, session_id: int, user_id: int, message_data: Dict[str, Any]) -> SessionMessage:
        """
        Send a message in a collaboration session.

        Args:
            session_id: Session ID
            user_id: User sending the message
            message_data: Message content and metadata

        Returns:
            Created SessionMessage object
        """
        # Verify user is participant
        participant = self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user_id,
                SessionParticipant.left_at.is_none()
            )
        ).first()

        if not participant:
            raise ValueError(f"User {user_id} is not an active participant in session {session_id}")

        # Create message
        message = SessionMessage(
            session_id=session_id,
            user_id=user_id,
            message_type=message_data.get('message_type', 'text'),
            message_content=message_data['message_content'],
            metadata=message_data.get('metadata', {})
        )

        self.db.add(message)
        self.db.commit()

        # Broadcast message to all session participants
        await self._broadcast_session_event(session_id, 'new_message', {
            'message_id': message.id,
            'user_id': user_id,
            'message_type': message.message_type,
            'message_content': message.message_content,
            'metadata': message.metadata,
            'timestamp': message.created_at.isoformat()
        })

        return message

    async def get_session_data(self, session_id: int) -> Optional[CollaborationSessionData]:
        """
        Get complete session data including participants and recent messages.

        Args:
            session_id: Session ID

        Returns:
            CollaborationSessionData or None if not found
        """
        cache_key = f"session_data:{session_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()

        if not session:
            return None

        # Get participants
        participants = self.db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id
        ).order_by(SessionParticipant.joined_at).all()

        participants_data = [{
            'participant_id': p.id,
            'user_id': p.user_id,
            'role': p.role,
            'joined_at': p.joined_at.isoformat() if p.joined_at else None,
            'left_at': p.left_at.isoformat() if p.left_at else None,
            'participation_score': p.participation_score
        } for p in participants]

        # Get recent messages (last 50)
        recent_messages = self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id
        ).order_by(desc(SessionMessage.created_at)).limit(50).all()

        messages_data = [{
            'message_id': m.id,
            'user_id': m.user_id,
            'message_type': m.message_type,
            'message_content': m.message_content,
            'metadata': m.metadata,
            'timestamp': m.created_at.isoformat()
        } for m in recent_messages]

        # Reverse to chronological order
        messages_data.reverse()

        session_data = CollaborationSessionData(
            session_id=session.id,
            title=session.title,
            description=session.description,
            host_user_id=session.host_user_id,
            session_type=session.session_type,
            status=session.status,
            max_participants=session.max_participants,
            current_participants=len([p for p in participants if p.left_at is None]),
            scheduled_start=session.scheduled_start,
            actual_start=session.actual_start,
            topics=session.topics or [],
            participants=participants_data
        )

        # Add messages to result
        result = asdict(session_data)
        result['recent_messages'] = messages_data

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=self.CACHE_TTL['session_data'])

        return result

    async def get_active_sessions(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get active collaboration sessions.

        Args:
            user_id: Optional user ID to filter sessions they're participating in

        Returns:
            List of active session data
        """
        cache_key = f"active_sessions:{user_id or 'all'}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        query = self.db.query(CollaborationSession).filter(
            CollaborationSession.status == 'active'
        )

        if user_id:
            # Filter to sessions where user is participating
            query = query.join(SessionParticipant).filter(
                and_(
                    SessionParticipant.user_id == user_id,
                    SessionParticipant.left_at.is_none()
                )
            )

        sessions = query.order_by(CollaborationSession.actual_start.desc()).all()

        result = []
        for session in sessions:
            # Get current participant count
            participant_count = self.db.query(SessionParticipant).filter(
                and_(
                    SessionParticipant.session_id == session.id,
                    SessionParticipant.left_at.is_none()
                )
            ).count()

            result.append({
                'session_id': session.id,
                'title': session.title,
                'description': session.description,
                'host_user_id': session.host_user_id,
                'session_type': session.session_type,
                'current_participants': participant_count,
                'max_participants': session.max_participants,
                'topics': session.topics or [],
                'started_at': session.actual_start.isoformat() if session.actual_start else None
            })

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=self.CACHE_TTL['active_sessions'])

        return result

    async def get_user_sessions(self, user_id: int, include_past: bool = False) -> List[Dict[str, Any]]:
        """
        Get collaboration sessions for a user.

        Args:
            user_id: User ID
            include_past: Whether to include completed sessions

        Returns:
            List of user's sessions
        """
        statuses = ['active', 'scheduled']
        if include_past:
            statuses.extend(['completed', 'cancelled'])

        sessions = self.db.query(CollaborationSession).join(SessionParticipant).filter(
            and_(
                SessionParticipant.user_id == user_id,
                CollaborationSession.status.in_(statuses)
            )
        ).order_by(desc(CollaborationSession.created_at)).all()

        result = []
        for session in sessions:
            # Get user's participation data
            participation = self.db.query(SessionParticipant).filter(
                and_(
                    SessionParticipant.session_id == session.id,
                    SessionParticipant.user_id == user_id
                )
            ).first()

            result.append({
                'session_id': session.id,
                'title': session.title,
                'description': session.description,
                'role': participation.role if participation else 'unknown',
                'status': session.status,
                'joined_at': participation.joined_at.isoformat() if participation and participation.joined_at else None,
                'left_at': participation.left_at.isoformat() if participation and participation.left_at else None,
                'session_type': session.session_type,
                'topics': session.topics or []
            })

        return result

    async def update_participation_feedback(self, session_id: int, user_id: int,
                                          rating: int, feedback: str) -> bool:
        """
        Update participation feedback for a completed session.

        Args:
            session_id: Session ID
            user_id: User ID providing feedback
            rating: Rating 1-5
            feedback: Optional feedback text

        Returns:
            True if feedback recorded
        """
        participant = self.db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user_id
            )
        ).first()

        if not participant:
            raise ValueError(f"User {user_id} did not participate in session {session_id}")

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        participant.feedback_rating = rating
        participant.feedback_text = feedback
        self.db.commit()

        logger.info(f"Feedback recorded for user {user_id} in session {session_id}: {rating}/5")
        return True

    # Private helper methods

    def _validate_session_data(self, data: Dict[str, Any]) -> None:
        """Validate session creation data."""
        required_fields = ['title']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")

        if len(data['title']) > 255:
            raise ValueError("Title too long (max 255 characters)")

        if len(data.get('description', '')) > 1000:
            raise ValueError("Description too long (max 1000 characters)")

        max_participants = data.get('max_participants', 2)
        if max_participants < 2 or max_participants > 10:
            raise ValueError("Max participants must be between 2 and 10")

        valid_types = ['pair_programming', 'code_review', 'debugging', 'learning']
        session_type = data.get('session_type', 'pair_programming')
        if session_type not in valid_types:
            raise ValueError(f"Invalid session type. Must be one of: {', '.join(valid_types)}")

    async def _broadcast_session_event(self, session_id: int, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Broadcast an event to all participants in a session.

        In a real implementation, this would use WebSocket connections or
        a pub/sub system like Redis. For now, it's a placeholder.
        """
        logger.info(f"Broadcasting {event_type} event to session {session_id}")

        # Get active participants
        active_participants = self.active_sessions.get(session_id, set())

        if active_participants:
            # In production, send to WebSocket connections
            # For now, just log the event
            event = {
                'session_id': session_id,
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.now().isoformat()
            }

            # Store event in session metadata for persistence
            session = self.db.query(CollaborationSession).filter(
                CollaborationSession.id == session_id
            ).first()

            if session:
                metadata = session.session_metadata or {}
                events = metadata.get('events', [])
                events.append(event)

                # Keep only last 100 events
                if len(events) > 100:
                    events = events[-100:]

                metadata['events'] = events
                session.session_metadata = metadata
                self.db.commit()

    async def calculate_session_stats(self, session_id: int) -> Dict[str, Any]:
        """
        Calculate statistics for a completed session.

        Args:
            session_id: Session ID

        Returns:
            Session statistics
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Calculate duration
        duration = None
        if session.actual_start and session.actual_end:
            duration = (session.actual_end - session.actual_start).total_seconds()

        # Get message count
        message_count = self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id
        ).count()

        # Get participant stats
        participants = self.db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id
        ).all()

        avg_rating = None
        ratings = [p.feedback_rating for p in participants if p.feedback_rating]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)

        return {
            'session_id': session_id,
            'duration_seconds': duration,
            'total_messages': message_count,
            'participant_count': len(participants),
            'average_rating': avg_rating,
            'feedback_count': len([p for p in participants if p.feedback_text])
        }
