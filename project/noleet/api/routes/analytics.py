"""
Analytics API routes for dashboard and insights.

This module provides REST API endpoints for accessing analytics data,
user progress, skills assessment, community metrics, and AI insights.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from noleet.analytics.analytics_service import AnalyticsService
from noleet.app.core.database import get_db
from noleet.app.core.auth import get_current_user
from noleet.app.core.caching import get_cache_manager
from noleet.app.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Pydantic models for request/response
class DashboardResponse(BaseModel):
    user_id: int
    generated_at: str
    progress: Dict[str, Any]
    skills: Dict[str, Any]
    community: Dict[str, Any]
    insights: Dict[str, Any]
    summary: Dict[str, Any]


class ProgressResponse(BaseModel):
    total_projects_completed: int
    total_questions_solved: int
    total_time_spent: int
    current_learning_streak: int
    favorite_topics: List[str]
    recommended_difficulty: str
    learning_velocity: Dict[str, float]


class SkillsResponse(BaseModel):
    overall_level: float
    topic_breakdown: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    learning_trajectory: str
    confidence_score: float
    recommended_focus_areas: List[str]


class CommunityOverviewResponse(BaseModel):
    time_period_days: int
    user_metrics: Dict[str, Any]
    content_metrics: Dict[str, Any]
    topic_analytics: Dict[str, Any]


class InsightsResponse(BaseModel):
    insights: List[Dict[str, Any]]
    overall_summary: str
    next_best_actions: List[str]
    learning_goals: List[str]
    generated_at: str
    ai_model_used: str


@router.get("/dashboard", response_model=DashboardResponse)
async def get_user_dashboard(
    force_refresh: bool = Query(False, description="Bypass cache and regenerate data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get complete dashboard data for the current user.

    Returns comprehensive analytics including progress, skills, community metrics, and AI insights.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        dashboard_data = await analytics_service.get_user_dashboard(
            current_user.id,
            force_refresh=force_refresh
        )
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


@router.get("/progress", response_model=ProgressResponse)
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get detailed learning progress for the current user.

    Includes project completion stats, learning velocity, streaks, and recommendations.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        progress_data = await analytics_service.get_user_progress(current_user.id)
        return progress_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress data: {str(e)}")


@router.get("/skills", response_model=SkillsResponse)
async def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get comprehensive skill assessment for the current user.

    Includes overall skill level, topic breakdown, strengths, weaknesses, and recommendations.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        skills_data = await analytics_service.get_user_skills(current_user.id)
        return skills_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get skills data: {str(e)}")


@router.get("/insights", response_model=InsightsResponse)
async def get_user_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get AI-generated personalized insights and recommendations.

    Includes actionable advice, learning goals, and next best actions.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        insights_data = await analytics_service.get_user_insights(current_user.id)
        return insights_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/community/overview", response_model=CommunityOverviewResponse)
async def get_community_overview(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get community-wide analytics overview.

    Includes user engagement, content metrics, and trending topics.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        community_data = await analytics_service.get_community_overview(days)
        return community_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get community data: {str(e)}")


@router.get("/topics/{topic}")
async def get_topic_analytics(
    topic: str,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get detailed analytics for a specific topic.

    Includes engagement metrics, difficulty distribution, and user skill levels.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        topic_data = await analytics_service.get_topic_analytics(topic, days)
        return topic_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic analytics: {str(e)}")


@router.get("/learning-effectiveness")
async def get_learning_effectiveness(
    days: int = Query(90, description="Number of days to analyze", ge=30, le=365),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get community learning effectiveness metrics.

    Includes completion rates, learning velocity, and engagement statistics.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        effectiveness_data = await analytics_service.get_learning_effectiveness(days)
        return effectiveness_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get effectiveness metrics: {str(e)}")


@router.get("/engagement-insights")
async def get_engagement_insights(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get detailed user engagement insights and patterns.

    Includes activity patterns, user segmentation, and engagement trends.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        engagement_data = await analytics_service.get_user_engagement_insights(days)
        return engagement_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engagement insights: {str(e)}")


@router.get("/leaderboard")
async def get_leaderboard(
    metric: str = Query("skill_level", description="Metric to rank by"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get community leaderboard for various metrics.

    Available metrics: skill_level, projects_completed, streak, etc.
    """
    valid_metrics = ["skill_level", "projects_completed", "streak", "learning_velocity"]

    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
        )

    analytics_service = AnalyticsService(db, cache_manager)

    try:
        leaderboard_data = await analytics_service.get_leaderboard(metric, limit)
        return {"leaderboard": leaderboard_data, "metric": metric, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


@router.get("/trending-content")
async def get_trending_content(
    days: int = Query(7, description="Number of days to analyze trending content", ge=1, le=30),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get trending learning content based on community engagement.

    Returns topics, projects, or other content gaining popularity.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        trending_data = await analytics_service.get_trending_content(days)
        return {"trending_content": trending_data, "analyzed_days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending content: {str(e)}")


@router.post("/invalidate-cache")
async def invalidate_user_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Invalidate cached analytics data for the current user.

    Forces fresh data generation on next analytics requests.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        await analytics_service.invalidate_user_cache(current_user.id)
        return {"message": "User cache invalidated successfully", "user_id": current_user.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.get("/learning-patterns")
async def analyze_learning_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache_manager=Depends(get_cache_manager)
):
    """
    Get advanced learning pattern analysis for the current user.

    Includes peak learning times, improvement velocity, and learning style inference.
    """
    analytics_service = AnalyticsService(db, cache_manager)

    try:
        patterns_data = await analytics_service.analyze_learning_patterns(current_user.id)
        return patterns_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze learning patterns: {str(e)}")


# WebSocket endpoint for real-time analytics updates (would be implemented separately)
# @router.websocket("/ws/dashboard")
# async def dashboard_websocket(websocket: WebSocket, current_user: User = Depends(get_current_user)):
#     """WebSocket endpoint for real-time dashboard updates."""
#     # Implementation would go here with proper WebSocket handling
#     pass
