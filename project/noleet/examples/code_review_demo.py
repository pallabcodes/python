#!/usr/bin/env python3
"""
Code Review Agent Demo

This script demonstrates NoLeet's AI-powered code review capabilities
for DSA implementations.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.code_review_agent import CodeReviewAgent, CodeReviewContext
from aiframework import AIFramework, AIFrameworkConfig


async def demo_code_review():
    """Demonstrate the Code Review Agent with sample DSA implementations."""
    print("🔍 NoLeet Code Review Agent Demo")
    print("=" * 60)

    # Initialize AI Framework and Code Review Agent
    ai_config = AIFrameworkConfig()
    ai_framework = AIFramework(ai_config)
    review_agent = CodeReviewAgent(ai_framework)

    print("✅ Code Review Agent initialized")
    print()

    # Sample DSA implementations to review
    review_samples = [
        {
            "title": "Two Sum - Good Implementation",
            "description": "Well-implemented Two Sum solution",
            "code": '''
def two_sum(nums, target):
    """
    Given an array of integers nums and an integer target,
    return indices of the two numbers such that they add up to target.
    """
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []

# Test cases
nums = [2, 7, 11, 15]
target = 9
result = two_sum(nums, target)
print(f"Indices: {result}")  # Should print [0, 1]
''',
            "topics": ["arrays", "hash_table"],
            "expected_algorithm": "hash_table_lookup",
            "expected_score_range": "85-95"
        },
        {
            "title": "Two Sum - Inefficient Implementation",
            "description": "Brute force approach with nested loops",
            "code": '''
def two_sum(nums, target):
    """Find two numbers that add up to target."""
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

# Test
nums = [2, 7, 11, 15]
target = 9
print(two_sum(nums, target))
''',
            "topics": ["arrays"],
            "expected_algorithm": "brute_force",
            "expected_score_range": "60-75"
        },
        {
            "title": "Binary Search - Buggy Implementation",
            "description": "Common off-by-one error in binary search",
            "code": '''
def binary_search(arr, target):
    """Search for target in sorted array."""
    left, right = 0, len(arr)  # Bug: should be len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1

# Test
arr = [1, 3, 5, 7, 9]
print(binary_search(arr, 5))  # Should work
print(binary_search(arr, 1))  # Will fail due to bug
''',
            "topics": ["binary_search", "arrays"],
            "expected_algorithm": "binary_search",
            "expected_score_range": "40-60"
        },
        {
            "title": "Dynamic Programming - Coin Change",
            "description": "Good DP implementation with documentation",
            "code": '''
def coin_change(coins, amount):
    """
    Return the minimum number of coins needed to make amount.
    Uses dynamic programming with O(amount * len(coins)) time.

    Args:
        coins: List of coin denominations
        amount: Target amount

    Returns:
        Minimum number of coins, or -1 if impossible
    """
    # Initialize dp array with infinity
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # Base case: 0 coins needed for amount 0

    # Fill dp array
    for coin in coins:
        for i in range(coin, amount + 1):
            if dp[i - coin] != float('inf'):
                dp[i] = min(dp[i], dp[i - coin] + 1)

    # Return result or -1 if impossible
    return dp[amount] if dp[amount] != float('inf') else -1

# Example usage
coins = [1, 2, 5]
amount = 11
result = coin_change(coins, amount)
print(f"Minimum coins for {amount}: {result}")
''',
            "topics": ["dynamic_programming", "arrays"],
            "expected_algorithm": "dynamic_programming",
            "expected_score_range": "90-100"
        }
    ]

    # Review each sample
    for i, sample in enumerate(review_samples, 1):
        print(f"\n{'='*60}")
        print(f"📝 REVIEW SAMPLE {i}: {sample['title']}")
        print(f"   {sample['description']}")
        print(f"   Expected Score: {sample['expected_score_range']}")
        print('='*60)

        # Create review context
        review_context = CodeReviewContext(
            code=sample["code"],
            language="python",
            project_description=f"Sample {i}: {sample['title']}",
            user_level="intermediate",
            topics=sample["topics"],
            expected_algorithm=sample["expected_algorithm"]
        )

        print(f"🤖 Analyzing {len(sample['code'].splitlines())} lines of code...")
        print()

        # Perform code review
        try:
            review_result = await review_agent.review_code(review_context)

            # Display key results
            print(f"📊 SCORE: {review_result.overall_score:.1f}/100 ({review_result.grade})")
            print(f"⏱️  TIME: {review_result.time_complexity or 'Unknown'}")
            print(f"💾 SPACE: {review_result.space_complexity or 'Unknown'}")
            print()

            # Show summary
            print("📝 SUMMARY:")
            print(f"   {review_result.summary}")
            print()

            # Show key issues
            critical_issues = [i for i in review_result.issues if i.severity.name == "CRITICAL"]
            major_issues = [i for i in review_result.issues if i.severity.name == "MAJOR"]

            if critical_issues:
                print("🚨 CRITICAL ISSUES:")
                for issue in critical_issues[:2]:
                    print(f"   ❌ {issue.title}: {issue.description}")
                print()

            if major_issues:
                print("⚠️  MAJOR ISSUES:")
                for issue in major_issues[:2]:
                    print(f"   ⚠️  {issue.title}: {issue.description}")
                print()

            # Show strengths
            if review_result.strengths:
                print("✅ STRENGTHS:")
                for strength in review_result.strengths[:2]:
                    print(f"   • {strength}")
                print()

            # Show learning points
            if review_result.learning_points:
                print("🎓 KEY LEARNINGS:")
                for point in review_result.learning_points[:2]:
                    print(f"   • {point}")
                print()

        except Exception as e:
            print(f"❌ Review failed: {e}")
            print()

    print(f"\n{'='*60}")
    print("🎯 CODE REVIEW DEMO COMPLETE")
    print('='*60)

    print("
📊 SUMMARY:"    print("   • Code Review Agent provides comprehensive analysis"    print("   • Covers correctness, efficiency, style, and DSA patterns"    print("   • Educational feedback helps learners improve"    print("   • Supports multiple skill levels and topics"    print("   • Identifies common mistakes and provides fixes"
    print("
🚀 INTEGRATION:"    print("   Use via CLI: noleet review 'your code' --topics arrays hash_table"    print("   Or from file: noleet review --file solution.py --project two_sum"
    print("
💡 IMPACT:"    print("   • Helps learners understand algorithmic correctness"    print("   • Teaches efficient problem-solving approaches"    print("   • Builds good coding habits and practices"    print("   • Accelerates learning through targeted feedback"
    print("
🎉 NoLeet's Code Review Agent makes DSA learning more effective"    print("   by providing expert-level feedback at every step of implementation!"


if __name__ == "__main__":
    asyncio.run(demo_code_review())
