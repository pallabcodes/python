"""Sentiment analysis agent for assessing question and content quality."""

import logging
from typing import Dict, List, Optional, Any
import re

from .base.agent_base import BaseAgent, AgentResult
from ..llm.llm_factory import LLMFactory
from ..llm.llm_config import LLMConfig


class SentimentAnalysisAgent(BaseAgent):
    """Agent for analyzing sentiment and quality of questions/discussions."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize sentiment analysis agent.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        super().__init__("sentiment_analysis", llm_config, logger)

        # Sentiment keywords for fallback analysis
        self._positive_keywords = [
            "good", "great", "excellent", "amazing", "helpful", "useful",
            "clear", "well explained", "perfect", "awesome", "brilliant",
            "love", "like", "best", "fantastic", "wonderful"
        ]

        self._negative_keywords = [
            "bad", "terrible", "awful", "horrible", "confusing", "useless",
            "worst", "hate", "dislike", "stupid", "annoying", "frustrating",
            "waste", "poor", "difficult", "hard"
        ]

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Analyze sentiment and quality of content.

        Args:
            input_data: Input data containing content to analyze

        Returns:
            Analysis results
        """
        try:
            content = input_data.get("content", "")
            content_type = input_data.get("content_type", "question")
            context = input_data.get("context", {})

            if not content:
                return AgentResult(
                    success=False,
                    message="No content provided for analysis",
                    errors=["Empty content"]
                )

            # Analyze sentiment
            sentiment_result = self._analyze_sentiment(content)

            # Analyze quality
            quality_result = self._analyze_quality(content, content_type, context)

            # Combine results
            overall_score = self._calculate_overall_score(sentiment_result, quality_result)

            result_data = {
                "sentiment": sentiment_result,
                "quality": quality_result,
                "overall_score": overall_score,
                "recommendation": self._get_recommendation(overall_score, content_type),
                "content_length": len(content),
                "content_type": content_type
            }

            # Add to memory
            self._add_to_memory(
                f"Analyzed {content_type} sentiment",
                f"Score: {overall_score:.2f}, Sentiment: {sentiment_result['label']}",
                {"content_type": content_type, "score": overall_score}
            )

            self._logger.info(
                f"Sentiment analysis completed: {content_type}, score: {overall_score:.2f}"
            )

            return AgentResult(
                success=True,
                data=result_data,
                message=f"Successfully analyzed {content_type} content"
            )

        except Exception as e:
            self._logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                message="Sentiment analysis failed",
                errors=[str(e)]
            )

    def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content."""
        # Try LLM-based analysis first
        if self.is_available():
            try:
                return self._llm_sentiment_analysis(content)
            except Exception as e:
                self._logger.warning(f"LLM sentiment analysis failed: {e}")

        # Fallback to keyword-based analysis
        return self._keyword_sentiment_analysis(content)

    def _llm_sentiment_analysis(self, content: str) -> Dict[str, Any]:
        """Use LLM for sentiment analysis."""
        prompt = f"""
        Analyze the sentiment and emotional tone of the following text. Focus on whether it's positive, negative, or neutral, and provide a confidence score.

        Text: "{content[:1000]}..."

        Respond with JSON in this format:
        {{
            "label": "positive|negative|neutral",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation",
            "key_phrases": ["phrase1", "phrase2"]
        }}
        """

        llm = self._llm_factory.create_llm()
        response = llm.generate(prompt)

        try:
            # Try to parse JSON response
            import json
            result = json.loads(response.strip())

            # Validate required fields
            if not all(key in result for key in ["label", "confidence", "reasoning"]):
                raise ValueError("Missing required fields in LLM response")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse LLM sentiment response: {e}")
            # Extract basic info from text response
            label = "neutral"
            if "positive" in response.lower():
                label = "positive"
            elif "negative" in response.lower():
                label = "negative"

            return {
                "label": label,
                "confidence": 0.5,
                "reasoning": "LLM response parsing failed",
                "key_phrases": []
            }

    def _keyword_sentiment_analysis(self, content: str) -> Dict[str, Any]:
        """Keyword-based sentiment analysis fallback."""
        content_lower = content.lower()

        positive_count = sum(1 for word in self._positive_keywords
                           if word in content_lower)
        negative_count = sum(1 for word in self._negative_keywords
                           if word in content_lower)

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            return {
                "label": "neutral",
                "confidence": 0.5,
                "reasoning": "No clear sentiment indicators found",
                "key_phrases": []
            }

        if positive_count > negative_count:
            confidence = min(0.9, positive_count / max(1, total_sentiment_words))
            label = "positive"
        elif negative_count > positive_count:
            confidence = min(0.9, negative_count / max(1, total_sentiment_words))
            label = "negative"
        else:
            confidence = 0.5
            label = "neutral"

        return {
            "label": label,
            "confidence": confidence,
            "reasoning": f"Keyword analysis: {positive_count} positive, {negative_count} negative",
            "key_phrases": self._extract_sentiment_phrases(content)
        }

    def _extract_sentiment_phrases(self, content: str) -> List[str]:
        """Extract phrases containing sentiment words."""
        phrases = []
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in
                   self._positive_keywords + self._negative_keywords):
                # Extract phrase around sentiment word
                for word in self._positive_keywords + self._negative_keywords:
                    if word in sentence_lower:
                        start = max(0, sentence_lower.find(word) - 20)
                        end = min(len(sentence), sentence_lower.find(word) + len(word) + 20)
                        phrase = sentence[start:end].strip()
                        if phrase:
                            phrases.append(phrase)
                        break

        return list(set(phrases))[:3]  # Return up to 3 unique phrases

    def _analyze_quality(self, content: str, content_type: str, context: Dict) -> Dict[str, Any]:
        """Analyze content quality."""
        quality_scores = {
            "length_score": self._score_content_length(content, content_type),
            "clarity_score": self._score_clarity(content),
            "relevance_score": self._score_relevance(content, context),
            "structure_score": self._score_structure(content, content_type)
        }

        overall_quality = sum(quality_scores.values()) / len(quality_scores)

        return {
            "overall_score": overall_quality,
            "component_scores": quality_scores,
            "issues": self._identify_quality_issues(content, content_type)
        }

    def _score_content_length(self, content: str, content_type: str) -> float:
        """Score content based on length appropriateness."""
        length = len(content)

        if content_type == "question":
            # Questions should be substantial but not too long
            if 100 <= length <= 2000:
                return 1.0
            elif 50 <= length < 100:
                return 0.7
            elif length < 50:
                return 0.3
            else:
                return 0.6  # Too long, but still has content
        elif content_type == "discussion":
            # Discussions can be longer
            if 200 <= length <= 5000:
                return 1.0
            elif 100 <= length < 200:
                return 0.6
            elif length < 100:
                return 0.2
            else:
                return 0.7
        else:
            # Generic content
            if length > 50:
                return 0.8
            else:
                return 0.4

    def _score_clarity(self, content: str) -> float:
        """Score content clarity."""
        # Check for excessive special characters
        special_chars = len(re.findall(r'[^\w\s]', content))
        special_ratio = special_chars / max(1, len(content))

        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

        clarity_score = 1.0

        # Penalize excessive special characters
        if special_ratio > 0.1:
            clarity_score -= 0.3

        # Penalize very short or very long sentences
        if avg_sentence_length < 5 or avg_sentence_length > 30:
            clarity_score -= 0.2

        # Penalize excessive caps
        caps_ratio = sum(1 for c in content if c.isupper()) / max(1, len(content))
        if caps_ratio > 0.3:
            caps_ratio -= 0.2

        return max(0.0, min(1.0, clarity_score))

    def _score_relevance(self, content: str, context: Dict) -> float:
        """Score content relevance based on context."""
        # This is a simplified implementation
        # In a real system, you'd use more sophisticated relevance scoring
        relevance_indicators = context.get("relevance_keywords", [])
        content_lower = content.lower()

        if not relevance_indicators:
            return 0.8  # Neutral score when no context

        matches = sum(1 for keyword in relevance_indicators
                     if keyword.lower() in content_lower)

        relevance_ratio = matches / len(relevance_indicators)
        return min(1.0, relevance_ratio + 0.3)  # Base score + matches

    def _score_structure(self, content: str, content_type: str) -> float:
        """Score content structure."""
        structure_score = 0.5  # Base score

        # Check for proper punctuation
        sentences = re.split(r'[.!?]+', content.strip())
        if len(sentences) > 1:
            structure_score += 0.2

        # Check for paragraphs (multiple lines)
        lines = content.split('\n')
        if len([line for line in lines if line.strip()]) > 2:
            structure_score += 0.2

        # Check for questions marks in questions
        if content_type == "question" and '?' in content:
            structure_score += 0.1

        return min(1.0, structure_score)

    def _identify_quality_issues(self, content: str, content_type: str) -> List[str]:
        """Identify specific quality issues."""
        issues = []

        # Length issues
        if len(content) < 50:
            issues.append("Content too short")
        elif len(content) > 5000:
            issues.append("Content too long")

        # Clarity issues
        if len(re.findall(r'[^\w\s]', content)) / max(1, len(content)) > 0.15:
            issues.append("Excessive special characters")

        caps_ratio = sum(1 for c in content if c.isupper()) / max(1, len(content))
        if caps_ratio > 0.4:
            issues.append("Excessive use of capital letters")

        # Structure issues
        sentences = re.split(r'[.!?]+', content.strip())
        if len(sentences) < 2 and len(content) > 200:
            issues.append("Lack of sentence structure")

        return issues

    def _calculate_overall_score(self, sentiment: Dict, quality: Dict) -> float:
        """Calculate overall content score."""
        sentiment_weight = 0.4
        quality_weight = 0.6

        # Convert sentiment to numerical score
        sentiment_score = {
            "positive": 1.0,
            "neutral": 0.5,
            "negative": 0.0
        }.get(sentiment["label"], 0.5)

        # Adjust by confidence
        sentiment_score = sentiment_score * sentiment["confidence"] + 0.5 * (1 - sentiment["confidence"])

        quality_score = quality["overall_score"]

        return sentiment_weight * sentiment_score + quality_weight * quality_score

    def _get_recommendation(self, score: float, content_type: str) -> str:
        """Get recommendation based on score."""
        if score >= 0.8:
            return f"High-quality {content_type} - suitable for inclusion"
        elif score >= 0.6:
            return f"Moderate quality {content_type} - consider for inclusion"
        elif score >= 0.4:
            return f"Low quality {content_type} - may need improvement"
        else:
            return f"Poor quality {content_type} - recommend exclusion"

