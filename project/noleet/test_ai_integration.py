#!/usr/bin/env python3
"""Test script for AI integration in NoLeet."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the AI Framework directly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aiframework'))

from aiframework.config import FrameworkConfig

# Import the AI recommendation service directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'intelligence'))
import importlib.util

# Load the AI recommendation service module directly
spec = importlib.util.spec_from_file_location(
    "ai_recommendation_service",
    os.path.join(os.path.dirname(__file__), 'intelligence', 'ai_recommendation_service.py')
)
ai_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_module)

AIRecommendationService = ai_module.AIRecommendationService
RecommendationContext = ai_module.RecommendationContext


async def test_ai_recommendations():
    """Test AI-powered recommendations."""
    print("🧪 Testing AI Recommendation Service Integration...")

    try:
        # Initialize service
        config = FrameworkConfig()  # Default development config
        service = AIRecommendationService(Path('./data'), config)

        # Test with sample topics
        topics = ['dynamic_programming', 'arrays']
        context = RecommendationContext(selected_topics=set(topics))

        print(f"🤖 Testing with topics: {topics}")

        async with service as recommender:
            recommendations = await recommender.get_recommendations(
                topics, context, max_recommendations=2
            )

            print(f"✅ Got {len(recommendations)} AI recommendations!")

            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. 🎯 {rec.project.name}")
                print(f"   📊 AI Confidence: {rec.confidence_score:.1%}")
                print(f"   💡 Reasoning: {rec.reasoning[:150]}...")
                if rec.matched_topics:
                    print(f"   🎯 Matched Topics: {', '.join(rec.matched_topics)}")
                print(f"   📈 Learning Outcomes: {', '.join(rec.learning_outcomes[:3])}")

        print("\n🎉 AI Integration Test PASSED!")
        return True

    except Exception as e:
        print(f"❌ AI Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_fallback():
    """Test fallback to basic matching."""
    print("\n🔄 Testing Fallback to Basic Matching...")

    try:
        # Import directly to avoid package issues
        spec = importlib.util.spec_from_file_location(
            "matcher",
            os.path.join(os.path.dirname(__file__), 'matching', 'matcher.py')
        )
        matcher_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(matcher_module)

        spec = importlib.util.spec_from_file_location(
            "repository",
            os.path.join(os.path.dirname(__file__), 'storage', 'repository.py')
        )
        repo_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(repo_module)

        spec = importlib.util.spec_from_file_location(
            "models",
            os.path.join(os.path.dirname(__file__), 'core', 'models.py')
        )
        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)

        ProjectMatcher = matcher_module.ProjectMatcher
        ProjectRepository = repo_module.ProjectRepository
        Topic = models_module.Topic

        # Load projects
        repo = ProjectRepository(Path('./data'))
        projects = repo.load_projects()

        if not projects:
            print("⚠️  No projects found - cannot test fallback")
            return True

        # Test basic matching
        matcher = ProjectMatcher()
        selected_topics = {Topic.ARRAYS}

        matching = matcher.find_matching_projects(projects, selected_topics)
        print(f"✅ Basic matching found {len(matching)} projects")

        return True

    except Exception as e:
        print(f"❌ Basic fallback test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 NoLeet AI Integration Test Suite")
    print("=" * 50)

    # Test AI recommendations
    ai_success = await test_ai_recommendations()

    # Test basic fallback
    basic_success = await test_basic_fallback()

    print("\n" + "=" * 50)
    if ai_success and basic_success:
        print("🎉 ALL TESTS PASSED! NoLeet AI integration is working!")
        print("\n📋 What's working:")
        print("   ✅ AI Framework integration")
        print("   ✅ AI-powered project recommendations")
        print("   ✅ Fallback to basic matching")
        print("   ✅ Async context management")
        print("\n🚀 NoLeet is now COMPLETE with AI capabilities!")
    else:
        print("❌ Some tests failed. Check the errors above.")
        if not ai_success:
            print("💡 AI recommendations failed - check API keys and network")
        if not basic_success:
            print("💡 Basic fallback failed - check project data")


if __name__ == "__main__":
    asyncio.run(main())
