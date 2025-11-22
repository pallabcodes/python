"""Scraper for Reddit posts about DSA questions."""

import re
import logging
from typing import List, Optional
from urllib.parse import urljoin

from noleet.data_gathering.base_scraper import BaseScraper, QuestionMetadata


class RedditScraper(BaseScraper):
    """Scraper for Reddit posts containing DSA question collections."""
    
    REDDIT_BASE_URL = "https://www.reddit.com"
    TARGET_SUBREDDITS = [
        "leetcode",
        "cscareerquestions",
        "ExperiencedDevs",
        "programming"
    ]
    
    SEARCH_TERMS = [
        "amazon oa",
        "google interview",
        "top 150",
        "blind 75",
        "neetcode",
        "sde interview"
    ]
    
    def __init__(self) -> None:
        """Initialize Reddit scraper."""
        super().__init__("reddit")
        self._logger = logging.getLogger(__name__)
    
    def scrape(
        self,
        subreddits: Optional[List[str]] = None,
        search_terms: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[QuestionMetadata]:
        """
        Scrape Reddit posts.
        
        Args:
            subreddits: Subreddits to search (defaults to TARGET_SUBREDDITS)
            search_terms: Terms to search for (defaults to SEARCH_TERMS)
            max_results: Maximum number of results
            
        Returns:
            List of collected questions
        """
        target_subreddits = subreddits or self.TARGET_SUBREDDITS
        target_terms = search_terms or self.SEARCH_TERMS
        
        questions: List[QuestionMetadata] = []
        
        self._logger.info(
            f"Starting Reddit scraping",
            extra={
                "subreddits": target_subreddits,
                "search_terms": target_terms,
                "max_results": max_results
            }
        )
        
        for subreddit in target_subreddits:
            for term in target_terms:
                try:
                    term_questions = self._scrape_subreddit_search(
                        subreddit,
                        term,
                        max_results // (len(target_subreddits) * len(target_terms))
                    )
                    questions.extend(term_questions)
                except Exception as e:
                    self._logger.error(
                        f"Failed to scrape {subreddit} for {term}: {e}",
                        exc_info=True,
                        extra={"subreddit": subreddit, "term": term}
                    )
        
        self._log_collection(len(questions))
        return questions
    
    def _scrape_subreddit_search(
        self,
        subreddit: str,
        search_term: str,
        max_results: int
    ) -> List[QuestionMetadata]:
        """
        Scrape posts from subreddit search.
        
        Args:
            subreddit: Subreddit name
            search_term: Search term
            max_results: Maximum results
            
        Returns:
            List of questions
        """
        questions: List[QuestionMetadata] = []
        
        search_url = f"{self.REDDIT_BASE_URL}/r/{subreddit}/search.json"
        params = {"q": search_term, "limit": max_results, "sort": "relevance"}
        
        try:
            json_data = self._fetch_json(search_url, params)
            if not json_data:
                return questions
            
            posts = json_data.get("data", {}).get("children", [])
            
            for post_data in posts:
                post = post_data.get("data", {})
                question = self._extract_question_from_post(post)
                if question:
                    questions.append(question)
        
        except Exception as e:
            self._logger.error(
                f"Error scraping {subreddit}: {e}",
                exc_info=True,
                extra={"subreddit": subreddit, "term": search_term}
            )
        
        return questions
    
    def _fetch_json(self, url: str, params: dict) -> Optional[dict]:
        """
        Fetch JSON data from URL.
        
        Args:
            url: URL to fetch
            params: Query parameters
            
        Returns:
            JSON data or None if failed
        """
        try:
            import urllib.request
            import urllib.parse
            
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "NoLeet/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                import json
                return json.loads(response.read().decode("utf-8"))
        
        except Exception as e:
            self._logger.error(
                f"Failed to fetch JSON from {url}: {e}",
                extra={"url": url}
            )
            return None
    
    def _extract_question_from_post(self, post_data: dict) -> Optional[QuestionMetadata]:
        """
        Extract question from Reddit post data.
        
        Args:
            post_data: Reddit post data dictionary
            
        Returns:
            Question metadata or None
        """
        title = post_data.get("title", "")
        selftext = post_data.get("selftext", "")
        url = post_data.get("url", "")
        post_id = post_data.get("id", "")
        
        if not title and not selftext:
            return None
        
        content = f"{title}\n\n{selftext}".strip()
        
        tags = self._extract_tags_from_content(content)
        company_tags = self._extract_company_tags_from_content(content)
        
        full_url = urljoin(self.REDDIT_BASE_URL, url) if url else None
        
        return self._create_question(
            source_id=post_id,
            title=title or "Untitled",
            content=content,
            url=full_url,
            tags=tags,
            company_tags=company_tags,
            raw_data=post_data
        )
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract tags from post content."""
        tags: List[str] = []
        
        tag_patterns = [
            r"#(\w+)",
            r"\[(\w+)\]",
            r"tag[:\s]+(\w+)"
        ]
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tags.extend(matches)
        
        return list(set(tags))
    
    def _extract_company_tags_from_content(self, content: str) -> List[str]:
        """Extract company mentions from content."""
        companies = ["amazon", "google", "facebook", "microsoft", "apple", "netflix", "meta"]
        content_lower = content.lower()
        
        found_companies = [
            company for company in companies
            if company in content_lower
        ]
        
        return found_companies

