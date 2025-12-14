"""
Peer Learning Service - Main service orchestrating all peer learning features.

This module provides a unified interface to all peer learning functionality:
- Code Review System
- Live Collaboration Sessions
- Implementation Showcase Gallery
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from peer_learning.code_review import CodeReviewEngine
from peer_learning.live_collaboration import CollaborationManager
from peer_learning.showcase_gallery import ShowcaseGallery
from peer_learning.models import PeerLearningStats
from noleet.app.core.caching import CacheManager
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class PeerLearningService:
    """Main service for peer learning features."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager

        # Initialize sub-services
        self.code_review = CodeReviewEngine(db_session, cache_manager)
        self.collaboration = CollaborationManager(db_session, cache_manager)
        self.showcase = ShowcaseGallery(db_session, cache_manager)

    # Code Review Methods

    async def submit_code_for_review(self, user_id: int, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit code for peer review."""
        submission = await self.code_review.submit_code_for_review(user_id, submission_data)
        return {
            'submission_id': submission.id,
            'status': submission.status,
            'reviewers_assigned': True,
            'message': 'Code submitted for review successfully'
        }

    async def get_available_reviews(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get code submissions available for review."""
        return await self.code_review.get_available_reviews(user_id, limit)

    async def start_code_review(self, reviewer_id: int, submission_id: int) -> Dict[str, Any]:
        """Start reviewing a code submission."""
        review = await self.code_review.start_review(reviewer_id, submission_id)
        return {
            'review_id': review.id,
            'status': review.status,
            'started_at': review.review_started_at.isoformat()
        }

    async def submit_review_feedback(self, review_id: int, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback for a completed review."""
        review = await self.code_review.submit_review_feedback(review_id, feedback_data)
        return {
            'review_id': review.id,
            'status': review.status,
            'rating': review.overall_rating,
            'completed_at': review.review_completed_at.isoformat()
        }

    async def get_user_reviews(self, user_id: int, review_type: str = 'given',
                              limit: int = 20) -> List[Dict[str, Any]]:
        """Get reviews given or received by a user."""
        return await self.code_review.get_user_reviews(user_id, review_type, limit)

    async def generate_ai_feedback(self, submission_id: int) -> Dict[str, Any]:
        """Generate AI-powered feedback for a submission."""
        return await self.code_review.generate_ai_feedback(submission_id)

    # Live Collaboration Methods

    async def create_collaboration_session(self, host_user_id: int, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaboration session."""
        session = await self.collaboration.create_session(host_user_id, session_data)
        return {
            'session_id': session.id,
            'title': session.title,
            'status': session.status,
            'max_participants': session.max_participants,
            'message': 'Collaboration session created successfully'
        }

    async def join_session(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """Join a collaboration session."""
        participant = await self.collaboration.join_session(user_id, session_id)
        return {
            'participant_id': participant.id,
            'session_id': session_id,
            'role': participant.role,
            'joined_at': participant.joined_at.isoformat()
        }

    async def leave_session(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """Leave a collaboration session."""
        left = await self.collaboration.leave_session(user_id, session_id)
        return {
            'success': left,
            'session_id': session_id,
            'message': 'Left session successfully' if left else 'Not currently in session'
        }

    async def start_session(self, session_id: int, host_user_id: int) -> Dict[str, Any]:
        """Start a collaboration session."""
        started = await self.collaboration.start_session(session_id, host_user_id)
        return {
            'success': started,
            'session_id': session_id,
            'message': 'Session started successfully' if started else 'Failed to start session'
        }

    async def end_session(self, session_id: int) -> Dict[str, Any]:
        """End a collaboration session."""
        ended = await self.collaboration.end_session(session_id)
        return {
            'success': ended,
            'session_id': session_id,
            'message': 'Session ended successfully' if ended else 'Failed to end session'
        }

    async def send_session_message(self, session_id: int, user_id: int, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message in a collaboration session."""
        message = await self.collaboration.send_message(session_id, user_id, message_data)
        return {
            'message_id': message.id,
            'session_id': session_id,
            'message_type': message.message_type,
            'timestamp': message.created_at.isoformat()
        }

    async def get_session_data(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get complete session data."""
        return await self.collaboration.get_session_data(session_id)

    async def get_active_sessions(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active collaboration sessions."""
        return await self.collaboration.get_active_sessions(user_id)

    async def get_user_sessions(self, user_id: int, include_past: bool = False) -> List[Dict[str, Any]]:
        """Get collaboration sessions for a user."""
        return await self.collaboration.get_user_sessions(user_id, include_past)

    async def update_session_feedback(self, session_id: int, user_id: int,
                                    rating: int, feedback: str) -> Dict[str, Any]:
        """Update participation feedback for a session."""
        updated = await self.collaboration.update_participation_feedback(session_id, user_id, rating, feedback)
        return {
            'success': updated,
            'session_id': session_id,
            'message': 'Feedback recorded successfully'
        }

    # Showcase Gallery Methods

    async def submit_showcase(self, user_id: int, showcase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an implementation to the showcase gallery."""
        showcase = await self.showcase.submit_showcase(user_id, showcase_data)
        return {
            'showcase_id': showcase.id,
            'status': showcase.status,
            'featured': showcase.featured,
            'message': 'Showcase submitted successfully'
        }

    async def get_gallery_showcases(self, filters: Optional[Dict[str, Any]] = None,
                                  sort_by: str = 'upvotes', limit: int = 50) -> List[Dict[str, Any]]:
        """Get showcases from the gallery."""
        showcases = await self.showcase.get_gallery_showcases(filters, sort_by, limit)
        return [asdict(showcase) for showcase in showcases]

    async def get_showcase_details(self, showcase_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a showcase."""
        showcase = await self.showcase.get_showcase_details(showcase_id)
        return asdict(showcase) if showcase else None

    async def vote_on_showcase(self, user_id: int, showcase_id: int, vote_type: str) -> Dict[str, Any]:
        """Vote on a showcase implementation."""
        voted = await self.showcase.vote_on_showcase(user_id, showcase_id, vote_type)
        return {
            'success': voted,
            'showcase_id': showcase_id,
            'vote_type': vote_type,
            'message': f'Vote recorded successfully'
        }

    async def add_showcase_comment(self, user_id: int, showcase_id: int, comment_text: str,
                                 parent_comment_id: Optional[int] = None) -> Dict[str, Any]:
        """Add a comment to a showcase."""
        comment = await self.showcase.add_comment(user_id, showcase_id, comment_text, parent_comment_id)
        return {
            'comment_id': comment.id,
            'showcase_id': showcase_id,
            'message': 'Comment added successfully'
        }

    async def get_showcase_comments(self, showcase_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get comments for a showcase."""
        return await self.showcase.get_showcase_comments(showcase_id, limit)

    async def get_user_showcases(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all showcases submitted by a user."""
        return await self.showcase.get_user_showcases(user_id)

    async def get_featured_showcases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured showcase implementations."""
        showcases = await self.showcase.get_featured_showcases(limit)
        return [asdict(showcase) for showcase in showcases]

    # Analytics and Statistics

    async def get_peer_learning_stats(self, user_id: Optional[int] = None) -> PeerLearningStats:
        """
        Get comprehensive peer learning statistics.

        Args:
            user_id: Optional user ID to get personal stats

        Returns:
            PeerLearningStats object with aggregated data
        """
        if user_id:
            # Personal stats
            code_reviews_given = await self.code_review.get_user_reviews(user_id, 'given')
            code_reviews_received = await self.code_review.get_user_reviews(user_id, 'received')
            user_sessions = await self.collaboration.get_user_sessions(user_id, True)
            user_showcases = await self.showcase.get_user_showcases(user_id)

            return PeerLearningStats(
                total_code_reviews=len(code_reviews_given) + len(code_reviews_received),
                active_collaboration_sessions=len([s for s in user_sessions if s['status'] == 'active']),
                showcase_implementations=len(user_showcases),
                total_upvotes_received=sum(s.get('upvotes', 0) for s in user_showcases),
                total_helpful_reviews=len([r for r in code_reviews_received if r.get('rating', 0) >= 4]),
                collaboration_hours=sum(
                    (s.get('left_at') - s.get('joined_at')).total_seconds() / 3600
                    for s in user_sessions
                    if s.get('left_at') and s.get('joined_at')
                ),
                top_languages=['python'],  # Placeholder
                most_helpful_topics=['algorithms']  # Placeholder
            )
        else:
            # Global stats
            # This would require more complex queries in production
            return PeerLearningStats(
                total_code_reviews=0,  # Would need to query database
                active_collaboration_sessions=0,
                showcase_implementations=0,
                total_upvotes_received=0,
                total_helpful_reviews=0,
                collaboration_hours=0.0,
                top_languages=[],
                most_helpful_topics=[]
            )

    async def get_user_activity_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get a summary of a user's peer learning activity.

        Args:
            user_id: User ID

        Returns:
            Activity summary dictionary
        """
        reviews_given = await self.code_review.get_user_reviews(user_id, 'given', 100)
        reviews_received = await self.code_review.get_user_reviews(user_id, 'received', 100)
        sessions = await self.collaboration.get_user_sessions(user_id, True)
        showcases = await self.showcase.get_user_showcases(user_id)

        # Calculate reputation score (simplified)
        reputation = (
            len(reviews_given) * 2 +  # Reviews given
            len(reviews_received) * 1 +  # Reviews received
            sum(r.get('rating', 0) for r in reviews_received) +  # Quality of reviews received
            len(showcases) * 5 +  # Showcases submitted
            sum(s.get('upvotes', 0) for s in showcases) * 3  # Community recognition
        )

        return {
            'user_id': user_id,
            'reviews_given': len(reviews_given),
            'reviews_received': len(reviews_received),
            'average_rating_received': (
                sum(r.get('rating', 0) for r in reviews_received) / len(reviews_received)
                if reviews_received else 0
            ),
            'sessions_participated': len(sessions),
            'showcases_submitted': len(showcases),
            'total_showcase_upvotes': sum(s.get('upvotes', 0) for s in showcases),
            'reputation_score': reputation,
            'activity_level': self._calculate_activity_level(reputation),
            'achievements': self._calculate_achievements(user_id, reviews_given, showcases)
        }

    # Private helper methods

    def _calculate_activity_level(self, reputation: int) -> str:
        """Calculate activity level based on reputation."""
        if reputation >= 1000:
            return 'expert'
        elif reputation >= 500:
            return 'advanced'
        elif reputation >= 100:
            return 'intermediate'
        elif reputation >= 25:
            return 'beginner'
        else:
            return 'newcomer'

    def _calculate_achievements(self, user_id: int, reviews_given: List[Dict],
                               showcases: List[Dict]) -> List[str]:
        """Calculate achievements based on user activity."""
        achievements = []

        if len(reviews_given) >= 10:
            achievements.append('Code Reviewer')
        if len(reviews_given) >= 50:
            achievements.append('Senior Reviewer')

        if len(showcases) >= 1:
            achievements.append('Showcase Contributor')
        if len(showcases) >= 5:
            achievements.append('Showcase Expert')

        total_upvotes = sum(s.get('upvotes', 0) for s in showcases)
        if total_upvotes >= 50:
            achievements.append('Community Favorite')
        if total_upvotes >= 100:
            achievements.append('Showcase Legend')

        return achievements

    # Health check and maintenance methods

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all peer learning components."""
        health_status = {
            'code_review': await self._check_code_review_health(),
            'collaboration': await self._check_collaboration_health(),
            'showcase': await self._check_showcase_health(),
            'overall_status': 'healthy'
        }

        # Determine overall status
        if any(component['status'] != 'healthy' for component in health_status.values()
               if isinstance(component, dict) and 'status' in component):
            health_status['overall_status'] = 'degraded'

        return health_status

    async def _check_code_review_health(self) -> Dict[str, Any]:
        """Check code review component health."""
        try:
            # Simple query to check database connectivity
            self.db.query(CodeSubmission).limit(1).all()
            return {'status': 'healthy', 'details': 'Database connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'details': str(e)}

    async def _check_collaboration_health(self) -> Dict[str, Any]:
        """Check collaboration component health."""
        try:
            self.db.query(CollaborationSession).limit(1).all()
            active_sessions = len(self.collaboration.active_sessions)
            return {
                'status': 'healthy',
                'details': f'Database OK, {active_sessions} active sessions'
            }
        except Exception as e:
            return {'status': 'unhealthy', 'details': str(e)}

    async def _check_showcase_health(self) -> Dict[str, Any]:
        """Check showcase component health."""
        try:
            self.db.query(ImplementationShowcase).limit(1).all()
            return {'status': 'healthy', 'details': 'Database connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'details': str(e)}
