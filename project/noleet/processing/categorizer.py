"""Intelligent question categorizer using embeddings + LLM."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

from ..llm.embedder import TextEmbedder
from ..llm.llm_factory import LLMFactory
from ..llm.llm_config import LLMConfig
from ..core.models import Topic


@dataclass
class CategorizationResult:
    """Result of question categorization."""
    question_id: str
    primary_topic: str
    secondary_topics: List[str]
    confidence: float
    reasoning: str
    embedding_similarity: Dict[str, float]


class QuestionCategorizer:
    """Intelligent categorizer using embeddings and LLM for question classification."""

    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize question categorizer.

        Args:
            embedder: Text embedder instance
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._embedder = embedder or TextEmbedder(llm_config)
        self._config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)

        # Topic definitions with descriptions
        self._topic_definitions = self._build_topic_definitions()

        # Cache for topic embeddings
        self._topic_embeddings: Optional[Dict[str, List[float]]] = None

    def _build_topic_definitions(self) -> Dict[str, str]:
        """Build comprehensive topic definitions."""
        return {
            "array": "Array manipulation, traversal, searching, sorting, and common patterns like two pointers, sliding window",
            "string": "String processing, manipulation, pattern matching, algorithms like KMP, Rabin-Karp, string hashing",
            "hash_table": "Hash maps, sets, frequency counting, collision handling, custom hashing strategies",
            "dynamic_programming": "DP problems including memoization, tabulation, knapsack, longest common subsequence, matrix DP",
            "tree": "Binary trees, BST, tree traversal (DFS/BFS), tree construction, balancing, lowest common ancestor",
            "graph": "Graph algorithms, DFS/BFS, shortest paths (Dijkstra, Bellman-Ford), topological sort, cycle detection",
            "heap": "Priority queues, heap operations, top K problems, merge K sorted arrays, heap-based algorithms",
            "stack": "Stack-based problems, parentheses matching, monotonic stack, expression evaluation, next greater element",
            "queue": "Queue problems, BFS implementations, sliding window maximum, deque usage, level order traversal",
            "linked_list": "Singly/doubly linked lists, cycle detection, reversal, merging, fast/slow pointers",
            "binary_search": "Binary search variants, search in rotated arrays, peak finding, search spaces",
            "bit_manipulation": "Bit operations, XOR tricks, bit masking, subset generation, bit DP",
            "greedy": "Greedy algorithms, interval scheduling, Huffman coding, fractional knapsack",
            "backtracking": "Backtracking solutions, N-queens, permutations, combinations, subsets, word search",
            "divide_and_conquer": "Divide and conquer algorithms, merge sort, quick sort, closest pair, maximum subarray",
            "math": "Mathematical problems, number theory, combinatorics, probability, modular arithmetic",
            "two_pointers": "Two pointer technique, array problems, linked list problems, sliding window variants",
            "sliding_window": "Sliding window problems, maximum/minimum window, variable size windows, fixed size windows",
            "merge_intervals": "Interval problems, merging overlapping intervals, inserting intervals, meeting rooms",
            "trie": "Trie (prefix tree) problems, autocomplete, word search, XOR maximization, prefix matching",
            "union_find": "Disjoint set union, connected components, cycle detection in undirected graphs",
            "segment_tree": "Segment trees, range queries, range updates, fenwick tree, sparse tables",
            "binary_indexed_tree": "Fenwick tree, prefix sum queries, range sum updates, 2D fenwick tree",
            "topological_sort": "Topological sorting, course scheduling, dependency resolution, Kahn's algorithm",
            "shortest_path": "Shortest path algorithms, Dijkstra, Bellman-Ford, Floyd-Warshall, A* search",
            "minimum_spanning_tree": "MST algorithms, Kruskal, Prim, Union-Find applications",
            "strongly_connected_components": "SCC algorithms, Kosaraju, Tarjan, 2-SAT problems",
            "flow_networks": "Maximum flow, min-cut, Ford-Fulkerson, Edmonds-Karp, Dinic's algorithm",
        }

    def categorize_question(
        self,
        question_id: str,
        title: str,
        content: str,
        initial_topics: Optional[List[str]] = None
    ) -> CategorizationResult:
        """
        Categorize a question using embeddings and LLM.

        Args:
            question_id: Unique question identifier
            title: Question title
            content: Question content
            initial_topics: Initial topic suggestions (optional)

        Returns:
            Categorization result
        """
        try:
            # Prepare question text
            question_text = f"Title: {title}\n\nContent: {content}"

            # Get topic embeddings
            topic_embeddings = self._get_topic_embeddings()

            # Embed question
            question_embedding = self._embedder.embed_texts([question_text])[0]

            # Calculate similarities
            similarities = self._calculate_similarities(question_embedding, topic_embeddings)

            # Get top candidates
            top_candidates = self._get_top_candidates(similarities, top_k=5)

            # Use LLM for final categorization
            final_result = self._llm_categorization(
                question_text,
                top_candidates,
                initial_topics or []
            )

            return CategorizationResult(
                question_id=question_id,
                primary_topic=final_result["primary_topic"],
                secondary_topics=final_result["secondary_topics"],
                confidence=final_result["confidence"],
                reasoning=final_result["reasoning"],
                embedding_similarity=similarities
            )

        except Exception as e:
            self._logger.error(f"Failed to categorize question {question_id}: {e}")
            return self._fallback_categorization(question_id, title, content)

    def _get_topic_embeddings(self) -> Dict[str, List[float]]:
        """Get or create embeddings for all topics."""
        if self._topic_embeddings is None:
            self._logger.info("Generating topic embeddings...")

            topic_texts = []
            topic_names = []

            for name, description in self._topic_definitions.items():
                # Create rich topic representation
                topic_text = f"Topic: {name}\nDescription: {description}\nCommon problems: {name} algorithms and data structures"
                topic_texts.append(topic_text)
                topic_names.append(name)

            # Embed all topics
            embeddings = self._embedder.embed_texts(topic_texts)

            # Store in cache
            self._topic_embeddings = dict(zip(topic_names, embeddings))

        return self._topic_embeddings

    def _calculate_similarities(
        self,
        question_embedding: List[float],
        topic_embeddings: Dict[str, List[float]]
    ) -> Dict[str, float]:
        """Calculate cosine similarities between question and topics."""
        similarities = {}

        question_vec = np.array(question_embedding)

        for topic_name, topic_vec in topic_embeddings.items():
            topic_vec = np.array(topic_vec)

            # Cosine similarity
            dot_product = np.dot(question_vec, topic_vec)
            question_norm = np.linalg.norm(question_vec)
            topic_norm = np.linalg.norm(topic_vec)

            if question_norm > 0 and topic_norm > 0:
                similarity = dot_product / (question_norm * topic_norm)
            else:
                similarity = 0.0

            similarities[topic_name] = float(similarity)

        return similarities

    def _get_top_candidates(
        self,
        similarities: Dict[str, float],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Get top-k most similar topics."""
        sorted_topics = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_topics[:top_k]

    def _llm_categorization(
        self,
        question_text: str,
        top_candidates: List[Tuple[str, float]],
        initial_topics: List[str]
    ) -> Dict[str, Any]:
        """Use LLM for final categorization decision."""

        # Build prompt
        candidates_text = "\n".join([
            f"- {topic}: {similarity:.3f} (description: {self._topic_definitions[topic]})"
            for topic, similarity in top_candidates
        ])

        initial_topics_text = ", ".join(initial_topics) if initial_topics else "None provided"

        prompt = f"""You are an expert DSA question categorizer. Analyze this question and determine the most appropriate primary topic and secondary topics.

Question:
{question_text}

Top candidate topics by semantic similarity:
{candidates_text}

Previously suggested topics: {initial_topics_text}

Instructions:
1. Choose ONE primary topic from the candidate topics
2. Choose 0-3 secondary topics (can include non-candidates if highly relevant)
3. Provide a confidence score (0.0-1.0) for your categorization
4. Give a brief reasoning for your choice

Consider:
- The core algorithmic concept being tested
- Data structures involved
- Problem-solving approach required
- Complexity analysis needs

Return JSON with: primary_topic, secondary_topics (array), confidence (float), reasoning (string)"""

        # Get LLM response
        llm = self._llm_factory.create_llm()
        response = llm.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=300
        )

        # Parse response
        try:
            import json
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)

            return {
                "primary_topic": result.get("primary_topic", top_candidates[0][0] if top_candidates else "array"),
                "secondary_topics": result.get("secondary_topics", []),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "LLM-based categorization")
            }

        except Exception as e:
            self._logger.warning(f"Failed to parse LLM categorization response: {e}")
            # Fallback to embedding-based result
            return {
                "primary_topic": top_candidates[0][0] if top_candidates else "array",
                "secondary_topics": [t[0] for t in top_candidates[1:3]] if len(top_candidates) > 1 else [],
                "confidence": top_candidates[0][1] if top_candidates else 0.5,
                "reasoning": "Embedding-based categorization (LLM parsing failed)"
            }

    def _fallback_categorization(
        self,
        question_id: str,
        title: str,
        content: str
    ) -> CategorizationResult:
        """Fallback categorization using simple keyword matching."""
        text = f"{title} {content}".lower()

        # Keyword to topic mapping
        keyword_mapping = {
            "array": ["array", "list", "vector", "matrix"],
            "string": ["string", "text", "substring", "palindrome"],
            "hash_table": ["hash", "map", "dictionary", "set", "frequency"],
            "dynamic_programming": ["dp", "dynamic programming", "memoization", "tabulation"],
            "tree": ["tree", "binary", "node", "bst", "traversal"],
            "graph": ["graph", "dfs", "bfs", "cycle", "path"],
            "heap": ["heap", "priority queue", "top k", "merge k"],
            "stack": ["stack", "monotonic", "next greater", "parentheses"],
            "queue": ["queue", "deque", "sliding window maximum"],
            "linked_list": ["linked list", "cycle", "reverse", "merge"],
            "binary_search": ["binary search", "rotated array", "peak"],
            "bit_manipulation": ["bit", "xor", "mask", "subset"],
            "greedy": ["greedy", "interval", "scheduling"],
            "backtracking": ["backtrack", "permutation", "combination", "subset"],
            "two_pointers": ["two pointers", "pointers"],
            "sliding_window": ["sliding window", "window"],
        }

        topic_scores = {}
        for topic, keywords in keyword_mapping.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                topic_scores[topic] = score

        # Get top topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        primary_topic = sorted_topics[0][0] if sorted_topics else "array"
        secondary_topics = [t[0] for t in sorted_topics[1:3]]

        return CategorizationResult(
            question_id=question_id,
            primary_topic=primary_topic,
            secondary_topics=secondary_topics,
            confidence=0.6,
            reasoning="Keyword-based fallback categorization",
            embedding_similarity={}
        )
