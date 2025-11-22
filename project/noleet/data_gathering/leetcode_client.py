"""LeetCode API client wrapper with high-level operations."""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from .leetcode_api import LeetCodeClient, LeetCodeCredentials, load_credentials_from_file
from .base_scraper import QuestionMetadata


class LeetCodeAPIClient:
    """High-level LeetCode API client for NoLeet."""

    def __init__(
        self,
        credentials_file: Optional[Path] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize LeetCode API client.

        Args:
            credentials_file: Path to credentials file
            email: LeetCode email (alternative to file)
            password: LeetCode password (alternative to file)
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._credentials: Optional[LeetCodeCredentials] = None
        self._client: Optional[LeetCodeClient] = None

        # Load credentials
        if credentials_file and credentials_file.exists():
            self._credentials = load_credentials_from_file(credentials_file)
        elif email and password:
            self._credentials = LeetCodeCredentials(email=email, password=password)
        else:
            self._logger.warning("No LeetCode credentials provided")

    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._credentials is not None and self._get_client() is not None

    def collect_dsa_questions(
        self,
        max_problems: int = 50,
        discussions_per_problem: int = 10
    ) -> List[QuestionMetadata]:
        """
        Collect DSA questions from LeetCode.

        Args:
            max_problems: Maximum problems to process
            discussions_per_problem: Discussions to collect per problem

        Returns:
            List of question metadata
        """
        if not self.is_authenticated():
            self._logger.error("Not authenticated - cannot collect questions")
            return []

        client = self._get_client()
        if not client:
            return []

        try:
            self._logger.info(
                f"Collecting DSA questions from LeetCode "
                f"(max_problems={max_problems}, discussions_per_problem={discussions_per_problem})"
            )

            questions = client.collect_questions_with_discussions(
                max_problems=max_problems,
                discussions_per_problem=discussions_per_problem
            )

            self._logger.info(f"Successfully collected {len(questions)} questions")
            return questions

        except Exception as e:
            self._logger.error(f"Error collecting questions: {e}")
            return []

    def get_recent_problems(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent problems from LeetCode.

        Args:
            limit: Maximum problems to return

        Returns:
            List of problem data
        """
        client = self._get_client()
        if not client:
            return []

        try:
            return client.get_recent_problems(limit=limit)
        except Exception as e:
            self._logger.error(f"Error getting recent problems: {e}")
            return []

    def _get_client(self) -> Optional[LeetCodeClient]:
        """Get or create LeetCode client."""
        if self._client is None and self._credentials:
            try:
                self._client = LeetCodeClient(self._credentials, self._logger)
            except Exception as e:
                self._logger.error(f"Failed to create LeetCode client: {e}")
                return None

        return self._client

    @classmethod
    def from_credentials_file(cls, file_path: Path) -> "LeetCodeAPIClient":
        """
        Create client from credentials file.

        Args:
            file_path: Path to credentials file

        Returns:
            LeetCodeAPIClient instance
        """
        return cls(credentials_file=file_path)

    @classmethod
    def from_credentials(
        cls,
        email: str,
        password: str
    ) -> "LeetCodeAPIClient":
        """
        Create client from email/password.

        Args:
            email: LeetCode email
            password: LeetCode password

        Returns:
            LeetCodeAPIClient instance
        """
        return cls(email=email, password=password)


# Example usage and testing
def test_leetcode_api() -> None:
    """Test function for LeetCode API (requires credentials)."""
    import os

    # Try to load from environment or credentials file
    email = os.getenv("LEETCODE_EMAIL")
    password = os.getenv("LEETCODE_PASSWORD")

    if not email or not password:
        print("No LeetCode credentials found. Set LEETCODE_EMAIL and LEETCODE_PASSWORD environment variables.")
        return

    print("Testing LeetCode API client...")

    client = LeetCodeAPIClient.from_credentials(email, password)

    if not client.is_authenticated():
        print("❌ Authentication failed")
        return

    print("✅ Authentication successful")

    # Test getting recent problems
    problems = client.get_recent_problems(limit=5)
    print(f"✅ Retrieved {len(problems)} recent problems")

    if problems:
        print(f"Sample problem: {problems[0].get('title', 'Unknown')}")

    # Test collecting questions (limit to avoid rate limits)
    questions = client.collect_dsa_questions(max_problems=2, discussions_per_problem=3)
    print(f"✅ Collected {len(questions)} questions with discussions")

    print("✅ LeetCode API test completed successfully")


if __name__ == "__main__":
    test_leetcode_api()

