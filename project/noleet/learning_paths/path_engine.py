"""
Learning Path Engine - Core logic for managing learning paths.

This module provides the main engine for creating, managing, and tracking
progress through learning paths in NoLeet.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from learning_paths.models import (
    LearningPath, LearningPathStep, UserPathEnrollment,
    PathRecommendation, PathStepData, PathProgressData,
    LearningPathData, PathRecommendationData
)
from noleet.analytics.skill_assessor import SkillAssessor
from noleet.analytics.progress_calculator import ProgressCalculator
from noleet.llm.llm_factory import LLMFactory
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


class PathEngine:
    """Core engine for learning path operations."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager
        self.skill_assessor = SkillAssessor(db_session)
        self.progress_calc = ProgressCalculator(db_session)
        self.llm_factory = LLMFactory()

        # Cache TTL settings
        self.CACHE_TTL = {
            'path_data': 3600,      # 1 hour
            'user_progress': 1800,  # 30 minutes
            'recommendations': 7200, # 2 hours
        }

    async def create_path(self, title: str, description: str, creator_id: int,
                         difficulty: str = 'intermediate', tags: List[str] = None,
                         steps: List[Dict[str, Any]] = None) -> LearningPath:
        """
        Create a new learning path.

        Args:
            title: Path title
            description: Path description
            creator_id: User ID of creator
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            tags: List of topic tags
            steps: List of step definitions

        Returns:
            Created LearningPath object
        """
        logger.info(f"Creating learning path: {title}")

        # Validate inputs
        if not title or not description:
            raise ValueError("Title and description are required")

        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'")

        # Create path
        path = LearningPath(
            title=title,
            slug=self._generate_slug(title),
            description=description,
            difficulty=difficulty,
            tags=tags or [],
            creator_id=creator_id,
            is_community_created=(creator_id is not None),
            metadata={'version': '1.0', 'auto_generated': False}
        )

        self.db.add(path)
        self.db.flush()  # Get path ID

        # Create steps if provided
        if steps:
            for i, step_data in enumerate(steps):
                step = LearningPathStep(
                    path_id=path.id,
                    step_order=i + 1,
                    title=step_data.get('title', f'Step {i + 1}'),
                    description=step_data.get('description', ''),
                    project_id=step_data.get('project_id'),
                    required_skills=step_data.get('required_skills', []),
                    estimated_time=step_data.get('estimated_time', 60),
                    prerequisites=step_data.get('prerequisites', {})
                )
                self.db.add(step)

            # Update total projects count
            path.total_projects = sum(1 for s in steps if s.get('project_id'))

        self.db.commit()

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"path_data:{path.id}")

        logger.info(f"Created learning path {path.id}: {title}")
        return path

    async def get_path(self, path_id: int) -> Optional[LearningPathData]:
        """
        Get complete path data by ID.

        Args:
            path_id: Path ID

        Returns:
            LearningPathData object or None if not found
        """
        cache_key = f"path_data:{path_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Query database
        path = self.db.query(LearningPath).filter(LearningPath.id == path_id).first()
        if not path:
            return None

        # Get steps
        steps = []
        for step in path.steps:
            step_data = PathStepData(
                step_id=step.id,
                order=step.step_order,
                title=step.title,
                description=step.description,
                project_id=step.project_id,
                required_skills=step.required_skills or [],
                estimated_time=step.estimated_time,
                prerequisites=step.prerequisites or {}
            )
            steps.append(step_data)

        # Get enrollment stats
        enrollment_stats = self.db.query(
            func.count(UserPathEnrollment.id).label('total_enrollments'),
            func.avg(UserPathEnrollment.progress_percentage).label('avg_progress'),
            func.avg(func.extract('epoch', UserPathEnrollment.completed_at - UserPathEnrollment.enrolled_at) / 86400).label('avg_completion_days')
        ).filter(UserPathEnrollment.path_id == path_id).first()

        path_data = LearningPathData(
            path_id=path.id,
            title=path.title,
            description=path.description,
            difficulty=path.difficulty,
            estimated_duration=path.estimated_duration,
            total_projects=path.total_projects,
            tags=path.tags or [],
            creator_id=path.creator_id,
            is_community_created=path.is_community_created,
            upvotes=path.upvotes,
            created_at=path.created_at,
            steps=steps,
            enrolled_users_count=enrollment_stats.total_enrollments or 0,
            average_completion_rate=enrollment_stats.avg_progress or 0.0,
            average_completion_time=int(enrollment_stats.avg_completion_days or 0)
        )

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, path_data, ttl=self.CACHE_TTL['path_data'])

        return path_data

    async def enroll_user(self, user_id: int, path_id: int) -> UserPathEnrollment:
        """
        Enroll a user in a learning path.

        Args:
            user_id: User ID
            path_id: Path ID

        Returns:
            UserPathEnrollment object
        """
        logger.info(f"Enrolling user {user_id} in path {path_id}")

        # Check if already enrolled
        existing = self.db.query(UserPathEnrollment).filter(
            and_(
                UserPathEnrollment.user_id == user_id,
                UserPathEnrollment.path_id == path_id
            )
        ).first()

        if existing:
            raise ValueError(f"User {user_id} is already enrolled in path {path_id}")

        # Create enrollment
        enrollment = UserPathEnrollment(
            user_id=user_id,
            path_id=path_id,
            enrolled_at=datetime.now(),
            progress_percentage=0.0,
            metadata={'enrollment_type': 'user_initiated'}
        )

        self.db.add(enrollment)
        self.db.commit()

        # Invalidate caches
        if self.cache:
            await self.cache.delete(f"user_progress:{user_id}:{path_id}")
            await self.cache.delete(f"path_data:{path_id}")

        logger.info(f"Enrolled user {user_id} in path {path_id}")
        return enrollment

    async def update_progress(self, user_id: int, path_id: int, step_id: int,
                            completed: bool = True) -> UserPathEnrollment:
        """
        Update user progress in a learning path.

        Args:
            user_id: User ID
            path_id: Path ID
            step_id: Step ID that was completed
            completed: Whether the step was completed

        Returns:
            Updated UserPathEnrollment
        """
        # Get enrollment
        enrollment = self.db.query(UserPathEnrollment).filter(
            and_(
                UserPathEnrollment.user_id == user_id,
                UserPathEnrollment.path_id == path_id
            )
        ).first()

        if not enrollment:
            raise ValueError(f"User {user_id} is not enrolled in path {path_id}")

        # Get path data
        path_data = await self.get_path(path_id)
        if not path_data:
            raise ValueError(f"Path {path_id} not found")

        # Update step completion
        if completed:
            enrollment.current_step_id = step_id
            enrollment.last_activity_at = datetime.now()

            # Calculate progress percentage
            completed_steps = sum(1 for step in path_data.steps if step.is_completed)
            if completed_steps < len(path_data.steps):
                enrollment.progress_percentage = (completed_steps / len(path_data.steps)) * 100
            else:
                # Path completed
                enrollment.progress_percentage = 100.0
                enrollment.completed_at = datetime.now()

        self.db.commit()

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"user_progress:{user_id}:{path_id}")

        logger.info(f"Updated progress for user {user_id} in path {path_id}: {enrollment.progress_percentage}%")
        return enrollment

    async def get_user_progress(self, user_id: int, path_id: int) -> Optional[PathProgressData]:
        """
        Get user's progress in a specific learning path.

        Args:
            user_id: User ID
            path_id: Path ID

        Returns:
            PathProgressData or None
        """
        cache_key = f"user_progress:{user_id}:{path_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Get enrollment
        enrollment = self.db.query(UserPathEnrollment).filter(
            and_(
                UserPathEnrollment.user_id == user_id,
                UserPathEnrollment.path_id == path_id
            )
        ).first()

        if not enrollment:
            return None

        # Get path data
        path_data = await self.get_path(path_id)
        if not path_data:
            return None

        # Determine completed and remaining steps
        completed_steps = []
        remaining_steps = []

        # This would typically come from a separate completion tracking table
        # For now, use current step as approximation
        current_step_order = 0
        if enrollment.current_step_id:
            current_step = self.db.query(LearningPathStep).filter(
                LearningPathStep.id == enrollment.current_step_id
            ).first()
            if current_step:
                current_step_order = current_step.step_order

        for step in path_data.steps:
            if step.order <= current_step_order:
                completed_steps.append(step.step_id)
            else:
                remaining_steps.append(step.step_id)

        progress_data = PathProgressData(
            enrollment_id=enrollment.id,
            path_id=path_id,
            current_step=enrollment.current_step_id,
            progress_percentage=enrollment.progress_percentage,
            total_time_spent=enrollment.total_time_spent,
            last_activity=enrollment.last_activity_at,
            completed_steps=completed_steps,
            remaining_steps=remaining_steps
        )

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, progress_data, ttl=self.CACHE_TTL['user_progress'])

        return progress_data

    async def recommend_paths(self, user_id: int, limit: int = 5) -> List[PathRecommendationData]:
        """
        Recommend learning paths for a user based on their skills and progress.

        Args:
            user_id: User ID
            limit: Maximum number of recommendations

        Returns:
            List of PathRecommendationData objects
        """
        cache_key = f"user_recommendations:{user_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Get user skills and progress
        user_skills = self.skill_assessor.assess_user_skills(user_id)
        user_progress = self.progress_calc.calculate_user_progress(user_id)

        # Get all available paths
        paths = self.db.query(LearningPath).filter(
            LearningPath.is_community_created == True
        ).all()

        recommendations = []

        for path in paths:
            # Skip if user is already enrolled
            enrolled = self.db.query(UserPathEnrollment).filter(
                and_(
                    UserPathEnrollment.user_id == user_id,
                    UserPathEnrollment.path_id == path.id
                )
            ).first()

            if enrolled:
                continue

            # Calculate recommendation score
            score, reasoning = await self._calculate_path_recommendation_score(
                user_skills, user_progress, path
            )

            if score > 0.3:  # Only recommend if score > 0.3
                # Find matching topics and skill gaps
                path_topics = set(path.tags or [])
                user_topics = set(user_progress.favorite_topics)
                matching_topics = list(path_topics.intersection(user_topics))

                skill_gaps = []
                if path.difficulty == 'easy' and user_skills.overall_level > 0.8:
                    skill_gaps.append("May be too easy for your current level")
                elif path.difficulty == 'hard' and user_skills.overall_level < 0.4:
                    skill_gaps.append("May be too challenging for your current level")

                recommendation = PathRecommendationData(
                    path_id=path.id,
                    path_title=path.title,
                    path_description=path.description,
                    difficulty=path.difficulty,
                    estimated_duration=path.estimated_duration,
                    total_projects=path.total_projects,
                    recommendation_score=round(score, 3),
                    reasoning=reasoning,
                    matching_topics=matching_topics,
                    skill_gaps_addressed=skill_gaps
                )

                recommendations.append(recommendation)

        # Sort by score and limit results
        recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
        top_recommendations = recommendations[:limit]

        # Cache results
        if self.cache:
            await self.cache.set(cache_key, top_recommendations, ttl=self.CACHE_TTL['recommendations'])

        return top_recommendations

    async def _calculate_path_recommendation_score(self, user_skills, user_progress,
                                                path: LearningPath) -> Tuple[float, str]:
        """
        Calculate recommendation score for a path.

        Returns:
            Tuple of (score, reasoning)
        """
        score = 0.0
        reasons = []

        # Difficulty match (30% weight)
        difficulty_score = self._calculate_difficulty_match(user_skills.overall_level, path.difficulty)
        score += difficulty_score * 0.3
        reasons.append(f"Difficulty match: {difficulty_score:.1f}")

        # Topic relevance (40% weight)
        topic_score = self._calculate_topic_relevance(user_progress.favorite_topics, path.tags or [])
        score += topic_score * 0.4
        reasons.append(f"Topic relevance: {topic_score:.1f}")

        # Skill gap coverage (20% weight)
        gap_score = self._calculate_skill_gap_coverage(user_skills.weaknesses, path.tags or [])
        score += gap_score * 0.2
        reasons.append(f"Skill gap coverage: {gap_score:.1f}")

        # Community rating (10% weight)
        rating_score = min(path.upvotes / 10.0, 1.0)  # Cap at 10 upvotes = max score
        score += rating_score * 0.1
        reasons.append(f"Community rating: {rating_score:.1f}")

        reasoning = f"Recommended because: {'; '.join(reasons)}. Overall match: {score:.1%}"

        return score, reasoning

    def _calculate_difficulty_match(self, user_level: float, path_difficulty: str) -> float:
        """Calculate how well path difficulty matches user skill level."""
        difficulty_levels = {'easy': 0.3, 'medium': 0.6, 'hard': 0.9}

        target_level = difficulty_levels.get(path_difficulty, 0.6)
        difference = abs(user_level - target_level)

        # Perfect match = 1.0, large gap = 0.0
        return max(0, 1.0 - difference)

    def _calculate_topic_relevance(self, user_topics: List[str], path_topics: List[str]) -> float:
        """Calculate topic relevance based on overlap."""
        if not user_topics or not path_topics:
            return 0.0

        user_set = set(user_topics)
        path_set = set(path_topics)

        overlap = len(user_set.intersection(path_set))
        union = len(user_set.union(path_set))

        return overlap / union if union > 0 else 0.0

    def _calculate_skill_gap_coverage(self, user_weaknesses: List[str], path_topics: List[str]) -> float:
        """Calculate how well path addresses user's skill gaps."""
        if not user_weaknesses or not path_topics:
            return 0.0

        weakness_set = set(user_weaknesses)
        path_set = set(path_topics)

        coverage = len(weakness_set.intersection(path_set))
        return coverage / len(weakness_set) if user_weaknesses else 0.0

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        import re
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')

        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while self.db.query(LearningPath).filter(LearningPath.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    async def generate_path_from_topics(self, topics: List[str], creator_id: int,
                                      difficulty: str = 'intermediate') -> LearningPath:
        """
        Generate a learning path from a list of topics using AI.

        Args:
            topics: List of DSA topics
            creator_id: User ID of creator
            difficulty: Difficulty level

        Returns:
            Generated LearningPath object
        """
        logger.info(f"Generating AI-powered learning path for topics: {topics}")

        # Use LLM to generate path structure
        prompt = f"""
        Create a structured learning path for the following DSA topics: {', '.join(topics)}

        Difficulty level: {difficulty}

        Generate a learning path with:
        1. A compelling title
        2. Brief description
        3. Logical sequence of steps/projects
        4. Prerequisites for each step
        5. Estimated time for each step

        Format as JSON with this structure:
        {{
            "title": "Path Title",
            "description": "Path description",
            "steps": [
                {{
                    "title": "Step 1 Title",
                    "description": "Step description",
                    "required_skills": ["skill1", "skill2"],
                    "estimated_time": 120,
                    "prerequisites": {{"type": "skills", "skills": ["basic_arrays"]}}
                }}
            ]
        }}
        """

        try:
            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            path_data = eval(response.content.strip())  # In production, use proper JSON parsing

            # Create path with generated data
            steps = path_data.get('steps', [])
            path = await self.create_path(
                title=path_data['title'],
                description=path_data['description'],
                creator_id=creator_id,
                difficulty=difficulty,
                tags=topics,
                steps=steps
            )

            # Mark as AI-generated
            path.metadata = {'auto_generated': True, 'source_topics': topics}
            self.db.commit()

            logger.info(f"Generated AI learning path: {path.title}")
            return path

        except Exception as e:
            logger.error(f"Failed to generate AI path: {e}")
            # Fallback to basic path
            return await self.create_path(
                title=f"Learning Path: {', '.join(topics[:3])}",
                description=f"Structured learning path covering {', '.join(topics)}",
                creator_id=creator_id,
                difficulty=difficulty,
                tags=topics
            )
