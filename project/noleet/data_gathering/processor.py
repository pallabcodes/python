"""Process collected questions and categorize by DSA topics."""

import logging
from typing import List, Dict, Set
from collections import defaultdict

from noleet.core.models import Topic
from noleet.data_gathering.base_scraper import QuestionMetadata


class QuestionProcessor:
    """Process and categorize collected questions by DSA topics."""
    
    TOPIC_KEYWORDS: Dict[Topic, List[str]] = {
        Topic.DYNAMIC_PROGRAMMING: [
            "dp", "dynamic programming", "memoization", "tabulation",
            "optimal substructure", "overlapping subproblems"
        ],
        Topic.SLIDING_WINDOW: [
            "sliding window", "two pointers", "window", "subarray",
            "substring", "contiguous"
        ],
        Topic.MERGE_INTERVALS: [
            "merge intervals", "interval", "overlapping", "meeting rooms",
            "schedule"
        ],
        Topic.TWO_POINTERS: [
            "two pointers", "left right", "start end", "front back"
        ],
        Topic.BINARY_SEARCH: [
            "binary search", "sorted array", "search", "bisect"
        ],
        Topic.GRAPH_TRAVERSAL: [
            "graph", "dfs", "bfs", "depth first", "breadth first",
            "adjacency", "traversal"
        ],
        Topic.TREE_TRAVERSAL: [
            "tree", "binary tree", "bst", "inorder", "preorder",
            "postorder", "traversal"
        ],
        Topic.BACKTRACKING: [
            "backtrack", "recursion", "permutation", "combination"
        ],
        Topic.GREEDY: [
            "greedy", "optimal choice", "local optimum"
        ],
        Topic.UNION_FIND: [
            "union find", "disjoint set", "connected components"
        ],
        Topic.TRIE: [
            "trie", "prefix tree", "autocomplete"
        ],
        Topic.HEAP: [
            "heap", "priority queue", "min heap", "max heap"
        ],
        Topic.HASH_TABLE: [
            "hash", "hashmap", "hashset", "dictionary", "map"
        ],
        Topic.LINKED_LIST: [
            "linked list", "node", "pointer"
        ],
        Topic.STACK: [
            "stack", "lifo", "push pop"
        ],
        Topic.QUEUE: [
            "queue", "fifo", "enqueue", "dequeue"
        ],
        Topic.BIT_MANIPULATION: [
            "bit", "xor", "and", "or", "shift"
        ],
        Topic.SORTING: [
            "sort", "quicksort", "mergesort", "heapsort"
        ],
        Topic.STRING_MATCHING: [
            "string", "pattern", "kmp", "rabin karp"
        ]
    }
    
    def __init__(self) -> None:
        """Initialize question processor."""
        self._logger = logging.getLogger(__name__)
    
    def categorize_questions(
        self,
        questions: List[QuestionMetadata]
    ) -> Dict[Topic, List[QuestionMetadata]]:
        """
        Categorize questions by DSA topics.
        
        Args:
            questions: List of questions to categorize
            
        Returns:
            Dictionary mapping topics to questions
        """
        categorized: Dict[Topic, List[QuestionMetadata]] = defaultdict(list)
        
        for question in questions:
            topics = self._identify_topics(question)
            for topic in topics:
                categorized[topic].append(question)
        
        self._logger.info(
            f"Categorized {len(questions)} questions into {len(categorized)} topics",
            extra={
                "total_questions": len(questions),
                "topic_count": len(categorized),
                "topics": [t.value for t in categorized.keys()]
            }
        )
        
        return dict(categorized)
    
    def _identify_topics(self, question: QuestionMetadata) -> Set[Topic]:
        """
        Identify DSA topics for a question.
        
        Args:
            question: Question metadata
            
        Returns:
            Set of identified topics
        """
        topics: Set[Topic] = set()
        
        content_lower = f"{question.title} {question.content}".lower()
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.add(topic)
        
        for tag in question.tags:
            tag_lower = tag.lower()
            for topic, keywords in self.TOPIC_KEYWORDS.items():
                if any(keyword in tag_lower for keyword in keywords):
                    topics.add(topic)
        
        return topics
    
    def get_topic_statistics(
        self,
        categorized: Dict[Topic, List[QuestionMetadata]]
    ) -> Dict[Topic, int]:
        """
        Get statistics about topic distribution.
        
        Args:
            categorized: Categorized questions
            
        Returns:
            Dictionary mapping topics to question counts
        """
        return {topic: len(questions) for topic, questions in categorized.items()}

