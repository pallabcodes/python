"""
AI-powered insights engine for NoLeet.

This module generates personalized learning insights and recommendations
using AI agents to analyze user behavior and provide actionable advice.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from noleet.llm.llm_factory import LLMFactory
from noleet.analytics.progress_calculator import ProgressCalculator, ProgressMetrics
from noleet.analytics.skill_assessor import SkillAssessor, SkillAssessment
from noleet.analytics.community_analytics import CommunityAnalytics
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LearningInsight:
    """A single learning insight or recommendation."""
    category: str  # 'skill_gap', 'learning_pattern', 'motivation', 'technique'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    actionable_steps: List[str]
    expected_impact: str
    confidence_score: float  # 0.0 to 1.0


@dataclass
class PersonalizedInsights:
    """Comprehensive personalized insights for a user."""
    insights: List[LearningInsight]
    overall_summary: str
    next_best_actions: List[str]
    learning_goals: List[str]
    generated_at: datetime
    ai_model_used: str


class InsightsEngine:
    """AI-powered insights and recommendations engine."""

    INSIGHT_CATEGORIES = {
        'skill_gap': 'Areas where you need improvement',
        'learning_pattern': 'Your learning habits and patterns',
        'motivation': 'Keeping you motivated and engaged',
        'technique': 'Specific techniques and strategies',
        'milestone': 'Celebrating your achievements',
        'social': 'Community and collaboration opportunities'
    }

    def __init__(self, db_session, llm_factory: Optional[LLMFactory] = None):
        self.db = db_session
        self.llm_factory = llm_factory or LLMFactory()
        self.progress_calc = ProgressCalculator(db_session)
        self.skill_assessor = SkillAssessor(db_session)
        self.community_analytics = CommunityAnalytics(db_session)

    async def generate_personalized_insights(self, user_id: int) -> PersonalizedInsights:
        """
        Generate comprehensive personalized insights for a user.

        Args:
            user_id: The user's ID

        Returns:
            PersonalizedInsights with AI-generated recommendations
        """
        logger.info(f"Generating personalized insights for user {user_id}")

        # Gather user data
        progress = self.progress_calc.calculate_user_progress(user_id)
        skills = self.skill_assessor.assess_user_skills(user_id)
        community_overview = self.community_analytics.get_community_overview()

        # Generate different types of insights
        insights = []

        # Skill gap insights
        skill_insights = await self._generate_skill_gap_insights(skills, progress)
        insights.extend(skill_insights)

        # Learning pattern insights
        pattern_insights = await self._generate_learning_pattern_insights(progress, skills)
        insights.extend(pattern_insights)

        # Motivation insights
        motivation_insights = await self._generate_motivation_insights(progress, skills)
        insights.extend(motivation_insights)

        # Technique insights
        technique_insights = await self._generate_technique_insights(skills, progress)
        insights.extend(technique_insights)

        # Community insights
        community_insights = await self._generate_community_insights(user_id, community_overview)
        insights.extend(community_insights)

        # Milestone insights
        milestone_insights = await self._generate_milestone_insights(progress)
        insights.extend(milestone_insights)

        # Sort by priority and limit to top insights
        insights.sort(key=lambda x: self._get_priority_weight(x.priority), reverse=True)
        top_insights = insights[:10]

        # Generate overall summary
        summary = await self._generate_overall_summary(progress, skills, community_overview)

        # Generate next best actions
        next_actions = await self._generate_next_best_actions(progress, skills, top_insights)

        # Generate learning goals
        learning_goals = await self._generate_learning_goals(skills, progress)

        return PersonalizedInsights(
            insights=top_insights,
            overall_summary=summary,
            next_best_actions=next_actions,
            learning_goals=learning_goals,
            generated_at=datetime.now(),
            ai_model_used=self.llm_factory.get_config()['llm']['default_provider']
        )

    async def _generate_skill_gap_insights(self, skills: SkillAssessment, progress: ProgressMetrics) -> List[LearningInsight]:
        """Generate insights about skill gaps."""
        insights = []

        # Identify weakest skills
        weak_skills = [(topic, level) for topic, level in skills.topic_breakdown.items() if level < 0.4]
        weak_skills.sort(key=lambda x: x[1])  # Sort by skill level (lowest first)

        if weak_skills:
            # Focus on top 2 weakest skills
            for topic, level in weak_skills[:2]:
                prompt = f"""
                The user has a skill level of {level:.1%} in {topic}.
                Their overall skill level is {skills.overall_level:.1%} and learning trajectory is {skills.learning_trajectory}.
                Suggest specific, actionable steps to improve in {topic}.
                Keep it encouraging and specific.
                """

                recommendation = await self._get_ai_recommendation(prompt)

                insights.append(LearningInsight(
                    category='skill_gap',
                    priority='high',
                    title=f"Strengthen Your {topic.title()} Skills",
                    description=f"You have room for improvement in {topic} (current level: {level:.1%}). {recommendation}",
                    actionable_steps=[
                        f"Complete 3 {topic} projects this week",
                        f"Study {topic} solutions from community showcase",
                        f"Practice {topic} problems daily for 30 minutes"
                    ],
                    expected_impact=f"Expected improvement: {min(0.3, 1-level):.1%} skill level increase in 2 weeks",
                    confidence_score=0.85
                ))

        return insights

    async def _generate_learning_pattern_insights(self, progress: ProgressMetrics, skills: SkillAssessment) -> List[LearningInsight]:
        """Generate insights about learning patterns."""
        insights = []

        # Analyze learning velocity
        velocity = progress.learning_velocity

        if velocity.consistency_score < 0.5:
            insights.append(LearningInsight(
                category='learning_pattern',
                priority='high',
                title="Build Consistent Learning Habits",
                description="Your learning consistency score is low. Consistent daily practice leads to better long-term retention.",
                actionable_steps=[
                    "Set a daily learning reminder",
                    "Create a fixed learning schedule",
                    "Track your daily progress in a journal",
                    "Join a study group for accountability"
                ],
                expected_impact="30% improvement in learning consistency and skill acquisition rate",
                confidence_score=0.90
            ))

        if velocity.projects_per_week < 1:
            insights.append(LearningInsight(
                category='learning_pattern',
                priority='medium',
                title="Increase Project Completion Rate",
                description=f"You're completing {velocity.projects_per_week:.1f} projects per week. Increasing this will accelerate your learning.",
                actionable_steps=[
                    "Break large projects into smaller daily tasks",
                    "Set weekly project completion goals",
                    "Focus on easier projects to build momentum",
                    "Use time-blocking techniques for focused sessions"
                ],
                expected_impact="2x increase in project completion rate within a month",
                confidence_score=0.80
            ))

        # Analyze topic diversity
        if velocity.topics_per_week < 2:
            insights.append(LearningInsight(
                category='learning_pattern',
                priority='medium',
                title="Explore More Topic Areas",
                description="You're focusing on fewer topics. Broadening your exposure helps with problem-solving versatility.",
                actionable_steps=[
                    "Try one project from a new topic this week",
                    "Alternate between familiar and new topics",
                    "Read about emerging algorithms in different areas",
                    "Join community discussions on various topics"
                ],
                expected_impact="Improved problem-solving flexibility and broader skill set",
                confidence_score=0.75
            ))

        return insights

    async def _generate_motivation_insights(self, progress: ProgressMetrics, skills: SkillAssessment) -> List[LearningInsight]:
        """Generate motivational insights."""
        insights = []

        # Check for recent achievements
        if progress.current_learning_streak >= 7:
            insights.append(LearningInsight(
                category='motivation',
                priority='medium',
                title=f"🎉 {progress.current_learning_streak}-Day Learning Streak!",
                description="You're on fire! Keep up the momentum.",
                actionable_steps=[
                    "Celebrate your consistency",
                    "Share your streak with the community",
                    "Set a new personal record goal",
                    "Help others maintain their streaks"
                ],
                expected_impact="Increased motivation and community engagement",
                confidence_score=0.95
            ))

        # Check skill progression
        recent_improvements = [
            topic for topic, level in skills.topic_breakdown.items()
            if level > 0.7  # Consider high skill levels as achievements
        ]

        if recent_improvements:
            insights.append(LearningInsight(
                category='milestone',
                priority='medium',
                title="Skill Mastery Achievement",
                description=f"You've reached high proficiency in: {', '.join(recent_improvements[:3])}. Excellent work!",
                actionable_steps=[
                    "Mentor others in your strong areas",
                    "Take on more challenging projects",
                    "Share your learning journey",
                    "Set new learning goals"
                ],
                expected_impact="Increased confidence and leadership opportunities",
                confidence_score=0.88
            ))

        # Check if they're falling behind community average
        if skills.learning_trajectory == 'beginner' and progress.total_projects_completed < 5:
            insights.append(LearningInsight(
                category='motivation',
                priority='low',
                title="Welcome to the Journey!",
                description="Everyone starts somewhere. Focus on consistent progress rather than speed.",
                actionable_steps=[
                    "Start with easy projects to build confidence",
                    "Connect with the community for support",
                    "Celebrate small wins daily",
                    "Remember: slow, steady progress wins the race"
                ],
                expected_impact="Improved engagement and reduced frustration",
                confidence_score=0.92
            ))

        return insights

    async def _generate_technique_insights(self, skills: SkillAssessment, progress: ProgressMetrics) -> List[LearningInsight]:
        """Generate technique-specific insights."""
        insights = []

        # Analyze based on skill levels and progress
        if skills.overall_level < 0.5:
            insights.append(LearningInsight(
                category='technique',
                priority='high',
                title="Master the Fundamentals First",
                description="Strong fundamentals are crucial for advanced problem-solving.",
                actionable_steps=[
                    "Focus on basic data structures (Arrays, Linked Lists, Trees)",
                    "Practice basic algorithms (Sorting, Searching, Recursion)",
                    "Understand time/space complexity analysis",
                    "Build projects using only basic constructs"
                ],
                expected_impact="40% improvement in problem-solving efficiency",
                confidence_score=0.85
            ))

        # Check for topic imbalances
        strengths = skills.strengths
        weaknesses = skills.weaknesses

        if len(strengths) > 0 and len(weaknesses) > 0:
            insights.append(LearningInsight(
                category='technique',
                priority='medium',
                title="Balance Your Skill Development",
                description=f"You're strong in {', '.join(strengths[:2])} but need work in {', '.join(weaknesses[:2])}.",
                actionable_steps=[
                    f"Dedicate 60% of time to weaknesses ({', '.join(weaknesses[:2])})",
                    f"Use strengths ({', '.join(strengths[:2])}) to tackle harder problems",
                    "Alternate between comfort zones and growth areas",
                    "Seek mentorship in weak areas from community"
                ],
                expected_impact="More balanced skill set and improved overall proficiency",
                confidence_score=0.78
            ))

        return insights

    async def _generate_community_insights(self, user_id: int, community_overview: Dict) -> List[LearningInsight]:
        """Generate community-related insights."""
        insights = []

        # Check community engagement
        user_engagement = self._calculate_user_engagement_rate(user_id)

        if user_engagement < 0.3:  # Less than 30% of community average
            insights.append(LearningInsight(
                category='social',
                priority='medium',
                title="Connect with the Community",
                description="Community learning accelerates your progress. You're missing out on peer insights and collaboration.",
                actionable_steps=[
                    "Join community discussions on projects you're working on",
                    "Share your solutions and get feedback",
                    "Participate in study groups or pair programming",
                    "Follow other learners' progress for inspiration"
                ],
                expected_impact="25% faster learning through peer learning and motivation",
                confidence_score=0.82
            ))

        # Check popular topics user hasn't explored
        user_topics = set(self._get_user_topics(user_id))
        popular_topics = [topic for topic, _ in community_overview['topic_analytics']['popular_topics'][:5]]

        unexplored_popular = [topic for topic in popular_topics if topic not in user_topics]

        if unexplored_popular:
            insights.append(LearningInsight(
                category='social',
                priority='low',
                title="Explore Trending Topics",
                description=f"The community is actively learning: {', '.join(unexplored_popular[:3])}. Join the conversation!",
                actionable_steps=[
                    f"Try one project in {unexplored_popular[0]} this week",
                    "Read community discussions on these topics",
                    "Ask questions in community forums",
                    "Share your perspective on these areas"
                ],
                expected_impact="Broader knowledge and new learning opportunities",
                confidence_score=0.70
            ))

        return insights

    async def _generate_milestone_insights(self, progress: ProgressMetrics) -> List[LearningInsight]:
        """Generate milestone celebration insights."""
        insights = []

        # Check for milestone achievements
        milestones = []

        if progress.total_projects_completed >= 10:
            milestones.append("10 Projects Completed! 🎉")
        if progress.total_projects_completed >= 25:
            milestones.append("25 Projects Completed! 🏆")
        if progress.total_projects_completed >= 50:
            milestones.append("50 Projects Completed! 👑")

        if progress.current_learning_streak >= 30:
            milestones.append("30-Day Learning Streak! 🔥")

        if progress.total_time_spent >= 100:  # 100 hours
            milestones.append("100 Hours of Learning! ⏰")

        if milestones:
            insights.append(LearningInsight(
                category='milestone',
                priority='low',
                title="Achievement Unlocked!",
                description=f"Congratulations! {milestones[0]}",
                actionable_steps=[
                    "Share your achievement with the community",
                    "Set your next milestone goal",
                    "Reflect on what helped you succeed",
                    "Mentor others who are pursuing similar goals"
                ],
                expected_impact="Increased motivation and community recognition",
                confidence_score=0.95
            ))

        return insights

    async def _generate_overall_summary(self, progress: ProgressMetrics, skills: SkillAssessment, community: Dict) -> str:
        """Generate an overall summary of the user's learning state."""
        prompt = f"""
        Write a personalized, encouraging summary for a learner with these stats:
        - Overall skill level: {skills.overall_level:.1%}
        - Learning trajectory: {skills.learning_trajectory}
        - Projects completed: {progress.total_projects_completed}
        - Current streak: {progress.current_learning_streak} days
        - Favorite topics: {', '.join(progress.favorite_topics[:3])}
        - Recommended difficulty: {progress.recommended_difficulty}

        Keep it positive, actionable, and under 150 words.
        """

        summary = await self._get_ai_recommendation(prompt)
        return summary

    async def _generate_next_best_actions(self, progress: ProgressMetrics, skills: SkillAssessment, insights: List[LearningInsight]) -> List[str]:
        """Generate the top 3 next best actions for the user."""
        prompt = f"""
        Based on this user profile, suggest their top 3 next best actions:

        Skill Level: {skills.overall_level:.1%}
        Trajectory: {skills.learning_trajectory}
        Projects Done: {progress.total_projects_completed}
        Current Streak: {progress.current_learning_streak} days
        Weaknesses: {', '.join(skills.weaknesses[:2])}
        Recommended Difficulty: {progress.recommended_difficulty}

        Focus on actionable, specific steps. Keep each action under 20 words.
        """

        actions_text = await self._get_ai_recommendation(prompt)
        # Split into list (assuming AI returns numbered list)
        actions = [line.strip('-123. ') for line in actions_text.split('\n') if line.strip()][:3]
        return actions

    async def _generate_learning_goals(self, skills: SkillAssessment, progress: ProgressMetrics) -> List[str]:
        """Generate personalized learning goals."""
        prompt = f"""
        Suggest 3 personalized learning goals for someone with:
        - Current skill level: {skills.overall_level:.1%}
        - Learning trajectory: {skills.learning_trajectory}
        - Completed projects: {progress.total_projects_completed}
        - Favorite topics: {', '.join(progress.favorite_topics[:2])}
        - Weak areas: {', '.join(skills.weaknesses[:2])}

        Make goals SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
        Keep each goal under 25 words.
        """

        goals_text = await self._get_ai_recommendation(prompt)
        goals = [line.strip('-123. ') for line in goals_text.split('\n') if line.strip()][:3]
        return goals

    async def _get_ai_recommendation(self, prompt: str) -> str:
        """Get AI-generated recommendation."""
        try:
            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            return response.content.strip()
        except Exception as e:
            logger.error(f"AI recommendation failed: {e}")
            return "Consider focusing on consistent daily practice and seeking community feedback on your solutions."

    def _get_priority_weight(self, priority: str) -> int:
        """Get numeric weight for priority sorting."""
        return {'high': 3, 'medium': 2, 'low': 1}.get(priority, 0)

    def _calculate_user_engagement_rate(self, user_id: int) -> float:
        """Calculate user's engagement relative to community."""
        # Simplified calculation - in real implementation would compare to community averages
        return 0.5  # Placeholder

    def _get_user_topics(self, user_id: int) -> List[str]:
        """Get topics the user has worked on."""
        # This would query the database for user's project topics
        return ['algorithms', 'data-structures']  # Placeholder
