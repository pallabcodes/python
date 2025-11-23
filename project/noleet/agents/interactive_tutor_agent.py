"""Interactive Tutor Agent - Provides real-time coding guidance and DSA explanations."""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from aiframework import AIFramework
from aiframework.types import GenerationRequest


class HintLevel(Enum):
    """Levels of hint specificity."""
    CONCEPTUAL = "conceptual"  # High-level concept explanation
    STRUCTURAL = "structural"  # Code structure guidance
    SPECIFIC = "specific"      # Specific implementation hints
    DETAILED = "detailed"      # Very specific code suggestions


class TutorMode(Enum):
    """Different tutoring interaction modes."""
    QUESTION_ANSWERING = "qa"          # Answer specific questions
    CODE_REVIEW = "review"             # Review and explain code
    DEBUGGING = "debug"                # Help with debugging
    LEARNING_PATH = "path"             # Suggest learning progression
    CONCEPT_EXPLANATION = "concept"    # Explain DSA concepts
    IMPLEMENTATION_GUIDANCE = "guide"  # Guide through implementation


@dataclass
class TutorSession:
    """Represents an active tutoring session."""
    session_id: str
    project_id: str
    user_level: str
    current_topic: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    hint_level: HintLevel = HintLevel.CONCEPTUAL
    questions_asked: Set[str] = field(default_factory=set)
    concepts_explained: Set[str] = field(default_factory=set)
    start_time: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    last_activity: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class TutorContext:
    """Context information for tutoring interactions."""
    user_code: Optional[str] = None
    current_file: Optional[str] = None
    error_message: Optional[str] = None
    question: Optional[str] = None
    project_description: Optional[str] = None
    user_level: str = "intermediate"
    topics: List[str] = field(default_factory=list)
    session: Optional[TutorSession] = None


@dataclass
class TutorResponse:
    """Response from the tutor agent."""
    answer: str
    hint_level: HintLevel
    suggestions: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    code_examples: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    mode: TutorMode = TutorMode.QUESTION_ANSWERING


