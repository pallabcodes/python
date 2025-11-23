"""Community Intelligence Agent - AI-powered analysis of peer learning content."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from pathlib import Path

from aiframework import AIFramework
from aiframework.types import GenerationRequest

from .contribution_system import (
    CommunityContributionSystem,
    CommunityContribution,
    ContributionType,
    ContributionSearchQuery
)


@dataclass
class CommunityInsight:
    """An AI-generated insight from community analysis."""
    insight_type: str  # 'pattern', 'best_practice', 'common_mistake', 'optimization'
    title: str
    description: str
    confidence_score: float
    related_contributions: List[str]
    applicable_topics: List[str]
    code_examples: List[str] = None


@dataclass
class PeerRecommendation:
    """AI-curated peer recommendation."""
    contribution: CommunityContribution
    relevance_score: float
    why_relevant: str
    learning_value: str
    implementation_notes: List[str]


@dataclass
class CommunityContext:
    """Context for community intelligence analysis."""
    user_topics: List[str]
    user_skill_level: str
    current_project: Optional[str] = None
    learning_goal: str = "general"
    preferred_languages: List[str] = None


class CommunityIntelligenceAgent:
    """AI agent that analyzes and surfaces community learning content."""

    def __init__(self, ai_framework: AIFramework, contribution_system: CommunityContributionSystem):
        """
        Initialize the Community Intelligence Agent.

        Args:
            ai_framework: AI Framework for content analysis
            contribution_system: Community contribution system
        """
        self._ai_framework = ai_framework
        self._contribution_system = contribution_system
        self._logger = logging.getLogger(__name__)

        # Cache for analysis results
        self._insights_cache: Dict[str, List[CommunityInsight]] = {}
        self._patterns_cache: Dict[str, Dict[str, Any]] = {}

    async def analyze_community_for_project(
        self,
        project_id: str,
        context: CommunityContext
    ) -> Dict[str, Any]:
        """
        Analyze community contributions for a specific project.

        Args:
            project_id: The project to analyze
            context: User context for personalization

        Returns:
            Analysis results with insights, patterns, and recommendations
        """
        try:
            self._logger.info(f"Analyzing community for project {project_id}")

            # Get all contributions for this project
            contributions = await self._contribution_system.get_project_contributions(
                project_id=project_id,
                limit=50  # Analyze up to 50 contributions
            )

            if not contributions:
                return {
                    "insights": [],
                    "patterns": {},
                    "peer_recommendations": [],
                    "community_stats": {"total_contributions": 0}
                }

            # Analyze contributions for insights and patterns
            insights = await self._extract_insights(contributions, context)
            patterns = await self._identify_patterns(contributions, context)
            peer_recommendations = await self._generate_peer_recommendations(
                contributions, context
            )

            # Community statistics
            community_stats = {
                "total_contributions": len(contributions),
                "average_quality_score": sum(c.quality_score for c in contributions) / len(contributions),
                "top_contribution_types": self._get_top_contribution_types(contributions),
                "most_helpful_contributions": len([c for c in contributions if c.helpful_count > 0])
            }

            return {
                "insights": insights,
                "patterns": patterns,
                "peer_recommendations": peer_recommendations,
                "community_stats": community_stats
            }

        except Exception as e:
            self._logger.error(f"Error analyzing community for project {project_id}: {e}")
            return {
                "insights": [],
                "patterns": {},
                "peer_recommendations": [],
                "community_stats": {"error": str(e)}
            }

    async def _extract_insights(
        self,
        contributions: List[CommunityContribution],
        context: CommunityContext
    ) -> List[CommunityInsight]:
        """
        Extract insights from community contributions.

        Args:
            contributions: List of contributions to analyze
            context: User context for relevance filtering

        Returns:
            List of extracted insights
        """
        if not contributions:
            return []

        # Combine contribution content for analysis
        combined_content = "\n\n".join([
            f"Title: {c.title}\nDescription: {c.description}\nContent: {c.content[:500]}..."
            for c in contributions[:10]  # Analyze top 10 contributions
        ])

        prompt = f"""
Analyze these community contributions about DSA implementation and extract key insights.

COMMUNITY CONTRIBUTIONS:
{combined_content}

USER CONTEXT:
- Skill Level: {context.user_skill_level}
- Topics of Interest: {', '.join(context.user_topics)}
- Learning Goal: {context.learning_goal}

Extract 3-5 key insights that would be valuable for someone learning these concepts. Each insight should include:

1. **Type**: pattern, best_practice, common_mistake, or optimization
2. **Title**: Clear, actionable title
3. **Description**: Detailed explanation with examples
4. **Confidence**: How confident you are in this insight (0.0-1.0)
5. **Topics**: Which DSA topics this applies to

Focus on insights that help with:
- Understanding algorithms better
- Avoiding common pitfalls
- Writing more efficient code
- Following best practices
- Debugging effectively

