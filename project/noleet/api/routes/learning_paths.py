"""
Learning Paths API routes.

This module provides REST API endpoints for learning path operations,
including browsing, creation, enrollment, progress tracking, and recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from learning_paths.path_engine import PathEngine
from learning_paths.path_recommender import PathRecommender
from learning_paths.community_paths import CommunityPathManager
from noleet.app.core.database import get_db
from noleet.app.core.auth import get_current_user
from noleet.app.core.caching import get_cache_manager
from noleet.app.models import User

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


# Pydantic models for request/response
class PathCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=20)
    difficulty: str = Field(..., examples=["easy", "medium", "hard"])
    tags: List[str] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class PathUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=20)
    difficulty: Optional[str] = Field(None, examples=["easy", "medium", "hard"])
    tags: Optional[List[str]] = None


class PathResponse(BaseModel):
    path_id: int
    title: str
    description: str
    difficulty: str
    estimated_duration: Optional[int]
    total_projects: int
    tags: List[str]
    creator_id: Optional[int]
    is_community_created: bool
    upvotes: int
    created_at: str
    enrolled_users_count: int = 0
    average_completion_rate: float = 0.0
    average_completion_time: int = 0


class PathDetailResponse(PathResponse):
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class PathRecommendationResponse(BaseModel):
    path_id: int
    path_title: str
    path_description: str
    difficulty: str
    estimated_duration: int
    total_projects: int
    recommendation_score: float
    reasoning: str
    matching_topics: List[str]
    skill_gaps_addressed: List[str]


class EnrollmentResponse(BaseModel):
    enrollment_id: int
    path_id: int
    enrolled_at: str
    progress_percentage: float
    completed_at: Optional[str]
    current_step_id: Optional[int]


class ProgressResponse(BaseModel):
    enrollment_id: int
    path_id: int
    current_step: Optional[int]
    progress_percentage: float
    total_time_spent: int
    last_activity: Optional[str]
    completed_steps: List[int]
    remaining_steps: List[int]


class PathValidationResponse(BaseModel):
    is_valid: bool
    score: float
    issues: List[str]
    suggestions: List[str]
    quality_score: float


# Routes

@router.post("/", response_model=PathResponse)
async def create_learning_path(
    path_data: PathCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Create a new learning path.

    Returns the created path information.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        path = await path_engine.create_path(
            title=path_data.title,
            description=path_data.description,
            creator_id=current_user.id,
            difficulty=path_data.difficulty,
            tags=path_data.tags,
            steps=path_data.steps
        )

        # Get full path data
        path_detail = await path_engine.get_path(path.id)
        if not path_detail:
            raise HTTPException(status_code=500, detail="Failed to retrieve created path")

        return PathResponse(**path_detail.__dict__)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create path: {str(e)}")


@router.get("/{path_id}", response_model=PathDetailResponse)
async def get_learning_path(
    path_id: int,
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get detailed information about a specific learning path.

    Includes all steps and metadata.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        path_data = await path_engine.get_path(path_id)
        if not path_data:
            raise HTTPException(status_code=404, detail="Path not found")

        return PathDetailResponse(**path_data.__dict__)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get path: {str(e)}")


@router.get("/", response_model=List[PathResponse])
async def list_learning_paths(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    difficulty: Optional[str] = Query(None, examples=["easy", "medium", "hard"]),
    tag: Optional[str] = Query(None),
    creator_id: Optional[int] = Query(None),
    sort_by: str = Query("upvotes", examples=["upvotes", "created_at", "completion_rate"]),
    sort_order: str = Query("desc", examples=["asc", "desc"]),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    List learning paths with optional filtering and sorting.

    Supports pagination, filtering by difficulty/tag/creator, and sorting.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        # This would implement proper filtering and pagination
        # For now, return a basic list
        paths = [
            {
                'path_id': 1,
                'title': 'Dynamic Programming Mastery',
                'description': 'Master dynamic programming through practical projects',
                'difficulty': 'hard',
                'estimated_duration': 8,
                'total_projects': 12,
                'tags': ['dynamic-programming', 'algorithms'],
                'creator_id': 1,
                'is_community_created': True,
                'upvotes': 45,
                'created_at': '2024-01-01T00:00:00Z',
                'enrolled_users_count': 245,
                'average_completion_rate': 0.75,
                'average_completion_time': 56
            }
        ]

        # Apply filtering
        if difficulty:
            paths = [p for p in paths if p['difficulty'] == difficulty]
        if tag:
            paths = [p for p in paths if tag in p['tags']]
        if creator_id:
            paths = [p for p in paths if p['creator_id'] == creator_id]

        # Apply sorting
        reverse = sort_order == 'desc'
        if sort_by == 'upvotes':
            paths.sort(key=lambda x: x['upvotes'], reverse=reverse)
        elif sort_by == 'created_at':
            paths.sort(key=lambda x: x['created_at'], reverse=reverse)
        elif sort_by == 'completion_rate':
            paths.sort(key=lambda x: x['average_completion_rate'], reverse=reverse)

        # Apply pagination
        paths = paths[skip:skip + limit]

        return [PathResponse(**path) for path in paths]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list paths: {str(e)}")


@router.post("/{path_id}/enroll", response_model=EnrollmentResponse)
async def enroll_in_path(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Enroll the current user in a learning path.

    Returns enrollment information.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        enrollment = await path_engine.enroll_user(current_user.id, path_id)

        return EnrollmentResponse(
            enrollment_id=enrollment.id,
            path_id=enrollment.path_id,
            enrolled_at=enrollment.enrolled_at.isoformat(),
            progress_percentage=enrollment.progress_percentage,
            completed_at=enrollment.completed_at.isoformat() if enrollment.completed_at else None,
            current_step_id=enrollment.current_step_id
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enroll: {str(e)}")


@router.get("/{path_id}/progress", response_model=ProgressResponse)
async def get_path_progress(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get the current user's progress in a specific learning path.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        progress = await path_engine.get_user_progress(current_user.id, path_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Not enrolled in this path")

        return ProgressResponse(**progress.__dict__)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.post("/{path_id}/progress/{step_id}")
async def update_path_progress(
    path_id: int,
    step_id: int,
    completed: bool = Query(True, description="Mark step as completed"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Update progress in a learning path by marking a step as completed.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        enrollment = await path_engine.update_progress(
            current_user.id, path_id, step_id, completed
        )

        return {
            "message": "Progress updated successfully",
            "enrollment_id": enrollment.id,
            "progress_percentage": enrollment.progress_percentage,
            "current_step_id": enrollment.current_step_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.get("/recommendations", response_model=List[PathRecommendationResponse])
async def get_path_recommendations(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get personalized learning path recommendations for the current user.

    Uses AI to analyze user skills, progress, and preferences.
    """
    path_recommender = PathRecommender(db, cache_manager)

    try:
        recommendations = await path_recommender.get_recommendations(
            current_user.id, limit
        )

        return [PathRecommendationResponse(**rec.__dict__) for rec in recommendations]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/{path_id}/success-prediction")
