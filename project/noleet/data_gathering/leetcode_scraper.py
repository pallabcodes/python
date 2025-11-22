"""Scraper for LeetCode discussions and questions."""

import re
import logging
from typing import List, Optional
from urllib.parse import urljoin

from noleet.data_gathering.base_scraper import BaseScraper, QuestionMetadata


class LeetCodeScraper(BaseScraper):
    """Scraper for LeetCode discussions tagged with interview questions."""
    
    LEEETCODE_BASE_URL = "https://leetcode.com"
    DISCUSSION_BASE = "https://leetcode.com/discuss"
    
    TARGET_TAGS = [
        "amazon-oa",
        "google-interview",
        "facebook-interview",
        "microsoft-interview",
        "apple-interview",
        "netflix-interview",
        "meta-interview"
    ]
    
    def __init__(self) -> None:
        """Initialize LeetCode scraper."""
        super().__init__("leetcode")
        self._logger = logging.getLogger(__name__)
    
    def scrape(
        self,
        tags: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[QuestionMetadata]:
        """
        Scrape LeetCode discussions.
        
        Args:
            tags: Specific tags to search for (defaults to TARGET_TAGS)
            max_results: Maximum number of results to collect
            
        Returns:
            List of collected questions
        """
        target_tags = tags or self.TARGET_TAGS
        questions: List[QuestionMetadata] = []
        
        self._logger.info(
            f"Starting LeetCode scraping with tags: {target_tags}",
            extra={"tags": target_tags, "max_results": max_results}
        )
        
        for tag in target_tags:
            try:
                tag_questions = self._scrape_tag(tag, max_results // len(target_tags))
                questions.extend(tag_questions)
            except Exception as e:
                self._logger.error(
                    f"Failed to scrape tag {tag}: {e}",
                    exc_info=True,
                    extra={"tag": tag}
                )
        
        self._log_collection(len(questions))
        return questions
    
    def _scrape_tag(self, tag: str, max_results: int) -> List[QuestionMetadata]:
        """
        Scrape questions for a specific tag.
        
        Args:
            tag: Tag to search for
            max_results: Maximum results for this tag
            
        Returns:
            List of questions
        """
        questions: List[QuestionMetadata] = []
        
        search_url = f"{self.DISCUSSION_BASE}/tag/{tag}"
        
        self._logger.debug(
            f"Scraping tag: {tag}",
            extra={"tag": tag, "url": search_url}
        )
        
        try:
            html_content = self._fetch_page(search_url)
            if not html_content:
                return questions
            
            question_links = self._extract_question_links(html_content, tag)
            
            for link in question_links[:max_results]:
                try:
                    question = self._scrape_question(link)
                    if question:
                        questions.append(question)
                except Exception as e:
                    self._logger.warning(
                        f"Failed to scrape question from {link}: {e}",
                        extra={"url": link}
                    )
        
        except Exception as e:
            self._logger.error(
                f"Error scraping tag {tag}: {e}",
                exc_info=True,
                extra={"tag": tag}
            )
        
        return questions
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "NoLeet/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")
        
        except Exception as e:
            self._logger.error(
                f"Failed to fetch {url}: {e}",
                extra={"url": url}
            )
            return None
    
    def _extract_question_links(self, html: str, tag: str) -> List[str]:
        """
        Extract question discussion links from HTML.
        
        Args:
            html: HTML content
            tag: Tag being searched
            
        Returns:
            List of question URLs
        """
        links: List[str] = []
        
        pattern = r'href="(/discuss/[^"]+)"'
        matches = re.findall(pattern, html)
        
        for match in matches:
            full_url = urljoin(self.LEEETCODE_BASE_URL, match)
            if full_url not in links:
                links.append(full_url)
        
        return links
    
    def _scrape_question(self, url: str) -> Optional[QuestionMetadata]:
        """
        Scrape individual question details.
        
        Args:
            url: Question discussion URL
            
        Returns:
            Question metadata or None if failed
        """
        html = self._fetch_page(url)
        if not html:
            return None
        
        title = self._extract_title(html)
        content = self._extract_content(html)
        tags = self._extract_tags(html)
        difficulty = self._extract_difficulty(html)
        
        if not title or not content:
            return None
        
        source_id = url.split("/")[-1] if "/" in url else url
        
        return self._create_question(
            source_id=source_id,
            title=title,
            content=content,
            url=url,
            tags=tags,
            difficulty=difficulty,
            company_tags=self._extract_company_tags(tags)
        )
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract question title from HTML."""
        pattern = r'<title>([^<]+)</title>'
        match = re.search(pattern, html, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_content(self, html: str) -> str:
        """Extract question content from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            content_div = soup.find("div", class_=re.compile("content|question|problem"))
            if content_div:
                return content_div.get_text(strip=True)
        except ImportError:
            pass
        
        pattern = r'<div[^>]*class="[^"]*content[^"]*"[^>]*>([^<]+)</div>'
        match = re.search(pattern, html, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _extract_tags(self, html: str) -> List[str]:
        """Extract tags from HTML."""
        tags: List[str] = []
        
        pattern = r'<a[^>]*class="[^"]*tag[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.IGNORECASE)
        tags.extend(matches)
        
        return [tag.strip() for tag in tags if tag.strip()]
    
    def _extract_difficulty(self, html: str) -> Optional[str]:
        """Extract difficulty level from HTML."""
        pattern = r'difficulty["\s]*:["\s]*([^"<\s]+)'
        match = re.search(pattern, html, re.IGNORECASE)
        return match.group(1).lower() if match else None
    
    def _extract_company_tags(self, tags: List[str]) -> List[str]:
        """Extract company-related tags."""
        companies = ["amazon", "google", "facebook", "microsoft", "apple", "netflix", "meta"]
        return [tag for tag in tags if any(comp in tag.lower() for comp in companies)]

