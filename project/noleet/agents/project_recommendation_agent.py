"""Project recommendation agent using intelligent matching and user profiling."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .base.agent_base import BaseAgent, AgentResult
from ..core.models import Project, Topic
from ..storage.repository import ProjectRepository
from ..intelligence.semantic_matcher import SemanticMatcher
from ..intelligence.recommendation_engine import RecommendationEngine
from ..intelligence.user_profiler import UserProfiler
from ..llm.llm_config import LLMConfig


class ProjectRecommendationAgent(BaseAgent):
    """Agent for intelligent project recommendations."""

    def __init__(
        self,
        project_repository: Optional[ProjectRepository] = None,
        semantic_matcher: Optional[SemanticMatcher] = None,
        user_profiler: Optional[UserProfiler] = None,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize project recommendation agent.

        Args:
            project_repository: Repository for accessing projects
            semantic_matcher: Semantic matching component
            user_profiler: User profiling component
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        super().__init__("project_recommendation", llm_config, logger)

        self._project_repo = project_repository or ProjectRepository()
        self._semantic_matcher = semantic_matcher or SemanticMatcher()
        self._user_profiler = user_profiler or UserProfiler()
        self._recommendation_engine = RecommendationEngine(
            self._semantic_matcher,
            self._user_profiler,
            logger
        )

        # Cache for loaded projects
        self._projects_cache: Optional[List[Project]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Generate project recommendations based on user input.

        Args:
            input_data: Input data containing user query and preferences

        Returns:
            Recommendation results
        """
        try:
            user_query = input_data.get("query", "")
            user_id = input_data.get("user_id")
            selected_topics = input_data.get("topics", [])
            max_recommendations = input_data.get("max_recommendations", 5)
            context = input_data.get("context", {})

            if not user_query and not selected_topics:
                return AgentResult(
                    success=False,
                    message="No query or topics provided for recommendations",
                    errors=["Missing query and topics"]
                )

            # Load projects
            projects = self._load_projects()

            if not projects:
                return AgentResult(
                    success=False,
                    message="No projects available for recommendations",
                    errors=["Empty project repository"]
                )

            # Convert topic strings to Topic enums
            topic_enums = self._parse_topics(selected_topics)

            # Generate recommendations
            recommendations = self._recommendation_engine.recommend_projects(
                projects=projects,
                user_query=user_query,
                user_id=user_id,
                selected_topics=topic_enums,
                max_recommendations=max_recommendations
            )

            # Format results
            formatted_results = self._format_recommendations(recommendations)

            # Add reasoning using LLM if available
            reasoning = self._generate_recommendation_reasoning(
                user_query, topic_enums, formatted_results, context
            )

            result_data = {
                "recommendations": formatted_results,
                "count": len(formatted_results),
                "query": user_query,
                "topics_used": [t.value for t in topic_enums],
                "reasoning": reasoning,
                "user_id": user_id
            }

            # Track user interaction
            if user_id:
                self._track_user_interaction(user_id, {
                    "query": user_query,
                    "topics": [t.value for t in topic_enums],
                    "recommendations_count": len(formatted_results)
                })

            # Add to memory
            self._add_to_memory(
                f"Generated recommendations for user {user_id or 'anonymous'}",
                f"Query: '{user_query}', Topics: {len(topic_enums)}, Recommendations: {len(formatted_results)}",
                {"query": user_query, "recommendation_count": len(formatted_results)}
            )

            self._logger.info(
                f"Generated {len(formatted_results)} recommendations for query: '{user_query}'"
            )

            return AgentResult(
                success=True,
                data=result_data,
                message=f"Successfully generated {len(formatted_results)} project recommendations"
            )

        except Exception as e:
            self._logger.error(f"Project recommendation failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                message="Project recommendation failed",
                errors=[str(e)]
            )

    def _load_projects(self) -> List[Project]:
        """Load projects with caching."""
        import time

        current_time = time.time()

        if (self._projects_cache is None or
            self._cache_timestamp is None or
            current_time - self._cache_timestamp > self._cache_ttl):

            self._projects_cache = self._project_repo.load_projects()
            self._cache_timestamp = current_time

            self._logger.debug(f"Loaded {len(self._projects_cache)} projects from repository")

        return self._projects_cache or []

    def _parse_topics(self, topic_strings: List[str]) -> List[Topic]:
        """Parse topic strings into Topic enums."""
        topics = []

        for topic_str in topic_strings:
            normalized = topic_str.lower().replace(" ", "_").replace("-", "_")

            # Try direct enum match
            try:
                topic = Topic(normalized)
                topics.append(topic)
                continue
            except ValueError:
                pass

            # Try fuzzy matching
            for topic_enum in Topic:
                if normalized in topic_enum.value or topic_enum.value in normalized:
                    topics.append(topic_enum)
                    break

        return topics

    def _format_recommendations(
        self,
        recommendations: List[Tuple[Project, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Format recommendations for output."""
        formatted = []

        for project, score_data in recommendations:
            formatted.append({
                "project_id": project.id,
                "title": project.title,
                "description": project.short_description,
                "difficulty": project.difficulty,
                "estimated_hours": project.estimated_hours,
                "primary_topics": [t.value.replace("_", " ").title() for t in project.primary_topics],
                "tags": project.tags,
                "score": score_data.total_score,
                "score_breakdown": {
                    "semantic": score_data.semantic_score,
                    "topic_overlap": score_data.topic_overlap_score,
                    "difficulty": score_data.difficulty_score,
                    "user_preference": score_data.user_preference_score
                }
            })

        return formatted

    def _generate_recommendation_reasoning(
        self,
        query: str,
        topics: List[Topic],
        recommendations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Generate reasoning for recommendations using LLM."""
        if not self.is_available() or not recommendations:
            return self._generate_fallback_reasoning(query, topics, recommendations)

        prompt = f"""
        Analyze these project recommendations and explain why they were chosen for the user's query.

        User Query: "{query}"
        Selected Topics: {', '.join(t.value.replace('_', ' ').title() for t in topics)}

        Recommendations:
        {self._format_recommendations_for_prompt(recommendations[:3])}

        Context: {context.get('additional_info', 'None provided')}

        Provide a concise explanation of why these projects were recommended, focusing on:
        1. Relevance to the query and topics
        2. Why these specific projects match well
        3. What the user will learn from each

        Keep the response under 300 words.
        """

        try:
            llm = self._llm_factory.create_llm()
            response = llm.generate(prompt)
            return response.strip()
        except Exception as e:
            self._logger.warning(f"LLM reasoning generation failed: {e}")
            return self._generate_fallback_reasoning(query, topics, recommendations)

    def _format_recommendations_for_prompt(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations for LLM prompt."""
        formatted = []

        for i, rec in enumerate(recommendations, 1):
            formatted.append(f"""
            {i}. {rec['title']}
               Difficulty: {rec['difficulty']}
               Topics: {', '.join(rec['primary_topics'])}
               Score: {rec['score']:.3f}
            """)

        return '\n'.join(formatted)

    def _generate_fallback_reasoning(
        self,
        query: str,
        topics: List[Topic],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate fallback reasoning without LLM."""
        if not recommendations:
            return "No suitable projects found for your query."

        reasoning_parts = [
            f"Based on your query '{query}' and selected topics "
            f"({', '.join(t.value.replace('_', ' ') for t in topics)}), "
            f"I recommend these {len(recommendations)} projects:"
        ]

        for rec in recommendations[:3]:
            reasoning_parts.append(
                f"- {rec['title']}: Matches your topics with a relevance score of {rec['score']:.2f}"
            )

        reasoning_parts.append(
            "These projects will help you practice the specific algorithms and data structures you selected."
        )

        return ' '.join(reasoning_parts)

    def _track_user_interaction(self, user_id: str, interaction_data: Dict[str, Any]):
        """Track user interaction for profiling."""
        try:
            self._user_profiler.track_project_interaction(
                user_id=user_id,
                project_id="recommendation_session",  # Generic ID for recommendation sessions
                interaction_type="recommendation_request",
                metadata=interaction_data
            )
        except Exception as e:
            self._logger.warning(f"Failed to track user interaction: {e}")

    def get_user_recommendation_history(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's recommendation history and preferences.

        Args:
            user_id: User identifier

        Returns:
            User's recommendation history
        """
        try:
            profile = self._user_profiler.get_profile(user_id)
            interactions = self._user_profiler.get_task_history("recommendation_request", limit=20)

            return {
                "user_id": user_id,
                "profile_exists": profile is not None,
                "total_recommendations": len(interactions),
                "recent_queries": [
                    {
                        "query": interaction["input_data"].get("query", ""),
                        "topics": interaction["input_data"].get("topics", []),
                        "timestamp": interaction["timestamp"]
                    }
                    for interaction in interactions[-5:]
                ]
            }

        except Exception as e:
            self._logger.error(f"Failed to get user history: {e}")
            return {"error": str(e)}

    def update_user_feedback(
        self,
        user_id: str,
        project_id: str,
        rating: float,
        feedback: Optional[str] = None
    ):
        """
        Update recommendation system with user feedback.

        Args:
            user_id: User identifier
            project_id: Project identifier
            rating: Rating (0.0 to 1.0)
            feedback: Optional feedback text
        """
        try:
            self._recommendation_engine.update_user_feedback(
                user_id, project_id, rating, feedback
            )

            self._logger.info(
                f"Updated user feedback for {user_id}: project {project_id}, rating {rating}"
            )

        except Exception as e:
            self._logger.error(f"Failed to update user feedback: {e}")

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get recommendation system statistics."""
        try:
            projects = self._load_projects()

            return {
                "total_projects": len(projects),
                "semantic_matcher_available": self._semantic_matcher.is_available(),
                "recommendation_engine_stats": self._recommendation_engine.get_recommendation_stats(),
                "cache_status": {
                    "projects_cached": self._projects_cache is not None,
                    "cache_age_seconds": (
                        None if self._cache_timestamp is None
                        else __import__("time").time() - self._cache_timestamp
                    )
                }
            }

        except Exception as e:
            self._logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

