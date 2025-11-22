"""Recommendation engine combining multiple signals."""

import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

from ..core.models import Project, Topic
from .semantic_matcher import SemanticMatcher
from .user_profiler import UserProfiler


@dataclass
class RecommendationScore:
    """Recommendation score with components."""
    semantic_score: float = 0.0
    topic_overlap_score: float = 0.0
    difficulty_score: float = 0.0
    user_preference_score: float = 0.0
    total_score: float = 0.0

    def calculate_total(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate total score with weights."""
        weights = weights or {
            "semantic": 0.4,
            "topic_overlap": 0.3,
            "difficulty": 0.1,
            "user_preference": 0.2
        }

        self.total_score = (
            self.semantic_score * weights["semantic"] +
            self.topic_overlap_score * weights["topic_overlap"] +
            self.difficulty_score * weights["difficulty"] +
            self.user_preference_score * weights["user_preference"]
        )

        return self.total_score


class RecommendationEngine:
    """Engine for intelligent project recommendations."""

    def __init__(
        self,
        semantic_matcher: Optional[SemanticMatcher] = None,
        user_profiler: Optional[UserProfiler] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize recommendation engine.

        Args:
            semantic_matcher: Semantic matching component
            user_profiler: User profiling component
            logger: Optional logger instance
        """
        self._semantic_matcher = semantic_matcher or SemanticMatcher()
        self._user_profiler = user_profiler or UserProfiler()
        self._logger = logger or logging.getLogger(__name__)

        # Scoring weights
        self._weights = {
            "semantic": 0.4,
            "topic_overlap": 0.3,
            "difficulty": 0.1,
            "user_preference": 0.2
        }

    def recommend_projects(
        self,
        projects: List[Project],
        user_query: str,
        user_id: Optional[str] = None,
        selected_topics: Optional[Set[Topic]] = None,
        max_recommendations: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[Project, RecommendationScore]]:
        """
        Recommend projects based on user query and preferences.

        Args:
            projects: Available projects
            user_query: User's search query or topic description
            user_id: User identifier for personalization
            selected_topics: Explicitly selected topics
            max_recommendations: Maximum recommendations to return
            min_score: Minimum score threshold

        Returns:
            List of (project, score) tuples
        """
        self._logger.info(f"Generating recommendations for query: '{user_query}'")

        # Extract topics from query if not provided
        if not selected_topics:
            selected_topics = self._extract_topics_from_query(user_query)

        if not selected_topics:
            self._logger.warning("No topics found in query, using all projects")
            selected_topics = set()  # Will match all projects

        # Get user profile if available
        user_profile = None
        if user_id:
            user_profile = self._user_profiler.get_profile(user_id)

        recommendations = []

        # Get semantic matches
        semantic_matches = self._semantic_matcher.find_matching_projects(
            projects, selected_topics, top_k=len(projects)
        )

        for project, semantic_score in semantic_matches:
            score = RecommendationScore(semantic_score=semantic_score)

            # Calculate topic overlap score
            score.topic_overlap_score = self._calculate_topic_overlap_score(
                project, selected_topics
            )

            # Calculate difficulty score
            score.difficulty_score = self._calculate_difficulty_score(
                project, user_profile
            )

            # Calculate user preference score
            score.user_preference_score = self._calculate_user_preference_score(
                project, user_profile
            )

            # Calculate final score
            final_score = score.calculate_total(self._weights)

            if final_score >= min_score:
                recommendations.append((project, score))

        # Sort by total score
        recommendations.sort(key=lambda x: x[1].total_score, reverse=True)

        self._logger.info(
            f"Generated {len(recommendations)} recommendations "
            f"(showing top {min(max_recommendations, len(recommendations))})"
        )

        return recommendations[:max_recommendations]

    def _extract_topics_from_query(self, query: str) -> Set[Topic]:
        """Extract DSA topics from user query."""
        from ..core.models import Topic

        query_lower = query.lower()
        found_topics = set()

        # Simple keyword matching for topics
        topic_keywords = {
            Topic.DYNAMIC_PROGRAMMING: ["dp", "dynamic programming"],
            Topic.SLIDING_WINDOW: ["sliding window", "window"],
            Topic.MERGE_INTERVALS: ["merge intervals", "intervals"],
            Topic.TWO_POINTERS: ["two pointers", "pointers"],
            Topic.BINARY_SEARCH: ["binary search", "search"],
            Topic.GRAPH_TRAVERSAL: ["graph", "dfs", "bfs"],
            Topic.TREE_TRAVERSAL: ["tree", "binary tree"],
            Topic.BACKTRACKING: ["backtracking", "backtrack"],
            Topic.GREEDY: ["greedy"],
            Topic.UNION_FIND: ["union find", "disjoint set"],
            Topic.TRIE: ["trie", "prefix tree"],
            Topic.HEAP: ["heap", "priority queue"],
            Topic.HASH_TABLE: ["hash", "hashmap", "hash table"],
            Topic.LINKED_LIST: ["linked list"],
            Topic.STACK: ["stack"],
            Topic.QUEUE: ["queue"],
            Topic.BIT_MANIPULATION: ["bit", "xor"],
            Topic.SORTING: ["sort", "sorting"],
            Topic.STRING_MATCHING: ["string", "pattern", "kmp"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_topics.add(topic)

        return found_topics

    def _calculate_topic_overlap_score(self, project: Project, query_topics: Set[Topic]) -> float:
        """Calculate topic overlap score."""
        if not query_topics:
            return 0.5  # Neutral score

        project_topics = project.primary_topics | project.required_topics
        overlap = len(project_topics.intersection(query_topics))

        return min(1.0, overlap / len(query_topics))

    def _calculate_difficulty_score(self, project: Project, user_profile: Optional[Dict] = None) -> float:
        """Calculate difficulty compatibility score."""
        difficulty_levels = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3
        }

        project_level = difficulty_levels.get(project.difficulty.lower(), 2)

        # Default to intermediate preference
        preferred_level = 2

        if user_profile:
            user_difficulty = user_profile.get("preferred_difficulty")
            if user_difficulty in difficulty_levels:
                preferred_level = difficulty_levels[user_difficulty]

        # Score based on difference (closer is better)
        difference = abs(project_level - preferred_level)
        return max(0.0, 1.0 - (difference * 0.3))

    def _calculate_user_preference_score(self, project: Project, user_profile: Optional[Dict] = None) -> float:
        """Calculate user preference score."""
        if not user_profile:
            return 0.5  # Neutral score

        score = 0.5

        # Check if user has completed similar projects
        completed_projects = user_profile.get("completed_projects", [])
        if any(cp["id"] == project.id for cp in completed_projects):
            return 0.0  # Don't recommend completed projects

        # Check preferred project types
        preferred_types = user_profile.get("preferred_project_types", [])
        if preferred_types:
            project_tags = set(project.tags or [])
            overlap = len(set(preferred_types).intersection(project_tags))
            if overlap > 0:
                score += 0.2

        return min(1.0, score)

    def update_user_feedback(
        self,
        user_id: str,
        project_id: str,
        rating: float,
        feedback: Optional[str] = None
    ):
        """
        Update recommendation engine with user feedback.

        Args:
            user_id: User identifier
            project_id: Project identifier
            rating: Rating (0.0 to 1.0)
            feedback: Optional feedback text
        """
        self._user_profiler.update_feedback(user_id, project_id, rating, feedback)

        self._logger.info(
            f"Updated user feedback for {user_id}: project {project_id}, rating {rating}"
        )

    def get_recommendation_stats(self) -> Dict[str, float]:
        """Get recommendation statistics."""
        return {
            "semantic_matcher_available": self._semantic_matcher.is_available(),
            "user_profiles_count": self._user_profiler.get_profile_count()
        }

