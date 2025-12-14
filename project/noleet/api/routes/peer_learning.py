"""
API Routes for Peer Learning Features.

This module provides REST API endpoints for:
- Code Review System
- Live Collaboration Sessions
- Implementation Showcase Gallery
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from peer_learning.peer_learning_service import PeerLearningService
from noleet.app.core.database import get_db
from noleet.app.core.auth import get_current_user
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/peer-learning", tags=["peer-learning"])


# Pydantic models for request/response
class CodeSubmissionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    code_content: str = Field(..., min_length=10, max_length=50000)
    language: str = "python"
    difficulty_level: str = "medium"
    topics: List[str] = Field(default_factory=list)
    project_id: Optional[int] = None


class CodeReviewFeedbackRequest(BaseModel):
    overall_rating: int = Field(..., ge=1, le=5)
    feedback_text: str = ""
    feedback_categories: List[str] = Field(default_factory=list)
    detailed_feedback: Dict[str, Any] = Field(default_factory=dict)
    comments: List[Dict[str, Any]] = Field(default_factory=list)


class CollaborationSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    session_type: str = "pair_programming"
    max_participants: int = Field(2, ge=2, le=10)
    scheduled_start: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    is_public: bool = True


class SessionMessageRequest(BaseModel):
    message_type: str = "text"
    message_content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str = ""


class ShowcaseSubmissionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    code_content: str = Field(..., min_length=50, max_length=50000)
    language: str = "python"
    difficulty_level: str = "medium"
    topics: List[str] = Field(default_factory=list)
    approach_description: Optional[str] = ""
    key_insights: List[str] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[int] = None


class ShowcaseCommentRequest(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[int] = None


# Dependency injection
def get_peer_learning_service(db: Session = Depends(get_db)) -> PeerLearningService:
    """Get PeerLearningService instance."""
    from noleet.app.core.caching import CacheManager
    cache_manager = CacheManager()  # In production, inject from DI container
    return PeerLearningService(db, cache_manager)


# Code Review Endpoints
@router.post("/code-review/submit", response_model=Dict[str, Any])
async def submit_code_for_review(
    request: CodeSubmissionRequest,
    background_tasks: BackgroundTasks,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit code for peer review.

    Automatically assigns reviewers and initiates the review process.
    """
    try:
        result = await service.submit_code_for_review(current_user["user_id"], request.dict())

        # Background task to auto-assign reviewers (if not done synchronously)
        background_tasks.add_task(
            _notify_reviewers,
            result["submission_id"],
            service,
            current_user["user_id"]
        )

        return result
    except Exception as e:
        logger.error(f"Code submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submission failed: {str(e)}"
        )


