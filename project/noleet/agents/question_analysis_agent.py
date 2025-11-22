"""Question analysis agent for difficulty assessment and topic extraction."""

import logging
from typing import Dict, List, Optional, Any, Set
import re

from .base.agent_base import BaseAgent, AgentResult
from ..core.models import Topic
from ..llm.llm_factory import LLMFactory
from ..llm.llm_config import LLMConfig


class QuestionAnalysisAgent(BaseAgent):
    """Agent for analyzing questions: difficulty, topics, quality."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize question analysis agent.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        super().__init__("question_analysis", llm_config, logger)

        # Difficulty keywords for fallback analysis
        self._easy_keywords = [
            "simple", "basic", "easy", "straightforward", "beginner",
            "elementary", "fundamental", "introductory"
        ]

        self._medium_keywords = [
            "medium", "intermediate", "moderate", "average", "standard",
            "typical", "normal", "regular"
        ]

        self._hard_keywords = [
            "hard", "difficult", "challenging", "advanced", "complex",
            "tricky", "tough", "complicated", "expert"
        ]

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Analyze a question for difficulty, topics, and quality.

        Args:
            input_data: Input data containing question content

        Returns:
            Analysis results
        """
        try:
            content = input_data.get("content", "")
            title = input_data.get("title", "")
            source = input_data.get("source", "unknown")
            existing_tags = input_data.get("existing_tags", [])

            if not content and not title:
                return AgentResult(
                    success=False,
                    message="No question content provided for analysis",
                    errors=["Empty question content"]
                )

            full_content = f"{title}\n\n{content}".strip()

            # Analyze difficulty
            difficulty_result = self._analyze_difficulty(full_content)

            # Extract topics
            topics_result = self._extract_topics(full_content, existing_tags)

            # Analyze technical quality
            quality_result = self._analyze_technical_quality(full_content)

            # Generate overall assessment
            assessment = self._generate_assessment(
                difficulty_result, topics_result, quality_result, source
            )

            result_data = {
                "difficulty": difficulty_result,
                "topics": topics_result,
                "quality": quality_result,
                "assessment": assessment,
                "content_length": len(full_content),
                "source": source
            }

            # Add to memory
            self._add_to_memory(
                f"Analyzed question from {source}",
                f"Difficulty: {difficulty_result['level']}, Topics: {len(topics_result['extracted_topics'])}",
                {"source": source, "difficulty": difficulty_result['level']}
            )

            self._logger.info(
                f"Question analysis completed: {source}, difficulty: {difficulty_result['level']}, "
                f"topics: {len(topics_result['extracted_topics'])}"
            )

            return AgentResult(
                success=True,
                data=result_data,
                message="Successfully analyzed question"
            )

        except Exception as e:
            self._logger.error(f"Question analysis failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                message="Question analysis failed",
                errors=[str(e)]
            )

    def _analyze_difficulty(self, content: str) -> Dict[str, Any]:
        """Analyze question difficulty."""
        # Try LLM-based analysis first
        if self.is_available():
            try:
                return self._llm_difficulty_analysis(content)
            except Exception as e:
                self._logger.warning(f"LLM difficulty analysis failed: {e}")

        # Fallback to keyword-based analysis
        return self._keyword_difficulty_analysis(content)

    def _llm_difficulty_analysis(self, content: str) -> Dict[str, Any]:
        """Use LLM for difficulty analysis."""
        prompt = f"""
        Analyze the difficulty level of this coding interview question. Consider:
        - Algorithm complexity required
        - Data structures needed
        - Problem-solving approach
        - Edge cases to handle

        Question: "{content[:1500]}..."

        Respond with JSON in this format:
        {{
            "level": "easy|medium|hard",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation of why this difficulty level",
            "required_concepts": ["concept1", "concept2"],
            "estimated_solve_time": "minutes as integer"
        }}
        """

        llm = self._llm_factory.create_llm()
        response = llm.generate(prompt)

        try:
            import json
            result = json.loads(response.strip())

            # Validate required fields
            if not all(key in result for key in ["level", "confidence", "reasoning"]):
                raise ValueError("Missing required fields in LLM response")

            # Validate difficulty level
            if result["level"] not in ["easy", "medium", "hard"]:
                result["level"] = "medium"  # Default

            return result

        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse LLM difficulty response: {e}")
            return self._keyword_difficulty_analysis(content)

    def _keyword_difficulty_analysis(self, content: str) -> Dict[str, Any]:
        """Keyword-based difficulty analysis fallback."""
        content_lower = content.lower()

        easy_score = sum(1 for word in self._easy_keywords if word in content_lower)
        medium_score = sum(1 for word in self._medium_keywords if word in content_lower)
        hard_score = sum(1 for word in self._hard_keywords if word in content_lower)

        # Analyze algorithmic complexity indicators
        complexity_indicators = {
            "easy": ["o(1)", "o(n)", "linear", "simple"],
            "medium": ["o(n log n)", "o(n^2)", "two pointers", "sliding window"],
            "hard": ["o(2^n)", "o(n!)", "dynamic programming", "graph algorithms", "hard"]
        }

        algo_scores = {"easy": 0, "medium": 0, "hard": 0}
        for level, indicators in complexity_indicators.items():
            algo_scores[level] = sum(1 for ind in indicators if ind in content_lower)

        # Combine scores
        total_easy = easy_score + algo_scores["easy"]
        total_medium = medium_score + algo_scores["medium"]
        total_hard = hard_score + algo_scores["hard"]

        max_score = max(total_easy, total_medium, total_hard)

        if max_score == 0:
            # No clear indicators, analyze by length and complexity
            if len(content) < 500 and "basic" in content_lower:
                level, confidence = "easy", 0.6
            elif len(content) > 1000 or "complex" in content_lower:
                level, confidence = "hard", 0.6
            else:
                level, confidence = "medium", 0.5
        elif total_hard > total_medium and total_hard > total_easy:
            level, confidence = "hard", min(0.9, 0.5 + (total_hard / 10))
        elif total_medium > total_easy:
            level, confidence = "medium", min(0.9, 0.5 + (total_medium / 10))
        else:
            level, confidence = "easy", min(0.9, 0.5 + (total_easy / 10))

        return {
            "level": level,
            "confidence": confidence,
            "reasoning": f"Keyword analysis: easy={total_easy}, medium={total_medium}, hard={total_hard}",
            "required_concepts": self._extract_concepts(content),
            "estimated_solve_time": self._estimate_solve_time(level)
        }

    def _extract_concepts(self, content: str) -> List[str]:
        """Extract DSA concepts mentioned in content."""
        concepts = []
        content_lower = content.lower()

        concept_mappings = {
            "array": ["array", "list", "vector"],
            "string": ["string", "text", "substring"],
            "linked list": ["linked list", "linkedlist", "node"],
            "tree": ["tree", "binary tree", "bst"],
            "graph": ["graph", "dfs", "bfs"],
            "dynamic programming": ["dp", "dynamic programming", "memoization"],
            "sorting": ["sort", "sorting"],
            "searching": ["search", "binary search"],
            "hash table": ["hash", "map", "dictionary"],
            "stack": ["stack", "lifo"],
            "queue": ["queue", "fifo"]
        }

        for concept, keywords in concept_mappings.items():
            if any(keyword in content_lower for keyword in keywords):
                concepts.append(concept)

        return concepts[:5]  # Limit to top concepts

    def _estimate_solve_time(self, difficulty: str) -> int:
        """Estimate solve time in minutes."""
        time_estimates = {
            "easy": 20,
            "medium": 40,
            "hard": 60
        }
        return time_estimates.get(difficulty, 30)

    def _extract_topics(self, content: str, existing_tags: List[str]) -> Dict[str, Any]:
        """Extract DSA topics from question content."""
        topics = set()

        # Convert existing tags to topics
        for tag in existing_tags:
            topic = self._tag_to_topic(tag)
            if topic:
                topics.add(topic)

        # Extract topics from content
        content_topics = self._extract_topics_from_content(content)
        topics.update(content_topics)

        # If no topics found, try LLM
        if not topics and self.is_available():
            try:
                llm_topics = self._llm_topic_extraction(content)
                topics.update(llm_topics)
            except Exception as e:
                self._logger.warning(f"LLM topic extraction failed: {e}")

        return {
            "extracted_topics": list(topics),
            "topic_count": len(topics),
            "primary_topic": self._get_primary_topic(topics),
            "confidence": min(1.0, len(topics) * 0.2 + 0.5)
        }

    def _tag_to_topic(self, tag: str) -> Optional[Topic]:
        """Convert tag string to Topic enum."""
        tag_lower = tag.lower().replace("-", "_").replace(" ", "_")

        # Common tag to topic mappings
        tag_mappings = {
            "dynamic_programming": Topic.DYNAMIC_PROGRAMMING,
            "dp": Topic.DYNAMIC_PROGRAMMING,
            "sliding_window": Topic.SLIDING_WINDOW,
            "two_pointers": Topic.TWO_POINTERS,
            "binary_search": Topic.BINARY_SEARCH,
            "graph": Topic.GRAPH_TRAVERSAL,
            "tree": Topic.TREE_TRAVERSAL,
            "backtracking": Topic.BACKTRACKING,
            "greedy": Topic.GREEDY,
            "union_find": Topic.UNION_FIND,
            "trie": Topic.TRIE,
            "heap": Topic.HEAP,
            "hash_table": Topic.HASH_TABLE,
            "linked_list": Topic.LINKED_LIST,
            "stack": Topic.STACK,
            "queue": Topic.QUEUE,
            "bit_manipulation": Topic.BIT_MANIPULATION,
            "sorting": Topic.SORTING,
            "string_matching": Topic.STRING_MATCHING
        }

        return tag_mappings.get(tag_lower)

    def _extract_topics_from_content(self, content: str) -> Set[Topic]:
        """Extract topics from content using keyword matching."""
        topics = set()
        content_lower = content.lower()

        topic_keywords = {
            Topic.DYNAMIC_PROGRAMMING: ["dynamic programming", "dp", "memoization", "tabulation"],
            Topic.SLIDING_WINDOW: ["sliding window", "window"],
            Topic.MERGE_INTERVALS: ["merge intervals", "intervals"],
            Topic.TWO_POINTERS: ["two pointers"],
            Topic.BINARY_SEARCH: ["binary search"],
            Topic.GRAPH_TRAVERSAL: ["graph", "dfs", "bfs", "adjacency"],
            Topic.TREE_TRAVERSAL: ["tree", "binary tree", "bst", "inorder", "preorder"],
            Topic.BACKTRACKING: ["backtrack", "backtracking", "recursion"],
            Topic.GREEDY: ["greedy"],
            Topic.UNION_FIND: ["union find", "disjoint set"],
            Topic.TRIE: ["trie", "prefix tree"],
            Topic.HEAP: ["heap", "priority queue"],
            Topic.HASH_TABLE: ["hash", "map", "dictionary"],
            Topic.LINKED_LIST: ["linked list"],
            Topic.STACK: ["stack"],
            Topic.QUEUE: ["queue"],
            Topic.BIT_MANIPULATION: ["bit", "xor", "and", "or"],
            Topic.SORTING: ["sort", "sorting"],
            Topic.STRING_MATCHING: ["string", "pattern", "kmp"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.add(topic)

        return topics

    def _llm_topic_extraction(self, content: str) -> Set[Topic]:
        """Use LLM for topic extraction."""
        prompt = f"""
        Extract the main DSA (Data Structures and Algorithms) topics from this coding question.
        Return only the topic names that are clearly relevant.

        Question: "{content[:1000]}..."

        Respond with a comma-separated list of topics from this list:
        dynamic_programming, sliding_window, merge_intervals, two_pointers, binary_search,
        graph_traversal, tree_traversal, backtracking, greedy, union_find, trie, heap,
        hash_table, linked_list, stack, queue, bit_manipulation, sorting, string_matching
        """

        llm = self._llm_factory.create_llm()
        response = llm.generate(prompt)

        topics = set()
        response_topics = [t.strip().lower().replace(" ", "_")
                          for t in response.split(",")]

        for topic_name in response_topics:
            try:
                topic = Topic(topic_name)
                topics.add(topic)
            except ValueError:
                continue  # Invalid topic name

        return topics

    def _get_primary_topic(self, topics: Set[Topic]) -> Optional[Topic]:
        """Get the primary topic from a set."""
        if not topics:
            return None

        # Simple heuristic: prefer more specific topics
        priority_order = [
            Topic.DYNAMIC_PROGRAMMING, Topic.GRAPH_TRAVERSAL, Topic.TREE_TRAVERSAL,
            Topic.BACKTRACKING, Topic.UNION_FIND, Topic.TRIE, Topic.HEAP,
            Topic.SLIDING_WINDOW, Topic.MERGE_INTERVALS, Topic.TWO_POINTERS,
            Topic.BINARY_SEARCH, Topic.GREEDY
        ]

        for topic in priority_order:
            if topic in topics:
                return topic

        return next(iter(topics))  # Return first topic

    def _analyze_technical_quality(self, content: str) -> Dict[str, Any]:
        """Analyze technical quality of the question."""
        quality_scores = {
            "problem_clarity": self._score_problem_clarity(content),
            "constraints_clarity": self._score_constraints_clarity(content),
            "examples_quality": self._score_examples_quality(content),
            "edge_cases": self._score_edge_cases(content)
        }

        overall_quality = sum(quality_scores.values()) / len(quality_scores)

        return {
            "overall_score": overall_quality,
            "component_scores": quality_scores,
            "strengths": self._identify_strengths(content),
            "weaknesses": self._identify_weaknesses(content)
        }

    def _score_problem_clarity(self, content: str) -> float:
        """Score how clearly the problem is stated."""
        score = 0.5  # Base score

        # Check for clear problem statement
        if "problem" in content.lower() or "given" in content.lower():
            score += 0.2

        # Check for clear objective
        if any(word in content.lower() for word in ["return", "find", "calculate", "determine"]):
            score += 0.2

        # Penalize for excessive jargon without explanation
        complex_terms = ["algorithm", "complexity", "optimization"]
        if sum(1 for term in complex_terms if term in content.lower()) > 2:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _score_constraints_clarity(self, content: str) -> float:
        """Score how clearly constraints are stated."""
        score = 0.3  # Base score

        content_lower = content.lower()

        # Check for common constraint indicators
        constraint_indicators = [
            "constraint", "limit", "range", "length", "size",
            "1 <= n <= ", "0 <= ", "n =", "time", "space"
        ]

        matches = sum(1 for ind in constraint_indicators if ind in content_lower)
        score += min(0.5, matches * 0.1)

        # Check for numerical constraints
        if re.search(r'\d+\s*[<>=]+\s*\d+', content):
            score += 0.2

        return max(0.0, min(1.0, score))

    def _score_examples_quality(self, content: str) -> float:
        """Score the quality of examples provided."""
        score = 0.2  # Base score

        content_lower = content.lower()

        # Check for examples
        if "example" in content_lower:
            score += 0.3

        # Check for input/output format
        if "input:" in content_lower and "output:" in content_lower:
            score += 0.3

        # Check for multiple examples
        example_count = content_lower.count("example")
        if example_count > 1:
            score += 0.2

        return max(0.0, min(1.0, score))

    def _score_edge_cases(self, content: str) -> float:
        """Score how well edge cases are considered."""
        score = 0.1  # Base score

        content_lower = content.lower()

        # Check for edge case mentions
        edge_indicators = [
            "edge case", "corner case", "empty", "null", "negative",
            "minimum", "maximum", "single", "duplicate"
        ]

        matches = sum(1 for ind in edge_indicators if ind in content_lower)
        score += min(0.6, matches * 0.15)

        # Check for constraint analysis
        if "constraint" in content_lower and any(word in content_lower for word in ["handle", "consider", "check"]):
            score += 0.3

        return max(0.0, min(1.0, score))

    def _identify_strengths(self, content: str) -> List[str]:
        """Identify strengths of the question."""
        strengths = []

        if self._score_problem_clarity(content) > 0.7:
            strengths.append("Clear problem statement")

        if self._score_constraints_clarity(content) > 0.6:
            strengths.append("Well-defined constraints")

        if self._score_examples_quality(content) > 0.7:
            strengths.append("Good examples provided")

        if self._score_edge_cases(content) > 0.5:
            strengths.append("Considers edge cases")

        if len(content) > 300:
            strengths.append("Detailed explanation")

        return strengths

    def _identify_weaknesses(self, content: str) -> List[str]:
        """Identify weaknesses of the question."""
        weaknesses = []

        if self._score_problem_clarity(content) < 0.5:
            weaknesses.append("Unclear problem statement")

        if self._score_constraints_clarity(content) < 0.4:
            weaknesses.append("Poor constraint definition")

        if self._score_examples_quality(content) < 0.4:
            weaknesses.append("Missing or poor examples")

        if self._score_edge_cases(content) < 0.3:
            weaknesses.append("Edge cases not considered")

        if len(content) < 100:
            weaknesses.append("Too brief")

        return weaknesses

    def _generate_assessment(self, difficulty: Dict, topics: Dict, quality: Dict, source: str) -> Dict[str, Any]:
        """Generate overall question assessment."""
        difficulty_level = difficulty["level"]
        topic_count = topics["topic_count"]
        quality_score = quality["overall_score"]

        # Calculate suitability score
        suitability_score = (
            quality_score * 0.5 +
            (topic_count / 10) * 0.3 +  # More topics = more valuable
            (1.0 if difficulty_level in ["medium", "hard"] else 0.7) * 0.2  # Prefer non-trivial questions
        )

        recommendation = "include" if suitability_score > 0.6 else "review" if suitability_score > 0.4 else "exclude"

        return {
            "suitability_score": suitability_score,
            "recommendation": recommendation,
            "target_audience": self._get_target_audience(difficulty_level, topic_count),
            "educational_value": self._assess_educational_value(difficulty, topics, quality),
            "source_reliability": self._assess_source_reliability(source)
        }

    def _get_target_audience(self, difficulty: str, topic_count: int) -> str:
        """Determine target audience for the question."""
        if difficulty == "easy" and topic_count <= 2:
            return "beginners"
        elif difficulty == "medium" or (difficulty == "easy" and topic_count > 2):
            return "intermediate"
        elif difficulty == "hard" or topic_count > 4:
            return "advanced"
        else:
            return "intermediate"

    def _assess_educational_value(self, difficulty: Dict, topics: Dict, quality: Dict) -> str:
        """Assess educational value."""
        quality_score = quality["overall_score"]
        topic_count = topics["topic_count"]

        if quality_score > 0.7 and topic_count >= 2:
            return "high"
        elif quality_score > 0.5 or topic_count >= 1:
            return "medium"
        else:
            return "low"

    def _assess_source_reliability(self, source: str) -> str:
        """Assess reliability of the source."""
        reliable_sources = ["leetcode", "interviewing.io", "system design"]
        medium_sources = ["reddit", "stackoverflow", "medium"]
        low_sources = ["unknown", "random"]

        source_lower = source.lower()

        if any(rel in source_lower for rel in reliable_sources):
            return "high"
        elif any(med in source_lower for med in medium_sources):
            return "medium"
        elif any(low in source_lower for low in low_sources):
            return "low"
        else:
            return "unknown"

