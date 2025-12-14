"""Quality scorer for assessing collected questions."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re


@dataclass
class QualityScore:
    """Quality assessment result."""
    overall_score: float  # 0.0-1.0
    clarity_score: float   # 0.0-1.0
    uniqueness_score: float  # 0.0-1.0
    educational_value: float  # 0.0-1.0
    completeness_score: float  # 0.0-1.0
    issues: List[str]     # List of quality issues found
    strengths: List[str]  # List of positive aspects


class QualityScorer:
    """Assesses quality of collected questions from various sources."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize quality scorer.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)

        # Quality thresholds
        self._min_content_length = 50
        self._max_content_length = 10000
        self._min_title_length = 10
        self._max_title_length = 200

        # Common low-quality indicators
        self._low_quality_patterns = [
            r'\b(test|testing|debug|broken|fix me|todo)\b',
            r'\b(spam|advertisement|promotion)\b',
            r'\b(homework|assignment|exam)\b.*\b(help|solution)\b',
            r'^\s*(hi|hello|hey)\s*$',
            r'\b(buy|sell|cheap|free|download)\b',
        ]

        # High-quality indicators
        self._high_quality_patterns = [
            r'\b(algorithm|complexity|time|space|optimization)\b',
            r'\b(leetcode|interview|coding|programming)\b',
            r'\b(solution|approach|method|technique)\b',
            r'\b(difficulty|level|hard|medium|easy)\b',
        ]

    def score_question(
        self,
        question_id: str,
        title: str,
        content: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Score a question's quality.

        Args:
            question_id: Unique question identifier
            title: Question title
            content: Question content
            source: Source of the question (reddit, leetcode, etc.)
            metadata: Additional metadata

        Returns:
            Quality assessment
        """
        try:
            # Initialize scores
            scores = {
                'clarity': 0.0,
                'uniqueness': 0.0,
                'educational_value': 0.0,
                'completeness': 0.0,
            }

            issues = []
            strengths = []

            # Assess clarity
            scores['clarity'], clarity_issues, clarity_strengths = self._assess_clarity(title, content)
            issues.extend(clarity_issues)
            strengths.extend(clarity_strengths)

            # Assess uniqueness
            scores['uniqueness'], uniqueness_issues, uniqueness_strengths = self._assess_uniqueness(title, content, metadata)
            issues.extend(uniqueness_issues)
            strengths.extend(uniqueness_strengths)

            # Assess educational value
            scores['educational_value'], edu_issues, edu_strengths = self._assess_educational_value(title, content)
            issues.extend(edu_issues)
            strengths.extend(edu_strengths)

            # Assess completeness
            scores['completeness'], complete_issues, complete_strengths = self._assess_completeness(title, content, source)
            issues.extend(complete_issues)
            strengths.extend(complete_strengths)

            # Calculate overall score (weighted average)
            weights = {
                'clarity': 0.3,
                'uniqueness': 0.2,
                'educational_value': 0.3,
                'completeness': 0.2,
            }

            overall_score = sum(scores[aspect] * weights[aspect] for aspect in scores)

            return QualityScore(
                overall_score=min(overall_score, 1.0),
                clarity_score=scores['clarity'],
                uniqueness_score=scores['uniqueness'],
                educational_value=scores['educational_value'],
                completeness_score=scores['completeness'],
                issues=issues,
                strengths=strengths
            )

        except Exception as e:
            self._logger.error(f"Failed to score question {question_id}: {e}")
            return QualityScore(
                overall_score=0.0,
                clarity_score=0.0,
                uniqueness_score=0.0,
                educational_value=0.0,
                completeness_score=0.0,
                issues=["Failed to analyze quality"],
                strengths=[]
            )

    def _assess_clarity(self, title: str, content: str) -> Tuple[float, List[str], List[str]]:
        """Assess question clarity."""
        issues = []
        strengths = []
        score = 0.5  # Base score

        # Check title quality
        if len(title.strip()) < self._min_title_length:
            issues.append("Title too short")
            score -= 0.2
        elif len(title.strip()) > self._max_title_length:
            issues.append("Title too long")
            score -= 0.1
        else:
            strengths.append("Good title length")
            score += 0.1

        # Check content quality
        if len(content.strip()) < self._min_content_length:
            issues.append("Content too short")
            score -= 0.3
        elif len(content.strip()) > self._max_content_length:
            issues.append("Content too long")
            score -= 0.1
        else:
            strengths.append("Appropriate content length")
            score += 0.1

        # Check for structure
        if '\n' in content and len(content.split('\n')) > 3:
            strengths.append("Well-structured content")
            score += 0.1

        # Check for code blocks
        if '```' in content or '    ' in content:
            strengths.append("Contains code examples")
            score += 0.1

        # Check for low-quality patterns
        for pattern in self._low_quality_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Contains low-quality pattern: {pattern}")
                score -= 0.2

        # Check for high-quality patterns
        high_quality_count = 0
        for pattern in self._high_quality_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                high_quality_count += 1

        if high_quality_count > 0:
            strengths.append(f"Contains {high_quality_count} technical indicators")
            score += min(high_quality_count * 0.05, 0.2)

        # Check for clear problem statement
        if any(word in content.lower() for word in ['given', 'input', 'output', 'example', 'constraints']):
            strengths.append("Clear problem structure")
            score += 0.1

        return max(0.0, min(score, 1.0)), issues, strengths

    def _assess_uniqueness(self, title: str, content: str, metadata: Optional[Dict]) -> Tuple[float, List[str], List[str]]:
        """Assess question uniqueness."""
        issues = []
        strengths = []
        score = 0.7  # Assume unique unless proven otherwise

        # Check for common duplicate patterns
        common_patterns = [
            r'\b(two sum|merge two sorted|valid parentheses)\b',
            r'\b(reverse linked list|climbing stairs)\b',
            r'\b(longest substring|maximum subarray)\b',
        ]

        for pattern in common_patterns:
            if re.search(pattern, title + " " + content, re.IGNORECASE):
                issues.append("Common problem pattern detected")
                score -= 0.1

        # Check metadata for uniqueness indicators
        if metadata:
            if metadata.get('duplicate_count', 0) > 0:
                issues.append("Marked as duplicate")
                score -= 0.2

            if metadata.get('similar_questions', []):
                issues.append("Has similar questions")
                score -= 0.1

            if metadata.get('is_original', False):
                strengths.append("Marked as original content")
                score += 0.1

        # Check for unique elements
        unique_indicators = [
            'specific constraints',
            'unusual requirements',
            'creative solution',
            'novel approach',
            'custom data structure'
        ]

        unique_count = sum(1 for indicator in unique_indicators
                          if indicator in content.lower())

        if unique_count > 0:
            strengths.append(f"Contains {unique_count} unique elements")
            score += min(unique_count * 0.05, 0.15)

        return max(0.0, min(score, 1.0)), issues, strengths

    def _assess_educational_value(self, title: str, content: str) -> Tuple[float, List[str], List[str]]:
        """Assess educational value."""
        issues = []
        strengths = []
        score = 0.4  # Base score

        # Check for learning indicators
        learning_keywords = [
            'algorithm', 'complexity', 'optimization', 'technique',
            'approach', 'method', 'strategy', 'pattern',
            'data structure', 'time', 'space', 'efficiency'
        ]

        learning_score = sum(1 for keyword in learning_keywords
                           if keyword in content.lower())

        if learning_score > 0:
            strengths.append(f"Contains {learning_score} educational keywords")
            score += min(learning_score * 0.05, 0.3)

        # Check for difficulty indicators
        if any(word in title.lower() for word in ['easy', 'medium', 'hard']):
            strengths.append("Includes difficulty assessment")
            score += 0.1

        # Check for solution hints
        if 'hint' in content.lower() or 'solution' in content.lower():
            issues.append("Contains direct solution hints")
            score -= 0.1

        # Check for multiple approaches
        if any(word in content.lower() for word in ['alternative', 'another way', 'different approach']):
            strengths.append("Discusses multiple approaches")
            score += 0.15

        # Check for common mistakes
        if any(word in content.lower() for word in ['common mistake', 'pitfall', 'trap']):
            strengths.append("Warns about common mistakes")
            score += 0.1

        return max(0.0, min(score, 1.0)), issues, strengths

    def _assess_completeness(self, title: str, content: str, source: str) -> Tuple[float, List[str], List[str]]:
        """Assess question completeness."""
        issues = []
        strengths = []
        score = 0.6  # Base score

        # Check for essential elements
        essential_elements = {
            'input_format': ['input', 'given', 'provided'],
            'output_format': ['output', 'return', 'result'],
            'examples': ['example', 'sample'],
            'constraints': ['constraint', 'range', 'limit'],
        }

        completeness_score = 0
        for element, keywords in essential_elements.items():
            if any(keyword in content.lower() for keyword in keywords):
                completeness_score += 1
                strengths.append(f"Contains {element}")
            else:
                issues.append(f"Missing {element}")

        # Adjust score based on completeness
        score += (completeness_score / len(essential_elements)) * 0.3

        # Source-specific checks
        if source == 'reddit':
            # Reddit posts should have discussion context
            if len(content.split()) < 20:
                issues.append("Reddit post too short for discussion")
                score -= 0.1
            else:
                strengths.append("Appropriate length for Reddit discussion")
                score += 0.05

        elif source == 'leetcode':
            # LeetCode questions should have clear structure
            if 'example' in content.lower():
                strengths.append("Contains examples (good for LeetCode)")
                score += 0.1

        # Check for follow-up questions or clarifications
        if any(word in content.lower() for word in ['clarify', 'question', 'confused', 'follow-up']):
            issues.append("Contains unresolved questions")
            score -= 0.05

        return max(0.0, min(score, 1.0)), issues, strengths

    def filter_low_quality(self, questions: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """
        Filter out low-quality questions.

        Args:
            questions: List of question dictionaries
            threshold: Minimum quality score to keep

        Returns:
            Filtered list of questions
        """
        filtered = []

        for question in questions:
            quality = self.score_question(
                question_id=question['id'],
                title=question['title'],
                content=question['content'],
                source=question.get('source', 'unknown'),
                metadata=question.get('metadata')
            )

            if quality.overall_score >= threshold:
                # Add quality metadata
                question['quality_score'] = quality.overall_score
                question['quality_issues'] = quality.issues
                question['quality_strengths'] = quality.strengths
                filtered.append(question)

        self._logger.info(f"Filtered {len(questions) - len(filtered)} low-quality questions")
        return filtered
