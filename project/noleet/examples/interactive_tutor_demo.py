#!/usr/bin/env python3
"""
Interactive Tutor Agent Demo

This script demonstrates the AI Interactive Tutor Agent capabilities in NoLeet.
It shows how the tutor provides real-time guidance during DSA project implementation.

Usage:
    python examples/interactive_tutor_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.interactive_tutor_agent import (
    InteractiveTutorAgent,
    TutorContext,
    TutorMode
)
from aiframework import AIFramework, AIFrameworkConfig


async def demo_interactive_tutor():
    """Demonstrate the Interactive Tutor Agent."""
    print("🎓 NoLeet Interactive Tutor Agent Demo")
    print("=" * 50)

    # Initialize AI Framework and Tutor Agent
    ai_config = AIFrameworkConfig()
    ai_framework = AIFramework(ai_config)
    tutor_agent = InteractiveTutorAgent(ai_framework)

    print("🤖 Interactive Tutor Agent initialized!")
    print()

    # Demo 1: Concept Explanation
    print("📚 DEMO 1: Concept Explanation")
    print("-" * 30)

    context = TutorContext(
        question="Explain dynamic programming to me",
        user_level="beginner",
        topics=["dynamic_programming"]
    )

    print("Student asks: 'Explain dynamic programming to me'")
    print("Tutor responds:")

    response = await tutor_agent.provide_guidance(context, TutorMode.CONCEPT_EXPLANATION)
    print(f"💡 {response.answer[:300]}...")
    print(f"🎯 Hint Level: {response.hint_level.value}")
    print()

    # Demo 2: Code Review
    print("🔍 DEMO 2: Code Review")
    print("-" * 30)

    sample_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test
print(fibonacci(10))
'''

    context = TutorContext(
        user_code=sample_code,
        question="Review my Fibonacci implementation",
        user_level="intermediate",
        topics=["recursion", "dynamic_programming"],
        project_description="Implementing Fibonacci sequence with multiple approaches"
    )

    print("Student submits Fibonacci code for review:")
    print(f"```python{sample_code}```")
    print("Tutor provides review:")

    response = await tutor_agent.provide_guidance(context, TutorMode.CODE_REVIEW)
    print(f"📝 {response.answer[:400]}...")

    if response.suggestions:
        print("💡 Suggestions:")
        for suggestion in response.suggestions[:2]:
            print(f"   • {suggestion}")

    print()

    # Demo 3: Debugging Help
    print("🐛 DEMO 3: Debugging Assistance")
    print("-" * 30)

    buggy_code = '''
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
'''

    context = TutorContext(
        user_code=buggy_code,
        error_message="This solution works but is inefficient",
        user_level="beginner",
        topics=["arrays", "two_pointers"],
        project_description="Solving Two Sum problem efficiently"
    )

    print("Student reports: 'My Two Sum solution works but is inefficient'")
    print("Tutor provides debugging guidance:")

    response = await tutor_agent.provide_guidance(context, TutorMode.DEBUGGING)
    print(f"🔧 {response.answer[:400]}...")

    if response.suggestions:
        print("🔧 Debug suggestions:")
        for suggestion in response.suggestions[:2]:
            print(f"   • {suggestion}")

    print()

    # Demo 4: Implementation Guidance
    print("🚀 DEMO 4: Implementation Guidance")
    print("-" * 30)

    context = TutorContext(
        question="How should I implement the core algorithm for this DP problem?",
        user_level="intermediate",
        topics=["dynamic_programming", "arrays"],
        project_description="Solving the Coin Change problem with dynamic programming"
    )

    print("Student asks: 'How should I implement the core algorithm for this DP problem?'")
    print("Tutor provides step-by-step guidance:")

    response = await tutor_agent.provide_guidance(context, TutorMode.IMPLEMENTATION_GUIDANCE)
    print(f"🧭 {response.answer[:400]}...")

    if response.next_steps:
        print("🚀 Next steps:")
        for step in response.next_steps[:2]:
            print(f"   • {step}")

    print()

    # Demo 5: Learning Path
    print("🛣️  DEMO 5: Learning Path Suggestions")
    print("-" * 30)

    context = TutorContext(
        user_level="intermediate",
        topics=["dynamic_programming"],
        project_description="Completed basic DP problems, looking for next challenges"
    )

    print("Student asks for learning path recommendations after completing basic DP")
    print("Tutor suggests progression:")

    response = await tutor_agent.provide_guidance(context, TutorMode.LEARNING_PATH)
    print(f"🧭 {response.answer[:400]}...")

    if response.related_concepts:
        print("🔗 Related concepts to explore:")
        for concept in response.related_concepts[:3]:
            print(f"   • {concept}")

    print()

    # Demo 6: CLI Integration Example
    print("💻 DEMO 6: CLI Integration Workflow")
    print("-" * 30)

    print("Typical NoLeet Interactive Learning Session:")
    print("1. 🤖 Get project recommendation:")
    print("   $ noleet find dynamic_programming arrays")
    print()
    print("2. 🔨 Generate project scaffold:")
    print("   $ noleet scaffold coin_change_dp")
    print()
    print("3. 🎓 Start tutoring session:")
    print("   $ noleet tutor start coin_change_dp --level intermediate")
    print()
    print("4. 💬 Ask questions during implementation:")
    print("   $ noleet tutor ask 'How does memoization work in DP?'")
    print("   $ noleet tutor ask 'Why is my recursive solution slow?' --code 'def fib(n): ...'")
    print()
    print("5. 🔍 Get code reviews:")
    print("   $ noleet tutor review --file main.py")
    print()
    print("6. 🐛 Debug issues:")
    print("   $ noleet tutor debug --error 'RecursionError: maximum recursion depth exceeded'")
    print()
    print("7. 📚 Learn concepts:")
    print("   $ noleet tutor explain memoization")
    print()
    print("8. 🚀 Get implementation guidance:")
    print("   $ noleet tutor guide 'implementing the DP table approach'")
    print()
    print("9. 🛣️  Plan next steps:")
    print("   $ noleet tutor path")
    print()
    print("10. 👋 End session:")
    print("    $ noleet tutor end")
    print()

    print("🎉 Demo Complete!")
    print("=" * 50)
    print("The Interactive Tutor Agent transforms NoLeet from a 'project recommender'")
    print("into a 'personal DSA learning companion' that guides you through every step")
    print("of the implementation journey!")
    print()
    print("🚀 Key Benefits:")
    print("   ✅ Eliminates 'stuck' moments with instant expert guidance")
    print("   ✅ Provides personalized explanations at your skill level")
    print("   ✅ Offers code reviews and debugging help in real-time")
    print("   ✅ Creates interactive, conversational learning experiences")
    print("   ✅ Builds confidence through progressive skill development")
    print()
    print("The tutor doesn't just answer questions - it teaches you HOW to think")
    print("like a DSA expert, making complex concepts accessible and actionable!")


if __name__ == "__main__":
    asyncio.run(demo_interactive_tutor())
