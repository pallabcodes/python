"""LeetCode API client with authentication and rate limiting."""

import time
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
import json

from ..data_gathering.base_scraper import QuestionMetadata


@dataclass
class LeetCodeCredentials:
    """LeetCode login credentials."""
    email: str
    password: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary (for secure storage)."""
        return {
            "email": self.email,
            "password": self.password  # Note: This should be encrypted in production
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "LeetCodeCredentials":
        """Create from dictionary."""
        return cls(
            email=data["email"],
            password=data["password"]
        )


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 10) -> None:
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
        """
        self._requests_per_minute = requests_per_minute
        self._requests: List[float] = []
        self._logger = logging.getLogger(__name__)

    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        current_time = time.time()

        # Remove old requests (older than 1 minute)
        self._requests = [
            req_time for req_time in self._requests
            if current_time - req_time < 60
        ]

        if len(self._requests) >= self._requests_per_minute:
            # Wait until we can make another request
            oldest_request = min(self._requests)
            wait_time = 60 - (current_time - oldest_request)

            if wait_time > 0:
                self._logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)

        self._requests.append(current_time)


class LeetCodeAuthenticator:
    """Handles LeetCode authentication and session management."""

    def __init__(
        self,
        credentials: LeetCodeCredentials,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize authenticator.

        Args:
            credentials: LeetCode login credentials
            logger: Optional logger instance
        """
        self._credentials = credentials
        self._logger = logger or logging.getLogger(__name__)
        self._session_token: Optional[str] = None
        self._csrf_token: Optional[str] = None
        self._session_expires: Optional[float] = None

    def get_session_token(self) -> Optional[str]:
        """
        Get valid session token, refreshing if needed.

        Returns:
            Session token or None if authentication failed
        """
        if self._is_session_valid():
            return self._session_token

        if self._login():
            return self._session_token

        return None

    def get_csrf_token(self) -> Optional[str]:
        """
        Get CSRF token.

        Returns:
            CSRF token or None
        """
        if not self._csrf_token:
            self._fetch_csrf_token()
        return self._csrf_token

    def _is_session_valid(self) -> bool:
        """Check if current session is still valid."""
        if not self._session_token or not self._session_expires:
            return False

        return time.time() < self._session_expires

    def _login(self) -> bool:
        """
        Perform login to LeetCode.

        Returns:
            True if login successful
        """
        try:
            import requests

            # First, get CSRF token
            if not self._fetch_csrf_token():
                return False

            # Login request
            login_url = "https://leetcode.com/accounts/login/"
            headers = {
                "Content-Type": "application/json",
                "X-CSRFToken": self._csrf_token,
                "Referer": "https://leetcode.com/accounts/login/"
            }

            login_data = {
                "login": self._credentials.email,
                "password": self._credentials.password,
                "next": "/"
            }

            session = requests.Session()
            session.headers.update({"User-Agent": "NoLeet/1.0"})

            # Set CSRF token in cookies
            session.cookies.set("csrftoken", self._csrf_token, domain="leetcode.com")

            response = session.post(login_url, json=login_data, headers=headers, timeout=30)

            if response.status_code == 200 and "sessionid" in session.cookies:
                self._session_token = session.cookies.get("sessionid")
                self._session_expires = time.time() + (24 * 60 * 60)  # 24 hours
                self._logger.info("Successfully logged in to LeetCode")
                return True
            else:
                self._logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self._logger.error(f"Login error: {e}")
            return False

    def _fetch_csrf_token(self) -> bool:
        """
        Fetch CSRF token from LeetCode.

        Returns:
            True if token fetched successfully
        """
        try:
            import requests

            response = requests.get(
                "https://leetcode.com/accounts/login/",
                headers={"User-Agent": "NoLeet/1.0"},
                timeout=10
            )

            if response.status_code == 200:
                # Extract CSRF token from response
                import re
                csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
                if csrf_match:
                    self._csrf_token = csrf_match.group(1)
                    return True

            self._logger.error("Failed to fetch CSRF token")
            return False

        except Exception as e:
            self._logger.error(f"CSRF token fetch error: {e}")
            return False


class LeetCodeClient:
    """LeetCode API client with authentication and rate limiting."""

    BASE_URL = "https://leetcode.com"
    GRAPHQL_URL = "https://leetcode.com/graphql"

    def __init__(
        self,
        credentials: LeetCodeCredentials,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize LeetCode client.

        Args:
            credentials: LeetCode login credentials
            logger: Optional logger instance
        """
        self._credentials = credentials
        self._logger = logger or logging.getLogger(__name__)
        self._auth = LeetCodeAuthenticator(credentials, logger)
        self._rate_limiter = RateLimiter(requests_per_minute=10)  # Conservative limit
        self._session: Optional[Any] = None

    def get_authenticated_session(self) -> Optional[Any]:
        """
        Get authenticated session.

        Returns:
            Authenticated requests session or None
        """
        session_token = self._auth.get_session_token()
        csrf_token = self._auth.get_csrf_token()

        if not session_token or not csrf_token:
            self._logger.error("Authentication failed")
            return None

        try:
            import requests

            session = requests.Session()
            session.headers.update({
                "User-Agent": "NoLeet/1.0",
                "X-CSRFToken": csrf_token,
                "Referer": self.BASE_URL
            })

            # Set authentication cookies
            session.cookies.set("sessionid", session_token, domain="leetcode.com")
            session.cookies.set("csrftoken", csrf_token, domain="leetcode.com")

            self._session = session
            return session

        except Exception as e:
            self._logger.error(f"Session creation error: {e}")
            return None

    def graphql_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query result or None
        """
        self._rate_limiter.wait_if_needed()

        session = self.get_authenticated_session()
        if not session:
            return None

        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }

            response = session.post(
                self.GRAPHQL_URL,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                self._logger.error(f"GraphQL query failed: {response.status_code}")
                if response.status_code == 429:
                    self._logger.warning("Rate limit hit, backing off")
                    time.sleep(60)  # Long backoff for rate limits
                return None

        except Exception as e:
            self._logger.error(f"GraphQL query error: {e}")
            return None

    def get_recent_problems(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent problems from LeetCode.

        Args:
            limit: Maximum number of problems to retrieve

        Returns:
            List of problem data
        """
        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
          problemsetQuestionList: questionList(
            categorySlug: $categorySlug
            limit: $limit
            skip: $skip
            filters: $filters
          ) {
            total: totalNum
            questions: data {
              acRate
              difficulty
              freqBar
              frontendQuestionId: questionFrontendId
              isFavor
              paidOnly: isPaidOnly
              status
              title
              titleSlug
              topicTags {
                name
                id
                slug
              }
              hasSolution
              hasVideoSolution
            }
          }
        }
        """

        variables = {
            "categorySlug": "",
            "skip": 0,
            "limit": limit,
            "filters": {}
        }

        result = self.graphql_query(query, variables)
        if result and "data" in result:
            return result["data"].get("problemsetQuestionList", {}).get("questions", [])

        return []

    def get_problem_discussions(
        self,
        problem_slug: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get discussions for a specific problem.

        Args:
            problem_slug: Problem slug (e.g., "two-sum")
            limit: Maximum discussions to retrieve

        Returns:
            List of discussion data
        """
        query = """
        query GetProblemDiscussions($slug: String!, $first: Int!, $orderBy: DiscussionOrderBy, $skip: Int) {
          problem: question(slug: $slug) {
            discussion: discussion(orderBy: $orderBy, first: $first, skip: $skip) {
              edges {
                node {
                  id
                  title
                  content
                  post {
                    creationDate
                    author {
                      username
                    }
                  }
                  tags {
                    name
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            "slug": problem_slug,
            "first": limit,
            "skip": 0,
            "orderBy": "hot"
        }

        result = self.graphql_query(query, variables)
        if result and "data" in result:
            discussions = result["data"].get("problem", {}).get("discussion", {}).get("edges", [])
            return [edge["node"] for edge in discussions]

        return []

    def collect_questions_with_discussions(
        self,
        max_problems: int = 20,
        discussions_per_problem: int = 5
    ) -> List[QuestionMetadata]:
        """
        Collect questions and their discussions.

        Args:
            max_problems: Maximum problems to process
            discussions_per_problem: Discussions to collect per problem

        Returns:
            List of question metadata
        """
        self._logger.info("Starting LeetCode data collection")

        problems = self.get_recent_problems(limit=max_problems)
        questions: List[QuestionMetadata] = []

        for problem in problems:
            try:
                problem_slug = problem.get("titleSlug")
                if not problem_slug:
                    continue

                # Get discussions for this problem
                discussions = self.get_problem_discussions(
                    problem_slug,
                    limit=discussions_per_problem
                )

                for discussion in discussions:
                    question_meta = self._discussion_to_question_metadata(
                        problem,
                        discussion
                    )
                    if question_meta:
                        questions.append(question_meta)

                # Brief pause between problems to be respectful
                time.sleep(1)

            except Exception as e:
                self._logger.error(f"Error processing problem {problem.get('titleSlug')}: {e}")

        self._logger.info(f"Collected {len(questions)} questions from LeetCode")
        return questions

    def _discussion_to_question_metadata(
        self,
        problem: Dict[str, Any],
        discussion: Dict[str, Any]
    ) -> Optional[QuestionMetadata]:
        """
        Convert problem + discussion to QuestionMetadata.

        Args:
            problem: Problem data
            discussion: Discussion data

        Returns:
            Question metadata or None
        """
        try:
            discussion_id = discussion.get("id")
            title = discussion.get("title", "")
            content = discussion.get("content", "")
            post_info = discussion.get("post", {})

            # Combine problem and discussion content
            full_content = f"Problem: {problem.get('title', '')}\n\n"
            full_content += f"Difficulty: {problem.get('difficulty', '')}\n\n"
            full_content += f"Discussion: {title}\n\n{content}"

            # Extract tags
            tags = []
            topic_tags = problem.get("topicTags", [])
            for tag in topic_tags:
                tags.append(tag.get("name", ""))

            discussion_tags = discussion.get("tags", [])
            for tag in discussion_tags:
                tags.append(tag.get("name", ""))

            # Create URL
            problem_id = problem.get("frontendQuestionId")
            url = f"https://leetcode.com/problems/{problem.get('titleSlug')}/discuss/{discussion_id}"

            return QuestionMetadata(
                source="leetcode_api",
                source_id=f"{problem_id}_{discussion_id}",
                title=title or f"Discussion for {problem.get('title', '')}",
                content=full_content,
                url=url,
                tags=list(set(tags)),
                difficulty=problem.get("difficulty"),
                company_tags=[],  # Would need additional processing
                raw_data={
                    "problem": problem,
                    "discussion": discussion
                }
            )

        except Exception as e:
            self._logger.error(f"Error converting discussion to metadata: {e}")
            return None


# Utility functions for secure credential management
def load_credentials_from_file(file_path: Path) -> Optional[LeetCodeCredentials]:
    """
    Load credentials from encrypted file.

    Args:
        file_path: Path to credentials file

    Returns:
        Credentials or None if loading failed
    """
    try:
        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)

        return LeetCodeCredentials.from_dict(data)

    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load credentials: {e}")
        return None


def save_credentials_to_file(credentials: LeetCodeCredentials, file_path: Path) -> bool:
    """
    Save credentials to file (WARNING: Not encrypted - use proper encryption in production).

    Args:
        credentials: Credentials to save
        file_path: File path to save to

    Returns:
        True if saved successfully
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(credentials.to_dict(), f, indent=2)

        return True

    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save credentials: {e}")
        return False

