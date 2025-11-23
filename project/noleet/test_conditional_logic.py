#!/usr/bin/env python3
"""Test script for conditional recommendation logic."""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_conditional_logic():
    """Test the conditional recommendation logic."""
    print("🧪 Testing Conditional Recommendation Logic...")

    try:
        # Import the conditional logic functions
        from intelligence.ai_recommendation_service import (
            RecommendationContext,
            AIRecommendationService
        )

        # Create test context
        context = RecommendationContext(
            selected_topics={"dynamic_programming", "arrays"},
            user_level="beginner",
            project_goal="portfolio",
            time_available="short",
            career_focus="frontend",
            previous_projects_count=1
        )

        print(f"✅ Created context: {context.user_level} level, {context.project_goal} goal")

        # Test the service initialization (without AI calls)
        service = AIRecommendationService(Path('./data'), None)
        print("✅ Service initialized successfully")

        # Test conditional filtering methods
        from unittest.mock import Mock

        # Create mock projects
        mock_projects = [
            Mock(difficulty="easy", estimated_hours=15, topics=["arrays"], tags=["frontend", "portfolio"]),
            Mock(difficulty="hard", estimated_hours=100, topics=["dynamic_programming"], tags=["backend"]),
            Mock(difficulty="medium", estimated_hours=50, topics=["arrays", "dynamic_programming"], tags=["frontend", "portfolio"])
        ]

        # Test filtering methods
        filtered = []
        for project in mock_projects:
            if (service._matches_user_level(project, context.user_level) and
                service._matches_time_availability(project, context.time_available) and
                service._matches_project_goal(project, context.project_goal) and
                service._matches_career_focus(project, context.career_focus)):
                filtered.append(project)

        print(f"✅ Conditional filtering: {len(mock_projects)} → {len(filtered)} projects")

        # Test relevance calculation
        for project in filtered:
            relevance = service._calculate_context_relevance(project, context)
            print(".2f")

        print("🎉 Conditional logic test PASSED!")
        return True

    except Exception as e:
        print(f"❌ Conditional logic test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conditional_logic()
    sys.exit(0 if success else 1)
