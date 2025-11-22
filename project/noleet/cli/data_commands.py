"""CLI commands for data gathering."""

import argparse
import logging
from pathlib import Path

from noleet.data_gathering.coordinator import DataGatheringCoordinator
from noleet.data_gathering.leetcode_client import LeetCodeAPIClient


class DataCommands:
    """CLI commands for data gathering operations."""
    
    def __init__(self, data_dir: Path) -> None:
        """
        Initialize data commands.
        
        Args:
            data_dir: Directory for data storage
        """
        self._data_dir = data_dir
        self._coordinator = DataGatheringCoordinator(data_dir / "collected")
        self._logger = logging.getLogger(__name__)
    
    def gather(self, max_results: int = 50) -> None:
        """
        Gather questions from all sources.

        Args:
            max_results: Maximum results per source
        """
        print("Starting data gathering from all sources...")
        print("This may take a few minutes...\n")

        try:
            categorized = self._coordinator.gather_all_sources(max_results)

            print(f"\nData gathering complete!")
            print(f"Collected questions categorized into {len(categorized)} topics:\n")

            for topic, questions in sorted(
                categorized.items(),
                key=lambda x: len(x[1]),
                reverse=True
            ):
                topic_name = topic.value.replace("_", " ").title()
                print(f"  {topic_name}: {len(questions)} questions")

            print(f"\nData saved to: {self._data_dir / 'collected'}")

        except Exception as e:
            self._logger.error(f"Data gathering failed: {e}", exc_info=True)
            print(f"Error: {e}")

    def gather_leetcode(
        self,
        max_problems: int = 20,
        discussions_per_problem: int = 5
    ) -> None:
        """
        Gather questions specifically from LeetCode API.

        Args:
            max_problems: Maximum problems to process
            discussions_per_problem: Discussions per problem
        """
        print("Starting LeetCode API data gathering...")
        print("This requires authentication and may take several minutes...\n")

        try:
            # Try to create client with provided credentials
            client = LeetCodeAPIClient.from_credentials(
                email="kayydraws@gmail.com",
                password="$i2!^iURcW^Q)3-"
            )

            if not client.is_authenticated():
                print("❌ Authentication failed. Please check credentials.")
                return

            print("✅ Authentication successful")

            questions = client.collect_dsa_questions(
                max_problems=max_problems,
                discussions_per_problem=discussions_per_problem
            )

            print(f"\n✅ Collected {len(questions)} questions from LeetCode API")

            if questions:
                print("Sample questions:")
                for i, q in enumerate(questions[:3], 1):
                    print(f"  {i}. {q.title[:60]}...")
                    print(f"     Difficulty: {q.difficulty}, Tags: {len(q.tags)}")

            print(f"\nData would be saved to: {self._data_dir / 'collected'}")

        except Exception as e:
            self._logger.error(f"LeetCode API gathering failed: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            print("\nNote: LeetCode API access may be restricted or require special permissions.")


def add_data_parser(subparsers) -> None:
    """Add data gathering commands to CLI."""
    data_parser = subparsers.add_parser("data", help="Data gathering commands")
    data_subparsers = data_parser.add_subparsers(dest="data_command", required=True)
    
    gather_parser = data_subparsers.add_parser("gather", help="Gather questions from sources")
    gather_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum results per source"
    )

    leetcode_parser = data_subparsers.add_parser("gather-leetcode", help="Gather from LeetCode API only")
    leetcode_parser.add_argument(
        "--max-problems",
        type=int,
        default=20,
        help="Maximum problems to process"
    )
    leetcode_parser.add_argument(
        "--discussions-per-problem",
        type=int,
        default=5,
        help="Discussions to collect per problem"
    )


def handle_data_commands(args, data_dir: Path) -> None:
    """Handle data command execution."""
    data_commands = DataCommands(data_dir)

    if args.data_command == "gather":
        data_commands.gather(args.max_results)
    elif args.data_command == "gather-leetcode":
        data_commands.gather_leetcode(
            args.max_problems,
            args.discussions_per_problem
        )
    else:
        print("Unknown data command")
