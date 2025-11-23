#!/usr/bin/env python3
"""
Code Scaffolding Agent Demo

This script demonstrates how the AI Code Scaffolding Agent works in NoLeet.
It shows how users can generate complete project boilerplate from project recommendations.

Usage:
    python examples/code_scaffolding_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Project, Topic
from agents.code_scaffolding_agent import (
    CodeScaffoldingAgent,
    ScaffoldingContext,
    Language,
    Framework
)
from aiframework import AIFramework, AIFrameworkConfig


async def demo_code_scaffolding():
    """Demonstrate the Code Scaffolding Agent."""
    print("🚀 NoLeet Code Scaffolding Agent Demo")
    print("=" * 50)

    # Create a sample project (like one that would be recommended)
    sample_project = Project(
        id="sample_dp_project",
        name="Dynamic Programming Coin Change Solver",
        description="Implement a dynamic programming solution to solve the coin change problem - finding the minimum number of coins needed to make a given amount.",
        topics=["dynamic_programming", "arrays", "greedy"],
        difficulty="intermediate",
        estimated_hours=8,
        learning_outcomes=[
            "Understand dynamic programming approach to optimization problems",
            "Implement bottom-up DP solutions with proper space optimization",
            "Analyze time and space complexity of DP algorithms",
            "Handle edge cases in algorithmic problems"
        ],
        prerequisites=["Basic programming", "Arrays", "Functions"],
        tags=["dynamic-programming", "optimization", "interview-prep"]
    )

    print(f"🎯 Sample Project: {sample_project.name}")
    print(f"📝 Description: {sample_project.description}")
    print(f"🏷️  Topics: {', '.join(sample_project.topics)}")
    print(f"📊 Difficulty: {sample_project.difficulty}")
    print()

    # Create scaffolding context for a beginner user
    scaffold_context = ScaffoldingContext(
        project=sample_project,
        user_level="beginner",
        preferred_language=Language.PYTHON,
        preferred_framework=Framework.NONE,  # Standard library only for beginners
        time_available="short",
        include_tests=True,
        include_docs=True,
        project_complexity="simple"
    )

    print("👤 User Context:")
    print(f"   • Skill Level: {scaffold_context.user_level}")
    print(f"   • Language: {scaffold_context.preferred_language.value}")
    print(f"   • Time Available: {scaffold_context.time_available}")
    print(f"   • Include Tests: {scaffold_context.include_tests}")
    print(f"   • Include Docs: {scaffold_context.include_docs}")
    print()

    # Initialize AI Framework and Scaffolding Agent
    print("🤖 Initializing AI Code Scaffolding Agent...")
    ai_config = AIFrameworkConfig()
    ai_framework = AIFramework(ai_config)
    scaffolding_agent = CodeScaffoldingAgent(ai_framework)

    try:
        # Generate the scaffold
        print("🔨 Generating project scaffold...")
        scaffold = await scaffolding_agent.generate_scaffold(scaffold_context)

        print("
✅ Scaffold Generated Successfully!"        print(f"🏗️  Project Name: {scaffold.project_name}")
        print(f"💻 Language: {scaffold.language.value}")
        print(f"🔧 Framework: {scaffold.framework.value if scaffold.framework != Framework.NONE else 'None'}")
        print(f"📄 Files: {len(scaffold.files)}")
        print(f"📂 Directories: {len(scaffold.directories)}")
        print(f"📦 Dependencies: {len(scaffold.dependencies)}")

        print("
📁 Project Structure:"        for directory in scaffold.directories:
            print(f"   📂 {directory}/")

        print("
📄 Generated Files:"        for file_info in scaffold.files:
            executable = " (executable)" if file_info.executable else ""
            template = " (template)" if file_info.is_template else ""
            print(f"   📄 {file_info.path} - {file_info.description}{executable}{template}")

        if scaffold.dependencies:
            print("
📦 Dependencies:"            for package, version in scaffold.dependencies.items():
                print(f"   • {package}{version}")

        if scaffold.setup_instructions:
            print("
🚀 Setup Instructions:"            for i, instruction in enumerate(scaffold.setup_instructions, 1):
                print(f"   {i}. {instruction}")

        print("
💡 Key Features of Generated Scaffold:"        print("   ✅ Complete project structure with proper organization")
        print("   ✅ Main application file with DSA algorithm placeholder")
        print("   ✅ Comprehensive test suite with example tests")
        print("   ✅ Detailed README with setup and learning instructions")
        print("   ✅ Technical documentation for implementation guidance")
        print("   ✅ Proper .gitignore and project configuration")
        print("   ✅ Educational comments explaining DSA concepts")
        print("   ✅ Beginner-friendly code structure and examples")

        print("
🎯 Learning Benefits:"        print("   • Eliminates 'blank page paralysis' for new projects")
        print("   • Provides proper project structure from day one")
        print("   • Includes testing framework to validate implementations")
        print("   • Offers educational documentation and guidance")
        print("   • Enables focus on DSA algorithm implementation, not boilerplate")

        # Show a sample of generated code
        main_file = next((f for f in scaffold.files if f.path == "main.py"), None)
        if main_file:
            print("
📝 Sample Generated Code (main.py):"            print("-" * 50)
            lines = main_file.content.split('\n')[:30]  # First 30 lines
            for i, line in enumerate(lines, 1):
                print("2d")
            if len(main_file.content.split('\n')) > 30:
                print("   ... (truncated - full file would be generated)")
            print("-" * 50)

        print("
🎉 Demo Complete!"        print("This scaffold gives beginners a complete starting point for their DSA project,")
        print("eliminating the overwhelming 'where do I start?' feeling and allowing them to")
        print("focus on learning and implementing the actual algorithms!")

    except Exception as e:
        print(f"❌ Error during scaffold generation: {e}")
        import traceback
        traceback.print_exc()


async def demo_cli_integration():
    """Show how scaffolding integrates with the CLI workflow."""
    print("\n" + "=" * 50)
    print("🔗 CLI Integration Demo")
    print("=" * 50)

    print("Typical NoLeet User Journey:")
    print("1. 📋 User explores topics: noleet topics")
    print("2. 🤖 Gets AI recommendations: noleet find dynamic_programming arrays")
    print("3. 📖 Reviews project details: noleet show sample_dp_project")
    print("4. 🔨 Generates scaffold: noleet scaffold sample_dp_project")
    print("5. 🚀 Starts building: cd coin_change_solver && python main.py")

    print("\n💡 The scaffold bridges the gap between 'great idea' and 'working code'!")
    print("   Users go from inspiration to implementation in minutes, not hours.")


if __name__ == "__main__":
    print("🤖 NoLeet AI Code Scaffolding Agent Demo")
    print("=" * 60)

    # Run the main demo
    asyncio.run(demo_code_scaffolding())

    # Show CLI integration
    asyncio.run(demo_cli_integration())

    print("\n🎯 Summary:")
    print("The Code Scaffolding Agent transforms project recommendations into")
    print("production-ready starting points, enabling users to focus on DSA")
    print("learning rather than project setup and boilerplate code!")
