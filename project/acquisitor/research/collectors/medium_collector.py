"""Medium data collector for research insights."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ExternalAPIError, ResearchCollectionError
from app.models.research_data import ResearchData
from .base_collector import BaseCollector


class MediumCollector(BaseCollector):
    """Collect research data from Medium publications."""

    def __init__(self, company_id: int):
        """Initialize Medium collector."""
        super().__init__("medium", company_id)
        self.base_url = "https://medium.com"
        self.search_url = "https://medium.com/search"
        self.publications = [
            "the-product-nerd", "ux-planet", "product-hunt",
            "startup-grind", "better-marketing", "ux-magazine",
            "productmanagement", "product-school", "ux-tools",
            "design-systems", "product-thinking"
        ]

    async def initialize_client(self):
        """Initialize HTTP client for Medium."""
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            timeout=settings.REQUEST_TIMEOUT,
            follow_redirects=True
        )
        self.logger.info("Medium HTTP client initialized")

    async def close_client(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def collect_data(self) -> List[ResearchData]:
        """Collect research data from Medium."""
        research_data = []
        collected_count = 0

        # Get company info for search terms
        company_keywords = await self._get_company_keywords()

        # Search across publications
        for publication in self.publications:
            if collected_count >= self.max_items_per_collection:
                break

            try:
                self.logger.info(f"Collecting from Medium publication: {publication}")

                # Search within publication
                articles = await self._search_publication(publication, company_keywords)

                for article_url in articles:
                    if collected_count >= self.max_items_per_collection:
                        break

                    try:
                        article_data = await self._process_article(article_url)
                        if article_data:
                            research_data.append(article_data)
                            collected_count += 1

                    except Exception as e:
                        self.logger.warning(f"Error processing article {article_url}: {e}")
                        continue

            except Exception as e:
                self.logger.error(f"Error collecting from publication {publication}: {e}")
                continue

        # Also search general Medium
        try:
            general_articles = await self._search_general_medium(company_keywords)
            for article_url in general_articles:
                if collected_count >= self.max_items_per_collection:
                    break

                try:
                    article_data = await self._process_article(article_url)
                    if article_data:
                        research_data.append(article_data)
                        collected_count += 1

                except Exception as e:
                    self.logger.warning(f"Error processing general article {article_url}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in general Medium search: {e}")

        self.logger.info(f"Collected {len(research_data)} items from Medium")
        return research_data

    async def _get_company_keywords(self) -> List[str]:
        """Get company-related keywords for searching."""
        # TODO: This should come from company model
        return ["productivity", "SaaS", "workflow", "tool", "software", "platform"]

    async def _search_publication(self, publication: str, keywords: List[str]) -> List[str]:
        """Search for articles within a specific publication."""
        article_urls = []

        for keyword in keywords[:3]:  # Limit keywords
            try:
                # Medium search URL format
                search_url = f"{self.base_url}/{publication}?q={keyword}"

                response = await self.make_request(search_url)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract article URLs from search results
                article_links = soup.find_all('a', href=True)

                for link in article_links:
                    href = link['href']
                    if href.startswith('/'):
                        full_url = f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue

                    # Filter for article URLs (contain publication slug)
                    if f"/{publication}/" in full_url and full_url not in article_urls:
                        article_urls.append(full_url)

                if len(article_urls) >= 20:  # Limit per keyword
                    break

            except Exception as e:
                self.logger.warning(f"Error searching publication {publication} for '{keyword}': {e}")
                continue

        return article_urls[:20]  # Limit results

    async def _search_general_medium(self, keywords: List[str]) -> List[str]:
        """Search general Medium articles."""
        article_urls = []

        for keyword in keywords[:2]:  # Limit keywords
            try:
                # Use Medium's search endpoint
                search_url = f"{self.search_url}?q={keyword}"

                response = await self.make_request(search_url)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract article URLs
                article_links = soup.find_all('a', {'data-action': 'open-post'})

                for link in article_links:
                    href = link.get('href', '')
                    if href and href.startswith('http') and href not in article_urls:
                        article_urls.append(href)

                if len(article_urls) >= 30:  # Limit per keyword
                    break

            except Exception as e:
                self.logger.warning(f"Error in general Medium search for '{keyword}': {e}")
                continue

        return article_urls[:30]

    async def _process_article(self, article_url: str) -> Optional[ResearchData]:
        """Process a Medium article into ResearchData."""
        try:
            response = await self.make_request(article_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract article metadata
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            content = self._extract_content(soup)

            # Skip if article is too old (more than 2 years)
            if publish_date and publish_date < datetime.now() - timedelta(days=730):
                return None

            # Clean content
            content = self._clean_text(content)
            if len(content) < 200:  # Skip very short articles
                return None

            # Calculate relevance
            keywords = await self._get_company_keywords()
            relevance_score = self._calculate_relevance_score(content, keywords)

            # Extract reading time if available
            reading_time = self._extract_reading_time(soup)

            # Extract tags/topics
            tags = self._extract_tags(soup)

            return self.create_research_data(
                content_type="article",
                title=title,
                content=content,
                source_url=article_url,
                source_title=self._extract_domain_from_url(article_url),
                source_author=author,
                source_date=publish_date,
                relevance_score=relevance_score,
                tags=tags,
                language="en",
                views=0,  # Medium doesn't expose view counts easily
                shares=0,  # Not easily accessible
            )

        except Exception as e:
            self.logger.warning(f"Error processing article {article_url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        # Try different selectors for title
        title_selectors = [
            'h1[data-testid="storyTitle"]',
            'h1.pw-post-title',
            'h1',
            'title'
        ]

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return self._clean_text(title_elem.get_text())

        return "Untitled Article"

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        author_selectors = [
            'a[data-testid="authorName"]',
            '.pw-author-name a',
            'span[data-testid="authorName"]',
            '.author-name'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return self._clean_text(author_elem.get_text())

        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract article publish date."""
        date_selectors = [
            'time[data-testid="storyPublishDate"]',
            'time.published',
            'time'
        ]

        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                datetime_str = date_elem.get('datetime')
                if datetime_str:
                    try:
                        # Handle different datetime formats
                        if datetime_str.endswith('Z'):
                            datetime_str = datetime_str[:-1] + '+00:00'
                        return datetime.fromisoformat(datetime_str)
                    except ValueError:
                        continue

        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content."""
        content_selectors = [
            'article[data-testid="post-content"]',
            'div.postArticle-content',
            'div.section-content',
            'div.article-content'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove script and style elements
                for script in content_elem(["script", "style"]):
                    script.decompose()

                return content_elem.get_text()

        return ""

    def _extract_reading_time(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract estimated reading time."""
        time_elem = soup.select_one('span[data-testid="storyReadTime"]')
        if time_elem:
            time_text = time_elem.get_text()
            # Extract number from "X min read"
            import re
            match = re.search(r'(\d+)', time_text)
            if match:
                return int(match.group(1))

        return None

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags/topics."""
        tags = []

        # Try different selectors for tags
        tag_selectors = [
            'a[data-testid="topicLink"]',
            '.tags a',
            '.topic-link'
        ]

        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_elem in tag_elements:
                tag_text = self._clean_text(tag_elem.get_text())
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

        return tags
