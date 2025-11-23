"""AI-powered project recommendation service using the AI Framework."""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from pathlib import Path

from ..core.models import Project, Topic
from ..storage.repository import ProjectRepository
from aiframework import AIFramework
from aiframework.config import FrameworkConfig
from aiframework.types import GenerationRequest


@dataclass
class AIRecommendation:
    """AI-powered recommendation with reasoning."""
    project: Project
    confidence_score: float
    reasoning: str
    matched_topics: Set[str]
    complexity_match: str
    learning_outcomes: List[str]


@dataclass
class RecommendationContext:
    """Context for AI recommendations."""
    selected_topics: Set[str]
    user_level: str = "intermediate"  # beginner, intermediate, advanced
    project_goal: str = "portfolio"  # portfolio, interview_prep, learning
    time_available: str = "medium"  # short, medium, long
    preferred_complexity: str = "medium"  # low, medium, high
    career_focus: Optional[str] = None  # frontend, backend, fullstack, ml, etc.
    previous_projects_count: int = 0  # number of projects completed
    learning_pace: str = "moderate"  # slow, moderate, fast


class AIRecommendationService:
    """AI-powered project recommendation service."""

    def __init__(
        self,
        data_dir: Path,
        ai_config: Optional[FrameworkConfig] = None
    ):
        """
        Initialize AI recommendation service.

        Args:
            data_dir: Directory containing project data
            ai_config: AI Framework configuration
        """
        self._data_dir = data_dir
        self._repository = ProjectRepository(data_dir)
        self._logger = logging.getLogger(__name__)

        # Initialize AI Framework
        if ai_config is None:
            ai_config = AIFrameworkConfig()
        self._ai_framework = AIFramework(ai_config)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ai_framework.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._ai_framework.__aexit__(exc_type, exc_val, exc_tb)

    async def get_recommendations(
        self,
        topic_names: List[str],
        context: Optional[RecommendationContext] = None,
        max_recommendations: int = 5
    ) -> List[AIRecommendation]:
        """
        Get AI-powered project recommendations with conditional logic.

        Args:
            topic_names: List of topic names selected by user
            context: Additional context for recommendations
            max_recommendations: Maximum number of recommendations to return

        Returns:
            List of AI-powered recommendations
        """
        try:
            # Load all projects
            projects = self._repository.load_projects()
            if not projects:
                self._logger.warning("No projects available for recommendations")
                return []

            if context is None:
                context = RecommendationContext(
                    selected_topics=set(topic_names)
                )
            else:
                context.selected_topics.update(topic_names)

            # Apply conditional filtering and prioritization
            filtered_projects = await self._apply_conditional_logic(projects, context)

            # Get AI-powered recommendations with enhanced context
            recommendations = await self._generate_ai_recommendations(
                filtered_projects, context, max_recommendations
            )

            self._logger.info(
                f"Generated {len(recommendations)} conditional AI recommendations for topics: {topic_names}"
            )

            return recommendations

        except Exception as e:
            self._logger.error(f"Failed to generate conditional AI recommendations: {e}")
            # Fallback to basic matching if AI fails
            return await self._fallback_recommendations(projects, topic_names, max_recommendations)

    async def _apply_conditional_logic(
        self,
        projects: List[Project],
        context: RecommendationContext
    ) -> List[Project]:
        """
        Apply conditional logic to filter and prioritize projects based on user context.

        Args:
            projects: All available projects
            context: User context for conditional logic

        Returns:
            Filtered and prioritized list of projects
        """
        filtered_projects = []

        for project in projects:
            # Apply user level filtering
            if not self._matches_user_level(project, context.user_level):
                continue

            # Apply time availability filtering
            if not self._matches_time_availability(project, context.time_available):
                continue

            # Apply project goal filtering
            if not self._matches_project_goal(project, context.project_goal):
                continue

            # Apply career focus filtering if specified
            if context.career_focus and not self._matches_career_focus(project, context.career_focus):
                continue

            filtered_projects.append(project)

        # Sort by relevance to user context
        filtered_projects.sort(key=lambda p: self._calculate_context_relevance(p, context), reverse=True)

        self._logger.info(
            f"Applied conditional logic: {len(projects)} → {len(filtered_projects)} projects"
        )

        return filtered_projects

    def _matches_user_level(self, project: Project, user_level: str) -> bool:
        """Check if project matches user's skill level."""
        level_mapping = {
            "beginner": ["beginner", "easy"],
            "intermediate": ["beginner", "intermediate", "easy", "medium"],
            "advanced": ["intermediate", "advanced", "medium", "hard"]
        }

        allowed_levels = level_mapping.get(user_level.lower(), ["beginner", "intermediate"])
        return project.difficulty.lower() in allowed_levels

    def _matches_time_availability(self, project: Project, time_available: str) -> bool:
        """Check if project matches user's time availability."""
        time_mapping = {
            "short": lambda h: h <= 20,  # 1-2 weeks
            "medium": lambda h: h <= 80,  # 1-2 months
            "long": lambda h: True  # Any duration
        }

        time_check = time_mapping.get(time_available.lower(), lambda h: True)
        return time_check(project.estimated_hours)

    def _matches_project_goal(self, project: Project, project_goal: str) -> bool:
        """Check if project matches user's learning goals."""
        goal_keywords = {
            "portfolio": ["portfolio", "showcase", "demo", "web", "app", "full-stack"],
            "interview_prep": ["algorithm", "coding", "interview", "technical", "problem"],
            "learning": []  # All projects are good for learning
        }

        if project_goal.lower() == "learning":
            return True

        keywords = goal_keywords.get(project_goal.lower(), [])
        if not keywords:
            return True

        project_text = f"{project.name} {project.description} {' '.join(project.tags)}".lower()
        return any(keyword in project_text for keyword in keywords)

    def _matches_career_focus(self, project: Project, career_focus: str) -> bool:
        """Check if project matches user's career focus."""
        focus_keywords = {
            "frontend": ["frontend", "web", "ui", "ux", "react", "vue", "angular", "javascript", "html", "css"],
            "backend": ["backend", "api", "server", "database", "python", "java", "node", "django", "flask"],
            "fullstack": ["full", "stack", "web", "frontend", "backend", "app"],
            "ml": ["machine", "learning", "ai", "data", "science", "neural", "model"],
            "mobile": ["mobile", "ios", "android", "react", "native", "flutter"],
            "devops": ["devops", "cloud", "aws", "docker", "kubernetes", "ci", "cd"]
        }

        keywords = focus_keywords.get(career_focus.lower(), [])
        if not keywords:
            return True

        project_text = f"{project.name} {project.description} {' '.join(project.tags)}".lower()
        return any(keyword in project_text for keyword in keywords)

    def _calculate_context_relevance(self, project: Project, context: RecommendationContext) -> float:
        """Calculate how relevant a project is to the user's context."""
        relevance_score = 0.0

        # Base relevance from topic matching
        topic_overlap = len(set(project.topics) & context.selected_topics)
        relevance_score += topic_overlap * 0.4

        # User level alignment bonus
        if self._matches_user_level(project, context.user_level):
            relevance_score += 0.2

        # Time availability alignment bonus
        if self._matches_time_availability(project, context.time_available):
            relevance_score += 0.15

        # Project goal alignment bonus
        if self._matches_project_goal(project, context.project_goal):
            relevance_score += 0.15

        # Career focus alignment bonus
        if context.career_focus and self._matches_career_focus(project, context.career_focus):
            relevance_score += 0.1

        # Experience level consideration
        if context.previous_projects_count > 5 and project.complexity == "hard":
            relevance_score += 0.1  # Experienced users can handle harder projects
        elif context.previous_projects_count <= 2 and project.complexity == "easy":
            relevance_score += 0.1  # New users benefit from easier starts

        return min(relevance_score, 1.0)  # Cap at 1.0

    async def _generate_ai_recommendations(
        self,
        projects: List[Project],
        context: RecommendationContext,
        max_recommendations: int
    ) -> List[AIRecommendation]:
        """Generate AI-powered recommendations using the AI Framework."""

        # Prepare project data for AI analysis
        project_summaries = []
        for project in projects:
            summary = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "topics": list(project.topics),
                "complexity": project.complexity,
                "estimated_time": project.estimated_time,
                "learning_outcomes": project.learning_outcomes,
                "prerequisites": project.prerequisites
            }
            project_summaries.append(summary)

        # Create AI prompt for recommendations
        prompt = self._build_recommendation_prompt(
            project_summaries, context, max_recommendations
        )

        # Generate recommendations using AI Framework
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
            system_message="You are an expert DSA educator who recommends projects that help developers master data structures and algorithms through practical application."
        )

        try:
            response = await self._ai_framework.generate(request)
            recommendations_data = self._parse_ai_response(response.content)

            # Convert to AIRecommendation objects
            recommendations = []
            for rec_data in recommendations_data[:max_recommendations]:
                project = next(
                    (p for p in projects if p.id == rec_data["project_id"]),
                    None
                )
                if project:
                    recommendation = AIRecommendation(
                        project=project,
                        confidence_score=rec_data.get("confidence_score", 0.8),
                        reasoning=rec_data.get("reasoning", ""),
                        matched_topics=set(rec_data.get("matched_topics", [])),
                        complexity_match=rec_data.get("complexity_match", "medium"),
                        learning_outcomes=rec_data.get("learning_outcomes", [])
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            self._logger.error(f"AI recommendation generation failed: {e}")
            # Fallback to basic recommendations
            return await self._fallback_recommendations(
                projects, list(context.selected_topics), max_recommendations
            )

    def _build_recommendation_prompt(
        self,
        projects: List[Dict[str, Any]],
        context: RecommendationContext,
        max_recommendations: int
    ) -> str:
        """Build the AI prompt for conditional project recommendations."""

        prompt = f"""
You are an expert DSA educator making personalized project recommendations. Use the user's context to make highly relevant suggestions.

USER CONTEXT PROFILE:
- Selected Topics: {', '.join(context.selected_topics)}
- Skill Level: {context.user_level.title()} ({'Just starting' if context.user_level == 'beginner' else 'Some experience' if context.user_level == 'intermediate' else 'Very experienced'})
- Learning Goal: {context.project_goal.replace('_', ' ').title()}
- Time Available: {context.time_available.title()} ({'1-2 weeks' if context.time_available == 'short' else '1-2 months' if context.time_available == 'medium' else '3+ months'})
- Preferred Complexity: {context.preferred_complexity.title()}
- Experience Level: {context.previous_projects_count} projects completed
{f'- Career Focus: {context.career_focus.title()}' if context.career_focus else ''}
{f'- Learning Pace: {context.learning_pace.title()}' if context.learning_pace != 'moderate' else ''}

CONDITIONAL RECOMMENDATION RULES:

1. SKILL LEVEL FILTERING:
   - BEGINNER: Only recommend easy/beginner projects with detailed guidance
   - INTERMEDIATE: Include easy-medium projects, moderate guidance needed
   - ADVANCED: Include medium-hard projects, minimal guidance required

2. TIME AVAILABILITY FILTERING:
   - SHORT: Projects completable in 1-2 weeks (≤20 hours)
   - MEDIUM: Projects completable in 1-2 months (≤80 hours)
   - LONG: Any duration projects acceptable

3. GOAL-BASED PRIORITIZATION:
   - PORTFOLIO: Prioritize impressive, demo-able projects with visual appeal
   - INTERVIEW_PREP: Focus on algorithm-heavy projects with technical depth
   - LEARNING: Balance educational value with practical applicability

4. EXPERIENCE CONSIDERATION:
   - 0-2 projects: Start with simpler, well-guided projects
   - 3-5 projects: Introduce moderate complexity with some independence
   - 6+ projects: Challenge with advanced concepts and self-directed learning

{f'5. CAREER FOCUS ({context.career_focus.title()}):'}
{f'   - Prioritize projects relevant to {context.career_focus} development'}
{f'   - Include industry-standard tools and frameworks'}
{f'   - Consider career progression and market demand'}

AVAILABLE PROJECTS (Pre-filtered for your context):
"""

        for i, project in enumerate(projects[:20], 1):  # Limit to top 20 for prompt efficiency
            prompt += f"""
{i}. Project ID: {project['id']}
   Name: {project['name']}
   Description: {project['description']}
   Topics: {', '.join(project['topics'])}
   Complexity: {project['complexity']} | Time: {project['estimated_time']}
   Learning Outcomes: {', '.join(project['learning_outcomes'][:2])}
   Prerequisites: {', '.join(project['prerequisites'][:2]) if project['prerequisites'] else 'None'}
"""

        prompt += f"""

RECOMMENDATION INSTRUCTIONS:

1. CONSIDER USER CONTEXT FIRST: Match skill level, time availability, and goals
2. TOPIC RELEVANCE: Ensure strong alignment with selected topics
3. PROGRESSION APPROPRIATE: Match complexity to user experience level
4. PRACTICAL VALUE: Consider real-world applicability and portfolio value
5. LEARNING IMPACT: Choose projects that build meaningful skills

RECOMMEND EXACTLY {max_recommendations} PROJECTS (or fewer if insufficient matches)

For each recommendation provide:
- project_id: The exact project ID from the list
- confidence_score: 0.0-1.0 based on context alignment
- reasoning: 2-3 sentences explaining the recommendation fit
- matched_topics: Topics from user selection covered by this project
- complexity_match: "low", "medium", or "high" vs user preferences
- learning_outcomes: 2-3 key outcomes for this user
- suitability_notes: Why this matches their profile and goals

Return as JSON array of recommendation objects.
"""

        return prompt

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response into recommendation data."""
        try:
            # Try to extract JSON from response
            import json
            import re

            # Find JSON array in response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                if isinstance(recommendations, list):
                    return recommendations

            # Fallback: try parsing entire response as JSON
            return json.loads(response.strip())

        except (json.JSONDecodeError, AttributeError) as e:
            self._logger.warning(f"Failed to parse AI response as JSON: {e}")
            # Return empty list if parsing fails
            return []

    async def _fallback_recommendations(
        self,
        projects: List[Project],
        topic_names: List[str],
        max_recommendations: int
    ) -> List[AIRecommendation]:
        """Fallback to basic keyword matching when AI fails."""
        self._logger.info("Using fallback recommendation method")

        # Basic topic matching
        selected_topics = set(topic_names)
        recommendations = []

        for project in projects:
            if project.matches_topics(selected_topics):
                score = project.get_match_score(selected_topics)
                if score > 20:  # Basic threshold
                    recommendation = AIRecommendation(
                        project=project,
                        confidence_score=min(score / 100.0, 0.9),
                        reasoning=f"This project matches your selected topics with a score of {score:.1f}%.",
                        matched_topics=selected_topics & set(project.topics),
                        complexity_match="medium",
                        learning_outcomes=project.learning_outcomes
                    )
                    recommendations.append(recommendation)

        # Sort by confidence score
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

        return recommendations[:max_recommendations]
