#!/usr/bin/env python3
"""
Community Learning Demo

This script demonstrates NoLeet's community-powered learning ecosystem.
It shows how learners can share implementations and learn from each other.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from community.contribution_system import CommunityContributionSystem, ContributionType
from community.community_intelligence import CommunityIntelligenceAgent, CommunityContext
from community.peer_learning import PeerLearningEngine
from aiframework import AIFramework, AIFrameworkConfig


async def demo_community_ecosystem():
    """Demonstrate the complete community learning ecosystem."""
    print("🌐 NoLeet Community Learning Ecosystem Demo")
    print("=" * 60)

    # Initialize systems
    ai_config = AIFrameworkConfig()
    ai_framework = AIFramework(ai_config)

    # Create data directory for demo
    data_dir = Path("./demo_data")
    data_dir.mkdir(exist_ok=True)

    contribution_system = CommunityContributionSystem(data_dir)
    community_intelligence = CommunityIntelligenceAgent(ai_framework, contribution_system)
    peer_learning = PeerLearningEngine(ai_framework, contribution_system, community_intelligence)

    print("✅ Community systems initialized")
    print()

    # Demo 1: Sharing Community Contributions
    print("📤 DEMO 1: Sharing Community Contributions")
    print("-" * 45)

    # Sample contributions that community members might share
    sample_contributions = [
        {
            "type": ContributionType.PROJECT_IMPLEMENTATION,
            "project_id": "coin_change_dp",
            "title": "Dynamic Programming Coin Change - Bottom-Up Approach",
            "description": "Complete implementation using tabulation with space optimization",
            "content": '''
def coin_change(coins, amount):
    """
    Dynamic Programming solution for Coin Change problem.
    Returns minimum number of coins needed to make the amount.

    Time: O(amount * len(coins))
    Space: O(amount) - optimized from O(amount * len(coins))
    """
    if amount == 0:
        return 0
    if not coins:
        return -1

    # Initialize dp array with infinity
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0

    # Fill dp array
    for coin in coins:
        for i in range(coin, amount + 1):
            if dp[i - coin] != float('inf'):
                dp[i] = min(dp[i], dp[i - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1

# Example usage
coins = [1, 2, 5]
amount = 11
result = coin_change(coins, amount)
print(f"Minimum coins for {amount}: {result}")
''',
            "topics": ["dynamic_programming", "arrays"],
            "author": "dp_expert"
        },
        {
            "type": ContributionType.LEARNING_INSIGHT,
            "project_id": "coin_change_dp",
            "title": "Key Insight: State Definition in DP",
            "description": "Understanding why dp[i] represents minimum coins for amount i",
            "content": '''
The key insight in Coin Change DP is understanding what your state represents:

dp[i] = minimum number of coins needed to make amount i

This seems simple, but many people struggle with:
1. Why we initialize dp[0] = 0 (0 coins for 0 amount)
2. Why we use float('inf') for impossible amounts
3. How the transition dp[i] = min(dp[i], dp[i-coin] + 1) works

The transition means: "To make amount i using this coin, take the minimum coins
needed for (i - coin_value) and add 1 for this coin."

This state definition makes the recurrence relation natural and easy to understand.
''',
            "topics": ["dynamic_programming"],
            "author": "dp_teacher"
        },
        {
            "type": ContributionType.DEBUG_STORY,
            "project_id": "coin_change_dp",
            "title": "Common Bug: Off-by-One in DP Array",
            "description": "Why dp array needs size amount+1, not amount",
            "content": '''
I spent 2 hours debugging why my coin change DP wasn't working. The issue?

I used: dp = [float('inf')] * amount  # Wrong!
Instead of: dp = [float('inf')] * (amount + 1)  # Correct!

Why? dp[i] represents coins needed for amount i.
- Amount 0 needs 0 coins → dp[0]
- Amount 1 needs some coins → dp[1]
- ...
- Amount 'amount' needs coins → dp[amount]

So we need indices 0 through amount, which means array size amount+1.

The bug manifested as IndexError when trying to access dp[amount], or worse,
using an uninitialized value that gave wrong answers.

Lesson: Always double-check your DP array bounds!
''',
            "topics": ["dynamic_programming", "debugging"],
            "author": "bug_hunter"
        }
    ]

    # Share the contributions
    for i, contrib_data in enumerate(sample_contributions, 1):
        try:
            contribution = await contribution_system.create_contribution(
                contribution_type=contrib_data["type"],
                project_id=contrib_data["project_id"],
                title=contrib_data["title"],
                description=contrib_data["description"],
                content=contrib_data["content"],
                author_id=contrib_data["author"],
                topics=contrib_data["topics"]
            )
            print(f"✅ Shared contribution {i}: {contribution.title}")
        except Exception as e:
            print(f"❌ Failed to share contribution {i}: {e}")

    print(f"\n📊 Community now has {len(await contribution_system.search_contributions({}))} contributions")
    print()

    # Demo 2: Community Intelligence Analysis
    print("🤖 DEMO 2: Community Intelligence Analysis")
    print("-" * 45)

    context = CommunityContext(
        user_topics=["dynamic_programming", "arrays"],
        user_skill_level="intermediate",
        current_project="coin_change_dp"
    )

    print("Analyzing community knowledge for intermediate learner...")
    analysis = await community_intelligence.analyze_community_for_project("coin_change_dp", context)

    print("
📊 Analysis Results:"    print(f"   📝 Community Insights: {len(analysis.get('insights', []))}")
    print(f"   👥 Peer Recommendations: {len(analysis.get('peer_recommendations', []))}")
    print(f"   📈 Learning Patterns: {len(analysis.get('patterns', {}).get('common_approaches', []))} approaches found")

    community_stats = analysis.get("community_stats", {})
    print(f"   🌐 Community Size: {community_stats.get('total_contributions', 0)} contributions")
    print(f"   ⭐ Average Quality: {community_stats.get('average_quality_score', 0):.2f}")

    # Show insights
    insights = analysis.get("insights", [])
    if insights:
        print(f"\n💡 Top Community Insights:")
        for i, insight in enumerate(insights[:2], 1):
            print(f"   {i}. {insight.title} (confidence: {insight.confidence_score:.1%})")
            print(f"      {insight.description[:100]}...")

    # Show peer recommendations
    peer_recs = analysis.get("peer_recommendations", [])
    if peer_recs:
        print(f"\n👥 Top Peer Recommendations:")
        for i, rec in enumerate(peer_recs[:2], 1):
            print(f"   {i}. {rec.contribution.title}")
            print(f"      Relevance: {rec.relevance_score:.1%}")
            print(f"      Why: {rec.why_relevant[:80]}...")

    print()

    # Demo 3: Learning Experience Creation
    print("🚀 DEMO 3: Personalized Learning Experience")
    print("-" * 45)

    print("Creating personalized learning experience for intermediate learner...")
    experience = await peer_learning.create_learning_experience(
        project_id="coin_change_dp",
        user_topics=["dynamic_programming", "arrays"],
        user_skill_level="intermediate",
        learning_goal="interview_prep"
    )

    print("
✅ Learning Experience Created!"    print(f"   📋 Learning Objectives: {len(experience.learning_objectives)}")
    print(f"   📚 Recommended Sequence: {len(experience.recommended_sequence or [])} steps")
    print(f"   ⏱️  Estimated Time: {experience.estimated_learning_time}")
    print(f"   🎯 Current Focus: {experience.current_focus or 'None'}")

    if experience.learning_objectives:
        print(f"\n🎯 Learning Objectives:")
        for i, obj in enumerate(experience.learning_objectives[:3], 1):
            print(f"   {i}. {obj}")

    if experience.community_insights:
        print(f"\n💡 Community Insights Available: {len(experience.community_insights)}")

    print()

    # Demo 4: CLI-Style Interaction
    print("💻 DEMO 4: CLI-Style Community Interaction")
    print("-" * 45)

    print("How learners would interact with the community:")
    print()
    print("1. 📋 Explore what's available:")
    print("   $ noleet community view coin_change_dp")
    print("   → Shows 3 community contributions we just shared")
    print()

    print("2. 🚀 Start learning with community guidance:")
    print("   $ noleet community learn coin_change_dp --level intermediate")
    print("   → Creates personalized learning experience")
    print("   → Recommends sequence of community contributions")
    print()

    print("3. 📤 Share your own implementation:")
    print("   $ noleet community share coin_change_dp \\")
    print("       --title 'My Recursive Solution' \\")
    print("       --content 'def coin_change_recursive(...)...' \\")
    print("       --topics dynamic_programming recursion")
    print("   → Contributes back to the community")
    print()

    print("4. 📊 Track learning progress:")
    print("   $ noleet community progress")
    print("   → Shows community statistics and insights")
    print()

    print("🎯 RESULT: A self-sustaining learning ecosystem where:")
    print("   • Learners teach each other through shared implementations")
    print("   • AI surfaces the most relevant community knowledge")
    print("   • Quality improves as more people contribute")
    print("   • Learning becomes a collaborative, community-driven experience")

    print("
🌟 This transforms NoLeet from 'individual learning tool' to"    print("   'thriving community of DSA learners helping each other grow'!")

    # Clean up demo data
    print("
🧹 Cleaning up demo data..."    import shutil
    if data_dir.exists():
        shutil.rmtree(data_dir)
    print("✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_community_ecosystem())
