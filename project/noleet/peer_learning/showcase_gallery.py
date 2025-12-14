"""
Implementation Showcase Gallery - Community-curated gallery of outstanding implementations.

This module manages the showcase gallery where users can submit their best code
implementations for community recognition, learning, and inspiration.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from peer_learning.models import (
    ImplementationShowcase, ShowcaseVote, ShowcaseComment,
    ShowcaseImplementationData
)
from noleet.llm.llm_factory import LLMFactory
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


class ShowcaseGallery:
    """Manager for the implementation showcase gallery."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager
        self.llm_factory = LLMFactory()

        # Quality thresholds
        self.MIN_QUALITY_SCORE = 0.7
        self.FEATURED_THRESHOLD = 0.85

        # Cache TTL settings
        self.CACHE_TTL = {
            'showcase_data': 1800,      # 30 minutes
            'gallery_listing': 900,    # 15 minutes
            'user_showcases': 1800,    # 30 minutes
        }

    async def submit_showcase(self, user_id: int, showcase_data: Dict[str, Any]) -> ImplementationShowcase:
        """
        Submit an implementation to the showcase gallery.

        Args:
            user_id: User submitting the showcase
            showcase_data: Showcase details and code

        Returns:
            Created ImplementationShowcase object
        """
        logger.info(f"User {user_id} submitting showcase implementation")

        # Validate showcase data
        self._validate_showcase_data(showcase_data)

        # Check for duplicate submissions (same user, same project, within 30 days)
        recent_submission = self.db.query(ImplementationShowcase).filter(
            and_(
                ImplementationShowcase.user_id == user_id,
                ImplementationShowcase.project_id == showcase_data.get('project_id'),
                ImplementationShowcase.submitted_at >= datetime.now() - timedelta(days=30)
            )
        ).first()

        if recent_submission:
            raise ValueError("You have already submitted a showcase for this project recently")

        # Calculate initial quality score
        quality_score = await self._calculate_quality_score(showcase_data)

        # Create showcase
        showcase = ImplementationShowcase(
            user_id=user_id,
            project_id=showcase_data.get('project_id'),
            title=showcase_data['title'],
            description=showcase_data['description'],
            code_content=showcase_data['code_content'],
            language=showcase_data.get('language', 'python'),
            topics=showcase_data.get('topics', []),
            difficulty_level=showcase_data.get('difficulty_level', 'medium'),
            approach_description=showcase_data.get('approach_description', ''),
            key_insights=showcase_data.get('key_insights', []),
            performance_metrics=showcase_data.get('performance_metrics', {}),
            status='pending' if quality_score >= self.MIN_QUALITY_SCORE else 'rejected',
            featured=quality_score >= self.FEATURED_THRESHOLD
        )

        self.db.add(showcase)
        self.db.commit()

        # Auto-approve if quality is high enough
        if quality_score >= self.MIN_QUALITY_SCORE:
            showcase.approved_at = datetime.now()
            self.db.commit()

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"user_showcases:{user_id}")
            await self.cache.delete("gallery_listing")

        logger.info(f"Showcase {showcase.id} submitted by user {user_id} with quality score {quality_score}")
        return showcase

    async def get_gallery_showcases(self, filters: Optional[Dict[str, Any]] = None,
                                  sort_by: str = 'upvotes', limit: int = 50) -> List[ShowcaseImplementationData]:
        """
        Get showcases from the gallery with optional filtering and sorting.

        Args:
            filters: Optional filters (language, topic, difficulty, featured)
            sort_by: Sort criteria ('upvotes', 'recent', 'views', 'trending')
            limit: Maximum number of results

        Returns:
            List of ShowcaseImplementationData objects
        """
        cache_key = f"gallery_listing:{str(filters)}:{sort_by}:{limit}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Build query
        query = self.db.query(ImplementationShowcase).filter(
            ImplementationShowcase.status == 'approved'
        )

        # Apply filters
        if filters:
            if filters.get('language'):
                query = query.filter(ImplementationShowcase.language == filters['language'])

            if filters.get('difficulty'):
                query = query.filter(ImplementationShowcase.difficulty_level == filters['difficulty'])

            if filters.get('featured'):
                query = query.filter(ImplementationShowcase.featured == True)

            if filters.get('topic'):
                query = query.filter(ImplementationShowcase.topics.contains([filters['topic']]))

        # Apply sorting
        if sort_by == 'upvotes':
            query = query.order_by(desc(ImplementationShowcase.upvotes))
        elif sort_by == 'recent':
            query = query.order_by(desc(ImplementationShowcase.approved_at))
        elif sort_by == 'views':
            query = query.order_by(desc(ImplementationShowcase.views))
        elif sort_by == 'trending':
            # Simple trending: upvotes in last 7 days + recent submissions
            seven_days_ago = datetime.now() - timedelta(days=7)
            query = query.filter(
                ImplementationShowcase.approved_at >= seven_days_ago
            ).order_by(desc(ImplementationShowcase.upvotes))

        showcases = query.limit(limit).all()

        # Convert to data objects with user info
        result = []
        for showcase in showcases:
            # Get user info (simplified - would use user service in production)
            user_name = f"User {showcase.user_id}"  # Placeholder
            user_reputation = 100  # Placeholder

            showcase_data = ShowcaseImplementationData(
                showcase_id=showcase.id,
                user_id=showcase.user_id,
                title=showcase.title,
                description=showcase.description,
                language=showcase.language,
                topics=showcase.topics or [],
                difficulty_level=showcase.difficulty_level,
                upvotes=showcase.upvotes,
                downvotes=showcase.downvotes,
                views=showcase.views,
                featured=showcase.featured,
                submitted_at=showcase.submitted_at,
                user_name=user_name,
                user_reputation=user_reputation,
                approach_description=showcase.approach_description,
                key_insights=showcase.key_insights or [],
                performance_metrics=showcase.performance_metrics or {}
            )
            result.append(showcase_data)

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=self.CACHE_TTL['gallery_listing'])

        return result

    async def get_showcase_details(self, showcase_id: int) -> Optional[ShowcaseImplementationData]:
        """
        Get detailed information about a specific showcase.

        Args:
            showcase_id: Showcase ID

        Returns:
            ShowcaseImplementationData or None if not found
        """
        cache_key = f"showcase_data:{showcase_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                # Increment view count (async, don't wait)
                asyncio.create_task(self._increment_views(showcase_id))
                return cached

        showcase = self.db.query(ImplementationShowcase).filter(
            and_(
                ImplementationShowcase.id == showcase_id,
                ImplementationShowcase.status == 'approved'
            )
        ).first()

        if not showcase:
            return None

        # Increment view count
        showcase.views += 1
        self.db.commit()

        # Get user info
        user_name = f"User {showcase.user_id}"  # Placeholder
        user_reputation = 100  # Placeholder

        showcase_data = ShowcaseImplementationData(
            showcase_id=showcase.id,
            user_id=showcase.user_id,
            title=showcase.title,
            description=showcase.description,
            language=showcase.language,
            topics=showcase.topics or [],
            difficulty_level=showcase.difficulty_level,
            upvotes=showcase.upvotes,
            downvotes=showcase.downvotes,
            views=showcase.views,
            featured=showcase.featured,
            submitted_at=showcase.submitted_at,
            user_name=user_name,
            user_reputation=user_reputation,
            approach_description=showcase.approach_description,
            key_insights=showcase.key_insights or [],
            performance_metrics=showcase.performance_metrics or {}
        )

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, showcase_data, ttl=self.CACHE_TTL['showcase_data'])

        return showcase_data

    async def vote_on_showcase(self, user_id: int, showcase_id: int, vote_type: str) -> bool:
        """
        Cast a vote on a showcase implementation.

        Args:
            user_id: User casting the vote
            user_id: Showcase ID
            vote_type: 'upvote' or 'downvote'

        Returns:
            True if vote recorded
        """
        if vote_type not in ['upvote', 'downvote']:
            raise ValueError("Vote type must be 'upvote' or 'downvote'")

        showcase = self.db.query(ImplementationShowcase).filter(
            ImplementationShowcase.id == showcase_id
        ).first()

        if not showcase or showcase.status != 'approved':
            raise ValueError(f"Showcase {showcase_id} not found or not approved")

        # Check if user already voted
        existing_vote = self.db.query(ShowcaseVote).filter(
            and_(
                ShowcaseVote.showcase_id == showcase_id,
                ShowcaseVote.user_id == user_id
            )
        ).first()

        if existing_vote:
            # If same vote type, remove vote
            if existing_vote.vote_type == vote_type:
                self.db.delete(existing_vote)
                if vote_type == 'upvote':
                    showcase.upvotes -= 1
                else:
                    showcase.downvotes -= 1
            else:
                # Change vote type
                existing_vote.vote_type = vote_type
                if vote_type == 'upvote':
                    showcase.upvotes += 1
                    showcase.downvotes -= 1
                else:
                    showcase.downvotes += 1
                    showcase.upvotes -= 1
        else:
            # New vote
            vote = ShowcaseVote(
                showcase_id=showcase_id,
                user_id=user_id,
                vote_type=vote_type
            )
            self.db.add(vote)

            if vote_type == 'upvote':
                showcase.upvotes += 1
            else:
                showcase.downvotes += 1

        self.db.commit()

        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"showcase_data:{showcase_id}")
            await self.cache.delete("gallery_listing")

        logger.info(f"User {user_id} {vote_type}d showcase {showcase_id}")
        return True

    async def add_comment(self, user_id: int, showcase_id: int, comment_text: str,
                         parent_comment_id: Optional[int] = None) -> ShowcaseComment:
        """
        Add a comment to a showcase.

        Args:
            user_id: User adding the comment
            showcase_id: Showcase ID
            comment_text: Comment content
            parent_comment_id: Optional parent comment for threading

        Returns:
            Created ShowcaseComment object
        """
        # Validate showcase exists and is approved
        showcase = self.db.query(ImplementationShowcase).filter(
            and_(
                ImplementationShowcase.id == showcase_id,
                ImplementationShowcase.status == 'approved'
            )
        ).first()

        if not showcase:
            raise ValueError(f"Showcase {showcase_id} not found or not approved")

        # Validate parent comment if provided
        if parent_comment_id:
            parent = self.db.query(ShowcaseComment).filter(
                ShowcaseComment.id == parent_comment_id
            ).first()
            if not parent:
                raise ValueError(f"Parent comment {parent_comment_id} not found")

        # Create comment
        comment = ShowcaseComment(
            showcase_id=showcase_id,
            user_id=user_id,
            comment_text=comment_text,
            parent_comment_id=parent_comment_id
        )

        self.db.add(comment)
        self.db.commit()

        logger.info(f"Comment added to showcase {showcase_id} by user {user_id}")
        return comment

    async def get_showcase_comments(self, showcase_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get comments for a showcase.

        Args:
            showcase_id: Showcase ID
            limit: Maximum number of comments

        Returns:
            List of comment data with threading
        """
        # Get top-level comments
        top_level_comments = self.db.query(ShowcaseComment).filter(
            and_(
                ShowcaseComment.showcase_id == showcase_id,
                ShowcaseComment.parent_comment_id.is_(None)
            )
        ).order_by(desc(ShowcaseComment.upvotes), desc(ShowcaseComment.created_at)).limit(limit).all()

        comments_data = []
        for comment in top_level_comments:
            comment_data = {
                'comment_id': comment.id,
                'user_id': comment.user_id,
                'comment_text': comment.comment_text,
                'upvotes': comment.upvotes,
                'created_at': comment.created_at.isoformat(),
                'replies': []
            }

            # Get replies
            replies = self.db.query(ShowcaseComment).filter(
                ShowcaseComment.parent_comment_id == comment.id
            ).order_by(ShowcaseComment.created_at).all()

            comment_data['replies'] = [{
                'comment_id': reply.id,
                'user_id': reply.user_id,
                'comment_text': reply.comment_text,
                'upvotes': reply.upvotes,
                'created_at': reply.created_at.isoformat()
            } for reply in replies]

            comments_data.append(comment_data)

        return comments_data

    async def get_user_showcases(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all showcases submitted by a user.

        Args:
            user_id: User ID

        Returns:
            List of user's showcase data
        """
        cache_key = f"user_showcases:{user_id}"

        # Check cache
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        showcases = self.db.query(ImplementationShowcase).filter(
            ImplementationShowcase.user_id == user_id
        ).order_by(desc(ImplementationShowcase.submitted_at)).all()

        result = []
        for showcase in showcases:
            result.append({
                'showcase_id': showcase.id,
                'title': showcase.title,
                'status': showcase.status,
                'upvotes': showcase.upvotes,
                'views': showcase.views,
                'featured': showcase.featured,
                'submitted_at': showcase.submitted_at.isoformat(),
                'approved_at': showcase.approved_at.isoformat() if showcase.approved_at else None
            })

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=self.CACHE_TTL['user_showcases'])

        return result

    async def get_featured_showcases(self, limit: int = 10) -> List[ShowcaseImplementationData]:
        """
        Get featured showcase implementations.

        Args:
            limit: Maximum number of showcases

        Returns:
            List of featured showcase data
        """
        featured = self.db.query(ImplementationShowcase).filter(
            and_(
                ImplementationShowcase.status == 'approved',
                ImplementationShowcase.featured == True
            )
        ).order_by(desc(ImplementationShowcase.upvotes)).limit(limit).all()

        result = []
        for showcase in featured:
            user_name = f"User {showcase.user_id}"
            user_reputation = 100

            showcase_data = ShowcaseImplementationData(
                showcase_id=showcase.id,
                user_id=showcase.user_id,
                title=showcase.title,
                description=showcase.description,
                language=showcase.language,
                topics=showcase.topics or [],
                difficulty_level=showcase.difficulty_level,
                upvotes=showcase.upvotes,
                downvotes=showcase.downvotes,
                views=showcase.views,
                featured=True,
                submitted_at=showcase.submitted_at,
                user_name=user_name,
                user_reputation=user_reputation,
                approach_description=showcase.approach_description,
                key_insights=showcase.key_insights or [],
                performance_metrics=showcase.performance_metrics or {}
            )
            result.append(showcase_data)

        return result

    # Private helper methods

    def _validate_showcase_data(self, data: Dict[str, Any]) -> None:
        """Validate showcase submission data."""
        required_fields = ['title', 'description', 'code_content']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")

        if len(data['title']) > 255:
            raise ValueError("Title too long (max 255 characters)")

        if len(data['description']) > 2000:
            raise ValueError("Description too long (max 2000 characters)")

        if len(data['code_content']) < 50:
            raise ValueError("Code content too short (min 50 characters)")

        if len(data['code_content']) > 50000:  # 50KB limit
            raise ValueError("Code content too large (max 50KB)")

        valid_languages = ['python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust', 'typescript']
        if data.get('language') and data['language'] not in valid_languages:
            raise ValueError(f"Unsupported language. Supported: {', '.join(valid_languages)}")

        valid_difficulties = ['easy', 'medium', 'hard']
        if data.get('difficulty_level') and data['difficulty_level'] not in valid_difficulties:
            raise ValueError(f"Invalid difficulty. Must be one of: {', '.join(valid_difficulties)}")

    async def _calculate_quality_score(self, showcase_data: Dict[str, Any]) -> float:
        """Calculate quality score for a showcase submission."""
        score = 0.0
        max_score = 10.0

        # Basic completeness (3 points)
        if showcase_data.get('approach_description'):
            score += 1.0
        if showcase_data.get('key_insights'):
            score += 1.0
        if showcase_data.get('performance_metrics'):
            score += 1.0

        # Content quality (4 points)
        description_length = len(showcase_data.get('description', ''))
        if description_length > 200:
            score += 1.0
        if description_length > 500:
            score += 1.0

        code_length = len(showcase_data.get('code_content', ''))
        if code_length > 200:
            score += 1.0
        if code_length > 1000:
            score += 1.0

        # Topics and metadata (3 points)
        if showcase_data.get('topics') and len(showcase_data['topics']) >= 2:
            score += 1.0
        if showcase_data.get('difficulty_level'):
            score += 1.0
        if showcase_data.get('performance_metrics') and len(showcase_data['performance_metrics']) > 0:
            score += 1.0

        # AI-based quality assessment (bonus points)
        ai_score = await self._assess_code_quality(showcase_data)
        score += ai_score

        return min(score / max_score, 1.0)

    async def _assess_code_quality(self, showcase_data: Dict[str, Any]) -> float:
        """Use AI to assess code quality."""
        try:
            prompt = f"""
            Assess the quality of this code submission for a showcase gallery:

            Language: {showcase_data.get('language', 'python')}
            Title: {showcase_data.get('title', '')}
            Description: {showcase_data.get('description', '')}
            Topics: {', '.join(showcase_data.get('topics', []))}

            Code (first 500 chars):
            {showcase_data.get('code_content', '')[:500]}

            Rate from 0.0 to 2.0 based on:
            - Code structure and organization
            - Best practices usage
            - Readability and documentation
            - Problem-solving approach

            Return only a number between 0.0 and 2.0.
            """

            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            score = float(response.content.strip())
            return max(0.0, min(2.0, score))

        except Exception as e:
            logger.error(f"AI quality assessment failed: {e}")
            return 0.5  # Neutral score

    async def _increment_views(self, showcase_id: int) -> None:
        """Increment view count for a showcase (async)."""
        try:
            showcase = self.db.query(ImplementationShowcase).filter(
                ImplementationShowcase.id == showcase_id
            ).first()

            if showcase:
                showcase.views += 1
                self.db.commit()

                # Invalidate cache
                if self.cache:
                    await self.cache.delete(f"showcase_data:{showcase_id}")

        except Exception as e:
            logger.error(f"Failed to increment views for showcase {showcase_id}: {e}")

    async def get_gallery_stats(self) -> Dict[str, Any]:
        """Get overall gallery statistics."""
        stats = self.db.query(
            func.count(ImplementationShowcase.id).label('total_showcases'),
            func.sum(ImplementationShowcase.upvotes).label('total_upvotes'),
            func.sum(ImplementationShowcase.views).label('total_views'),
            func.count(func.distinct(ImplementationShowcase.user_id)).label('unique_contributors')
        ).filter(ImplementationShowcase.status == 'approved').first()

        # Language distribution
        language_stats = self.db.query(
            ImplementationShowcase.language,
            func.count(ImplementationShowcase.id).label('count')
        ).filter(ImplementationShowcase.status == 'approved').group_by(
            ImplementationShowcase.language
        ).all()

        return {
            'total_showcases': stats.total_showcases or 0,
            'total_upvotes': stats.total_upvotes or 0,
            'total_views': stats.total_views or 0,
            'unique_contributors': stats.unique_contributors or 0,
            'language_distribution': {lang: count for lang, count in language_stats}
        }
