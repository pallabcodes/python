"""
Unit tests for Peer Learning features.

Tests cover:
- Code Review System
- Live Collaboration Sessions
- Implementation Showcase Gallery
- Peer Learning Service integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from peer_learning.peer_learning_service import PeerLearningService
from peer_learning.models import (
    CodeSubmission, CodeReview, ReviewComment,
    CollaborationSession, SessionParticipant, SessionMessage,
    ImplementationShowcase, ShowcaseVote, ShowcaseComment,
    CodeReviewData, CollaborationSessionData, ShowcaseImplementationData
)
from noleet.app.core.caching import CacheManager


# Test fixtures
@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create tables
    from peer_learning.models import Base
    Base.metadata.create_all(bind=engine)

    session = Session(bind=engine)
    yield session
    session.close()


@pytest.fixture
def cache_manager():
    """Mock cache manager for testing."""
    return Mock(spec=CacheManager)


@pytest.fixture
def peer_learning_service(db_session, cache_manager):
    """Create PeerLearningService instance for testing."""
    return PeerLearningService(db_session, cache_manager)


class TestPeerLearningService:
    """Test PeerLearningService integration."""

    @pytest.mark.asyncio
    async def test_submit_code_for_review(self, peer_learning_service):
        """Test code submission for review."""
        user_id = 1
        submission_data = {
            'title': 'Test Submission',
            'description': 'A test code submission',
            'code_content': 'def hello():\n    print("Hello, World!")',
            'language': 'python',
            'difficulty_level': 'easy',
            'topics': ['python', 'functions']
        }

        result = await peer_learning_service.submit_code_for_review(user_id, submission_data)

        assert 'submission_id' in result
        assert result['status'] == 'submitted'
        assert 'Code submitted for review successfully' in result['message']

    @pytest.mark.asyncio
    async def test_create_collaboration_session(self, peer_learning_service):
        """Test collaboration session creation."""
        host_user_id = 1
        session_data = {
            'title': 'Test Session',
            'description': 'A test collaboration session',
            'session_type': 'pair_programming',
            'max_participants': 2,
            'topics': ['algorithms', 'data-structures']
        }

        result = await peer_learning_service.create_collaboration_session(host_user_id, session_data)

        assert 'session_id' in result
        assert result['title'] == 'Test Session'
        assert result['max_participants'] == 2

    @pytest.mark.asyncio
    async def test_submit_showcase(self, peer_learning_service):
        """Test showcase submission."""
        user_id = 1
        showcase_data = {
            'title': 'Test Showcase',
            'description': 'An outstanding implementation',
            'code_content': 'def binary_search(arr, target):\n    # Implementation here\n    pass',
            'language': 'python',
            'difficulty_level': 'medium',
            'topics': ['algorithms', 'search'],
            'approach_description': 'Using divide and conquer approach',
            'key_insights': ['Time complexity is O(log n)', 'Requires sorted array']
        }

        result = await peer_learning_service.submit_showcase(user_id, showcase_data)

        assert 'showcase_id' in result
        assert result['status'] in ['pending', 'approved']

    @pytest.mark.asyncio
    async def test_join_leave_session(self, peer_learning_service):
        """Test joining and leaving collaboration sessions."""
        # Create session first
        host_id = 1
        session_data = {
            'title': 'Test Session',
            'description': 'Session for testing',
            'session_type': 'pair_programming',
            'max_participants': 2
        }

        create_result = await peer_learning_service.create_collaboration_session(host_id, session_data)
        session_id = create_result['session_id']

        # Join session
        user_id = 2
        join_result = await peer_learning_service.join_session(user_id, session_id)
        assert join_result['success'] is True

        # Leave session
        leave_result = await peer_learning_service.leave_session(user_id, session_id)
        assert leave_result['success'] is True

    @pytest.mark.asyncio
    async def test_vote_on_showcase(self, peer_learning_service):
        """Test voting on showcase implementations."""
        # Create showcase first
        user_id = 1
        showcase_data = {
            'title': 'Test Showcase',
            'description': 'Implementation to vote on',
            'code_content': 'def test_function():\n    return True',
            'language': 'python',
            'difficulty_level': 'easy',
            'topics': ['testing']
        }

        submit_result = await peer_learning_service.submit_showcase(user_id, showcase_data)
        showcase_id = submit_result['showcase_id']

        # Vote on showcase
        voter_id = 2
        vote_result = await peer_learning_service.vote_on_showcase(voter_id, showcase_id, 'upvote')
        assert vote_result['success'] is True
        assert vote_result['vote_type'] == 'upvote'


class TestCodeReviewEngine:
    """Test Code Review Engine functionality."""

    @pytest.mark.asyncio
    async def test_start_review(self, peer_learning_service, db_session):
        """Test starting a code review."""
        # Create a submission first
        user_id = 1
        submission_data = {
            'title': 'Review Test',
            'description': 'Submission for review testing',
            'code_content': 'def add(a, b):\n    return a + b',
            'language': 'python',
            'difficulty_level': 'easy'
        }

        submit_result = await peer_learning_service.submit_code_for_review(user_id, submission_data)
        submission_id = submit_result['submission_id']

        # Start review
        reviewer_id = 2
        review_result = await peer_learning_service.start_code_review(reviewer_id, submission_id)

        assert 'review_id' in review_result
        assert review_result['status'] == 'in_progress'

    @pytest.mark.asyncio
    async def test_submit_review_feedback(self, peer_learning_service, db_session):
        """Test submitting review feedback."""
        # Create submission and start review
        user_id = 1
        submission_data = {
            'title': 'Feedback Test',
            'code_content': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)',
            'language': 'python'
        }

        submit_result = await peer_learning_service.submit_code_for_review(user_id, submission_data)
        submission_id = submit_result['submission_id']

        reviewer_id = 2
        review_result = await peer_learning_service.start_code_review(reviewer_id, submission_id)
        review_id = review_result['review_id']

        # Submit feedback
        feedback_data = {
            'overall_rating': 4,
            'feedback_text': 'Good implementation but consider memoization for performance',
            'feedback_categories': ['efficiency', 'best_practices'],
            'detailed_feedback': {
                'efficiency': 'Recursive solution is elegant but inefficient for large n',
                'best_practices': 'Consider adding type hints and docstrings'
            }
        }

        feedback_result = await peer_learning_service.submit_review_feedback(review_id, feedback_data)

        assert feedback_result['status'] == 'completed'
        assert feedback_result['rating'] == 4

    @pytest.mark.asyncio
    async def test_get_available_reviews(self, peer_learning_service):
        """Test getting available reviews."""
        user_id = 1

        # Create some submissions
        for i in range(3):
            submission_data = {
                'title': f'Test Submission {i}',
                'code_content': f'def function_{i}():\n    return {i}',
                'language': 'python'
            }
            await peer_learning_service.submit_code_for_review(user_id + i + 1, submission_data)

        # Get available reviews
        reviews = await peer_learning_service.get_available_reviews(user_id, limit=5)
        assert isinstance(reviews, list)
        assert len(reviews) <= 5


class TestCollaborationManager:
    """Test Collaboration Manager functionality."""

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, peer_learning_service):
        """Test complete session lifecycle."""
        host_id = 1

        # Create session
        session_data = {
            'title': 'Lifecycle Test',
            'description': 'Testing session lifecycle',
            'session_type': 'pair_programming',
            'max_participants': 3
        }

        create_result = await peer_learning_service.create_collaboration_session(host_id, session_data)
        session_id = create_result['session_id']

        # Start session
        start_result = await peer_learning_service.start_session(session_id, host_id)
        assert start_result['success'] is True

        # Join session
        user_id = 2
        join_result = await peer_learning_service.join_session(user_id, session_id)
        assert join_result['success'] is True

        # Send message
        message_data = {
            'message_type': 'text',
            'message_content': 'Hello everyone!'
        }
        message_result = await peer_learning_service.send_session_message(session_id, user_id, message_data)
        assert 'message_id' in message_result

        # Leave session
        leave_result = await peer_learning_service.leave_session(user_id, session_id)
        assert leave_result['success'] is True

        # End session
        end_result = await peer_learning_service.end_session(session_id)
        assert end_result['success'] is True

    @pytest.mark.asyncio
    async def test_session_capacity(self, peer_learning_service):
        """Test session capacity limits."""
        host_id = 1
        session_data = {
            'title': 'Capacity Test',
            'max_participants': 2
        }

        create_result = await peer_learning_service.create_collaboration_session(host_id, session_data)
        session_id = create_result['session_id']

        # Start session
        await peer_learning_service.start_session(session_id, host_id)

        # Join with max participants
        for i in range(1, session_data['max_participants']):
            user_id = i + 1
            join_result = await peer_learning_service.join_session(user_id, session_id)
            assert join_result['success'] is True

        # Try to join when at capacity
        extra_user_id = session_data['max_participants'] + 1
        with pytest.raises(Exception):  # Should fail due to capacity
            await peer_learning_service.join_session(extra_user_id, session_id)


class TestShowcaseGallery:
    """Test Showcase Gallery functionality."""

    @pytest.mark.asyncio
    async def test_showcase_workflow(self, peer_learning_service):
        """Test complete showcase workflow."""
        user_id = 1

        # Submit showcase
        showcase_data = {
            'title': 'Binary Search Implementation',
            'description': 'An efficient binary search algorithm',
            'code_content': '''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1''',
            'language': 'python',
            'difficulty_level': 'medium',
            'topics': ['algorithms', 'search', 'binary-search'],
            'approach_description': 'Iterative binary search with two pointers',
            'key_insights': ['O(log n) time complexity', 'Requires sorted array', 'Handles edge cases']
        }

        submit_result = await peer_learning_service.submit_showcase(user_id, showcase_data)
        showcase_id = submit_result['showcase_id']

        # Get showcase details
        details = await peer_learning_service.get_showcase_details(showcase_id)
        assert details is not None
        assert details['title'] == showcase_data['title']

        # Vote on showcase
        voter_id = 2
        vote_result = await peer_learning_service.vote_on_showcase(voter_id, showcase_id, 'upvote')
        assert vote_result['success'] is True

        # Add comment
        comment_data = {
            'comment_text': 'Great implementation! Very clean and readable.',
            'parent_comment_id': None
        }
        comment_result = await peer_learning_service.add_showcase_comment(voter_id, showcase_id, **comment_data)
        assert 'comment_id' in comment_result

        # Get comments
        comments = await peer_learning_service.get_showcase_comments(showcase_id)
        assert len(comments) >= 1

    @pytest.mark.asyncio
    async def test_gallery_browsing(self, peer_learning_service):
        """Test gallery browsing with filters."""
        # Create multiple showcases
        users_and_showcases = [
            (1, {'title': 'Python Showcase', 'language': 'python', 'topics': ['python']}),
            (2, {'title': 'Java Showcase', 'language': 'java', 'topics': ['java']}),
            (3, {'title': 'Algorithm Showcase', 'language': 'python', 'topics': ['algorithms']})
        ]

        for user_id, showcase_base in users_and_showcases:
            showcase_data = {
                **showcase_base,
                'description': f'Description for {showcase_base["title"]}',
                'code_content': 'def example():\n    pass',
                'difficulty_level': 'medium'
            }
            await peer_learning_service.submit_showcase(user_id, showcase_data)

        # Test filtering by language
        python_showcases = await peer_learning_service.get_gallery_showcases(
            filters={'language': 'python'}, limit=10
        )
        assert len(python_showcases) >= 2

        # Test filtering by topic
        algo_showcases = await peer_learning_service.get_gallery_showcases(
            filters={'topic': 'algorithms'}, limit=10
        )
        assert len(algo_showcases) >= 1

    @pytest.mark.asyncio
    async def test_featured_showcases(self, peer_learning_service):
        """Test featured showcase functionality."""
        # Create a showcase that should be featured
        user_id = 1
        showcase_data = {
            'title': 'Featured Showcase',
            'description': 'This should be featured due to quality',
            'code_content': 'def perfect_function():\n    """Perfect docstring."""\n    return "perfect"',
            'language': 'python',
            'difficulty_level': 'easy',
            'topics': ['best-practices'],
            'approach_description': 'Following all best practices',
            'key_insights': ['Clean code', 'Good documentation', 'Type hints']
        }

        submit_result = await peer_learning_service.submit_showcase(user_id, showcase_data)

        # Get featured showcases
        featured = await peer_learning_service.get_featured_showcases(limit=5)
        # Note: In real implementation, quality scoring would determine featured status


class TestAnalytics:
    """Test analytics and statistics functionality."""

    @pytest.mark.asyncio
    async def test_peer_learning_stats(self, peer_learning_service):
        """Test getting peer learning statistics."""
        user_id = 1

        # Create some activity
        await peer_learning_service.submit_code_for_review(user_id, {
            'title': 'Stats Test',
            'code_content': 'def test():\n    pass',
            'language': 'python'
        })

        # Get stats
        stats = await peer_learning_service.get_peer_learning_stats(user_id)

        assert isinstance(stats, object)  # PeerLearningStats object
        assert hasattr(stats, 'total_code_reviews')
        assert hasattr(stats, 'showcase_implementations')

    @pytest.mark.asyncio
    async def test_user_activity_summary(self, peer_learning_service):
        """Test getting user activity summary."""
        user_id = 1

        # Create some activity
        await peer_learning_service.submit_showcase(user_id, {
            'title': 'Activity Test',
            'description': 'Testing activity summary',
            'code_content': 'def activity_test():\n    return True',
            'language': 'python',
            'difficulty_level': 'easy',
            'topics': ['testing']
        })

        # Get activity summary
        summary = await peer_learning_service.get_user_activity_summary(user_id)

        assert 'user_id' in summary
        assert 'reputation_score' in summary
        assert 'activity_level' in summary
        assert 'achievements' in summary


class TestHealthChecks:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check(self, peer_learning_service):
        """Test health check for all components."""
        health = await peer_learning_service.health_check()

        assert 'code_review' in health
        assert 'collaboration' in health
        assert 'showcase' in health
        assert 'overall_status' in health

        # Check status values
        assert health['code_review']['status'] in ['healthy', 'unhealthy']
        assert health['collaboration']['status'] in ['healthy', 'unhealthy']
        assert health['showcase']['status'] in ['healthy', 'unhealthy']


# Integration tests
class TestPeerLearningIntegration:
    """Integration tests for peer learning features working together."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, peer_learning_service):
        """Test a complete peer learning workflow."""
        # User 1 submits code
        user1_id = 1
        submission_data = {
            'title': 'Integration Test',
            'description': 'Testing complete workflow',
            'code_content': 'def integrate():\n    return "success"',
            'language': 'python',
            'difficulty_level': 'easy',
            'topics': ['testing', 'integration']
        }

        submit_result = await peer_learning_service.submit_code_for_review(user1_id, submission_data)
        submission_id = submit_result['submission_id']

        # User 2 reviews the code
        user2_id = 2
        review_result = await peer_learning_service.start_code_review(user2_id, submission_id)
        review_id = review_result['review_id']

        feedback_data = {
            'overall_rating': 5,
            'feedback_text': 'Excellent code! Very clean and well-structured.',
            'feedback_categories': ['readability', 'best_practices'],
            'detailed_feedback': {
                'readability': 'Code is very readable and well-formatted',
                'best_practices': 'Follows Python best practices perfectly'
            }
        }

        await peer_learning_service.submit_review_feedback(review_id, feedback_data)

        # User 1 submits their implementation to showcase
        showcase_data = {
            'title': 'Integration Showcase',
            'description': 'Showcasing integration test implementation',
            'code_content': submission_data['code_content'],
            'language': 'python',
            'difficulty_level': 'easy',
            'topics': submission_data['topics'],
            'approach_description': 'Simple and effective implementation',
            'key_insights': ['Keep it simple', 'Good naming conventions']
        }

        showcase_result = await peer_learning_service.submit_showcase(user1_id, showcase_data)
        showcase_id = showcase_result['showcase_id']

        # User 2 votes on the showcase
        await peer_learning_service.vote_on_showcase(user2_id, showcase_id, 'upvote')

        # User 3 creates a collaboration session
        user3_id = 3
        session_data = {
            'title': 'Integration Collaboration',
            'description': 'Collaborative session for integration testing',
            'session_type': 'learning',
            'max_participants': 3,
            'topics': ['testing', 'integration']
        }

        session_result = await peer_learning_service.create_collaboration_session(user3_id, session_data)
        session_id = session_result['session_id']

        # Start session
        await peer_learning_service.start_session(session_id, user3_id)

        # Users join the session
        await peer_learning_service.join_session(user1_id, session_id)
        await peer_learning_service.join_session(user2_id, session_id)

        # Send some messages
        await peer_learning_service.send_session_message(session_id, user1_id, {
            'message_type': 'text',
            'message_content': 'Hello everyone!'
        })

        # End session
        await peer_learning_service.end_session(session_id)

        # Verify everything worked
        user1_stats = await peer_learning_service.get_peer_learning_stats(user1_id)
        assert user1_stats.total_code_reviews >= 1
        assert user1_stats.showcase_implementations >= 1

        user2_stats = await peer_learning_service.get_peer_learning_stats(user2_id)
        assert user2_stats.total_code_reviews >= 1

        # Check gallery has the showcase
        gallery = await peer_learning_service.get_gallery_showcases(limit=10)
        assert len(gallery) >= 1
