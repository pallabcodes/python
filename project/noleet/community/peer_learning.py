"""Peer Learning Engine - Orchestrates community-powered learning experiences."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from aiframework import AIFramework

from .contribution_system import CommunityContributionSystem, CommunityContribution, ContributionType
from .community_intelligence import CommunityIntelligenceAgent, CommunityContext


@dataclass
class LearningExperience:
    """A complete learning experience powered by community intelligence."""
    project_id: str
    project_title: str
    user_context: CommunityContext

    # Community insights and analysis
    community_insights: List[Any] = None  # CommunityInsight objects
    peer_recommendations: List[Any] = None  # PeerRecommendation objects
    learning_patterns: Dict[str, Any] = None
    community_stats: Dict[str, Any] = None

    # Personalized learning path
    recommended_sequence: List[str] = None  # Contribution IDs in recommended order
    learning_objectives: List[str] = None
    estimated_learning_time: str = None

    # Progress tracking
    completed_contributions: List[str] = None
    current_focus: str = None


@dataclass
class LearningSession:
    """An active learning session with community support."""
    session_id: str
    experience: LearningExperience
    start_time: float = None
    current_contribution: str = None
    session_insights: List[str] = None


class PeerLearningEngine:
    """Engine that orchestrates community-powered learning experiences."""

    def __init__(
        self,
        ai_framework: AIFramework,
        contribution_system: CommunityContributionSystem,
        community_intelligence: CommunityIntelligenceAgent
    ):
        """
        Initialize the Peer Learning Engine.

        Args:
            ai_framework: AI Framework for content analysis
            contribution_system: Community contribution management
            community_intelligence: AI-powered community analysis
        """
        self._ai_framework = ai_framework
        self._contribution_system = contribution_system
        self._community_intelligence = community_intelligence
        self._logger = logging.getLogger(__name__)

        # Active learning sessions
        self._active_sessions: Dict[str, LearningSession] = {}

    async def create_learning_experience(
        self,
        project_id: str,
        user_topics: List[str],
        user_skill_level: str,
        learning_goal: str = "general",
        preferred_languages: Optional[List[str]] = None
    ) -> LearningExperience:
        """
        Create a personalized learning experience for a project.

        Args:
            project_id: The project to learn
            user_topics: User's DSA topics of interest
            user_skill_level: User's skill level
            learning_goal: Learning objective
            preferred_languages: Preferred programming languages

        Returns:
            Complete learning experience with community insights
        """
        try:
            self._logger.info(f"Creating learning experience for project {project_id}")

            # Create community context
            context = CommunityContext(
                user_topics=user_topics,
                user_skill_level=user_skill_level,
                current_project=project_id,
                learning_goal=learning_goal,
                preferred_languages=preferred_languages or ["python"]
            )

            # Analyze community for this project
            community_analysis = await self._community_intelligence.analyze_community_for_project(
                project_id, context
            )

            # Create learning objectives
            learning_objectives = await self._generate_learning_objectives(
                project_id, context, community_analysis
            )

            # Create recommended learning sequence
            recommended_sequence = await self._create_learning_sequence(
                project_id, context, community_analysis
            )

            # Estimate learning time
            estimated_time = await self._estimate_learning_time(
                project_id, context, recommended_sequence
            )

            # Create the complete learning experience
            experience = LearningExperience(
                project_id=project_id,
                project_title=f"Project {project_id}",  # Could be enhanced to get actual title
                user_context=context,
                community_insights=community_analysis.get("insights", []),
                peer_recommendations=community_analysis.get("peer_recommendations", []),
                learning_patterns=community_analysis.get("patterns", {}),
                community_stats=community_analysis.get("community_stats", {}),
                recommended_sequence=recommended_sequence,
                learning_objectives=learning_objectives,
                estimated_learning_time=estimated_time,
                completed_contributions=[],
                current_focus=recommended_sequence[0] if recommended_sequence else None
            )

            self._logger.info(f"Created learning experience with {len(recommended_sequence)} recommended contributions")
            return experience

        except Exception as e:
            self._logger.error(f"Error creating learning experience: {e}")
            # Return basic experience on error
            return LearningExperience(
                project_id=project_id,
                project_title=f"Project {project_id}",
                user_context=context,
                learning_objectives=["Complete the project implementation"]
            )

    async def start_learning_session(
        self,
        experience: LearningExperience
    ) -> str:
        """
        Start an interactive learning session.

        Args:
            experience: The learning experience to start

        Returns:
            Session ID for the learning session
        """
        session_id = f"learn_session_{experience.project_id}_{int(asyncio.get_event_loop().time())}"

        session = LearningSession(
            session_id=session_id,
            experience=experience,
            start_time=asyncio.get_event_loop().time(),
            current_contribution=experience.current_focus,
            session_insights=[]
        )

        self._active_sessions[session_id] = session

        self._logger.info(f"Started learning session {session_id} for project {experience.project_id}")
        return session_id

    async def get_next_learning_step(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get the next recommended learning step for a session.

        Args:
            session_id: The learning session ID

        Returns:
            Next learning step with contribution and guidance
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        experience = session.experience

        # Find next incomplete contribution
        next_contribution_id = None
        for contrib_id in experience.recommended_sequence:
            if contrib_id not in experience.completed_contributions:
                next_contribution_id = contrib_id
                break

        if not next_contribution_id:
            return {
                "status": "completed",
                "message": "All recommended contributions completed!",
                "next_steps": ["Create your own implementation", "Share with the community"]
            }

        # Get the contribution
        contribution = await self._contribution_system.get_contribution(next_contribution_id)
        if not contribution:
            return {"error": "Recommended contribution not found"}

        # Generate learning guidance
        guidance = await self._generate_step_guidance(contribution, experience.user_context)

        return {
            "status": "in_progress",
            "contribution": contribution,
            "guidance": guidance,
            "progress": {
                "completed": len(experience.completed_contributions),
                "total": len(experience.recommended_sequence),
                "percentage": len(experience.completed_contributions) / len(experience.recommended_sequence) * 100
            }
        }

    async def mark_contribution_complete(
        self,
        session_id: str,
        contribution_id: str,
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None
    ) -> bool:
        """
        Mark a contribution as completed in the learning session.

        Args:
            session_id: The learning session ID
            contribution_id: The completed contribution ID
            user_rating: Optional user rating (1-5)
            user_feedback: Optional user feedback

        Returns:
            True if marked successfully, False otherwise
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return False

        experience = session.experience

        if contribution_id not in experience.completed_contributions:
            experience.completed_contributions.append(contribution_id)

            # Record user feedback if provided
            if user_rating or user_feedback:
                await self._record_user_feedback(contribution_id, user_rating, user_feedback)

        # Update current focus to next contribution
        for contrib_id in experience.recommended_sequence:
            if contrib_id not in experience.completed_contributions:
                experience.current_focus = contrib_id
                break
        else:
            experience.current_focus = None  # All completed

        self._logger.info(f"Marked contribution {contribution_id} complete in session {session_id}")
        return True

    async def get_learning_insights(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get personalized learning insights for the current session.

        Args:
            session_id: The learning session ID

        Returns:
            Learning insights and recommendations
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        experience = session.experience

        # Generate insights based on completed work
        insights = await self._generate_session_insights(session)

        # Get community patterns
        patterns = experience.learning_patterns or {}

        # Generate next recommendations
        next_recommendations = await self._get_next_recommendations(session)

        return {
            "personal_insights": insights,
            "community_patterns": patterns,
            "next_recommendations": next_recommendations,
            "progress_summary": {
                "completed": len(experience.completed_contributions),
                "total_recommended": len(experience.recommended_sequence),
                "completion_rate": len(experience.completed_contributions) / max(len(experience.recommended_sequence), 1) * 100
            }
        }

    async def _generate_learning_objectives(
        self,
        project_id: str,
        context: CommunityContext,
        community_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized learning objectives."""

        # Get project contributions to understand scope
        contributions = await self._contribution_system.get_project_contributions(
            project_id=project_id,
            limit=10
        )

        if not contributions:
            return [
                f"Implement {project_id} using appropriate DSA concepts",
                "Test your implementation thoroughly",
                "Optimize for time and space complexity"
            ]

        # Analyze contribution topics
        all_topics = set()
        for contrib in contributions:
            all_topics.update(contrib.topics)

        objectives = [
            f"Master {', '.join(list(all_topics)[:3])} through practical implementation",
            "Compare your approach with community solutions",
            "Understand different implementation strategies and trade-offs"
        ]

        if context.user_skill_level == "beginner":
            objectives.extend([
                "Focus on code correctness and understanding",
                "Learn basic problem-solving patterns"
            ])
        elif context.user_skill_level == "intermediate":
            objectives.extend([
                "Optimize for efficiency and edge cases",
                "Explore alternative algorithmic approaches"
            ])
        else:  # advanced
            objectives.extend([
                "Implement custom optimizations and extensions",
                "Analyze theoretical complexity vs practical performance"
            ])

        return objectives

    async def _create_learning_sequence(
        self,
        project_id: str,
        context: CommunityContext,
        community_analysis: Dict[str, Any]
    ) -> List[str]:
        """Create a recommended learning sequence."""

        # Get all project contributions
        contributions = await self._contribution_system.get_project_contributions(
            project_id=project_id,
            limit=20
        )

        if not contributions:
            return []

        # Sort by quality and relevance
        scored_contributions = []
        for contrib in contributions:
            relevance = self._calculate_learning_relevance(contrib, context)
            quality = contrib.quality_score
            combined_score = (relevance * 0.6) + (quality * 0.4)
            scored_contributions.append((contrib.id, combined_score))

        # Sort by combined score
        scored_contributions.sort(key=lambda x: x[1], reverse=True)

        # Return top contribution IDs (limit based on skill level)
        limit = 3 if context.user_skill_level == "beginner" else 5
        return [contrib_id for contrib_id, score in scored_contributions[:limit]]

    def _calculate_learning_relevance(
        self,
        contribution: CommunityContribution,
        context: CommunityContext
    ) -> float:
        """Calculate how relevant a contribution is for learning."""

        score = 0.0

        # Topic relevance
        topic_overlap = len(set(contribution.topics) & set(context.user_topics))
        score += topic_overlap * 0.4

        # Skill level appropriateness
        if context.user_skill_level == "beginner":
            if any(tag in contribution.tags for tag in ["beginner", "basic", "simple"]):
                score += 0.3
        elif context.user_skill_level == "intermediate":
            if any(tag in contribution.tags for tag in ["intermediate", "medium"]):
                score += 0.3
        else:  # advanced
            if any(tag in contribution.tags for tag in ["advanced", "expert", "complex"]):
                score += 0.3

        # Contribution type value for learning
        if contribution.contribution_type == ContributionType.PROJECT_IMPLEMENTATION:
            score += 0.2  # Complete implementations are highly valuable
        elif contribution.contribution_type == ContributionType.LEARNING_INSIGHT:
            score += 0.15  # Insights provide learning value

        return min(score, 1.0)

    async def _estimate_learning_time(
        self,
        project_id: str,
        context: CommunityContext,
        sequence: List[str]
    ) -> str:
        """Estimate total learning time for the sequence."""

        if not sequence:
            return "2-4 hours"

        # Base time estimates by skill level
        base_times = {
            "beginner": 2,      # hours per contribution
            "intermediate": 1.5,
            "advanced": 1
        }

        base_time_per = base_times.get(context.user_skill_level, 1.5)
        total_hours = len(sequence) * base_time_per

        if total_hours < 4:
            return f"{int(total_hours * 60)} minutes - {int((total_hours + 0.5) * 60)} minutes"
        elif total_hours < 24:
            return f"{int(total_hours)} - {int(total_hours + 2)} hours"
        else:
            days = total_hours / 8
            return f"{int(days)} - {int(days + 1)} days"

    async def _generate_step_guidance(
        self,
        contribution: CommunityContribution,
        context: CommunityContext
    ) -> Dict[str, Any]:
        """Generate guidance for learning from a specific contribution."""

        guidance = {
            "focus_areas": [],
            "learning_tips": [],
            "comparison_points": [],
            "next_questions": []
        }

        # Generate personalized guidance based on contribution type and user context
        if contribution.contribution_type == ContributionType.PROJECT_IMPLEMENTATION:
            guidance["focus_areas"] = [
                "Study the overall problem-solving approach",
                "Analyze the data structures and algorithms chosen",
                "Review error handling and edge cases"
            ]

            guidance["learning_tips"] = [
                "Compare this implementation with your current approach",
                "Note any optimization techniques used",
                "Consider how this handles different input scenarios"
            ]

        elif contribution.contribution_type == ContributionType.LEARNING_INSIGHT:
            guidance["focus_areas"] = [
                "Understand the key insight or pattern described",
                "See how it applies to the current problem",
                "Consider when this insight would be useful"
            ]

        guidance["comparison_points"] = [
            "How does this approach differ from others you've seen?",
            "What are the trade-offs in terms of time/space complexity?",
            "When would you choose this approach over alternatives?"
        ]

        guidance["next_questions"] = [
            "What would you change about this implementation?",
            "How could you extend this to solve related problems?",
            "What other DSA concepts could be applied here?"
        ]

        return guidance

    async def _record_user_feedback(
        self,
        contribution_id: str,
        rating: Optional[int],
        feedback: Optional[str]
    ) -> None:
        """Record user feedback on a contribution."""
        # This could be enhanced to update contribution quality scores
        # For now, just log the feedback
        self._logger.info(f"User feedback for {contribution_id}: rating={rating}, feedback='{feedback}'")

    async def _generate_session_insights(self, session: LearningSession) -> List[str]:
        """Generate insights based on session progress."""

        experience = session.experience
        completed_count = len(experience.completed_contributions)
        total_count = len(experience.recommended_sequence)

        insights = []

        if completed_count == 0:
            insights.append("You're just starting your learning journey - focus on understanding the core concepts first.")
        elif completed_count < total_count / 2:
            insights.append("You're making good progress! Try comparing different approaches you've studied.")
        elif completed_count < total_count:
            insights.append("You're in the home stretch! Focus on synthesizing what you've learned across all contributions.")
        else:
            insights.append("Excellent work completing all recommended contributions! Now try implementing your own version.")

        # Add topic-specific insights
        if experience.user_context.user_topics:
            topic_insights = await self._generate_topic_insights(experience.user_context.user_topics)
            insights.extend(topic_insights)

        return insights

    async def _generate_topic_insights(self, topics: List[str]) -> List[str]:
        """Generate insights about specific topics."""
        insights = []

        topic_patterns = {
            "dynamic_programming": "Focus on identifying overlapping subproblems and optimal substructure",
            "arrays": "Master multiple traversal techniques and in-place modifications",
            "trees": "Understand recursive patterns and different traversal orders",
            "graphs": "Practice with different representations and traversal algorithms",
            "sorting": "Compare time/space trade-offs between different algorithms"
        }

        for topic in topics[:3]:  # Limit to top 3 topics
            if topic in topic_patterns:
                insights.append(f"For {topic.replace('_', ' ')}: {topic_patterns[topic]}")

        return insights

    async def _get_next_recommendations(self, session: LearningSession) -> List[Dict[str, Any]]:
        """Get next recommended learning steps."""

        experience = session.experience

        if not experience.current_focus:
            # All recommended completed - suggest next steps
            return [
                {
                    "type": "implementation",
                    "title": "Create Your Own Implementation",
                    "description": "Now that you've studied community approaches, implement your own version"
                },
                {
                    "type": "contribution",
                    "title": "Share Your Solution",
                    "description": "Contribute your implementation back to the community"
                },
                {
                    "type": "extension",
                    "title": "Extend the Project",
                    "description": "Add new features or optimize the existing implementation"
                }
            ]

        # Get next contribution
        next_contrib = await self._contribution_system.get_contribution(experience.current_focus)
        if next_contrib:
            return [{
                "type": "study",
                "title": f"Study: {next_contrib.title}",
                "description": next_contrib.description[:100] + "...",
                "contribution_id": next_contrib.id
            }]

        return []

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active learning sessions."""
        return {
            "active_sessions": len(self._active_sessions),
            "total_sessions_started": len(self._active_sessions),  # Could track historical
            "most_popular_projects": [],  # Could analyze session data
            "average_completion_rate": 0.0  # Could calculate from session data
        }