@router.get("/code-review/available", response_model=List[Dict[str, Any]])
async def get_available_reviews(
    limit: int = 10,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get code submissions available for review by the current user."""
    try:
        return await service.get_available_reviews(current_user["user_id"], limit)
    except Exception as e:
        logger.error(f"Failed to get available reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available reviews"
        )


@router.post("/code-review/{submission_id}/start", response_model=Dict[str, Any])
async def start_code_review(
    submission_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start reviewing a specific code submission."""
    try:
        result = await service.start_code_review(current_user["user_id"], submission_id)
        return result
    except Exception as e:
        logger.error(f"Failed to start review: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start review: {str(e)}"
        )


@router.post("/code-review/{review_id}/feedback", response_model=Dict[str, Any])
async def submit_review_feedback(
    review_id: int,
    feedback: CodeReviewFeedbackRequest,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit feedback for a completed code review."""
    try:
        result = await service.submit_review_feedback(review_id, feedback.dict())
        return result
    except Exception as e:
        logger.error(f"Failed to submit review feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/code-review/my-reviews", response_model=Dict[str, List[Dict[str, Any]]])
async def get_user_reviews(
    review_type: str = "given",
    limit: int = 20,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get reviews given or received by the current user."""
    if review_type not in ["given", "received"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="review_type must be 'given' or 'received'"
        )

    try:
        reviews = await service.get_user_reviews(current_user["user_id"], review_type, limit)
        return {review_type: reviews}
    except Exception as e:
        logger.error(f"Failed to get user reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user reviews"
        )


@router.get("/code-review/{submission_id}/ai-feedback", response_model=Dict[str, Any])
async def get_ai_feedback(
    submission_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate AI-powered feedback for a code submission."""
    try:
        feedback = await service.generate_ai_feedback(submission_id)
        return feedback
    except Exception as e:
        logger.error(f"Failed to generate AI feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI feedback"
        )


# Live Collaboration Endpoints
@router.post("/collaboration/sessions", response_model=Dict[str, Any])
async def create_collaboration_session(
    request: CollaborationSessionRequest,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new collaboration session."""
    try:
        result = await service.create_collaboration_session(current_user["user_id"], request.dict())
        return result
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session creation failed: {str(e)}"
        )


@router.post("/collaboration/sessions/{session_id}/join", response_model=Dict[str, Any])
async def join_collaboration_session(
    session_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Join a collaboration session."""
    try:
        result = await service.join_session(current_user["user_id"], session_id)
        return result
    except Exception as e:
        logger.error(f"Failed to join session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to join session: {str(e)}"
        )


@router.post("/collaboration/sessions/{session_id}/leave", response_model=Dict[str, Any])
async def leave_collaboration_session(
    session_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Leave a collaboration session."""
    try:
        result = await service.leave_session(current_user["user_id"], session_id)
        return result
    except Exception as e:
        logger.error(f"Failed to leave session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to leave session: {str(e)}"
        )


@router.post("/collaboration/sessions/{session_id}/start", response_model=Dict[str, Any])
async def start_collaboration_session(
    session_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start a scheduled collaboration session."""
    try:
        result = await service.start_session(session_id, current_user["user_id"])
        return result
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/collaboration/sessions/{session_id}/end", response_model=Dict[str, Any])
async def end_collaboration_session(
    session_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """End a collaboration session."""
    try:
        result = await service.end_session(session_id)
        return result
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to end session: {str(e)}"
        )


@router.post("/collaboration/sessions/{session_id}/messages", response_model=Dict[str, Any])
async def send_session_message(
    session_id: int,
    message: SessionMessageRequest,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Send a message in a collaboration session."""
    try:
        result = await service.send_session_message(session_id, current_user["user_id"], message.dict())
        return result
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/collaboration/sessions/{session_id}", response_model=Optional[Dict[str, Any]])
async def get_session_data(
    session_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a collaboration session."""
    try:
        session_data = await service.get_session_data(session_id)
        return session_data
    except Exception as e:
        logger.error(f"Failed to get session data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session data"
        )


@router.get("/collaboration/sessions/active", response_model=List[Dict[str, Any]])
async def get_active_sessions(
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all active collaboration sessions."""
    try:
        sessions = await service.get_active_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )


@router.get("/collaboration/sessions/my", response_model=List[Dict[str, Any]])
async def get_user_sessions(
    include_past: bool = False,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get collaboration sessions for the current user."""
    try:
        sessions = await service.get_user_sessions(current_user["user_id"], include_past)
        return sessions
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )


@router.post("/collaboration/sessions/{session_id}/feedback", response_model=Dict[str, Any])
async def submit_session_feedback(
    session_id: int,
    feedback: SessionFeedbackRequest,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit feedback for a completed collaboration session."""
    try:
        result = await service.update_session_feedback(
            session_id, current_user["user_id"], feedback.rating, feedback.feedback
        )
        return result
    except Exception as e:
        logger.error(f"Failed to submit session feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# Showcase Gallery Endpoints
@router.post("/showcase/submit", response_model=Dict[str, Any])
async def submit_showcase(
    request: ShowcaseSubmissionRequest,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit an implementation to the showcase gallery."""
    try:
        result = await service.submit_showcase(current_user["user_id"], request.dict())
        return result
    except Exception as e:
        logger.error(f"Showcase submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submission failed: {str(e)}"
        )


@router.get("/showcase/gallery", response_model=List[Dict[str, Any]])
async def get_showcase_gallery(
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
    featured: Optional[bool] = None,
    sort_by: str = "upvotes",
    limit: int = 50,
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """Get showcases from the gallery with optional filtering."""
    filters = {}
    if language:
        filters['language'] = language
    if difficulty:
        filters['difficulty'] = difficulty
    if topic:
        filters['topic'] = topic
    if featured is not None:
        filters['featured'] = featured

    try:
        showcases = await service.get_gallery_showcases(filters, sort_by, limit)
        return showcases
    except Exception as e:
        logger.error(f"Failed to get showcase gallery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve showcase gallery"
        )


@router.get("/showcase/{showcase_id}", response_model=Optional[Dict[str, Any]])
async def get_showcase_details(
    showcase_id: int,
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """Get detailed information about a specific showcase."""
    try:
        showcase = await service.get_showcase_details(showcase_id)
        return showcase
    except Exception as e:
        logger.error(f"Failed to get showcase details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve showcase details"
        )


@router.post("/showcase/{showcase_id}/vote", response_model=Dict[str, Any])
async def vote_on_showcase(
    showcase_id: int,
    vote_type: str,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Vote on a showcase implementation."""
    if vote_type not in ["upvote", "downvote"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vote_type must be 'upvote' or 'downvote'"
        )

    try:
        result = await service.vote_on_showcase(current_user["user_id"], showcase_id, vote_type)
        return result
    except Exception as e:
        logger.error(f"Failed to vote on showcase: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vote failed: {str(e)}"
        )


@router.post("/showcase/{showcase_id}/comments", response_model=Dict[str, Any])
async def add_showcase_comment(
    showcase_id: int,
    comment: ShowcaseCommentRequest,
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a comment to a showcase."""
    try:
        result = await service.add_showcase_comment(
            current_user["user_id"], showcase_id,
            comment.comment_text, comment.parent_comment_id
        )
        return result
    except Exception as e:
        logger.error(f"Failed to add showcase comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.get("/showcase/{showcase_id}/comments", response_model=List[Dict[str, Any]])
async def get_showcase_comments(
    showcase_id: int,
    limit: int = 50,
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """Get comments for a showcase."""
    try:
        comments = await service.get_showcase_comments(showcase_id, limit)
        return comments
    except Exception as e:
        logger.error(f"Failed to get showcase comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve showcase comments"
        )


@router.get("/showcase/my", response_model=List[Dict[str, Any]])
async def get_user_showcases(
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all showcases submitted by the current user."""
    try:
        showcases = await service.get_user_showcases(current_user["user_id"])
        return showcases
    except Exception as e:
        logger.error(f"Failed to get user showcases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user showcases"
        )


@router.get("/showcase/featured", response_model=List[Dict[str, Any]])
async def get_featured_showcases(
    limit: int = 10,
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """Get featured showcase implementations."""
    try:
        showcases = await service.get_featured_showcases(limit)
        return showcases
    except Exception as e:
        logger.error(f"Failed to get featured showcases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve featured showcases"
        )


# Analytics and Statistics Endpoints
@router.get("/stats", response_model=Dict[str, Any])
async def get_peer_learning_stats(
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get peer learning statistics for the current user."""
    try:
        stats = await service.get_peer_learning_stats(current_user["user_id"])
        return {
            'user_id': current_user["user_id"],
            'total_code_reviews': stats.total_code_reviews,
            'active_collaboration_sessions': stats.active_collaboration_sessions,
            'showcase_implementations': stats.showcase_implementations,
            'total_upvotes_received': stats.total_upvotes_received,
            'total_helpful_reviews': stats.total_helpful_reviews,
            'collaboration_hours': stats.collaboration_hours,
            'top_languages': stats.top_languages,
            'most_helpful_topics': stats.most_helpful_topics
        }
    except Exception as e:
        logger.error(f"Failed to get peer learning stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve peer learning statistics"
        )


@router.get("/activity-summary", response_model=Dict[str, Any])
async def get_user_activity_summary(
    service: PeerLearningService = Depends(get_peer_learning_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a comprehensive activity summary for the current user."""
    try:
        summary = await service.get_user_activity_summary(current_user["user_id"])
        return summary
    except Exception as e:
        logger.error(f"Failed to get activity summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity summary"
        )


@router.get("/health", response_model=Dict[str, Any])
async def peer_learning_health_check(
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """Health check for peer learning components."""
    try:
        health = await service.health_check()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': str(datetime.now())
        }


# Background task functions
async def _notify_reviewers(submission_id: int, service: PeerLearningService, submitter_id: int):
    """Background task to notify reviewers of new submission."""
    try:
        # This would integrate with notification system
        logger.info(f"Notifying reviewers for submission {submission_id}")

        # Get submission details
        # Get assigned reviewers
        # Send notifications (email, in-app, etc.)

        # For now, just log
        logger.info(f"Reviewers notified for submission {submission_id} by user {submitter_id}")

    except Exception as e:
        logger.error(f"Failed to notify reviewers for submission {submission_id}: {e}")


# WebSocket endpoints would be added here for real-time features
# @router.websocket("/collaboration/ws/{session_id}")
# async def collaboration_websocket(websocket: WebSocket, session_id: int):
#     """WebSocket endpoint for real-time collaboration."""
#     # Implementation would go here for live editing, cursor positions, etc.
