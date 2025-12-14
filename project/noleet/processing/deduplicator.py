"""Semantic deduplicator using embeddings to find similar questions."""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
import numpy as np
from collections import defaultdict


@dataclass
class DuplicateGroup:
    """Group of duplicate questions."""
    canonical_question: Dict[str, Any]
    duplicates: List[Dict[str, Any]]
    similarity_score: float
    reason: str


@dataclass
class DeduplicationResult:
    """Result of deduplication process."""
    unique_questions: List[Dict[str, Any]]
    duplicate_groups: List[DuplicateGroup]
    total_duplicates_removed: int
    average_similarity: float


class QuestionDeduplicator:
    """Deduplicates questions using semantic similarity."""

    def __init__(
        self,
        embedder: Optional[Any] = None,
        similarity_threshold: float = 0.85,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize deduplicator.

        Args:
            embedder: Text embedder instance
            similarity_threshold: Minimum similarity to consider duplicate
            logger: Optional logger instance
        """
        self._embedder = embedder
        self._similarity_threshold = similarity_threshold
        self._logger = logger or logging.getLogger(__name__)

    def deduplicate_questions(
        self,
        questions: List[Dict[str, Any]]
    ) -> DeduplicationResult:
        """
        Remove duplicate questions based on semantic similarity.

        Args:
            questions: List of question dictionaries

        Returns:
            Deduplication result
        """
        if len(questions) <= 1:
            return DeduplicationResult(
                unique_questions=questions,
                duplicate_groups=[],
                total_duplicates_removed=0,
                average_similarity=0.0
            )

        try:
            # Generate embeddings for all questions
            question_texts = [
                f"Title: {q['title']}\nContent: {q['content']}"
                for q in questions
            ]

            embeddings = self._embedder.embed_texts(question_texts)

            # Find duplicate groups
            duplicate_groups, unique_indices = self._find_duplicates(
                questions, embeddings
            )

            # Extract unique questions
            unique_questions = [questions[i] for i in unique_indices]

            # Calculate average similarity
            similarities = []
            for group in duplicate_groups:
                similarities.append(group.similarity_score)

            average_similarity = sum(similarities) / len(similarities) if similarities else 0.0

            result = DeduplicationResult(
                unique_questions=unique_questions,
                duplicate_groups=duplicate_groups,
                total_duplicates_removed=len(questions) - len(unique_questions),
                average_similarity=average_similarity
            )

            self._logger.info(
                f"Deduplicated {len(questions)} questions: "
                f"kept {len(unique_questions)}, "
                f"removed {result.total_duplicates_removed} duplicates"
            )

            return result

        except Exception as e:
            self._logger.error(f"Failed to deduplicate questions: {e}")
            # Return original questions if deduplication fails
            return DeduplicationResult(
                unique_questions=questions,
                duplicate_groups=[],
                total_duplicates_removed=0,
                average_similarity=0.0
            )

    def _find_duplicates(
        self,
        questions: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> Tuple[List[DuplicateGroup], Set[int]]:
        """
        Find duplicate groups and unique question indices.

        Returns:
            Tuple of (duplicate_groups, unique_indices)
        """
        duplicate_groups = []
        processed_indices = set()
        unique_indices = set()

        # Convert embeddings to numpy arrays for efficient computation
        embeddings_array = np.array(embeddings)

        for i, question in enumerate(questions):
            if i in processed_indices:
                continue

            # Find similar questions
            similar_indices = self._find_similar_questions(
                i, embeddings_array, processed_indices
            )

            if similar_indices:
                # Create duplicate group
                group_questions = [questions[j] for j in [i] + similar_indices]

                # Select canonical question (highest quality or earliest)
                canonical_idx = self._select_canonical_question(group_questions)
                canonical_question = group_questions[canonical_idx]

                # Remove canonical from duplicates
                duplicates = [
                    q for j, q in enumerate(group_questions)
                    if j != canonical_idx
                ]

                # Calculate average similarity
                similarities = []
                canonical_emb = embeddings_array[i if canonical_idx == 0 else similar_indices[canonical_idx - 1]]
                for j in ([i] + similar_indices):
                    if j != (i if canonical_idx == 0 else similar_indices[canonical_idx - 1]):
                        sim = self._cosine_similarity(canonical_emb, embeddings_array[j])
                        similarities.append(sim)

                avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

                duplicate_group = DuplicateGroup(
                    canonical_question=canonical_question,
                    duplicates=duplicates,
                    similarity_score=avg_similarity,
                    reason=f"Semantic similarity > {self._similarity_threshold}"
                )

                duplicate_groups.append(duplicate_group)

                # Mark all as processed
                processed_indices.update([i] + similar_indices)
                unique_indices.add(i if canonical_idx == 0 else similar_indices[canonical_idx - 1])
            else:
                # No duplicates found, add to unique
                unique_indices.add(i)

        return duplicate_groups, unique_indices

    def _find_similar_questions(
        self,
        target_idx: int,
        embeddings_array: np.ndarray,
        processed_indices: Set[int]
    ) -> List[int]:
        """Find questions similar to the target question."""
        target_embedding = embeddings_array[target_idx]
        similar_indices = []

        for i, embedding in enumerate(embeddings_array):
            if i == target_idx or i in processed_indices:
                continue

            similarity = self._cosine_similarity(target_embedding, embedding)

            if similarity >= self._similarity_threshold:
                similar_indices.append(i)

        return similar_indices

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 > 0 and norm2 > 0:
            return dot_product / (norm1 * norm2)
        return 0.0

    def _select_canonical_question(self, questions: List[Dict[str, Any]]) -> int:
        """
        Select the canonical question from a group.

        Prefers questions with:
        1. Higher quality scores
        2. More complete content
        3. Earlier creation date
        """
        if len(questions) == 1:
            return 0

        # Score each question
        scores = []
        for question in questions:
            score = 0

            # Quality score (if available)
            quality_score = question.get('quality_score', 0.5)
            score += quality_score * 3

            # Content completeness
            content_length = len(question.get('content', ''))
            score += min(content_length / 1000, 1) * 2

            # Source preference (prefer leetcode over reddit)
            source = question.get('source', 'unknown')
            if source == 'leetcode':
                score += 1
            elif source == 'reddit':
                score += 0.5

            scores.append(score)

        # Return index of highest scoring question
        return scores.index(max(scores))

    def find_similar_questions(
        self,
        target_question: Dict[str, Any],
        question_pool: List[Dict[str, Any]],
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find questions similar to a target question.

        Args:
            target_question: The question to find similarities for
            question_pool: Pool of questions to search in
            top_k: Maximum number of similar questions to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (question, similarity_score) tuples
        """
        if not question_pool:
            return []

        try:
            # Prepare texts
            target_text = f"Title: {target_question['title']}\nContent: {target_question['content']}"
            pool_texts = [
                f"Title: {q['title']}\nContent: {q['content']}"
                for q in question_pool
            ]

            # Embed all texts
            all_texts = [target_text] + pool_texts
            embeddings = self._embedder.embed_texts(all_texts)

            target_embedding = embeddings[0]
            pool_embeddings = embeddings[1:]

            # Calculate similarities
            similarities = []
            for i, embedding in enumerate(pool_embeddings):
                similarity = self._cosine_similarity(target_embedding, embedding)
                if similarity >= min_similarity:
                    similarities.append((question_pool[i], similarity))

            # Sort by similarity (descending) and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            self._logger.error(f"Failed to find similar questions: {e}")
            return []
