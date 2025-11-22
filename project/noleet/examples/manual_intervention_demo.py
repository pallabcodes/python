#!/usr/bin/env python3
"""
Manual Intervention Demo for NoLeet

This script demonstrates how to use the manual intervention system
in the NoLeet platform for enhanced human-AI collaboration.
"""

import asyncio
import json
from pathlib import Path
import time

from noleet.agents.agent_orchestrator import AgentOrchestrator
from noleet.manual_intervention.intervention_config import InterventionConfig
from noleet.llm.llm_config import LLMConfig


class ManualInterventionDemo:
    """Demonstrates manual intervention workflows."""

    def __init__(self):
        """Initialize the demo."""
        print("🤖 NoLeet Manual Intervention Demo")
        print("=" * 50)

        # Setup configuration
        self.intervention_config = InterventionConfig(
            enabled=True,
            intervention_points=["project_recommendation_agent"],
            max_wait_time_seconds=300,  # 5 minutes for demo
            export_directory=Path.home() / ".noleet" / "demo_intervention"
        )

        # Create orchestrator with intervention support
        llm_config = LLMConfig()
        self.orchestrator = AgentOrchestrator(
            llm_config=llm_config,
            intervention_config=self.intervention_config
        )

        print("✅ Demo environment initialized")

    async def run_demo(self):
        """Run the complete manual intervention demo."""
        print("\n🚀 Starting Manual Intervention Demo")
        print("-" * 40)

        # Step 1: Start a recommendation workflow
        print("\n1️⃣ Starting project recommendation workflow...")
        workflow_result = await self._start_recommendation_workflow()

        if workflow_result.get("status") == "waiting_for_manual_input":
            session_id = workflow_result["intervention_session"]
            export_path = workflow_result.get("export_path", "")

            print(f"⏸️ Workflow paused for manual intervention")
            print(f"Session ID: {session_id}")
            print(f"Data exported to: {export_path}")

            # Step 2: Simulate manual processing
            print("\n2️⃣ Simulating manual processing...")
            await self._simulate_manual_processing(session_id, export_path)

            # Step 3: Resume workflow
            print("\n3️⃣ Resuming workflow with manual input...")
            await self._resume_workflow(session_id)

        else:
            print("ℹ️ Workflow completed automatically (no intervention triggered)")
            print(f"Result: {workflow_result}")

        # Step 4: Show statistics
        print("\n4️⃣ Final statistics...")
        self._show_statistics()

    async def _start_recommendation_workflow(self) -> dict:
        """Start a project recommendation workflow."""
        # Create recommendation workflow
        workflow_name = self.orchestrator.create_recommendation_workflow()

        # Execute with sample data
        input_data = {
            "query": "projects with dynamic programming and sliding window techniques",
            "topics": ["dynamic_programming", "sliding_window"],
            "user_id": "demo_user",
            "max_recommendations": 3
        }

        print(f"Executing workflow: {workflow_name}")
        print(f"Input: {input_data}")

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.orchestrator.execute_workflow(
                workflow_name, input_data, allow_manual_intervention=True
            )
        )

        return result

    async def _simulate_manual_processing(self, session_id: str, export_path: str):
        """Simulate manual processing of exported data."""
        print("🎯 Manual processing simulation:")
        print("- Reading exported data...")
        print("- Analyzing with external tools (Cursor, ChatGPT, etc.)...")
        print("- Creating enhanced recommendations...")

        # Wait a bit to simulate processing time
        await asyncio.sleep(2)

        # Create sample manual recommendations
        manual_recommendations = {
            "recommendations": [
                {
                    "project_id": "custom_dp_project_1",
                    "title": "Advanced Dynamic Programming Engine",
                    "confidence_score": 0.95,
                    "reasoning": "Expert analysis shows this combines multiple DP techniques with practical applications",
                    "key_topics": ["dynamic_programming", "optimization", "memoization"],
                    "estimated_complexity": "advanced",
                    "learning_objectives": [
                        "Master advanced DP techniques",
                        "Understand optimization trade-offs",
                        "Apply DP to real-world problems"
                    ]
                },
                {
                    "project_id": "custom_window_project_1",
                    "title": "Intelligent Sliding Window System",
                    "confidence_score": 0.88,
                    "reasoning": "Manual review identified opportunities for adaptive window sizing algorithms",
                    "key_topics": ["sliding_window", "two_pointers", "algorithm_optimization"],
                    "estimated_complexity": "intermediate",
                    "learning_objectives": [
                        "Implement variable-size windows",
                        "Optimize for different data patterns",
                        "Handle edge cases efficiently"
                    ]
                }
            ],
            "metadata": {
                "manual_reviewer": "Demo Expert",
                "review_timestamp": "2024-01-15T10:30:00Z",
                "additional_notes": "Enhanced recommendations based on industry best practices and recent research papers"
            }
        }

        # Save manual recommendations
        manual_file = Path(export_path).parent / f"manual_recommendations_{session_id[:8]}.json"
        with open(manual_file, "w") as f:
            json.dump(manual_recommendations, f, indent=2)

        print(f"✅ Manual recommendations saved to: {manual_file}")
        print("📋 Manual recommendations created:"
        for rec in manual_recommendations["recommendations"]:
            print(f"  - {rec['title']} (Score: {rec['confidence_score']})")

    async def _resume_workflow(self, session_id: str):
        """Resume the workflow with manual input."""
        print(f"Resuming session: {session_id}")

        # Resume the workflow
        resume_result = self.orchestrator.resume_workflow(session_id)

        if resume_result["success"]:
            print("✅ Workflow resumed successfully!")
            print(f"Resumed from: {resume_result.get('resumed_from', 'unknown')}")
            print(f"Manual data applied: {resume_result.get('manual_data_applied', False)}")

            # Show final results
            results = resume_result.get("results", {})
            print("\n📊 Final Workflow Results:")
            for agent, result in results.items():
                status = "✅" if isinstance(result, dict) and "error" not in result else "❌"
                print(f"  {status} {agent}")

        else:
            print(f"❌ Failed to resume workflow: {resume_result.get('error', 'Unknown error')}")

    def _show_statistics(self):
        """Show intervention statistics."""
        stats = self.orchestrator.get_intervention_statistics()

        print("\n📈 Intervention Statistics:")
        print(f"Total sessions: {stats['total_sessions']}")
        print(f"Completed sessions: {stats['completed_sessions']}")
        print(f"Active sessions: {stats['active_sessions']}")

        if stats['average_completion_time_seconds'] > 0:
            print(f"Average completion time: {stats['average_completion_time_seconds']:.1f}s")


async def main():
    """Main demo function."""
    demo = ManualInterventionDemo()

    try:
        await demo.run_demo()
        print("\n🎉 Manual Intervention Demo completed successfully!")
        print("\n💡 Key Benefits Demonstrated:")
        print("  • Human expertise enhances AI recommendations")
        print("  • Flexible workflow with pause/resume capability")
        print("  • Seamless integration of manual and automated processing")
        print("  • Data export/import for external tool integration")
        print("  • Production-ready pause/resume workflow management")

    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