class InteractiveTutorAgent:
    """AI agent that provides interactive tutoring during DSA project implementation."""

    def __init__(self, ai_framework: AIFramework):
        """
        Initialize the Interactive Tutor Agent.

        Args:
            ai_framework: AI Framework instance for content generation
        """
        self._ai_framework = ai_framework
        self._logger = logging.getLogger(__name__)

        # Session management
        self._active_sessions: Dict[str, TutorSession] = {}

        # DSA knowledge base
        self._dsa_concepts = self._load_dsa_concepts()
        self._algorithm_patterns = self._load_algorithm_patterns()

    def _load_dsa_concepts(self) -> Dict[str, Dict[str, Any]]:
        """Load DSA concepts knowledge base."""
        return {
            "dynamic_programming": {
                "description": "Solving complex problems by breaking them down into simpler subproblems",
                "key_principles": ["Optimal substructure", "Overlapping subproblems", "Memoization vs Tabulation"],
                "common_patterns": ["Top-down with memoization", "Bottom-up tabulation", "Space optimization"],
                "difficulty_level": "intermediate"
            },
            "arrays": {
                "description": "Fundamental data structure for storing elements of same type",
                "key_principles": ["Contiguous memory", "Fixed size", "Random access"],
                "common_operations": ["Traversal", "Searching", "Sorting", "Modification"],
                "difficulty_level": "beginner"
            },
            "linked_lists": {
                "description": "Linear data structure with nodes connected by pointers",
                "key_principles": ["Node structure", "Head/tail pointers", "Traversal mechanics"],
                "common_patterns": ["Sentinel nodes", "Fast/slow pointers", "Reversal techniques"],
                "difficulty_level": "beginner"
            },
            "trees": {
                "description": "Hierarchical data structure with parent-child relationships",
                "key_principles": ["Root node", "Parent-child relationships", "Traversal orders"],
                "common_patterns": ["DFS/BFS", "Binary search trees", "Balanced trees"],
                "difficulty_level": "intermediate"
            },
            "graphs": {
                "description": "Data structure representing relationships between entities",
                "key_principles": ["Vertices and edges", "Directed/undirected", "Weighted/unweighted"],
                "common_patterns": ["Adjacency lists/matrices", "Traversal algorithms", "Shortest paths"],
                "difficulty_level": "intermediate"
            },
            "sorting": {
                "description": "Arranging elements in a specific order",
                "key_principles": ["Comparison-based vs non-comparison", "Stability", "In-place sorting"],
                "common_algorithms": ["Quick sort", "Merge sort", "Heap sort", "Insertion sort"],
                "difficulty_level": "beginner"
            },
            "searching": {
                "description": "Finding elements within data structures",
                "key_principles": ["Linear vs binary search", "Hashing", "Tree-based search"],
                "common_patterns": ["Binary search on arrays", "Hash tables", "Trie structures"],
                "difficulty_level": "beginner"
            }
        }

    def _load_algorithm_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common algorithm implementation patterns."""
        return {
            "two_pointers": {
                "description": "Using two pointers to traverse arrays efficiently",
                "use_cases": ["Finding pairs with sum", "Removing duplicates", "Container problems"],
                "complexity": "O(n) time, O(1) space",
                "key_insights": ["Opposite direction movement", "Same direction with different speeds"]
            },
            "sliding_window": {
                "description": "Maintaining a window of elements for subarray problems",
                "use_cases": ["Maximum subarray sum", "Longest substring", "Minimum window"],
                "complexity": "O(n) time, O(1) space",
                "key_insights": ["Window expansion/contraction", "Tracking window properties"]
            },
            "binary_search": {
                "description": "Efficiently finding elements in sorted arrays",
                "use_cases": ["Finding target values", "Finding boundaries", "Optimization problems"],
                "complexity": "O(log n) time",
                "key_insights": ["Sorted requirement", "Mid calculation", "Search space reduction"]
            },
            "dfs_backtracking": {
                "description": "Exploring all possible solutions with pruning",
                "use_cases": ["Permutations", "Combinations", "Maze solving", "N-Queens"],
                "complexity": "Exponential in worst case",
                "key_insights": ["State representation", "Base cases", "Pruning conditions"]
            },
            "greedy_algorithms": {
                "description": "Making locally optimal choices at each step",
                "use_cases": ["Coin change", "Activity selection", "Huffman coding"],
                "complexity": "Varies by problem",
                "key_insights": ["Optimal substructure", "Greedy choice property", "Proof of correctness"]
            }
        }

    async def start_session(
        self,
        project_id: str,
        user_level: str,
        topics: List[str]
    ) -> str:
        """
        Start a new tutoring session.

        Args:
            project_id: ID of the project being worked on
            user_level: User's skill level (beginner/intermediate/advanced)
            topics: DSA topics being covered

        Returns:
            Session ID for the new tutoring session
        """
        session_id = f"tutor_session_{project_id}_{int(asyncio.get_event_loop().time())}"

        session = TutorSession(
            session_id=session_id,
            project_id=project_id,
            user_level=user_level,
            current_topic=topics[0] if topics else "general",
            conversation_history=[]
        )

        self._active_sessions[session_id] = session

        self._logger.info(f"Started tutoring session {session_id} for project {project_id}")
        return session_id

    async def end_session(self, session_id: str) -> None:
        """
        End a tutoring session.

        Args:
            session_id: ID of the session to end
        """
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            duration = asyncio.get_event_loop().time() - session.start_time
            self._logger.info(
                f"Ended tutoring session {session_id} after {duration:.1f} seconds, "
                f"{len(session.conversation_history)} interactions"
            )
            del self._active_sessions[session_id]

    async def provide_guidance(
        self,
        context: TutorContext,
        mode: TutorMode = TutorMode.QUESTION_ANSWERING
    ) -> TutorResponse:
        """
        Provide tutoring guidance based on context.

        Args:
            context: Current tutoring context
            mode: Type of tutoring interaction requested

        Returns:
            Structured tutoring response
        """
        try:
            # Determine the appropriate hint level based on user progress
            hint_level = self._determine_hint_level(context)

            # Generate response based on mode
            if mode == TutorMode.QUESTION_ANSWERING:
                response = await self._answer_question(context, hint_level)
            elif mode == TutorMode.CODE_REVIEW:
                response = await self._review_code(context, hint_level)
            elif mode == TutorMode.DEBUGGING:
                response = await self._help_debug(context, hint_level)
            elif mode == TutorMode.CONCEPT_EXPLANATION:
                response = await self._explain_concept(context, hint_level)
            elif mode == TutorMode.IMPLEMENTATION_GUIDANCE:
                response = await self._guide_implementation(context, hint_level)
            elif mode == TutorMode.LEARNING_PATH:
                response = await self._suggest_learning_path(context, hint_level)
            else:
                response = await self._provide_general_guidance(context, hint_level)

            # Update session history if session exists
            if context.session:
                self._update_session_history(context.session, context.question or "", response.answer)

            return response

        except Exception as e:
            self._logger.error(f"Error providing guidance: {e}")
            return TutorResponse(
                answer="I apologize, but I'm having trouble providing guidance right now. Please try rephrasing your question or check your code for syntax errors.",
                hint_level=HintLevel.CONCEPTUAL,
                confidence_score=0.5
            )

    def _determine_hint_level(self, context: TutorContext) -> HintLevel:
        """Determine appropriate hint level based on context."""
        if not context.session:
            return HintLevel.CONCEPTUAL

        session = context.session

        # Beginner users get more guidance
        if session.user_level == "beginner":
            return HintLevel.STRUCTURAL
        elif session.user_level == "intermediate":
            return HintLevel.SPECIFIC
        else:  # advanced
            return HintLevel.DETAILED

    async def _answer_question(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Answer a specific question about DSA concepts or implementation."""

        if not context.question:
            return TutorResponse(
                answer="I'd be happy to help! What specific question do you have about your DSA implementation?",
                hint_level=hint_level
            )

        question = context.question.lower()

        # Check if it's a concept explanation request
        for concept, info in self._dsa_concepts.items():
            if concept in question:
                return await self._explain_concept(context, hint_level)

        # Check if it's about algorithm patterns
        for pattern, info in self._algorithm_patterns.items():
            if pattern.replace("_", " ") in question or pattern in question:
                return await self._explain_pattern(context, pattern, hint_level)

        # General question answering
        prompt = f"""
You are an expert DSA tutor helping a {context.user_level} level developer.

Question: {context.question}

Project Context: {context.project_description or 'General DSA implementation'}
Topics: {', '.join(context.topics)}

Provide a helpful, educational answer that:
1. Directly addresses the question
2. Includes relevant code examples where appropriate
3. Explains concepts at the right level for a {context.user_level} developer
4. Suggests related concepts to explore
5. Offers next steps or practice suggestions

Keep the answer focused and actionable.
"""

        request = GenerationRequest(
            prompt=prompt,
            max_tokens=600,
            temperature=0.3
        )

        response = await self._ai_framework.generate(request)

        return TutorResponse(
            answer=response.content.strip(),
            hint_level=hint_level,
            mode=TutorMode.QUESTION_ANSWERING,
            related_concepts=self._extract_related_concepts(context.question)
        )

    async def _explain_concept(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Explain a DSA concept in detail."""

        # Find the concept in our knowledge base
        concept = None
        for c, info in self._dsa_concepts.items():
            if c in (context.question or "").lower() or c in " ".join(context.topics):
                concept = c
                break

        if not concept:
            return await self._answer_question(context, hint_level)

        info = self._dsa_concepts[concept]

        # Adjust explanation based on user level and hint level
        if context.user_level == "beginner":
            explanation = await self._generate_beginner_explanation(concept, info)
        elif context.user_level == "intermediate":
            explanation = await self._generate_intermediate_explanation(concept, info)
        else:
            explanation = await self._generate_advanced_explanation(concept, info)

        return TutorResponse(
            answer=explanation,
            hint_level=hint_level,
            mode=TutorMode.CONCEPT_EXPLANATION,
            related_concepts=info.get("key_principles", []),
            code_examples=[f"Example: {concept.replace('_', ' ').title()} implementation patterns"]
        )

    async def _generate_beginner_explanation(self, concept: str, info: Dict[str, Any]) -> str:
        """Generate beginner-friendly concept explanation."""
        prompt = f"""
Explain the DSA concept "{concept.replace('_', ' ')}" to a complete beginner.

Concept info: {info}

Provide a simple, clear explanation that:
1. Uses everyday analogies
2. Avoids complex terminology initially
3. Includes a simple example
4. Shows why this concept is useful
5. Suggests easy practice problems

Keep it encouraging and accessible.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=400, temperature=0.2)
        response = await self._ai_framework.generate(request)
        return response.content.strip()

    async def _generate_intermediate_explanation(self, concept: str, info: Dict[str, Any]) -> str:
        """Generate intermediate-level concept explanation."""
        prompt = f"""
Explain the DSA concept "{concept.replace('_', ' ')}" to an intermediate developer.

Concept info: {info}

Provide a detailed explanation that:
1. Covers key principles and patterns
2. Includes time/space complexity considerations
3. Shows common implementation approaches
4. Discusses trade-offs and use cases
5. Provides practical implementation tips

Be technical but accessible.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=500, temperature=0.3)
        response = await self._ai_framework.generate(request)
        return response.content.strip()

    async def _generate_advanced_explanation(self, concept: str, info: Dict[str, Any]) -> str:
        """Generate advanced-level concept explanation."""
        prompt = f"""
