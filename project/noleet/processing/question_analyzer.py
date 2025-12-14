"""LLM-powered question analyzer for topics, difficulty, and sentiment."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from ..llm.llm_factory import LLMFactory
from ..llm.llm_config import LLMConfig
from ..core.models import Topic


@dataclass
class QuestionAnalysis:
    """Analysis result for a question."""
    question_id: str
    title: str
    content: str
    topics: List[str]
    difficulty: str  # easy, medium, hard
    sentiment: str   # positive, negative, neutral
    quality_score: float  # 0.0-1.0
    reasoning: str
    confidence_scores: Dict[str, float]


class QuestionAnalyzer:
    """LLM-powered analyzer for questions from LeetCode, Reddit, etc."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize question analyzer.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)

        # Available topics for categorization
        self._available_topics = [topic.value for topic in Topic]

        # Analysis prompts
        self._analysis_prompt = self._build_analysis_prompt()

    def _build_analysis_prompt(self) -> str:
        """Build the analysis prompt for LLM."""
        topics_str = ", ".join(f'"{topic}"' for topic in self._available_topics)

        return f"""You are an expert DSA (Data Structures and Algorithms) analyst. Analyze the following coding question and provide a detailed analysis in JSON format.

Available DSA Topics: {topics_str}

For each question, provide:
1. **topics**: Array of relevant DSA topics (choose from available topics)
2. **difficulty**: "easy", "medium", or "hard" based on algorithmic complexity
3. **sentiment**: "positive", "negative", or "neutral" based on community reception
4. **quality_score**: Float 0.0-1.0 indicating question quality (clarity, uniqueness, learning value)
5. **reasoning**: Brief explanation of your analysis
6. **confidence_scores**: Object with confidence scores for each major component

Guidelines:
- Topics: Choose 1-4 most relevant topics, prefer specific over general
- Difficulty: Consider time/space complexity, algorithmic concepts involved
- Sentiment: Based on title/content tone, community helpfulness indicators
- Quality: Higher for clear, well-structured, educational questions
- Be conservative with difficulty assessment - prefer medium unless clearly simple/complex

Return only valid JSON with these exact keys: topics, difficulty, sentiment, quality_score, reasoning, confidence_scores
"""

    def analyze_question(
        self,
        question_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QuestionAnalysis:
        """
        Analyze a single question using LLM.

        Args:
            question_id: Unique question identifier
            title: Question title
            content: Question content/description
            metadata: Additional metadata (source, tags, etc.)

        Returns:
            Analysis result
        """
        try:
            # Prepare input for LLM
            question_text = f"Title: {title}\n\nContent: {content}"

            # Get LLM instance
            llm = self._llm_factory.create_llm()

            # Analyze with LLM
            response = llm.generate(
                prompt=self._analysis_prompt,
                context=f"Question to analyze:\n\n{question_text}",
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500
            )

            # Parse LLM response
            analysis_data = self._parse_llm_response(response)

            # Validate and clean analysis
            validated_analysis = self._validate_analysis(analysis_data)

            return QuestionAnalysis(
                question_id=question_id,
                title=title,
                content=content,
                topics=validated_analysis["topics"],
                difficulty=validated_analysis["difficulty"],
                sentiment=validated_analysis["sentiment"],
                quality_score=validated_analysis["quality_score"],
                reasoning=validated_analysis["reasoning"],
                confidence_scores=validated_analysis["confidence_scores"]
            )

        except Exception as e:
            self._logger.error(f"Failed to analyze question {question_id}: {e}")

            # Return fallback analysis
            return self._fallback_analysis(question_id, title, content)

    def analyze_questions_batch(
        self,
        questions: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> List[QuestionAnalysis]:
        """
        Analyze multiple questions in batches.

        Args:
            questions: List of question dictionaries
            batch_size: Number of questions to analyze together

        Returns:
            List of analysis results
        """
        results = []

        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]

            for question in batch:
                analysis = self.analyze_question(
                    question_id=question["id"],
                    title=question["title"],
                    content=question["content"],
                    metadata=question.get("metadata")
                )
                results.append(analysis)

        return results

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON data."""
        try:
            # Try to extract JSON from response
            # Look for JSON block
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing entire response as JSON
                return json.loads(response)

        except json.JSONDecodeError as e:
            self._logger.warning(f"Failed to parse LLM response as JSON: {e}")
            self._logger.debug(f"Raw response: {response}")

            # Return default structure
            return {
                "topics": [],
                "difficulty": "medium",
                "sentiment": "neutral",
                "quality_score": 0.5,
                "reasoning": "Failed to parse LLM response",
                "confidence_scores": {
                    "topics": 0.0,
                    "difficulty": 0.5,
                    "sentiment": 0.5,
                    "quality": 0.5
                }
            }

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean analysis results."""
        validated = {}

        # Validate topics
        topics = analysis.get("topics", [])
        if isinstance(topics, str):
            topics = [topics]

        validated_topics = []
        for topic in topics:
            if topic in self._available_topics:
                validated_topics.append(topic)

        validated["topics"] = validated_topics[:4]  # Max 4 topics

        # Validate difficulty
        difficulty = analysis.get("difficulty", "medium")
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"
        validated["difficulty"] = difficulty

        # Validate sentiment
        sentiment = analysis.get("sentiment", "neutral")
        if sentiment not in ["positive", "negative", "neutral"]:
            sentiment = "neutral"
        validated["sentiment"] = sentiment

        # Validate quality score
        quality_score = analysis.get("quality_score", 0.5)
        if not isinstance(quality_score, (int, float)) or not (0.0 <= quality_score <= 1.0):
            quality_score = 0.5
        validated["quality_score"] = float(quality_score)

        # Validate reasoning
        validated["reasoning"] = str(analysis.get("reasoning", "LLM analysis"))

        # Validate confidence scores
        confidence_scores = analysis.get("confidence_scores", {})
        validated["confidence_scores"] = {
            "topics": float(confidence_scores.get("topics", 0.5)),
            "difficulty": float(confidence_scores.get("difficulty", 0.5)),
            "sentiment": float(confidence_scores.get("sentiment", 0.5)),
            "quality": float(confidence_scores.get("quality", validated["quality_score"])),
        }

        return validated

    def _fallback_analysis(
        self,
        question_id: str,
        title: str,
        content: str
    ) -> QuestionAnalysis:
        """Provide fallback analysis when LLM fails."""
        # Simple keyword-based analysis
        text = f"{title} {content}".lower()

        # Topic detection
        topics = []
        topic_keywords = {
            "array": ["array", "list", "vector"],
            "string": ["string", "text", "substring"],
            "dynamic_programming": ["dp", "dynamic programming", "memoization"],
            "tree": ["tree", "binary", "node", "bst"],
            "graph": ["graph", "dfs", "bfs", "cycle"],
            "sorting": ["sort", "merge", "quick", "heap"],
            "hash_table": ["hash", "map", "dictionary", "set"],
            "sliding_window": ["window", "sliding"],
            "two_pointers": ["two pointers", "pointers"],
            "backtracking": ["backtrack", "permutation", "combination"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)

        # Difficulty estimation
        difficulty = "medium"
        if any(word in text for word in ["easy", "simple", "basic"]):
            difficulty = "easy"
        elif any(word in text for word in ["hard", "difficult", "complex", "expert"]):
            difficulty = "hard"

        # Sentiment (neutral fallback)
        sentiment = "neutral"

        # Quality score based on content length and structure
        quality_score = min(0.8, len(content) / 1000.0)

        return QuestionAnalysis(
            question_id=question_id,
            title=title,
            content=content,
            topics=topics[:4],
            difficulty=difficulty,
            sentiment=sentiment,
            quality_score=quality_score,
            reasoning="Fallback keyword-based analysis",
            confidence_scores={
                "topics": 0.6,
                "difficulty": 0.7,
                "sentiment": 0.5,
                "quality": 0.6,
            }
        )
