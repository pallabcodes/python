"""
Community Path Creation and Curation System.

This module handles user-generated learning paths, including creation,
validation, voting, moderation, and quality assessment features.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from learning_paths.path_engine import PathEngine
from learning_paths.models import LearningPath, LearningPathStep, PathRecommendation
from noleet.llm.llm_factory import LLMFactory
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


@dataclass
class PathValidationResult:
    """Result of path validation."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: List[str]
    suggestions: List[str]
    quality_score: float


@dataclass
class PathQualityMetrics:
    """Quality metrics for a learning path."""
    completeness_score: float
    coherence_score: float
    difficulty_progression_score: float
    time_estimation_accuracy: float
    topic_coverage_score: float
    overall_quality: float


class CommunityPathManager:
    """Manages community-created learning paths."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager
        self.path_engine = PathEngine(db_session, cache_manager)
        self.llm_factory = LLMFactory()

        # Quality thresholds
        self.MIN_QUALITY_SCORE = 0.6
        self.MIN_STEPS = 3
        self.MAX_STEPS = 20

    async def submit_community_path(self, creator_id: int, path_data: Dict[str, Any]) -> Tuple[LearningPath, PathValidationResult]:
        """
        Submit a new community-created learning path.

        Args:
            creator_id: User ID of creator
            path_data: Path data dictionary

        Returns:
            Tuple of (LearningPath, PathValidationResult)
        """
        logger.info(f"Submitting community path from user {creator_id}")

        # Validate path data
        validation = await self.validate_path_data(path_data)

        if not validation.is_valid:
            raise ValueError(f"Path validation failed: {'; '.join(validation.issues)}")

        # Create the path
        path = await self.path_engine.create_path(
            title=path_data['title'],
            description=path_data['description'],
            creator_id=creator_id,
            difficulty=path_data.get('difficulty', 'intermediate'),
            tags=path_data.get('tags', []),
            steps=path_data.get('steps', [])
        )

        # Mark as community path and store quality metrics
        path.is_community_created = True
        path.metadata = {
            **(path.metadata or {}),
            'quality_score': validation.quality_score,
            'validation_issues': validation.issues,
            'submitted_for_review': True,
            'review_status': 'pending' if validation.score >= self.MIN_QUALITY_SCORE else 'needs_improvement'
        }

        self.db.commit()

        # Auto-approve if quality is high enough
        if validation.score >= self.MIN_QUALITY_SCORE:
            await self.approve_path(path.id)

        logger.info(f"Community path {path.id} submitted with quality score {validation.quality_score}")
        return path, validation

    async def validate_path_data(self, path_data: Dict[str, Any]) -> PathValidationResult:
        """
        Validate path data and calculate quality metrics.

        Args:
            path_data: Path data to validate

        Returns:
            PathValidationResult with validation details
        """
        issues = []
        suggestions = []

        # Basic validation
        if not path_data.get('title') or len(path_data['title'].strip()) < 5:
            issues.append("Title must be at least 5 characters long")

        if not path_data.get('description') or len(path_data['description'].strip()) < 20:
            issues.append("Description must be at least 20 characters long")

        steps = path_data.get('steps', [])
        if len(steps) < self.MIN_STEPS:
            issues.append(f"Path must have at least {self.MIN_STEPS} steps")
        elif len(steps) > self.MAX_STEPS:
            issues.append(f"Path cannot have more than {self.MAX_STEPS} steps")

        # Advanced validation
        quality_metrics = await self._calculate_quality_metrics(path_data)

        # Generate suggestions based on quality metrics
        suggestions = await self._generate_quality_suggestions(quality_metrics, path_data)

        # Calculate overall score
        is_valid = len(issues) == 0 and quality_metrics.overall_quality >= self.MIN_QUALITY_SCORE
        overall_score = quality_metrics.overall_quality if is_valid else 0.0

        return PathValidationResult(
            is_valid=is_valid,
            score=overall_score,
            issues=issues,
            suggestions=suggestions,
            quality_score=quality_metrics.overall_quality
        )

    async def _calculate_quality_metrics(self, path_data: Dict[str, Any]) -> PathQualityMetrics:
        """Calculate detailed quality metrics for the path."""
        steps = path_data.get('steps', [])

        # Completeness score
        completeness_score = self._calculate_completeness_score(path_data)

        # Coherence score
        coherence_score = await self._calculate_coherence_score(path_data)

        # Difficulty progression score
        difficulty_progression = self._calculate_difficulty_progression_score(steps)

        # Time estimation accuracy
        time_accuracy = self._calculate_time_estimation_accuracy(steps)

        # Topic coverage score
        topic_coverage = self._calculate_topic_coverage_score(path_data)

        # Overall quality (weighted average)
        overall_quality = (
            completeness_score * 0.25 +
            coherence_score * 0.25 +
            difficulty_progression * 0.20 +
            time_accuracy * 0.15 +
            topic_coverage * 0.15
        )

        return PathQualityMetrics(
            completeness_score=round(completeness_score, 3),
            coherence_score=round(coherence_score, 3),
            difficulty_progression_score=round(difficulty_progression, 3),
            time_estimation_accuracy=round(time_accuracy, 3),
            topic_coverage_score=round(topic_coverage, 3),
            overall_quality=round(overall_quality, 3)
        )

    def _calculate_completeness_score(self, path_data: Dict[str, Any]) -> float:
        """Calculate completeness score based on required fields."""
        score = 0.0
        max_score = 5.0

        # Title and description (required)
        if path_data.get('title') and len(path_data['title'].strip()) >= 10:
            score += 1.0
        if path_data.get('description') and len(path_data['description'].strip()) >= 50:
            score += 1.0

        # Difficulty level
        if path_data.get('difficulty') in ['easy', 'medium', 'hard']:
            score += 0.5

        # Tags/topics
        tags = path_data.get('tags', [])
        if tags and len(tags) >= 2:
            score += 0.5

        # Steps
        steps = path_data.get('steps', [])
        if steps and len(steps) >= self.MIN_STEPS:
            score += 1.0
            # Check step completeness
            complete_steps = sum(1 for step in steps if
                               step.get('title') and step.get('description') and
                               step.get('estimated_time', 0) > 0)
            score += min(complete_steps / len(steps), 1.0)

        return score / max_score

    async def _calculate_coherence_score(self, path_data: Dict[str, Any]) -> float:
        """Calculate coherence score using AI analysis."""
        try:
            prompt = f"""
            Analyze the coherence of this learning path:

            Title: {path_data.get('title', '')}
            Description: {path_data.get('description', '')}
            Steps: {[step.get('title', '') for step in path_data.get('steps', [])]}

            Rate the logical flow and coherence from 0.0 to 1.0.
            Consider: logical progression, topic consistency, prerequisite relationships.

            Return only a number between 0.0 and 1.0.
            """

            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"Coherence analysis failed: {e}")
            return 0.5  # Neutral score on failure

    def _calculate_difficulty_progression_score(self, steps: List[Dict[str, Any]]) -> float:
        """Calculate difficulty progression score."""
        if len(steps) < 2:
            return 0.5

        # This is a simplified heuristic - could be enhanced with AI
        difficulties = []
        for step in steps:
            # Infer difficulty from step content
            title_lower = step.get('title', '').lower()
            desc_lower = step.get('description', '').lower()

            if any(word in title_lower + desc_lower for word in ['basic', 'introduction', 'fundamentals']):
                difficulties.append(1)  # Easy
            elif any(word in title_lower + desc_lower for word in ['intermediate', 'moderate', 'standard']):
                difficulties.append(2)  # Medium
            elif any(word in title_lower + desc_lower for word in ['advanced', 'complex', 'difficult']):
                difficulties.append(3)  # Hard
            else:
                difficulties.append(2)  # Default to medium

        # Check for reasonable progression (not all same, not decreasing significantly)
        if len(set(difficulties)) == 1:
            return 0.7  # Consistent difficulty is okay

        # Check for increasing trend
        increasing_pairs = sum(1 for i in range(len(difficulties)-1)
                             if difficulties[i] <= difficulties[i+1])
        progression_ratio = increasing_pairs / (len(difficulties) - 1)

        return min(progression_ratio + 0.3, 1.0)  # Bonus for any progression

    def _calculate_time_estimation_accuracy(self, steps: List[Dict[str, Any]]) -> float:
        """Calculate time estimation accuracy score."""
        if not steps:
            return 0.0

        total_time = sum(step.get('estimated_time', 0) for step in steps)
        avg_time_per_step = total_time / len(steps)

        # Reasonable bounds: 15-180 minutes per step
        reasonable_estimates = sum(1 for step in steps if
                                 15 <= step.get('estimated_time', 0) <= 180)

        reasonableness_score = reasonable_estimates / len(steps)

        # Check for reasonable total time (not too short or long)
        if 60 <= total_time <= 2400:  # 1 hour to 40 hours total
            total_score = 1.0
        elif 30 <= total_time <= 4800:  # Lenient bounds
            total_score = 0.7
        else:
            total_score = 0.3

        return (reasonableness_score + total_score) / 2

    def _calculate_topic_coverage_score(self, path_data: Dict[str, Any]) -> float:
        """Calculate topic coverage score."""
        tags = path_data.get('tags', [])
        steps = path_data.get('steps', [])

        if not tags:
            return 0.0

        # Check how well steps cover the declared topics
        step_topics = set()
        for step in steps:
            required_skills = step.get('required_skills', [])
            step_topics.update(required_skills)

        # Calculate coverage ratio
        tag_set = set(tags)
        coverage = len(tag_set.intersection(step_topics)) / len(tag_set) if tag_set else 0

        # Bonus for additional topics covered
        extra_coverage = max(0, len(step_topics) - len(tag_set)) / len(tag_set) if tag_set else 0
        extra_bonus = min(extra_coverage * 0.2, 0.2)  # Max 20% bonus

        return min(coverage + extra_bonus, 1.0)

    async def _generate_quality_suggestions(self, metrics: PathQualityMetrics,
                                          path_data: Dict[str, Any]) -> List[str]:
        """Generate quality improvement suggestions."""
        suggestions = []

        if metrics.completeness_score < 0.8:
            suggestions.append("Add more detailed descriptions to steps and ensure all required fields are filled")

        if metrics.coherence_score < 0.7:
            suggestions.append("Review the logical flow between steps to ensure smooth progression")

        if metrics.difficulty_progression_score < 0.6:
            suggestions.append("Ensure difficulty increases gradually from basic to advanced concepts")

        if metrics.time_estimation_accuracy < 0.7:
            suggestions.append("Review time estimates to ensure they're realistic (15-180 minutes per step)")

        if metrics.topic_coverage_score < 0.8:
            suggestions.append("Ensure all declared topics are adequately covered in the steps")

        # AI-powered suggestions
        ai_suggestions = await self._generate_ai_suggestions(path_data)
        suggestions.extend(ai_suggestions)

        return suggestions[:5]  # Limit to top 5

    async def _generate_ai_suggestions(self, path_data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered improvement suggestions."""
        try:
            prompt = f"""
            Review this learning path and suggest 2-3 specific improvements:

            Title: {path_data.get('title', '')}
            Description: {path_data.get('description', '')}
            Steps: {[step.get('title', '') for step in path_data.get('steps', [])[:5]]}
            Topics: {path_data.get('tags', [])}

            Focus on educational effectiveness, engagement, and completeness.
            Keep suggestions actionable and specific.
            """

            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            suggestions_text = response.content.strip()

            # Parse suggestions (assuming they're in a list format)
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                if line and not line.startswith(('Title:', 'Description:', 'Steps:', 'Topics:')):
                    # Clean up common prefixes
                    line = re.sub(r'^\d+\.?\s*', '', line)
                    line = re.sub(r'^-\s*', '', line)
                    if line:
                        suggestions.append(line)

            return suggestions[:3]

        except Exception as e:
            logger.error(f"AI suggestions failed: {e}")
            return []

    async def approve_path(self, path_id: int, moderator_id: Optional[int] = None) -> bool:
        """
        Approve a community path for publication.

        Args:
            path_id: Path ID to approve
            moderator_id: Moderator user ID (optional)

        Returns:
            True if approved, False otherwise
        """
        path = self.db.query(LearningPath).filter(LearningPath.id == path_id).first()
        if not path:
            return False

        path.metadata = {
            **(path.metadata or {}),
            'review_status': 'approved',
            'approved_at': datetime.now().isoformat(),
            'approved_by': moderator_id
        }

        self.db.commit()

        # Clear cache
        if self.cache:
            await self.cache.delete(f"path_data:{path_id}")

        logger.info(f"Path {path_id} approved for publication")
        return True

    async def reject_path(self, path_id: int, reason: str, moderator_id: Optional[int] = None) -> bool:
        """
        Reject a community path.

        Args:
            path_id: Path ID to reject
            reason: Rejection reason
            moderator_id: Moderator user ID (optional)

        Returns:
            True if rejected, False otherwise
        """
        path = self.db.query(LearningPath).filter(LearningPath.id == path_id).first()
        if not path:
            return False

        path.metadata = {
            **(path.metadata or {}),
            'review_status': 'rejected',
            'rejected_at': datetime.now().isoformat(),
            'rejected_by': moderator_id,
            'rejection_reason': reason
        }

        self.db.commit()

        # Clear cache
        if self.cache:
            await self.cache.delete(f"path_data:{path_id}")

        logger.info(f"Path {path_id} rejected: {reason}")
        return True

    def vote_on_path(self, user_id: int, path_id: int, vote_type: str) -> bool:
        """
        Cast a vote on a community path.

        Args:
            user_id: User ID casting vote
            path_id: Path ID being voted on
            vote_type: 'upvote' or 'downvote'

        Returns:
            True if vote recorded, False otherwise
        """
        path = self.db.query(LearningPath).filter(LearningPath.id == path_id).first()
        if not path or not path.is_community_created:
            return False

        # Simple voting system (could be enhanced with vote tracking table)
        if vote_type == 'upvote':
            path.upvotes += 1
        elif vote_type == 'downvote':
            path.upvotes -= 1

        self.db.commit()

        logger.info(f"User {user_id} {vote_type}d path {path_id}")
        return True

    async def get_pending_reviews(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get paths pending review."""
        pending_paths = self.db.query(LearningPath).filter(
            and_(
                LearningPath.is_community_created == True,
                LearningPath.metadata['review_status'].astext == 'pending'
            )
        ).order_by(LearningPath.created_at.desc()).limit(limit).all()

        result = []
        for path in pending_paths:
            validation = await self.validate_path_data({
                'title': path.title,
                'description': path.description,
                'difficulty': path.difficulty,
                'tags': path.tags,
                'steps': [{'title': s.title, 'description': s.description,
                          'estimated_time': s.estimated_time}
                         for s in path.steps]
            })

            result.append({
                'path_id': path.id,
                'title': path.title,
                'creator_id': path.creator_id,
                'created_at': path.created_at,
                'quality_score': validation.quality_score,
                'issues': validation.issues,
                'suggestions': validation.suggestions
            })

        return result

    def get_top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top community path contributors."""
        contributors = self.db.query(
            LearningPath.creator_id,
            func.count(LearningPath.id).label('paths_created'),
            func.sum(LearningPath.upvotes).label('total_upvotes'),
            func.avg(LearningPath.metadata['quality_score'].astext.cast(Float)).label('avg_quality')
        ).filter(
            and_(
                LearningPath.is_community_created == True,
                LearningPath.metadata['review_status'].astext == 'approved'
            )
        ).group_by(LearningPath.creator_id).order_by(
            desc(func.sum(LearningPath.upvotes))
        ).limit(limit).all()

        return [{
            'user_id': contrib.creator_id,
            'paths_created': contrib.paths_created,
            'total_upvotes': contrib.total_upvotes or 0,
            'avg_quality': round(contrib.avg_quality or 0, 3),
            'contribution_score': (contrib.total_upvotes or 0) * (contrib.avg_quality or 0.5)
        } for contrib in contributors]

    async def suggest_path_improvements(self, path_id: int) -> Dict[str, Any]:
        """
        Generate AI-powered suggestions for improving an existing path.

        Args:
            path_id: Path ID to improve

        Returns:
            Improvement suggestions
        """
        path_data = await self.path_engine.get_path(path_id)
        if not path_data:
            return {'error': 'Path not found'}

        # Convert path data to format for analysis
        path_dict = {
            'title': path_data.title,
            'description': path_data.description,
            'difficulty': path_data.difficulty,
            'tags': path_data.tags,
            'steps': [
                {
                    'title': step.title,
                    'description': step.description,
                    'estimated_time': step.estimated_time,
                    'required_skills': step.required_skills
                }
                for step in path_data.steps
            ]
        }

        # Get current quality metrics
        validation = await self.validate_path_data(path_dict)

        # Generate improvement suggestions
        suggestions = await self._generate_ai_improvements(path_dict, validation)

        return {
            'path_id': path_id,
            'current_quality': validation.quality_score,
            'issues': validation.issues,
            'suggestions': validation.suggestions,
            'ai_improvements': suggestions,
            'estimated_improvement': min(validation.quality_score + 0.2, 1.0)
        }

    async def _generate_ai_improvements(self, path_data: Dict[str, Any],
                                      validation: PathValidationResult) -> List[str]:
        """Generate AI-powered improvement suggestions."""
        try:
            prompt = f"""
            Analyze this learning path and suggest specific improvements to increase its quality and effectiveness:

            Current Quality Score: {validation.quality_score}
            Issues: {validation.issues[:3]}
            Existing Suggestions: {validation.suggestions[:3]}

            Path Details:
            Title: {path_data.get('title')}
            Description: {path_data.get('description')}
            Difficulty: {path_data.get('difficulty')}
            Topics: {path_data.get('tags')}
            Number of Steps: {len(path_data.get('steps', []))}

            Provide 3-5 specific, actionable improvement suggestions that would significantly enhance the path's educational value.
            """

            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            suggestions_text = response.content.strip()

            # Parse suggestions
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                if line and len(line) > 10:  # Filter out short/irrelevant lines
                    line = re.sub(r'^\d+\.?\s*', '', line)
                    line = re.sub(r'^-\s*', '', line)
                    if line:
                        suggestions.append(line)

            return suggestions[:5]

        except Exception as e:
            logger.error(f"AI improvements failed: {e}")
            return ["Consider adding more detailed step descriptions",
                   "Review difficulty progression between steps",
                   "Ensure time estimates are realistic"]