Provide an advanced explanation of "{concept.replace('_', ' ')}" for experienced developers.

Concept info: {info}

Cover:
1. Theoretical foundations and proofs
2. Advanced optimization techniques
3. Edge cases and pathological scenarios
4. Research-level insights and recent developments
5. Performance characteristics and benchmarking

Be rigorous and technically deep.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=600, temperature=0.4)
        response = await self._ai_framework.generate(request)
        return response.content.strip()

    async def _review_code(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Review and explain user code."""

        if not context.user_code:
            return TutorResponse(
                answer="I'd love to review your code! Please share the code you'd like me to look at.",
                hint_level=hint_level,
                mode=TutorMode.CODE_REVIEW
            )

        prompt = f"""
Review this DSA implementation code for a {context.user_level} developer:

```python
{context.user_code}
```

Project Context: {context.project_description or 'General DSA problem'}
Topics: {', '.join(context.topics)}

Provide a constructive code review that:
1. Identifies algorithmic correctness
2. Comments on code structure and readability
3. Suggests improvements or optimizations
4. Explains what the code is doing conceptually
5. Offers learning insights

Be encouraging and educational rather than just critical.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=500, temperature=0.3)
        response = await self._ai_framework.generate(request)

        return TutorResponse(
            answer=response.content.strip(),
            hint_level=hint_level,
            mode=TutorMode.CODE_REVIEW,
            suggestions=["Consider edge cases", "Add input validation", "Optimize time/space complexity"],
            next_steps=["Test with various inputs", "Compare with optimal solution", "Refactor for clarity"]
        )

    async def _help_debug(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Help debug code issues."""

        debug_context = ""
        if context.user_code:
            debug_context += f"\nCode:\n```python\n{context.user_code}\n```"
        if context.error_message:
            debug_context += f"\nError: {context.error_message}"

        prompt = f"""
Help debug this DSA code issue for a {context.user_level} developer:

{debug_context}

Project: {context.project_description or 'General DSA problem'}
Topics: {', '.join(context.topics)}

Provide debugging guidance that:
1. Identifies the likely cause of the issue
2. Explains what's happening in the code
3. Suggests specific fixes
4. Offers debugging strategies
5. Provides learning insights about the problem

Be methodical and educational.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=500, temperature=0.3)
        response = await self._ai_framework.generate(request)

        return TutorResponse(
            answer=response.content.strip(),
            hint_level=hint_level,
            mode=TutorMode.DEBUGGING,
            suggestions=["Add print statements", "Check edge cases", "Verify algorithm logic"],
            next_steps=["Fix the identified issue", "Test thoroughly", "Understand why it failed"]
        )

    async def _guide_implementation(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Guide through implementation steps."""

        prompt = f"""
Guide a {context.user_level} developer through implementing: {context.project_description or 'this DSA problem'}

Current Context: {context.user_code or 'Just starting'}
Topics: {', '.join(context.topics)}
Hint Level: {hint_level.value}

Provide implementation guidance that:
1. Breaks down the problem into steps
2. Suggests the right approach for their skill level
3. Offers pseudocode or high-level structure
4. Explains key decision points
5. Suggests what to implement next

Match the guidance level to their experience.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=500, temperature=0.4)
        response = await self._ai_framework.generate(request)

        return TutorResponse(
            answer=response.content.strip(),
            hint_level=hint_level,
            mode=TutorMode.IMPLEMENTATION_GUIDANCE,
            next_steps=["Implement the suggested approach", "Test incrementally", "Debug as you go"],
            code_examples=["Pseudocode structure", "Key algorithm components"]
        )

    async def _suggest_learning_path(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Suggest learning progression and next steps."""

        prompt = f"""
Suggest a learning path for a {context.user_level} developer working on: {context.project_description or 'DSA projects'}

Current Topics: {', '.join(context.topics)}
Current Progress: Working on implementation

Provide learning path suggestions that:
1. Recommend next projects to build upon this one
2. Suggest related concepts to explore
3. Offer practice problems of increasing difficulty
4. Recommend resources for further learning
5. Suggest milestones to track progress

Tailor to their skill level and interests.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=400, temperature=0.3)
        response = await self._ai_framework.generate(request)

        return TutorResponse(
            answer=response.content.strip(),
            hint_level=hint_level,
            mode=TutorMode.LEARNING_PATH,
            related_concepts=self._suggest_related_concepts(context.topics),
            next_steps=["Complete current project", "Tackle suggested next project", "Explore related concepts"]
        )

    def _extract_related_concepts(self, question: str) -> List[str]:
        """Extract related concepts from a question."""
        related = []
        question_lower = question.lower()

        # Simple keyword matching for related concepts
        concept_keywords = {
            "time complexity": ["Big O notation", "algorithm analysis", "performance optimization"],
            "space complexity": ["memory usage", "in-place algorithms", "space-time tradeoff"],
            "recursion": ["base cases", "recursive calls", "stack overflow", "memoization"],
            "iteration": ["loops", "while statements", "for loops", "efficiency"],
            "data structures": ["arrays", "linked lists", "stacks", "queues", "trees", "graphs"],
            "algorithms": ["sorting", "searching", "dynamic programming", "greedy", "divide and conquer"]
        }

        for keyword, concepts in concept_keywords.items():
            if keyword in question_lower:
                related.extend(concepts)

        return list(set(related))[:3]  # Return up to 3 unique concepts

    def _suggest_related_concepts(self, topics: List[str]) -> List[str]:
        """Suggest concepts related to current topics."""
        concept_map = {
            "arrays": ["two pointers", "sliding window", "prefix sums"],
            "dynamic_programming": ["memoization", "tabulation", "optimal substructure"],
            "trees": ["binary search trees", "tree traversal", "balanced trees"],
            "graphs": ["DFS", "BFS", "shortest paths", "topological sort"],
            "sorting": ["comparison sorts", "stable sorting", "in-place sorting"],
            "searching": ["binary search", "hash tables", "ternary search"]
        }

        related = []
        for topic in topics:
            if topic in concept_map:
                related.extend(concept_map[topic])

        return list(set(related))[:5]

    def _update_session_history(self, session: TutorSession, question: str, answer: str) -> None:
        """Update session conversation history."""
        session.conversation_history.append({
            "timestamp": asyncio.get_event_loop().time(),
            "question": question,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer
        })
        session.last_activity = asyncio.get_event_loop().time()

        # Keep only last 10 interactions
        if len(session.conversation_history) > 10:
            session.conversation_history = session.conversation_history[-10:]

    async def _provide_general_guidance(
        self,
        context: TutorContext,
        hint_level: HintLevel
    ) -> TutorResponse:
        """Provide general guidance when mode is unclear."""

        prompt = f"""
Provide helpful guidance for a {context.user_level} developer working on a DSA project.

Context:
- Project: {context.project_description or 'General DSA implementation'}
- Topics: {', '.join(context.topics)}
- Current Code: {context.user_code[:200] + '...' if context.user_code and len(context.user_code) > 200 else context.user_code or 'Not provided'}
- Question: {context.question or 'General guidance requested'}

Offer encouraging, actionable advice that helps them move forward with their implementation.
"""

        request = GenerationRequest(prompt=prompt, max_tokens=300, temperature=0.4)
        response = await self._ai_framework.generate(request)

        return TutorResponse(
            answer=response.content.strip(),
            hint_level=hint_level,
            suggestions=["Break down the problem", "Start with pseudocode", "Test incrementally"],
            next_steps=["Implement core logic", "Add edge case handling", "Optimize performance"]
        )