async def predict_path_success(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Predict the user's success probability for a specific path.

    Provides completion probability and recommendations for success.
    """
    path_recommender = PathRecommender(db, cache_manager)

    try:
        prediction = await path_recommender.get_path_success_prediction(
            current_user.id, path_id
        )

        return prediction

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict success: {str(e)}")


@router.post("/community/submit", response_model=Dict[str, Any])
async def submit_community_path(
    path_data: PathCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Submit a new community-created learning path for review.

    Returns path information and validation results.
    """
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        path, validation = await community_manager.submit_community_path(
            current_user.id, path_data.dict()
        )

        return {
            "path_id": path.id,
            "title": path.title,
            "status": "submitted",
            "validation": {
                "is_valid": validation.is_valid,
                "quality_score": validation.quality_score,
                "issues": validation.issues,
                "suggestions": validation.suggestions
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit path: {str(e)}")


@router.post("/community/{path_id}/vote")
async def vote_on_path(
    path_id: int,
    vote_type: str = Query(..., examples=["upvote", "downvote"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Cast a vote on a community path.
    """
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        success = community_manager.vote_on_path(current_user.id, path_id, vote_type)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to cast vote")

        return {"message": f"Successfully {vote_type}d path", "path_id": path_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to vote: {str(e)}")


@router.get("/community/pending-review")
async def get_pending_reviews(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get community paths pending review (moderator endpoint).

    Requires moderator privileges.
    """
    # TODO: Add moderator permission check
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        pending_paths = await community_manager.get_pending_reviews(limit)
        return {"pending_reviews": pending_paths}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending reviews: {str(e)}")


@router.post("/community/{path_id}/approve")
async def approve_path(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Approve a community path for publication (moderator endpoint).
    """
    # TODO: Add moderator permission check
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        success = await community_manager.approve_path(path_id, current_user.id)

        if not success:
            raise HTTPException(status_code=404, detail="Path not found")

        return {"message": "Path approved successfully", "path_id": path_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve path: {str(e)}")


@router.post("/validate")
async def validate_path(
    path_data: PathCreateRequest,
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Validate a learning path without creating it.

    Returns validation results and quality metrics.
    """
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        validation = await community_manager.validate_path_data(path_data.dict())

        return PathValidationResponse(**validation.__dict__)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate path: {str(e)}")


@router.get("/community/top-contributors")
async def get_top_contributors(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get top community path contributors.

    Ranks users by path creation quality and community engagement.
    """
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        contributors = community_manager.get_top_contributors(limit)
        return {"contributors": contributors}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contributors: {str(e)}")


@router.get("/community/{path_id}/improvements")
async def suggest_path_improvements(
    path_id: int,
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get AI-powered suggestions for improving an existing path.
    """
    community_manager = CommunityPathManager(db, cache_manager)

    try:
        suggestions = await community_manager.suggest_path_improvements(path_id)
        return suggestions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get improvements: {str(e)}")


@router.post("/generate-from-topics")
async def generate_path_from_topics(
    topics: List[str] = Body(..., examples=[["dynamic-programming", "algorithms"]]),
    difficulty: str = Query("intermediate", examples=["easy", "medium", "hard"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Generate a complete learning path from a list of topics using AI.

    Creates a structured path with logical progression and detailed steps.
    """
    path_engine = PathEngine(db, cache_manager)

    try:
        path = await path_engine.generate_path_from_topics(
            topics, current_user.id, difficulty
        )

        return {
            "message": "Path generated successfully",
            "path_id": path.id,
            "title": path.title,
            "topics": topics,
            "difficulty": difficulty
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate path: {str(e)}")
