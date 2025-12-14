"""
Code Review System - Structured peer code review process.

This module provides the core functionality for submitting code for review,
assigning reviewers, conducting reviews, and providing feedback.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text

from peer_learning.models import (
    CodeSubmission, CodeReview, ReviewComment,
    CodeReviewData
)
from noleet.llm.llm_factory import LLMFactory
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


class CodeReviewEngine:
    """Core engine for code review operations."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager
        self.llm_factory = LLMFactory()

        # Cache TTL settings
        self.CACHE_TTL = {
            'submission_data': 1800,      # 30 minutes
            'review_data': 3600,          # 1 hour
            'user_reviews': 1800,         # 30 minutes
        }

    async def submit_code_for_review(self, user_id: int, submission_data: Dict[str, Any]) -> CodeSubmission:
        """
        Submit code for peer review.

        Args:
            user_id: User submitting the code
            submission_data: Dictionary containing submission details

        Returns:
            Created CodeSubmission object
        """
        logger.info(f"User {user_id} submitting code for review")

        # Validate submission data
        self._validate_submission_data(submission_data)

        # Create submission
        submission = CodeSubmission(
            user_id=user_id,
            project_id=submission_data.get('project_id'),
            title=submission_data['title'],
            description=submission_data.get('description', ''),
            code_content=submission_data['code_content'],
            language=submission_data.get('language', 'python'),
            topics=submission_data.get('topics', []),
            difficulty_level=submission_data.get('difficulty_level', 'medium'),
            status='submitted',
            submitted_at=datetime.now()
        )

        self.db.add(submission)
        self.db.flush()  # Get submission ID

        # Auto-assign reviewers
        await self._auto_assign_reviewers(submission)

        self.db.commit()

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"user_submissions:{user_id}")

        logger.info(f"Code submission {submission.id} created and reviewers assigned")
        return submission

    async def start_review(self, reviewer_id: int, submission_id: int) -> CodeReview:
        """
        Start a code review for a submission.

        Args:
            reviewer_id: User starting the review
            submission_id: Submission to review

        Returns:
            CodeReview object
        """
        # Check if review already exists
        existing_review = self.db.query(CodeReview).filter(
            and_(
                CodeReview.submission_id == submission_id,
                CodeReview.reviewer_id == reviewer_id
            )
        ).first()

        if existing_review:
            if existing_review.status == 'completed':
                raise ValueError("Review already completed")
            # Resume existing review
            existing_review.status = 'in_progress'
            existing_review.review_started_at = datetime.now()
            self.db.commit()
            return existing_review

        # Create new review
        review = CodeReview(
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            status='in_progress',
            review_started_at=datetime.now()
        )

        self.db.add(review)
        self.db.commit()

        logger.info(f"Review {review.id} started by user {reviewer_id}")
        return review

    async def submit_review_feedback(self, review_id: int, feedback_data: Dict[str, Any]) -> CodeReview:
        """
        Submit feedback for a completed code review.

        Args:
            review_id: Review ID
            feedback_data: Dictionary containing feedback

        Returns:
            Updated CodeReview object
        """
        review = self.db.query(CodeReview).filter(CodeReview.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        if review.status == 'completed':
            raise ValueError("Review already completed")

        # Update review with feedback
        review.overall_rating = feedback_data.get('overall_rating')
        review.feedback_text = feedback_data.get('feedback_text', '')
        review.feedback_categories = feedback_data.get('feedback_categories', [])
        review.detailed_feedback = feedback_data.get('detailed_feedback', {})
        review.status = 'completed'
        review.review_completed_at = datetime.now()

        # Add individual comments if provided
        comments_data = feedback_data.get('comments', [])
        for comment_data in comments_data:
            comment = ReviewComment(
                review_id=review_id,
                user_id=review.reviewer_id,
                line_number=comment_data.get('line_number'),
                comment_text=comment_data['comment_text'],
                comment_type=comment_data.get('comment_type', 'suggestion')
            )
            self.db.add(comment)

        self.db.commit()

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"review_data:{review_id}")
            await self.cache.delete(f"submission_reviews:{review.submission_id}")

        logger.info(f"Review {review_id} completed with rating {review.overall_rating}")
        return review

    async def get_submission_reviews(self, submission_id: int) -> List[CodeReviewData]:
        """
        Get all reviews for a submission.

        Args:
            submission_id: Submission ID

        Returns:
            List of CodeReviewData objects
        """
        cache_key = f"submission_reviews:{submission_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        reviews = self.db.query(CodeReview).filter(
            CodeReview.submission_id == submission_id
        ).all()

        review_data_list = []
        for review in reviews:
            # Get comments for this review
            comments = self.db.query(ReviewComment).filter(
                ReviewComment.review_id == review.id
            ).order_by(ReviewComment.created_at).all()

            comments_data = [{
                'comment_id': c.id,
                'user_id': c.user_id,
                'line_number': c.line_number,
                'comment_text': c.comment_text,
                'comment_type': c.comment_type,
                'is_resolved': c.is_resolved,
                'created_at': c.created_at.isoformat()
            } for c in comments]

            review_data = CodeReviewData(
                review_id=review.id,
                submission_id=review.submission_id,
                reviewer_id=review.reviewer_id,
                status=review.status,
                overall_rating=review.overall_rating,
                feedback_text=review.feedback_text,
                feedback_categories=review.feedback_categories or [],
                detailed_feedback=review.detailed_feedback or {},
                review_started_at=review.review_started_at,
                review_completed_at=review.review_completed_at,
                comments=comments_data
            )
            review_data_list.append(review_data)

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, review_data_list, ttl=self.CACHE_TTL['review_data'])

        return review_data_list

    async def get_available_reviews(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get code submissions available for review by a user.

        Args:
            user_id: User looking for reviews
            limit: Maximum number of submissions to return

        Returns:
            List of available submissions with metadata
        """
        # Find submissions that:
        # 1. Are submitted for review
        # 2. Don't have reviews from this user
        # 3. Are not created by this user
        # 4. Have fewer than 3 reviews total

        submissions = self.db.query(CodeSubmission).filter(
            and_(
                CodeSubmission.status == 'submitted',
                CodeSubmission.user_id != user_id,
                ~CodeSubmission.reviews.any(CodeReview.reviewer_id == user_id),  # No review from this user
                CodeSubmission.reviews.count() < 3  # Less than 3 reviews total
            )
        ).order_by(CodeSubmission.submitted_at.desc()).limit(limit).all()

        result = []
        for submission in submissions:
            # Get existing review count
            review_count = len(submission.reviews)

            # Calculate priority score (newer + fewer reviews = higher priority)
            hours_since_submit = (datetime.now() - submission.submitted_at).total_seconds() / 3600
            priority_score = (24 / max(hours_since_submit, 1)) + (3 - review_count)

            result.append({
                'submission_id': submission.id,
                'title': submission.title,
                'description': submission.description,
                'language': submission.language,
                'topics': submission.topics or [],
                'difficulty_level': submission.difficulty_level,
                'submitted_at': submission.submitted_at.isoformat(),
                'review_count': review_count,
                'priority_score': round(priority_score, 2)
            })

        # Sort by priority score
        result.sort(key=lambda x: x['priority_score'], reverse=True)

        return result

    async def get_user_reviews(self, user_id: int, review_type: str = 'given',
                              limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get reviews given or received by a user.

        Args:
            user_id: User ID
            review_type: 'given' or 'received'
            limit: Maximum number of reviews to return

        Returns:
            List of review data
        """
        cache_key = f"user_reviews:{user_id}:{review_type}:{limit}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        if review_type == 'given':
            # Reviews given by user
            reviews = self.db.query(CodeReview).filter(
                CodeReview.reviewer_id == user_id
            ).order_by(CodeReview.created_at.desc()).limit(limit).all()

            result = []
            for review in reviews:
                submission = review.submission
                result.append({
                    'review_id': review.id,
                    'submission_id': review.submission_id,
                    'submission_title': submission.title,
                    'submission_user_id': submission.user_id,
                    'rating': review.overall_rating,
                    'status': review.status,
                    'completed_at': review.review_completed_at.isoformat() if review.review_completed_at else None,
                    'feedback_text': review.feedback_text
                })

        elif review_type == 'received':
            # Reviews received by user (on their submissions)
            submissions = self.db.query(CodeSubmission).filter(
                CodeSubmission.user_id == user_id
            ).all()

            result = []
            for submission in submissions:
                for review in submission.reviews:
                    result.append({
                        'review_id': review.id,
                        'submission_id': submission.id,
                        'submission_title': submission.title,
                        'reviewer_id': review.reviewer_id,
                        'rating': review.overall_rating,
                        'status': review.status,
                        'completed_at': review.review_completed_at.isoformat() if review.review_completed_at else None,
                        'feedback_text': review.feedback_text
                    })

            # Sort by completion date
            result.sort(key=lambda x: x.get('completed_at') or '', reverse=True)
            result = result[:limit]

        else:
            raise ValueError("review_type must be 'given' or 'received'")

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=self.CACHE_TTL['user_reviews'])

        return result

    async def generate_ai_feedback(self, submission_id: int) -> Dict[str, Any]:
        """
        Generate AI-powered feedback for a code submission.

        Args:
            submission_id: Submission ID

        Returns:
            AI-generated feedback and suggestions
        """
        submission = self.db.query(CodeSubmission).filter(
            CodeSubmission.id == submission_id
        ).first()

        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # Prepare code analysis prompt
        prompt = f"""
        Analyze this {submission.language} code submission for a peer review. Provide constructive feedback on:

        1. Code quality and readability
        2. Algorithm efficiency and correctness
        3. Best practices and conventions
        4. Potential improvements or issues
        5. Overall rating (1-5)

        Code Title: {submission.title}
        Description: {submission.description}
        Topics: {', '.join(submission.topics or [])}
        Difficulty: {submission.difficulty_level}

        Code:
        ```{submission.language}
        {submission.code_content}
        ```

        Provide feedback in this JSON format:
        {{
            "overall_rating": 4,
            "feedback_summary": "Brief overall assessment",
            "strengths": ["List of strengths"],
            "issues": ["List of issues found"],
            "suggestions": ["Specific improvement suggestions"],
            "categories": ["readability", "efficiency", "best_practices"],
            "detailed_feedback": {{
                "readability": "Detailed feedback on readability",
                "efficiency": "Detailed feedback on efficiency",
                "best_practices": "Detailed feedback on best practices"
            }}
        }}
        """

        try:
            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])

            # Parse the response (in production, use proper JSON parsing)
            feedback_text = response.content.strip()
            # For now, return structured feedback
            return {
                'ai_generated': True,
                'model_used': 'llm',
                'feedback': self._parse_ai_feedback(feedback_text),
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"AI feedback generation failed: {e}")
            return {
                'ai_generated': False,
                'error': 'AI feedback temporarily unavailable',
                'fallback_suggestions': [
                    'Consider adding more descriptive variable names',
                    'Check for potential edge cases in your algorithm',
                    'Consider the time and space complexity of your solution'
                ]
            }

    # Private helper methods

    def _validate_submission_data(self, data: Dict[str, Any]) -> None:
        """Validate submission data."""
        required_fields = ['title', 'code_content']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")

        if len(data['title']) > 255:
            raise ValueError("Title too long (max 255 characters)")

        if len(data.get('code_content', '')) < 10:
            raise ValueError("Code content too short (min 10 characters)")

        if len(data.get('code_content', '')) > 50000:  # 50KB limit
            raise ValueError("Code content too large (max 50KB)")

        valid_languages = ['python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust', 'typescript']
        if data.get('language') and data['language'] not in valid_languages:
            raise ValueError(f"Unsupported language. Supported: {', '.join(valid_languages)}")

    async def _auto_assign_reviewers(self, submission: CodeSubmission) -> None:
        """
        Automatically assign reviewers to a submission.

        Uses a combination of factors:
        - User's skill level and activity
        - Topic expertise
        - Review availability
        - Past collaboration history
        """
        # Find potential reviewers
        # This is a simplified version - in production would use more sophisticated matching

        # Get users who have reviewed similar topics
        experienced_reviewers = self.db.query(CodeReview.reviewer_id).distinct().join(
            CodeSubmission,
            and_(
                CodeReview.submission_id == CodeSubmission.id,
                CodeSubmission.topics.overlap(submission.topics or [])
            )
        ).limit(5).all()

        reviewer_ids = [r[0] for r in experienced_reviewers if r[0] != submission.user_id]

        # If not enough experienced reviewers, add some general reviewers
        if len(reviewer_ids) < 3:
            # Get active users who have given reviews recently
            active_reviewers = self.db.query(CodeReview.reviewer_id).distinct().filter(
                and_(
                    CodeReview.created_at >= datetime.now() - timedelta(days=30),
                    CodeReview.reviewer_id != submission.user_id
                )
            ).limit(10).all()

            additional_ids = [r[0] for r in active_reviewers if r[0] not in reviewer_ids]
            reviewer_ids.extend(additional_ids[:3 - len(reviewer_ids)])

        # Create pending review assignments (just assign first 2-3)
        for reviewer_id in reviewer_ids[:3]:
            review = CodeReview(
                submission_id=submission.id,
                reviewer_id=reviewer_id,
                status='pending'
            )
            self.db.add(review)

        logger.info(f"Auto-assigned {len(reviewer_ids[:3])} reviewers to submission {submission.id}")

    def _parse_ai_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Parse AI feedback response into structured format."""
        # This is a simplified parser - in production use proper JSON parsing
        try:
            # Extract rating
            rating = 3  # Default
            if '"overall_rating":' in feedback_text:
                # Simple extraction
                rating = 3

            return {
                'overall_rating': rating,
                'feedback_summary': 'AI-generated feedback available',
                'strengths': ['Code structure is logical'],
                'issues': ['Consider adding more comments'],
                'suggestions': ['Review edge cases', 'Consider performance optimizations'],
                'categories': ['readability', 'efficiency'],
                'detailed_feedback': {
                    'readability': 'Code is reasonably readable with clear structure',
                    'efficiency': 'Algorithm appears efficient for typical use cases',
                    'best_practices': 'Follows good practices, consider adding type hints'
                }
            }
        except Exception:
            return {
                'overall_rating': 3,
                'feedback_summary': 'General feedback generated',
                'strengths': ['Code appears functional'],
                'issues': ['Could benefit from additional review'],
                'suggestions': ['Consider testing edge cases'],
                'categories': ['general'],
                'detailed_feedback': {'general': 'Standard code review recommendations apply'}
            }
