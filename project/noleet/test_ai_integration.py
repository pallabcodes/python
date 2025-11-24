#!/usr/bin/env python3
"""Basic functionality tests for NoLeet core features."""

import sys
from pathlib import Path
import tempfile
import json

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_core_functionality():
    """Test core NoLeet functionality without AI dependencies."""
    print("🧪 Testing Core NoLeet Functionality...")

    try:
        # Test imports
        from noleet.core.models import Topic, Project
        from noleet.matching.matcher import ProjectMatcher
        from noleet.storage.repository import ProjectRepository
        from noleet.examples.sample_projects import create_sample_projects

        print("✅ Core imports successful")

        # Test topic creation
        dp_topic = Topic.DYNAMIC_PROGRAMMING
        arrays_topic = Topic.ARRAYS
        print("✅ Topic creation works")

        # Test sample projects creation
        projects = create_sample_projects()
        print(f"✅ Sample projects created: {len(projects)} projects")

        # Test project repository
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = ProjectRepository(Path(temp_dir))
            repo.save_projects(projects)
            loaded_projects = repo.load_projects()
            assert len(loaded_projects) == len(projects)
            print("✅ Project repository works")

        # Test project matcher
        matcher = ProjectMatcher()
        selected_topics = {Topic.DYNAMIC_PROGRAMMING, Topic.ARRAYS}

        # Test with projects that have these topics
        matching_projects = matcher.find_matching_projects(projects, selected_topics)
        assert len(matching_projects) > 0
        print(f"✅ Project matching works: found {len(matching_projects)} matches")

        # Test topic combinations
        combinations = matcher.get_topic_combinations(projects)
        assert len(combinations) > 0
        print(f"✅ Topic combinations extracted: {len(combinations)} combinations")

        print("🎉 All core functionality tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Core functionality test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_community_system():
    """Test community contribution system."""
    print("🧪 Testing Community System...")

    try:
        from noleet.community.contribution_system import CommunityContributionSystem
        from noleet.core.models import Topic

        with tempfile.TemporaryDirectory() as temp_dir:
            system = CommunityContributionSystem(Path(temp_dir))

            # Test contribution creation
            contribution_id = system.share_implementation(
                title="Dynamic Programming Solution",
                content="Here's my DP approach...",
                topics=[Topic.DYNAMIC_PROGRAMMING],
                author="test_user"
            )

            print(f"✅ Community contribution created: {contribution_id}")

            # Test contribution retrieval
            contributions = system.get_contributions_by_topic(Topic.DYNAMIC_PROGRAMMING)
            assert len(contributions) > 0
            print(f"✅ Community contributions retrieved: {len(contributions)} items")

        print("🎉 Community system tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Community system test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Running NoLeet Core Functionality Tests")
    print("=" * 60)

    success = True

    # Run core functionality tests
    if not test_core_functionality():
        success = False

    print()

    # Run community system tests
    if not test_community_system():
        success = False

    print()
    print("=" * 60)

    if success:
        print("🎉 ALL TESTS PASSED! NoLeet core functionality is working correctly.")
        print("📋 Ready for Principal Engineer review.")
    else:
        print("❌ SOME TESTS FAILED! Please fix issues before Principal Engineer review.")
        sys.exit(1)
