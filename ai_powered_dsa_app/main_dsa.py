#!/usr/bin/env python3
"""
AI-Powered DSA Learning Application

Uses AI Framework to provide personalized project recommendations,
code explanations, and learning guidance.
"""

import asyncio
from aiframework import AIFramework

async def main():
    async with AIFramework(mode="development") as ai:
        print("🎯 AI-Powered DSA Learning Platform")
        print("=" * 40)

        # Example DSA learning interactions
        print("\n📚 Topic: Dynamic Programming")
        dp_explanation = await ai.generate(
            "Explain dynamic programming with a simple example",
            quality_requirement="high"
        )
        print(f"AI Explanation: {dp_explanation.content[:200]}...")

        print("\n💻 Code Generation: Fibonacci with DP")
        fib_code = await ai.generate(
            "Write Python code for Fibonacci using dynamic programming with memoization",
            quality_requirement="high"
        )
        print(f"Generated Code:\n{fib_code.content[:300]}...")

        print("\n🎯 Project Recommendation")
        project_idea = await ai.generate(
            "Suggest a beginner-friendly dynamic programming project for learning",
            quality_requirement="standard"
        )
        print(f"Project Idea: {project_idea.content[:150]}...")

        print("\n✅ DSA Learning Platform Ready!")
        print("💰 Current Cost: $0.00 (Development Mode)")

if __name__ == "__main__":
    asyncio.run(main())