Return as a JSON array of insight objects.
"""

        try:
            request = GenerationRequest(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )

            response = await self._ai_framework.generate(request)

            # Parse the JSON response
            import json
            insights_data = json.loads(response.content.strip())

            insights = []
            for item in insights_data[:5]:  # Limit to top 5 insights
                insight = CommunityInsight(
                    insight_type=item.get('type', 'pattern'),
                    title=item.get('title', 'Community Insight'),
                    description=item.get('description', ''),
                    confidence_score=min(float(item.get('confidence', 0.8)), 1.0),
                    related_contributions=[c.id for c in contributions[:3]],  # Top 3 contributions
                    applicable_topics=item.get('topics', context.user_topics),
                    code_examples=item.get('code_examples', [])
                )
                insights.append(insight)

            return insights

        except Exception as e:
            self._logger.error(f"Error extracting insights: {e}")
            return []

    async def _identify_patterns(
        self,
        contributions: List[CommunityContribution],
        context: CommunityContext
    ) -> Dict[str, Any]:
        """
        Identify common patterns and approaches in contributions.

        Args:
            contributions: Contributions to analyze
            context: User context

        Returns:
            Dictionary of identified patterns
        """
        if len(contributions) < 3:
            return {"note": "Need more contributions to identify patterns"}

        # Analyze contribution types and approaches
        implementation_count = len([c for c in contributions
                                  if c.contribution_type == ContributionType.PROJECT_IMPLEMENTATION])
        snippet_count = len([c for c in contributions
                           if c.contribution_type == ContributionType.CODE_SNIPPET])

        # Common topics across contributions
        all_topics = set()
        for contribution in contributions:
            all_topics.update(contribution.topics)

        # Quality distribution
        high_quality = len([c for c in contributions if c.quality_score > 5.0])
        medium_quality = len([c for c in contributions if 2.0 <= c.quality_score <= 5.0])
        low_quality = len([c for c in contributions if c.quality_score < 2.0])

        patterns = {
            "contribution_distribution": {
                "implementations": implementation_count,
                "code_snippets": snippet_count,
                "other_types": len(contributions) - implementation_count - snippet_count
            },
            "topic_coverage": list(all_topics),
            "quality_distribution": {
                "high_quality": high_quality,
                "medium_quality": medium_quality,
                "low_quality": low_quality
            },
            "common_approaches": await self._analyze_common_approaches(contributions),
            "recommended_learning_path": await self._suggest_learning_path(contributions, context)
        }

        return patterns

    async def _analyze_common_approaches(
        self,
        contributions: List[CommunityContribution]
    ) -> List[str]:
        """Analyze common implementation approaches."""
        approaches = set()

        for contribution in contributions:
            content_lower = contribution.content.lower()
            # Simple pattern matching for common approaches
            if any(word in content_lower for word in ['recursion', 'recursive']):
                approaches.add("Recursive solutions")
            if any(word in content_lower for word in ['iterative', 'loop', 'while', 'for']):
                approaches.add("Iterative solutions")
            if any(word in content_lower for word in ['dynamic programming', 'dp', 'memoization']):
                approaches.add("Dynamic programming")
            if any(word in content_lower for word in ['greedy', 'greedy algorithm']):
                approaches.add("Greedy algorithms")
            if any(word in content_lower for word in ['two pointers', 'sliding window']):
                approaches.add("Two pointers / Sliding window")

        return list(approaches)

    async def _suggest_learning_path(
        self,
        contributions: List[CommunityContribution],
        context: CommunityContext
    ) -> List[str]:
        """Suggest a learning path based on community patterns."""
        path = []

        # Analyze contribution progression
        beginner_contributions = [c for c in contributions if 'basic' in c.tags or 'beginner' in c.tags]
        intermediate_contributions = [c for c in contributions if 'intermediate' in c.tags]
        advanced_contributions = [c for c in contributions if 'advanced' in c.tags or 'expert' in c.tags]

        if beginner_contributions:
            path.append("Start with basic implementations and understanding")
        if intermediate_contributions:
            path.append("Move to intermediate optimizations and edge cases")
        if advanced_contributions:
            path.append("Explore advanced techniques and custom implementations")

        path.append("Compare multiple approaches from the community")
        path.append("Focus on code readability and documentation")

        return path

    async def _generate_peer_recommendations(
        self,
        contributions: List[CommunityContribution],
        context: CommunityContext
    ) -> List[PeerRecommendation]:
        """
        Generate personalized peer recommendations.

        Args:
            contributions: Available contributions
            context: User context

        Returns:
            List of personalized peer recommendations
        """
        recommendations = []

        # Sort contributions by relevance to user context
        scored_contributions = []
        for contribution in contributions:
            relevance_score = self._calculate_relevance(contribution, context)
            if relevance_score > 0.3:  # Only include reasonably relevant contributions
                scored_contributions.append((contribution, relevance_score))

        # Sort by relevance score
        scored_contributions.sort(key=lambda x: x[1], reverse=True)

        # Generate detailed recommendations for top contributions
        for contribution, relevance_score in scored_contributions[:5]:
            recommendation = await self._create_peer_recommendation(
                contribution, relevance_score, context
            )
            recommendations.append(recommendation)

        return recommendations

    def _calculate_relevance(
        self,
        contribution: CommunityContribution,
        context: CommunityContext
    ) -> float:
        """Calculate how relevant a contribution is to the user's context."""
        score = 0.0

        # Topic overlap
        topic_overlap = len(set(contribution.topics) & set(context.user_topics))
        score += topic_overlap * 0.4

        # Quality bonus
        score += min(contribution.quality_score / 10.0, 0.3)

        # Skill level alignment
        if context.user_skill_level == "beginner" and any(tag in contribution.tags for tag in ['beginner', 'basic', 'simple']):
            score += 0.2
        elif context.user_skill_level == "intermediate" and any(tag in contribution.tags for tag in ['intermediate', 'medium']):
            score += 0.2
        elif context.user_skill_level == "advanced" and any(tag in contribution.tags for tag in ['advanced', 'expert', 'complex']):
            score += 0.2

        # Learning goal alignment
        if context.learning_goal == "interview_prep" and any(tag in contribution.tags for tag in ['interview', 'technical']):
            score += 0.15
        elif context.learning_goal == "portfolio" and contribution.contribution_type == ContributionType.PROJECT_IMPLEMENTATION:
            score += 0.15

        return min(score, 1.0)

    async def _create_peer_recommendation(
        self,
        contribution: CommunityContribution,
        relevance_score: float,
        context: CommunityContext
    ) -> PeerRecommendation:
        """Create a detailed peer recommendation."""

        # Generate personalized explanation
        prompt = f"""
Create a personalized recommendation for this community contribution.

CONTRIBUTION:
Title: {contribution.title}
Type: {contribution.contribution_type.value}
Description: {contribution.description}
Topics: {', '.join(contribution.topics)}
Quality Score: {contribution.quality_score:.1f}
Helpful Marks: {contribution.helpful_count}

USER CONTEXT:
Skill Level: {context.user_skill_level}
Learning Topics: {', '.join(context.user_topics)}
Goal: {context.learning_goal}

Write a compelling recommendation that explains:
1. Why this contribution is relevant to the user's learning journey
2. What specific value they'll gain from studying it
3. How it fits into their broader learning goals
4. Any implementation notes or considerations

Keep it encouraging and focused on learning outcomes.
"""

        try:
            request = GenerationRequest(prompt=prompt, max_tokens=300, temperature=0.4)
            response = await self._ai_framework.generate(request)
            explanation = response.content.strip()
        except Exception:
            explanation = f"This {contribution.contribution_type.value} provides valuable insights for {', '.join(contribution.topics)}."

        # Extract learning value and implementation notes
        learning_value = f"Learn {', '.join(contribution.topics)} through real implementation experience"
        implementation_notes = [
            "Compare with your own approach",
            "Note the problem-solving methodology",
            "Observe code organization and documentation"
        ]

        return PeerRecommendation(
            contribution=contribution,
            relevance_score=relevance_score,
            why_relevant=explanation,
            learning_value=learning_value,
            implementation_notes=implementation_notes
        )

    def _get_top_contribution_types(self, contributions: List[CommunityContribution]) -> Dict[str, int]:
        """Get distribution of contribution types."""
        type_counts = {}
        for contribution in contributions:
            type_name = contribution.contribution_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True))

    async def get_learning_insights(
        self,
        topics: List[str],
        skill_level: str,
        limit: int = 5
    ) -> List[CommunityInsight]:
        """
        Get learning insights for specific topics and skill level.

        Args:
            topics: DSA topics to get insights for
            skill_level: User's skill level
            limit: Maximum number of insights to return

        Returns:
            List of relevant learning insights
        """
        # Search for contributions on these topics
        query = ContributionSearchQuery(
            topics=topics,
            min_score=2.0,  # Only high-quality contributions
            limit=20
        )

        contributions = await self._contribution_system.search_contributions(query)

        if not contributions:
            return []

        # Extract insights from these contributions
        context = CommunityContext(
            user_topics=topics,
            user_skill_level=skill_level
        )

        insights = await self._extract_insights(contributions, context)
        return insights[:limit]

    async def find_similar_implementations(
        self,
        user_approach: str,
        topics: List[str],
        limit: int = 3
    ) -> List[CommunityContribution]:
        """
        Find community implementations similar to user's approach.

        Args:
            user_approach: Description of user's implementation approach
            topics: Relevant DSA topics
            limit: Maximum number of similar implementations

        Returns:
            List of similar community implementations
        """
        # Get all contributions for these topics
        query = ContributionSearchQuery(
            topics=topics,
            contribution_type=ContributionType.PROJECT_IMPLEMENTATION,
            limit=50
        )

        contributions = await self._contribution_system.search_contributions(query)

        # Score similarity (simplified - could use embeddings for better similarity)
        scored_contributions = []
        for contribution in contributions:
            similarity_score = self._calculate_text_similarity(user_approach, contribution.content)
            if similarity_score > 0.1:  # Basic threshold
                scored_contributions.append((contribution, similarity_score))

        # Sort by similarity and return top matches
        scored_contributions.sort(key=lambda x: x[1], reverse=True)
        return [contrib for contrib, score in scored_contributions[:limit]]

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (could be enhanced with embeddings)."""
        # Very basic similarity - count common keywords
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
