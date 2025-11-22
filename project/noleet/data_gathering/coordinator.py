"""Coordinate data gathering from multiple sources."""

import logging
from typing import List, Dict
from pathlib import Path
import json

from noleet.data_gathering.base_scraper import QuestionMetadata
from noleet.data_gathering.leetcode_scraper import LeetCodeScraper
from noleet.data_gathering.reddit_scraper import RedditScraper
from noleet.data_gathering.processor import QuestionProcessor
from noleet.core.models import Topic


class DataGatheringCoordinator:
    """Coordinates data gathering from multiple sources."""
    
    def __init__(self, storage_dir: Path) -> None:
        """
        Initialize coordinator.
        
        Args:
            storage_dir: Directory to store collected data
        """
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._leetcode_scraper = LeetCodeScraper()
        self._reddit_scraper = RedditScraper()
        self._processor = QuestionProcessor()
        
        self._logger = logging.getLogger(__name__)
    
    def gather_all_sources(
        self,
        max_results_per_source: int = 50
    ) -> Dict[Topic, List[QuestionMetadata]]:
        """
        Gather questions from all sources.
        
        Args:
            max_results_per_source: Maximum results per source
            
        Returns:
            Dictionary of categorized questions by topic
        """
        all_questions: List[QuestionMetadata] = []
        
        self._logger.info("Starting data gathering from all sources")
        
        try:
            leetcode_questions = self._leetcode_scraper.scrape(
                max_results=max_results_per_source
            )
            all_questions.extend(leetcode_questions)
        except Exception as e:
            self._logger.error(f"Failed to scrape LeetCode: {e}", exc_info=True)
        
        try:
            reddit_questions = self._reddit_scraper.scrape(
                max_results=max_results_per_source
            )
            all_questions.extend(reddit_questions)
        except Exception as e:
            self._logger.error(f"Failed to scrape Reddit: {e}", exc_info=True)
        
        categorized = self._processor.categorize_questions(all_questions)
        
        self._save_collected_data(all_questions, categorized)
        
        return categorized
    
    def _save_collected_data(
        self,
        questions: List[QuestionMetadata],
        categorized: Dict[Topic, List[QuestionMetadata]]
    ) -> None:
        """
        Save collected data to storage.
        
        Args:
            questions: All collected questions
            categorized: Categorized questions
        """
        questions_file = self._storage_dir / "questions.json"
        categorized_file = self._storage_dir / "categorized_questions.json"
        
        questions_data = [self._serialize_question(q) for q in questions]
        
        with open(questions_file, "w", encoding="utf-8") as f:
            json.dump(questions_data, f, indent=2, ensure_ascii=False, default=str)
        
        categorized_data = {
            topic.value: [self._serialize_question(q) for q in qs]
            for topic, qs in categorized.items()
        }
        
        with open(categorized_file, "w", encoding="utf-8") as f:
            json.dump(categorized_data, f, indent=2, ensure_ascii=False, default=str)
        
        self._logger.info(
            f"Saved {len(questions)} questions to storage",
            extra={
                "total_questions": len(questions),
                "topics": len(categorized)
            }
        )
    
    def _serialize_question(self, question: QuestionMetadata) -> dict:
        """Serialize question to dictionary."""
        return {
            "source": question.source,
            "source_id": question.source_id,
            "title": question.title,
            "content": question.content[:1000],
            "url": question.url,
            "tags": question.tags,
            "difficulty": question.difficulty,
            "company_tags": question.company_tags,
            "collected_at": question.collected_at.isoformat() if question.collected_at else None
        }

