"""Main CLI interface for NoLeet."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Set

from noleet.core.models import Topic
from noleet.matching.matcher import ProjectMatcher
from noleet.storage.repository import ProjectRepository
from noleet.intelligence.ai_recommendation_service import AIRecommendationService, RecommendationContext
from noleet.agents.code_scaffolding_agent import CodeScaffoldingAgent, ScaffoldingContext, Language, Framework
from noleet.agents.interactive_tutor_agent import InteractiveTutorAgent, TutorContext, TutorMode, TutorSession
from noleet.agents.code_review_agent import CodeReviewAgent, CodeReviewContext, CodeReviewResult
from noleet.community import CommunityContributionSystem, CommunityIntelligenceAgent, PeerLearningEngine
from aiframework import AIFrameworkConfig, AIFramework
from noleet.cli.data_commands import DataCommands, add_data_parser, handle_data_commands
from noleet.cli.intervention_commands import add_intervention_parser, handle_intervention_commands

# Optional TUI import
try:
    from noleet.tui.app import NoLeetApp
    TUI_AVAILABLE = True
except ImportError:
    TUI_AVAILABLE = False
    NoLeetApp = None


class NoLeetCLI:
    """Command-line interface for NoLeet platform."""
    
    def __init__(self, data_dir: Path) -> None:
        """
        Initialize CLI.

        Args:
            data_dir: Directory containing project data
        """
        self._data_dir = data_dir
        self._repository = ProjectRepository(data_dir)
        self._basic_matcher = ProjectMatcher()  # Keep for fallback

        # Initialize AI recommendation service
        ai_config = AIFrameworkConfig()
        self._ai_recommender = AIRecommendationService(data_dir, ai_config)

        # Feature flags for optional components (zero deployment cost)
        self._enable_advanced_features = os.getenv('NOLEET_ENABLE_ADVANCED', 'false').lower() == 'true'

        # Initialize AI Framework (only if advanced features enabled)
        if self._enable_advanced_features:
            ai_framework = AIFramework(ai_config)

            # Initialize Interactive Tutor Agent
            self._tutor_agent = InteractiveTutorAgent(ai_framework)
            self._active_tutor_session: Optional[TutorSession] = None

            # Initialize Code Review Agent
            self._code_review_agent = CodeReviewAgent(ai_framework)
        else:
            # Mark as None for clean error handling
            self._tutor_agent = None
            self._code_review_agent = None

        # Initialize Community Learning System (core feature, always enabled)
        self._contribution_system = CommunityContributionSystem(self._data_dir)
        if self._enable_advanced_features:
            ai_framework = AIFramework(ai_config)  # Re-initialize if needed
            self._community_intelligence = CommunityIntelligenceAgent(
                ai_framework, self._contribution_system
            )
            self._peer_learning_engine = PeerLearningEngine(
                ai_framework, self._contribution_system, self._community_intelligence
            )
        else:
            # Basic community system without AI enhancements
            self._community_intelligence = None
            self._peer_learning_engine = None

        self._logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def list_topics(self) -> None:
        """List all available DSA topics."""
        print("\nAvailable DSA Topics:")
        print("=" * 50)
        topics = list(Topic)
        for i, topic in enumerate(topics, 1):
            display_name = topic.value.replace("_", " ").title()
            print(f"{i:2d}. {display_name}")
        print()
    
    async def find_projects(self, topic_names: list[str]) -> None:
        """
        Find projects matching selected topics using conditional AI recommendations.

        Args:
            topic_names: List of topic names to search for
        """
        try:
            selected_topics = self._parse_topics(topic_names)
            if not selected_topics:
                print("Error: No valid topics selected.")
                self.list_topics()
                return

            # Gather user context for conditional recommendations
            context = await self._gather_user_context(topic_names)

            print(f"\n🤖 Analyzing your profile and topic selection: {', '.join(topic_names)}")
            print("💡 Generating personalized AI-powered project recommendations...\n")

            # Get AI-powered recommendations with conditional logic
            async with self._ai_recommender as recommender:
                recommendations = await recommender.get_recommendations(
                    topic_names, context, max_recommendations=5
                )

            if not recommendations:
                print(f"\n❌ No AI recommendations available for topics: {', '.join(topic_names)}")
                print("🔄 Falling back to basic matching...\n")

                # Fallback to basic matching
                projects = self._repository.load_projects()
                if not projects:
                    print("No projects available. Please add projects first.")
                    return

                matching_projects = self._basic_matcher.find_matching_projects(
                    projects, selected_topics
                )

                if not matching_projects:
                    print(f"\nNo projects found matching topics: {', '.join(topic_names)}")
                    print("\nTry selecting different topics or check available topics with:")
                    print("  noleet topics")
                    return

                self._display_basic_results(matching_projects, selected_topics)
                return

            # Display AI-powered results with context information
            self._display_conditional_ai_results(recommendations, context)

        except Exception as e:
            self._logger.error(f"Error finding projects: {e}", exc_info=True)
            print(f"Error: {e}")

    async def scaffold_project(self, project_id: str, output_dir: Path) -> None:
        """
        Generate complete project scaffolding for a recommended project.

        Args:
            project_id: ID of the project to scaffold
            output_dir: Directory to create the scaffolded project in
        """
        try:
            # Find the project
            projects = self._repository.load_projects()
            project = next((p for p in projects if p.id == project_id), None)

            if not project:
                print(f"❌ Project with ID '{project_id}' not found.")
                print("\n💡 Available projects:")
                all_projects = self._repository.load_projects()
                for p in all_projects[:10]:  # Show first 10
                    print(f"  {p.id}: {p.name}")
                if len(all_projects) > 10:
                    print(f"  ... and {len(all_projects) - 10} more")
                return

            print(f"🔨 Generating scaffolding for: {project.name}")
            print(f"📝 {project.description}")
            print("=" * 60)

            # Gather scaffolding context
            scaffold_context = await self._gather_scaffolding_context(project)

            # Initialize AI Framework and Scaffolding Agent
            ai_config = AIFrameworkConfig()
            ai_framework = AIFramework(ai_config)
            scaffolding_agent = CodeScaffoldingAgent(ai_framework)

            # Generate scaffold
            print("🤖 AI Code Scaffolding Agent is working...")
            scaffold = await scaffolding_agent.generate_scaffold(scaffold_context)

            # Create the project structure
            project_dir = output_dir / scaffold.project_name
            await self._create_scaffold_files(scaffold, project_dir)

            # Display results and instructions
            self._display_scaffolding_results(scaffold, project_dir)

        except Exception as e:
            self._logger.error(f"Error scaffolding project: {e}", exc_info=True)
            print(f"❌ Error generating scaffold: {e}")

    async def handle_tutor_command(self, args) -> None:
        """
        Handle tutor-related commands.

        Args:
            args: Parsed command line arguments
        """
        if not self._enable_advanced_features:
            print("❌ Advanced features are disabled. Enable with NOLEET_ENABLE_ADVANCED=true")
            print("💡 This keeps deployment lightweight and focused on core functionality")
            return

        try:
            tutor_command = args.tutor_command

            if tutor_command == "start":
                await self._start_tutor_session(args.project_id, args.level)
            elif tutor_command == "ask":
                await self._ask_tutor_question(args.question, args.code, args.file)
            elif tutor_command == "review":
                await self._request_code_review(args.code, args.file)
            elif tutor_command == "debug":
                await self._request_debug_help(args.error, args.code)
            elif tutor_command == "explain":
                await self._explain_concept(args.concept, args.level)
            elif tutor_command == "guide":
                await self._request_implementation_guide(args.step, args.code)
            elif tutor_command == "path":
                await self._suggest_learning_path()
            elif tutor_command == "end":
                await self._end_tutor_session()
            else:
                print("❌ Unknown tutor command. Use 'noleet tutor --help' for available commands.")

        except Exception as e:
            self._logger.error(f"Error handling tutor command: {e}", exc_info=True)
            print(f"❌ Error with tutor command: {e}")

    async def _start_tutor_session(self, project_id: str, user_level: str) -> None:
        """
        Start a new tutoring session.

        Args:
            project_id: Project to tutor for
            user_level: User's skill level
        """
        try:
            # Find the project
            projects = self._repository.load_projects()
            project = next((p for p in projects if p.id == project_id), None)

            if not project:
                print(f"❌ Project '{project_id}' not found.")
                return

            # End any existing session
            if self._active_tutor_session:
                await self._tutor_agent.end_session(self._active_tutor_session.session_id)

            # Start new session
            session_id = await self._tutor_agent.start_session(
                project_id=project_id,
                user_level=user_level,
                topics=list(project.topics)
            )

            # Create session object for CLI tracking
            self._active_tutor_session = TutorSession(
                session_id=session_id,
                project_id=project_id,
                user_level=user_level,
                current_topic=list(project.topics)[0] if project.topics else "general"
            )

            print("🎓 Interactive Tutor Session Started!")
            print("=" * 50)
            print(f"📚 Project: {project.name}")
            print(f"🏷️  Topics: {', '.join(project.topics)}")
            print(f"📊 Your Level: {user_level.title()}")
            print()
            print("💡 Available tutor commands:")
            print("  noleet tutor ask 'your question'          # Ask about DSA concepts")
            print("  noleet tutor review --code 'your code'    # Get code review")
            print("  noleet tutor debug --error 'error msg'    # Debug help")
            print("  noleet tutor explain arrays               # Explain concepts")
            print("  noleet tutor guide 'current step'         # Implementation guidance")
            print("  noleet tutor path                         # Learning path suggestions")
            print("  noleet tutor end                          # End session")
            print()
            print("🤖 I'm here to help you learn by doing! Ask me anything about your implementation.")

        except Exception as e:
            self._logger.error(f"Error starting tutor session: {e}")
            print(f"❌ Failed to start tutoring session: {e}")

    async def _ask_tutor_question(
        self,
        question: str,
        code: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> None:
        """
        Ask the tutor a question.

        Args:
            question: The question to ask
            code: Optional code context
            file_path: Optional file being worked on
        """
        if not self._active_tutor_session:
            print("❌ No active tutoring session. Start one with: noleet tutor start <project_id>")
            return

        # Load code from file if specified
        if file_path and not code:
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
            except Exception as e:
                print(f"⚠️  Could not read file {file_path}: {e}")

        # Get project description
        projects = self._repository.load_projects()
        project = next((p for p in projects if p.id == self._active_tutor_session.project_id), None)
        project_desc = project.description if project else None

        # Create tutor context
        context = TutorContext(
            user_code=code,
            current_file=file_path,
            question=question,
            project_description=project_desc,
            user_level=self._active_tutor_session.user_level,
            topics=[self._active_tutor_session.current_topic],
            session=self._active_tutor_session
        )

        print(f"🤔 Thinking about: {question}")
        print("💭" + "=" * 50)

        # Get tutor response
        response = await self._tutor_agent.provide_guidance(context, TutorMode.QUESTION_ANSWERING)

        # Display response
        print(response.answer)

        if response.suggestions:
            print("\n💡 Suggestions:")
            for suggestion in response.suggestions:
                print(f"   • {suggestion}")

        if response.next_steps:
            print("\n🚀 Next Steps:")
            for step in response.next_steps:
                print(f"   • {step}")

        print("\n" + "=" * 50)

    async def _request_code_review(self, code: Optional[str] = None, file_path: Optional[str] = None) -> None:
        """
        Request code review from tutor.

        Args:
            code: Code to review
            file_path: File containing code to review
        """
        if not self._active_tutor_session:
            print("❌ No active tutoring session. Start one with: noleet tutor start <project_id>")
            return

        # Load code from file if specified
        if file_path and not code:
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
            except Exception as e:
                print(f"❌ Could not read file {file_path}: {e}")
                return

        if not code:
            print("❌ No code provided. Use --code 'your code' or --file path/to/file")
            return

        # Get project context
        projects = self._repository.load_projects()
        project = next((p for p in projects if p.id == self._active_tutor_session.project_id), None)
        project_desc = project.description if project else None

        context = TutorContext(
            user_code=code,
            current_file=file_path,
            project_description=project_desc,
            user_level=self._active_tutor_session.user_level,
            topics=[self._active_tutor_session.current_topic],
            session=self._active_tutor_session
        )

        print("🔍 Analyzing your code...")
        print("📝" + "=" * 50)

        response = await self._tutor_agent.provide_guidance(context, TutorMode.CODE_REVIEW)

        print(response.answer)

        if response.suggestions:
            print("\n💡 Improvement Suggestions:")
            for suggestion in response.suggestions:
                print(f"   • {suggestion}")

        print("\n" + "=" * 50)

    async def _request_debug_help(self, error: Optional[str] = None, code: Optional[str] = None) -> None:
        """
        Request debugging help from tutor.

        Args:
            error: Error message
            code: Code with issues
        """
        if not self._active_tutor_session:
            print("❌ No active tutoring session. Start one with: noleet tutor start <project_id>")
            return

        if not error and not code:
            print("❌ Provide either --error 'error message' or --code 'problematic code'")
            return

        # Get project context
        projects = self._repository.load_projects()
        project = next((p for p in projects if p.id == self._active_tutor_session.project_id), None)
        project_desc = project.description if project else None

        context = TutorContext(
            user_code=code,
            error_message=error,
            project_description=project_desc,
            user_level=self._active_tutor_session.user_level,
            topics=[self._active_tutor_session.current_topic],
            session=self._active_tutor_session
        )

        print("🐛 Debugging your issue...")
        print("🔧" + "=" * 50)

        response = await self._tutor_agent.provide_guidance(context, TutorMode.DEBUGGING)

        print(response.answer)

        if response.suggestions:
            print("\n🔧 Debug Steps:")
            for suggestion in response.suggestions:
                print(f"   • {suggestion}")

        print("\n" + "=" * 50)

    async def _explain_concept(self, concept: str, level: str) -> None:
        """
        Explain a DSA concept.

        Args:
            concept: Concept to explain
            level: Explanation depth level
        """
        if not self._active_tutor_session:
            print("❌ No active tutoring session. Start one with: noleet tutor start <project_id>")
            return

        context = TutorContext(
            question=f"Explain {concept}",
            user_level=level,
            topics=[concept],
            session=self._active_tutor_session
        )

        print(f"📚 Explaining {concept}...")
        print("🎓" + "=" * 50)

        response = await self._tutor_agent.provide_guidance(context, TutorMode.CONCEPT_EXPLANATION)

        print(response.answer)

        if response.related_concepts:
            print(f"\n🔗 Related Concepts:")
            for concept in response.related_concepts:
                print(f"   • {concept}")

        print("\n" + "=" * 50)

    async def _request_implementation_guide(self, step: str, code: Optional[str] = None) -> None:
        """
        Request implementation guidance.

        Args:
            step: Current implementation step
            code: Current code state
        """
        if not self._active_tutor_session:
            print("❌ No active tutoring session. Start one with: noleet tutor start <project_id>")
            return

        # Get project context
        projects = self._repository.load_projects()
        project = next((p for p in projects if p.id == self._active_tutor_session.project_id), None)
        project_desc = f"{project.description if project else 'General DSA problem'} - Current step: {step}"

        context = TutorContext(
            user_code=code,
            question=f"Guide me through implementing: {step}",
            project_description=project_desc,
            user_level=self._active_tutor_session.user_level,
            topics=[self._active_tutor_session.current_topic],
            session=self._active_tutor_session
        )

        print(f"🚀 Guiding you through: {step}")
        print("🧭" + "=" * 50)

        response = await self._tutor_agent.provide_guidance(context, TutorMode.IMPLEMENTATION_GUIDANCE)

        print(response.answer)

        if response.next_steps:
            print("\n🚀 Implementation Steps:")
            for next_step in response.next_steps:
                print(f"   • {next_step}")

        print("\n" + "=" * 50)

    async def _suggest_learning_path(self) -> None:
        """Suggest learning path and next steps."""
        if not self._active_tutor_session:
            print("❌ No active tutoring session. Start one with: noleet tutor start <project_id>")
            return

        context = TutorContext(
            user_level=self._active_tutor_session.user_level,
            topics=[self._active_tutor_session.current_topic],
            session=self._active_tutor_session
        )

        print("🛣️  Planning your learning journey...")
        print("🧭" + "=" * 50)

        response = await self._tutor_agent.provide_guidance(context, TutorMode.LEARNING_PATH)

        print(response.answer)

        if response.related_concepts:
            print("\n🔗 Concepts to Explore:")
            for concept in response.related_concepts:
                print(f"   • {concept}")

        if response.next_steps:
            print("\n🚀 Recommended Next Steps:")
            for step in response.next_steps:
                print(f"   • {step}")

        print("\n" + "=" * 50)

    async def _end_tutor_session(self) -> None:
        """End the current tutoring session."""
        if not self._active_tutor_session:
            print("ℹ️  No active tutoring session to end.")
            return

        session_id = self._active_tutor_session.session_id
        await self._tutor_agent.end_session(session_id)

        print("👋 Tutoring session ended.")
        print(f"📊 Session ID: {session_id}")
        print("💡 Hope you learned something valuable! Start a new session anytime with:")
        print("   noleet tutor start <project_id>")

        self._active_tutor_session = None

    async def handle_community_command(self, args) -> None:
        """
        Handle community-related commands.

        Args:
            args: Parsed command line arguments
        """
        try:
            community_command = args.community_command

            if community_command == "view":
                await self._view_community_contributions(args.project_id, args.type)
            elif community_command == "learn":
                await self._start_community_learning(args.project_id, args.level)
            elif community_command == "share":
                await self._share_community_contribution(args)
            elif community_command == "next":
                await self._get_next_learning_step()
            elif community_command == "progress":
                await self._view_learning_progress()
            elif community_command == "complete":
                await self._mark_contribution_complete(args.rating)
            else:
                print("❌ Unknown community command. Use 'noleet community --help' for available commands.")

        except Exception as e:
            self._logger.error(f"Error handling community command: {e}", exc_info=True)
            print(f"❌ Error with community command: {e}")

    async def _view_community_contributions(self, project_id: str, contribution_type: str) -> None:
        """View community contributions for a project."""
        print(f"🌐 Community Contributions for Project: {project_id}")
        print("=" * 60)

        # Get contributions
        contributions = await self._contribution_system.get_project_contributions(
            project_id=project_id,
            limit=10
        )

        if not contributions:
            print(f"📝 No community contributions found for project {project_id}.")
            print("\n💡 Be the first to share!")
            print(f"   noleet community share {project_id} --title 'Your Implementation' --content 'Your code here'")
            return

        print(f"📊 Found {len(contributions)} community contributions")
        print()

        for i, contrib in enumerate(contributions, 1):
            print(f"{i}. {contrib.title}")
            print(f"   👤 {contrib.author_id} • 👍 {contrib.upvotes} • 👀 {contrib.views}")
            print(f"   📝 {contrib.description[:100]}{'...' if len(contrib.description) > 100 else ''}")

            if contrib.topics:
                print(f"   🏷️  Topics: {', '.join(contrib.topics)}")

            print(f"   📊 Type: {contrib.contribution_type.value.replace('_', ' ').title()}")
            print()

        print("💡 Commands:")
        print("   noleet community learn <project_id>    # Start learning session")
        print("   noleet community share <project_id>    # Share your solution")

    async def _start_community_learning(self, project_id: str, skill_level: str) -> None:
        """Start a community-powered learning session."""
        print(f"🚀 Starting Community Learning Session")
        print(f"📚 Project: {project_id}")
        print(f"🏆 Skill Level: {skill_level}")
        print("=" * 60)

        # Get user's topics of interest
        print("\nWhat DSA topics are you focusing on? (space-separated, or press Enter for defaults):")
        try:
            topics_input = input("Topics: ").strip()
            topics = topics_input.split() if topics_input else ["arrays", "dynamic_programming"]
        except (EOFError, KeyboardInterrupt):
            topics = ["arrays", "dynamic_programming"]

        print(f"🎯 Learning Topics: {', '.join(topics)}")
        print("\n🤖 Analyzing community knowledge for your learning journey...")

        # Create learning experience
        try:
            experience = await self._peer_learning_engine.create_learning_experience(
                project_id=project_id,
                user_topics=topics,
                user_skill_level=skill_level,
                learning_goal="portfolio"
            )

            print("✅ Community Learning Experience Created!")
            print(f"📋 Learning Objectives: {len(experience.learning_objectives)}")
            print(f"📚 Recommended Contributions: {len(experience.recommended_sequence) if experience.recommended_sequence else 0}")
            print(f"⏱️  Estimated Time: {experience.estimated_learning_time}")

            # Start learning session
            session_id = await self._peer_learning_engine.start_learning_session(experience)

            print(f"\n🎓 Session Started! (ID: {session_id})")
            print("\n🎯 Next Steps:")
            print("   noleet community next     # Get your first learning assignment")
            print("   noleet community progress # View community insights")
            print("   noleet community complete # Mark learning as complete")

        except Exception as e:
            self._logger.error(f"Error starting community learning: {e}")
            print(f"❌ Failed to start learning session: {e}")
            print("💡 Try: noleet community view <project_id> to see available content")

    async def _share_community_contribution(self, args) -> None:
        """Share a community contribution."""
        print("📤 Sharing Your Contribution with the Community")
        print("=" * 50)

        # Get content
        content = args.content
        if not content and args.file:
            try:
                with open(args.file, 'r') as f:
                    content = f.read()
            except Exception as e:
                print(f"❌ Could not read file {args.file}: {e}")
                return
        elif not content:
            print("❌ No content provided. Use --content 'your content' or --file path/to/file")
            return

        # Map contribution type
        from noleet.community.contribution_system import ContributionType
        type_mapping = {
            "implementation": ContributionType.PROJECT_IMPLEMENTATION,
            "snippet": ContributionType.CODE_SNIPPET,
            "insight": ContributionType.LEARNING_INSIGHT,
            "mistake": ContributionType.DEBUG_STORY
        }
        contrib_type = type_mapping.get(args.type, ContributionType.PROJECT_IMPLEMENTATION)

        try:
            # Create contribution
            contribution = await self._contribution_system.create_contribution(
                contribution_type=contrib_type,
                project_id=args.project_id,
                title=args.title,
                description=f"Shared {args.type} for project {args.project_id}",
                content=content,
                author_id="cli_user",
                topics=args.topics or []
            )

            print("✅ Contribution Shared Successfully!")
            print(f"🆔 ID: {contribution.id}")
            print(f"📝 Title: {contribution.title}")
            print(f"🏷️  Type: {contrib_type.value.replace('_', ' ').title()}")

            if args.topics:
                print(f"🎯 Topics: {', '.join(args.topics)}")

            print("🙏 Thank you for contributing to the community!")
            print("   Your shared knowledge will help other learners master DSA through real projects.")
        except Exception as e:
            self._logger.error(f"Error sharing contribution: {e}")
            print(f"❌ Failed to share contribution: {e}")

    async def _get_next_learning_step(self) -> None:
        """Get the next learning step (simplified for now)."""
        print("📚 Next Learning Step")
        print("=" * 40)

        print("ℹ️  Interactive learning sessions are being enhanced!")
        print("   For now, explore community content:")
        print("   noleet community view <project_id>")
        print("   noleet community progress")

    async def _view_learning_progress(self) -> None:
        """View learning progress and community insights."""
        print("📊 Community Learning Insights")
        print("=" * 50)

        # Get community statistics
        stats = self._contribution_system.get_stats()

        print(f"🌐 Community Overview:")
        print(f"   📝 Total Contributions: {stats['total_contributions']}")
        print(f"   👀 Total Views: {stats['total_views']}")
        print(f"   👍 Helpful Marks: {stats['total_helpful_marks']}")
        print(f"   ⭐ Average Quality: {stats['average_quality_score']:.2f}")

        if stats['top_topics']:
            print(f"\n🔥 Popular Learning Topics:")
            for topic, count in stats['top_topics'][:5]:
                print(f"   • {topic}: {count} contributions")

        print("💡 Community Learning Tips:")
        print("   • Share your implementations to help others")
        print("   • Compare different approaches to the same problem")
        print("   • Learn from community insights and debugging stories")
        print("   • Contribute back after completing projects")

    async def _mark_contribution_complete(self, rating: Optional[int]) -> None:
        """Mark learning progress."""
        print("✅ Learning Progress Recorded")
        print("=" * 35)

        if rating:
            print(f"⭐ You rated this contribution: {rating}/5")
            print("   Your feedback helps improve the community!")

        print("📈 Every contribution you study makes you a better DSA engineer!")
        print("   Keep exploring the community - there's always more to learn.")

    async def handle_review_command(self, args) -> None:
        """
        Handle code review command.

        Args:
            args: Parsed command line arguments
        """
        if not self._enable_advanced_features:
            print("❌ Advanced features are disabled. Enable with NOLEET_ENABLE_ADVANCED=true")
            print("💡 This keeps deployment lightweight and focused on core functionality")
            return

        try:
            print("🔍 NoLeet Code Review")
            print("=" * 50)

            # Get code to review
            if args.file:
                try:
                    with open(args.file, 'r') as f:
                        code = f.read()
                    print(f"📁 Reviewing code from file: {args.file}")
                except Exception as e:
                    print(f"❌ Could not read file {args.file}: {e}")
                    return
            else:
                code = args.code
                # If code looks like a file path, try to read it
                if not code.strip().startswith(('def ', 'class ', 'import ', '#')) and len(code.split()) == 1:
                    try:
                        with open(code, 'r') as f:
                            code = f.read()
                        print(f"📁 Reviewing code from file: {code}")
                    except:
                        # It's not a file path, treat as code string
                        pass

            if not code.strip():
                print("❌ No code provided to review.")
                print("Usage:")
                print("  noleet review 'your code here'")
                print("  noleet review --file path/to/code.py")
                return

            print(f"📝 Analyzing {len(code.splitlines())} lines of code...")
            print()

            # Create review context
            review_context = CodeReviewContext(
                code=code,
                language="python",  # Default to Python for now
                project_description=args.project,
                user_level=args.level,
                topics=args.topics or [],
                expected_algorithm=args.algorithm
            )

            # Perform code review
            print("🤖 AI Code Review in progress...")
            review_result = await self._code_review_agent.review_code(review_context)

            # Display results
            self._display_review_results(review_result)

        except Exception as e:
            self._logger.error(f"Error handling review command: {e}", exc_info=True)
            print(f"❌ Error during code review: {e}")

    def _display_review_results(self, result: CodeReviewResult) -> None:
        """
        Display code review results in a formatted way.

        Args:
            result: Code review result to display
        """
        # Overall score and grade
        print(f"📊 OVERALL SCORE: {result.overall_score:.1f}/100 ({result.grade})")
        print()

        # Summary
        print("📝 SUMMARY:")
        print(f"   {result.summary}")
        print()

        # Strengths
        if result.strengths:
            print("✅ STRENGTHS:")
            for strength in result.strengths[:5]:  # Limit to 5
                print(f"   • {strength}")
            print()

        # Issues by severity
        critical_issues = [i for i in result.issues if i.severity.name == "CRITICAL"]
        major_issues = [i for i in result.issues if i.severity.name == "MAJOR"]
        minor_issues = [i for i in result.issues if i.severity.name == "MINOR"]
        info_issues = [i for i in result.issues if i.severity.name == "INFO"]

        if critical_issues:
            print("🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"   ❌ {issue.title}")
                print(f"      {issue.description}")
                if issue.suggestion:
                    print(f"      💡 {issue.suggestion}")
                print()

        if major_issues:
            print("⚠️  MAJOR ISSUES:")
            for issue in major_issues[:3]:  # Limit display
                print(f"   ⚠️  {issue.title}")
                print(f"      {issue.description}")
                if issue.suggestion:
                    print(f"      💡 {issue.suggestion}")
                print()

        if minor_issues:
            print("ℹ️  MINOR ISSUES:")
            for issue in minor_issues[:3]:  # Limit display
                print(f"   ℹ️  {issue.title}")
                print(f"      {issue.description}")
                if issue.suggestion:
                    print(f"      💡 {issue.suggestion}")
                print()

        # Complexity analysis
        if result.time_complexity or result.space_complexity:
            print("⚡ COMPLEXITY ANALYSIS:")
            if result.time_complexity:
                print(f"   ⏱️  Time: {result.time_complexity}")
            if result.space_complexity:
                print(f"   💾 Space: {result.space_complexity}")
            print()

        # Suggestions
        if result.suggestions:
            print("💡 IMPROVEMENT SUGGESTIONS:")
            for suggestion in result.suggestions[:5]:  # Limit to 5
                print(f"   • {suggestion}")
            print()

        # Learning points
        if result.learning_points:
            print("🎓 LEARNING POINTS:")
            for point in result.learning_points[:5]:  # Limit to 5
                print(f"   • {point}")
            print()

        # Encouragement based on score
        if result.overall_score >= 90:
            print("🌟 EXCELLENT! Your implementation is outstanding!")
        elif result.overall_score >= 80:
            print("👍 GREAT job! Solid implementation with minor improvements possible.")
        elif result.overall_score >= 70:
            print("👌 GOOD work! Focus on the major issues to improve significantly.")
        elif result.overall_score >= 60:
            print("📚 KEEP learning! Review the suggestions and try again.")
        else:
            print("🎯 Keep practicing! Every great developer started somewhere.")

        print()
        print("💪 Code review helps you grow. Keep coding and learning!")
        print()

        # Show confidence
        confidence_pct = int(result.confidence_score * 100)
        print(f"🤖 AI Confidence: {confidence_pct}% (based on analysis quality)")

        # Learning goal
        print("\nWhat's your primary goal with these projects?")
        print("1. Portfolio - Build impressive projects to showcase")
        print("2. Interview Prep - Focus on technical interview preparation")
        print("3. Learning - General skill development and practice")

        while True:
            try:
                choice = input("Enter your choice (1-3) [1]: ").strip() or "1"
                goal_map = {"1": "portfolio", "2": "interview_prep", "3": "learning"}
                project_goal = goal_map.get(choice, "portfolio")
                if project_goal:
                    break
            except (EOFError, KeyboardInterrupt):
                project_goal = "portfolio"
                break

        # Time availability
        print("\nHow much time do you have for this project?")
        print("1. Short - 1-2 weeks (20 hours or less)")
        print("2. Medium - 1-2 months (20-80 hours)")
        print("3. Long - 3+ months (80+ hours)")

        while True:
            try:
                choice = input("Enter your choice (1-3) [2]: ").strip() or "2"
                time_map = {"1": "short", "2": "medium", "3": "long"}
                time_available = time_map.get(choice, "medium")
                if time_available:
                    break
            except (EOFError, KeyboardInterrupt):
                time_available = "medium"
                break

        # Optional: Career focus
        print("\nDo you have a specific career focus? (Optional)")
        print("1. Frontend - Web UI/UX development")
        print("2. Backend - Server-side and APIs")
        print("3. Full-stack - Complete web applications")
        print("4. Mobile - iOS/Android development")
        print("5. ML/AI - Machine learning and data science")
        print("6. DevOps - Infrastructure and deployment")
        print("7. Skip - No specific focus")

        career_focus = None
        try:
            choice = input("Enter your choice (1-7) or press Enter to skip [7]: ").strip() or "7"
            career_map = {
                "1": "frontend", "2": "backend", "3": "fullstack",
                "4": "mobile", "5": "ml", "6": "devops"
            }
            career_focus = career_map.get(choice)
        except (EOFError, KeyboardInterrupt):
            pass

        # Estimate previous projects (simplified)
        previous_projects_count = 0
        try:
            count_input = input("\nRoughly how many coding projects have you completed? [0]: ").strip() or "0"
            previous_projects_count = min(int(count_input), 20)  # Cap at 20
        except (ValueError, EOFError, KeyboardInterrupt):
            pass

        context = RecommendationContext(
            selected_topics=set(topic_names),
            user_level=user_level,
            project_goal=project_goal,
            time_available=time_available,
            career_focus=career_focus,
            previous_projects_count=previous_projects_count
        )

        print(f"\n✅ Profile captured: {user_level.title()} level, {project_goal.replace('_', ' ').title()} focus, {time_available.title()} timeline")
        if career_focus:
            print(f"🎯 Career focus: {career_focus.title()}")

        return context

    async def _gather_scaffolding_context(self, project) -> ScaffoldingContext:
        """
        Gather context information for scaffolding.

        Args:
            project: The project to scaffold

        Returns:
            ScaffoldingContext with user preferences
        """
        print("\n🔧 Let's customize your project scaffold!")
        print("This ensures the generated code matches your skill level and preferences.\n")

        # Reuse existing context gathering for consistency
        # In a full implementation, this would gather scaffolding-specific preferences
        rec_context = await self._gather_user_context([])

        # Determine preferred language (default to Python for DSA)
        print("\n💻 Preferred programming language for this project?")
        print("1. Python (recommended for DSA)")
        print("2. JavaScript")
        print("3. Java")
        print("4. C++")
        print("5. Go")

        preferred_language = Language.PYTHON  # Default
        try:
            choice = input("Enter your choice (1-5) [1]: ").strip() or "1"
            lang_map = {
                "1": Language.PYTHON,
                "2": Language.JAVASCRIPT,
                "3": Language.JAVA,
                "4": Language.CPP,
                "5": Language.GO
            }
            preferred_language = lang_map.get(choice, Language.PYTHON)
        except (EOFError, KeyboardInterrupt):
            pass

        # Convert recommendation context to scaffolding context
        scaffold_context = ScaffoldingContext(
            project=project,
            user_level=rec_context.user_level,
            preferred_language=preferred_language,
            career_focus=rec_context.career_focus,
            time_available=rec_context.time_available,
            include_tests=True,
            include_docs=True,
            project_complexity="medium"  # Could be determined from project metadata
        )

        print(f"\n✅ Scaffold context ready: {preferred_language.value.title()} | {rec_context.user_level} level")
        return scaffold_context

    async def _create_scaffold_files(self, scaffold, project_dir: Path) -> None:
        """
        Create the actual scaffold files and directories.

        Args:
            scaffold: The generated scaffold
            project_dir: Directory to create files in
        """
        print(f"\n📁 Creating project structure in: {project_dir}")

        # Create directories
        for directory in scaffold.directories:
            dir_path = project_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  📂 Created directory: {directory}")

        # Create root directory
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create files
        for file_info in scaffold.files:
            file_path = project_dir / file_info.path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info.content)

            # Make executable if needed
            if file_info.executable:
                import os
                os.chmod(file_path, 0o755)

            print(f"  📄 Created file: {file_info.path} - {file_info.description}")

        print(f"\n✅ Scaffold created with {len(scaffold.files)} files and {len(scaffold.directories)} directories")

    def _display_scaffolding_results(self, scaffold, project_dir: Path) -> None:
        """
        Display the scaffolding results and next steps.

        Args:
            scaffold: The generated scaffold
            project_dir: Where the scaffold was created
        """
        print(f"\n🎉 Project scaffold generated successfully!")
        print("=" * 60)
        print(f"📁 Location: {project_dir}")
        print(f"🏗️  Language: {scaffold.language.value.title()}")
        print(f"🔧 Framework: {scaffold.framework.value.title() if scaffold.framework != Framework.NONE else 'None'}")
        print(f"📄 Files Created: {len(scaffold.files)}")
        print(f"📂 Directories: {len(scaffold.directories)}")

        print(f"\n🚀 Next Steps:")
        print(f"1. cd {scaffold.project_name}")
        print(f"2. pip install -r requirements.txt")
        print(f"3. python main.py")
        print(f"4. python -m pytest tests/  # Run tests")

        if scaffold.setup_instructions:
            print(f"\n📋 Detailed Setup:")
            for i, instruction in enumerate(scaffold.setup_instructions, 1):
                print(f"   {i}. {instruction}")

        if scaffold.run_instructions:
            print(f"\n🎯 Quick Start:")
            for instruction in scaffold.run_instructions:
                print(f"   • {instruction}")

        print(f"\n📚 Learning Focus:")
        print(f"   This scaffold is designed for {scaffold.language.value.title()} developers")
        print(f"   implementing DSA concepts through practical projects.")

        print(f"\n💡 Pro Tips:")
        print(f"   • Start by implementing the _core_algorithm() method")
        print(f"   • Run tests frequently to verify your implementation")
        print(f"   • Check the docs/ folder for detailed implementation guides")
        print(f"   • Customize the code to match your learning style")

        print(f"\n🎯 Ready to build something amazing! The scaffold provides a solid foundation,")
        print(f"   but the real learning happens when you implement the DSA algorithms yourself.")

    def _display_conditional_ai_results(self, recommendations: list, context: RecommendationContext) -> None:
        """Display conditional AI-powered recommendations with personalization details."""
        print(f"\n🎯 Conditional AI-Powered Recommendations ({len(recommendations)} found)")
        print("=" * 90)

        # Show personalization summary
        print(f"📋 Personalized for: {context.user_level.title()} level | {context.project_goal.replace('_', ' ').title()} | {context.time_available.title()} timeline")
        if context.career_focus:
            print(f"🎯 Career focus: {context.career_focus.title()}")
        print()

        for i, rec in enumerate(recommendations, 1):
            project = rec.project

            # Enhanced confidence indicator
            if rec.confidence_score >= 0.85:
                confidence_icon, confidence_label = "🟢", "Excellent Match"
            elif rec.confidence_score >= 0.7:
                confidence_icon, confidence_label = "🟡", "Good Match"
            else:
                confidence_icon, confidence_label = "🔵", "Suitable Match"

            confidence_pct = int(rec.confidence_score * 100)

            print(f"{i}. {project.name}")
            print(f"   {confidence_icon} {confidence_label} ({confidence_pct}% confidence)")
            print(f"   💡 {rec.reasoning}")

            if rec.matched_topics:
                print(f"   🎯 Covers: {', '.join(rec.matched_topics)}")

            print(f"   📊 Complexity: {rec.complexity_match.title()} | ⏱️  {project.estimated_time}")

            if rec.learning_outcomes:
                outcomes = rec.learning_outcomes[:2] if len(rec.learning_outcomes) > 2 else rec.learning_outcomes
                print(f"   🎓 You'll learn: {', '.join(outcomes)}")
                if len(rec.learning_outcomes) > 2:
                    print(f"      ... plus {len(rec.learning_outcomes) - 2} more skills")

            print()

        print("=" * 90)
        print("\n🔍 These recommendations are conditionally personalized:")
        print(f"   • Skill Level: Filtered for {context.user_level} experience")
        print(f"   • Time Frame: Matches your {context.time_available} availability")
        print(f"   • Learning Goal: Aligned with {context.project_goal.replace('_', ' ')}")
        if context.career_focus:
            print(f"   • Career Focus: Prioritized {context.career_focus} relevant projects")
        print(f"   • Experience: Considered your {context.previous_projects_count} completed projects")

        print("\n💡 Why this works better than basic matching:")
        print("   ✅ No more overwhelming advanced projects for beginners")
        print("   ✅ No more simple projects wasting expert time")
        print("   ✅ Projects that actually fit your schedule and goals")
        print("   ✅ Career-relevant recommendations when specified")

        print("\n🚀 Ready to start building? Generate a complete project scaffold:")
        print("   noleet scaffold <project_id>  # Auto-generates starter code & structure")
        print("\nTo view detailed project information, use:")
        print("  noleet show <project_id>")

    def _display_ai_results(self, recommendations: list) -> None:
        """Display basic AI-powered recommendations (fallback)."""
        print(f"\n🎯 AI-Powered Project Recommendations ({len(recommendations)} found)")
        print("=" * 80)

        for i, rec in enumerate(recommendations, 1):
            project = rec.project

            # Confidence indicator
            confidence_icon = "🟢" if rec.confidence_score >= 0.8 else "🟡" if rec.confidence_score >= 0.6 else "🔴"
            confidence_pct = int(rec.confidence_score * 100)

            print(f"\n{i}. {project.name}")
            print(f"   {confidence_icon} AI Confidence: {confidence_pct}% match")
            print(f"   📝 {rec.reasoning}")
            print(f"   🎯 Matched Topics: {', '.join(rec.matched_topics)}")
            print(f"   📊 Complexity: {rec.complexity_match.title()}")
            print(f"   🕒 Estimated Time: {project.estimated_time}")
            print(f"   🎓 Learning Outcomes: {', '.join(rec.learning_outcomes[:3])}")
            if len(rec.learning_outcomes) > 3:
                print(f"      ... and {len(rec.learning_outcomes) - 3} more")

        print("\n" + "=" * 80)
        print("\n💡 These recommendations are AI-powered and consider:")
        print("   • Topic combinations and real-world applicability")
        print("   • Your learning goals and current skill level")
        print("   • Project complexity and time requirements")
        print("   • Practical value for portfolio/interview preparation")
        print("\nTo view project details, use:")
        print("  noleet show <project_id>")

    def _display_basic_results(self, projects: list, selected_topics: Set[Topic]) -> None:
        """Display basic keyword-matched results (fallback)."""
        print(f"\n🔍 Basic Matching Results ({len(projects)} found)")
        print("=" * 70)

        for i, project in enumerate(projects, 1):
            coverage = project.get_topic_coverage()
            primary_topics = [
                topic.value.replace("_", " ").title()
                for topic, percentage in coverage.items()
                if percentage >= 15.0
            ]

            print(f"\n{i}. {project.title}")
            print(f"   {project.short_description}")
            print(f"   Difficulty: {project.difficulty.title()}")
            print(f"   Estimated Hours: {project.estimated_hours}")
            print(f"   Primary Topics: {', '.join(primary_topics)}")
            if project.tags:
                print(f"   Tags: {', '.join(project.tags)}")

        print("\n" + "=" * 70)
        print("\n⚠️  Note: These are basic keyword matches.")
        print("   AI recommendations are not available right now.")
        print("\nTo view project details, use:")
        print("  noleet show <project_id>")
    
    def show_project(self, project_id: str) -> None:
        """
        Show detailed project information.
        
        Args:
            project_id: ID of project to display
        """
        projects = self._repository.load_projects()
        project = next((p for p in projects if p.id == project_id), None)
        
        if not project:
            print(f"Project '{project_id}' not found.")
            return
        
        print("\n" + "=" * 70)
        print(f"Project: {project.title}")
        print("=" * 70)
        print(f"\nDescription:\n{project.description}\n")
        print(f"Difficulty: {project.difficulty.title()}")
        print(f"Estimated Hours: {project.estimated_hours}")
        
        coverage = project.get_topic_coverage()
        if coverage:
            print("\nDSA Topic Coverage:")
            for topic, percentage in sorted(
                coverage.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                display_name = topic.value.replace("_", " ").title()
                print(f"  {display_name}: {percentage:.1f}%")
        
        if project.research_references:
            print("\nResearch References:")
            for ref in project.research_references:
                print(f"  - {ref.title}")
                if ref.authors:
                    print(f"    Authors: {', '.join(ref.authors)}")
                if ref.url:
                    print(f"    URL: {ref.url}")
                if ref.github_repo:
                    print(f"    GitHub: {ref.github_repo}")
        
        print("\n" + "=" * 70)
        print("Tasks:")
        print("=" * 70)
        
        for task in sorted(project.tasks, key=lambda t: t.order):
            print(f"\nTask {task.order + 1}: {task.title}")
            print(f"  {task.description}")
            
            if task.dsa_involvements:
                print("  DSA Involvement:")
                for inv in task.dsa_involvements:
                    display_name = inv.topic.value.replace("_", " ").title()
                    print(f"    {display_name}: {inv.percentage:.1f}%")
            
            if task.subtasks:
                print("  Subtasks:")
                for subtask in sorted(task.subtasks, key=lambda st: st.order):
                    print(f"    {subtask.order + 1}. {subtask.title}")
                    print(f"       {subtask.description}")
                    if subtask.dsa_involvements:
                        print("       DSA Involvement:")
                        for inv in subtask.dsa_involvements:
                            display_name = inv.topic.value.replace("_", " ").title()
                            print(f"         {display_name}: {inv.percentage:.1f}%")
        
        print("\n" + "=" * 70)
    
    def _parse_topics(self, topic_names: list[str]) -> Set[Topic]:
        """
        Parse topic names into Topic enum set.
        
        Args:
            topic_names: List of topic name strings
            
        Returns:
            Set of Topic enums
        """
        selected_topics: Set[Topic] = set()
        
        for name in topic_names:
            normalized = name.lower().replace(" ", "_")
            try:
                topic = Topic(normalized)
                selected_topics.add(topic)
            except ValueError:
                self._logger.warning(f"Unknown topic: {name}")
        
        return selected_topics


def launch_tui(data_dir: Path) -> None:
    """
    Launch the Terminal User Interface.

    Args:
        data_dir: Directory containing project data
    """
    if not TUI_AVAILABLE:
        print("❌ TUI not available. Install textual: pip install textual")
        print("💡 Continuing with CLI-only mode")
        return

    try:
        app = NoLeetApp(data_dir=data_dir)
        app.run()
    except KeyboardInterrupt:
        print("\nTUI closed by user.")
    except Exception as e:
        print(f"Error launching TUI: {e}")
        logging.getLogger(__name__).error(f"TUI launch failed: {e}", exc_info=True)


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="NoLeet: Learn DSA by building real-world products"
    )
    
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Directory containing project data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    topics_parser = subparsers.add_parser("topics", help="List all available topics")
    
    find_parser = subparsers.add_parser("find", help="Find projects by topics")
    find_parser.add_argument(
        "topics",
        nargs="+",
        help="DSA topics to search for (e.g., dynamic_programming sliding_window)"
    )
    
    show_parser = subparsers.add_parser("show", help="Show project details")
    show_parser.add_argument("project_id", help="Project ID to display")

    scaffold_parser = subparsers.add_parser("scaffold", help="Generate project scaffolding")
    scaffold_parser.add_argument("project_id", help="Project ID to scaffold")
    scaffold_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./generated_projects"),
        help="Output directory for scaffolded project"
    )

    # Review command
    review_parser = subparsers.add_parser("review", help="Get AI-powered code review for DSA implementation (advanced feature)")
    review_parser.add_argument("code", help="Code to review (as string or file path)")
    review_parser.add_argument("--file", help="Read code from file instead of command line")
    review_parser.add_argument("--project", help="Related project ID for context")
    review_parser.add_argument("--topics", nargs="+", help="DSA topics covered (e.g., dynamic_programming arrays)")
    review_parser.add_argument("--level", choices=["beginner", "intermediate", "advanced"],
                              default="intermediate", help="Your skill level")
    review_parser.add_argument("--algorithm", help="Expected algorithm type for validation")

    # Tutor commands
    tutor_parser = subparsers.add_parser("tutor", help="Interactive tutoring for DSA projects (advanced feature)")
    tutor_subparsers = tutor_parser.add_subparsers(dest="tutor_command", help="Tutor subcommands")

    # Start tutoring session
    start_parser = tutor_subparsers.add_parser("start", help="Start a tutoring session")
    start_parser.add_argument("project_id", help="Project ID to tutor for")
    start_parser.add_argument("--level", choices=["beginner", "intermediate", "advanced"],
                             default="intermediate", help="Your skill level")

    # Ask questions
    ask_parser = tutor_subparsers.add_parser("ask", help="Ask a question about your implementation")
    ask_parser.add_argument("question", help="Your question about DSA or implementation")
    ask_parser.add_argument("--code", help="Include code snippet for context")
    ask_parser.add_argument("--file", help="Current file you're working on")

    # Code review
    review_parser = tutor_subparsers.add_parser("review", help="Get code review and explanations")
    review_parser.add_argument("--code", help="Code to review")
    review_parser.add_argument("--file", help="File containing code to review")

    # Debug help
    debug_parser = tutor_subparsers.add_parser("debug", help="Get debugging assistance")
    debug_parser.add_argument("--error", help="Error message you're seeing")
    debug_parser.add_argument("--code", help="Code that's causing issues")

    # Explain concepts
    explain_parser = tutor_subparsers.add_parser("explain", help="Explain DSA concepts")
    explain_parser.add_argument("concept", help="DSA concept to explain")
    explain_parser.add_argument("--level", choices=["beginner", "intermediate", "advanced"],
                               default="intermediate", help="Explanation depth")

    # Implementation guidance
    guide_parser = tutor_subparsers.add_parser("guide", help="Get implementation guidance")
    guide_parser.add_argument("step", help="What step are you working on?")
    guide_parser.add_argument("--code", help="Current code state")

    # Learning path
    path_parser = tutor_subparsers.add_parser("path", help="Get learning path suggestions")

    # End session
    end_parser = tutor_subparsers.add_parser("end", help="End current tutoring session")

    # Community commands
    community_parser = subparsers.add_parser("community", help="Community-powered learning")
    community_subparsers = community_parser.add_subparsers(dest="community_command", help="Community subcommands")

    # View community contributions
    view_parser = community_subparsers.add_parser("view", help="View community contributions for a project")
    view_parser.add_argument("project_id", help="Project ID to view community content for")
    view_parser.add_argument("--type", choices=["all", "implementations", "insights", "snippets"],
                           default="all", help="Type of contributions to show")

    # Start learning session
    learn_parser = community_subparsers.add_parser("learn", help="Start a community-powered learning session")
    learn_parser.add_argument("project_id", help="Project ID to learn")
    learn_parser.add_argument("--level", choices=["beginner", "intermediate", "advanced"],
                             default="intermediate", help="Your skill level")

    # Share contribution
    share_parser = community_subparsers.add_parser("share", help="Share your implementation or insight")
    share_parser.add_argument("project_id", help="Project this contribution relates to")
    share_parser.add_argument("--type", choices=["implementation", "snippet", "insight", "mistake"],
                             default="implementation", help="Type of contribution")
    share_parser.add_argument("--title", required=True, help="Title for your contribution")
    share_parser.add_argument("--content", help="Content (or use --file)")
    share_parser.add_argument("--file", help="File containing the content to share")
    share_parser.add_argument("--topics", nargs="+", help="DSA topics this covers")

    # Learning session commands
    session_parser = community_subparsers.add_parser("next", help="Get next learning step in active session")
    progress_parser = community_subparsers.add_parser("progress", help="View learning progress and insights")
    complete_parser = community_subparsers.add_parser("complete", help="Mark current contribution as complete")
    complete_parser.add_argument("--rating", type=int, choices=range(1, 6), help="Rate the contribution (1-5)")

    add_data_parser(subparsers)
    add_intervention_parser(subparsers)

    # TUI command
    tui_parser = subparsers.add_parser("tui", help="Launch Terminal User Interface")
    tui_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Path to data directory"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = NoLeetCLI(args.data_dir)

    async def run_async_commands():
        if args.command == "find":
            await cli.find_projects(args.topics)
        # Add other async commands here as needed

    if args.command == "topics":
        cli.list_topics()
    elif args.command == "find":
        asyncio.run(run_async_commands())
    elif args.command == "show":
        cli.show_project(args.project_id)
    elif args.command == "scaffold":
        asyncio.run(cli.scaffold_project(args.project_id, args.output_dir))
    elif args.command == "review":
        asyncio.run(cli.handle_review_command(args))
    elif args.command == "tutor":
        asyncio.run(cli.handle_tutor_command(args))
    elif args.command == "community":
        asyncio.run(cli.handle_community_command(args))
    elif args.command == "data":
        handle_data_commands(args, args.data_dir)
    elif args.command == "intervention":
        handle_intervention_commands(args, args.data_dir)
    elif args.command == "tui":
        launch_tui(args.data_dir or args.data_dir)


if __name__ == "__main__":
    main()

