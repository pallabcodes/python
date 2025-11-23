"""Code Review Agent - Provides algorithmic correctness analysis and educational feedback."""

import asyncio
import logging
import ast
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from aiframework import AIFramework
from aiframework.types import GenerationRequest


class ReviewSeverity(Enum):
    """Severity levels for code review issues."""
    CRITICAL = "critical"    # Algorithm completely wrong, will crash
    MAJOR = "major"         # Significant logic errors, wrong results
    MINOR = "minor"         # Performance issues, style problems
    INFO = "info"          # Suggestions for improvement, best practices


class ReviewCategory(Enum):
    """Categories of code review feedback."""
    CORRECTNESS = "correctness"          # Algorithm logic and correctness
    EFFICIENCY = "efficiency"            # Time/space complexity optimization
    STYLE = "style"                      # Code readability and conventions
    DSA_PATTERNS = "dsa_patterns"        # Proper use of DSA concepts
    EDGE_CASES = "edge_cases"            # Handling of edge cases
    TESTING = "testing"                  # Test coverage and validation


@dataclass
class CodeReviewIssue:
    """Represents a single code review issue."""
    category: ReviewCategory
    severity: ReviewSeverity
    title: str
    description: str
    code_location: Optional[str] = None  # Line number or function name
    suggestion: str = ""
    dsa_concept: Optional[str] = None  # Related DSA concept
    learning_insight: str = ""  # Educational explanation
    code_example: Optional[str] = None  # Corrected code example


@dataclass
class CodeReviewResult:
    """Complete code review analysis."""
    overall_score: float  # 0-100 score
    grade: str  # A, B, C, D, F
    summary: str
    strengths: List[str] = field(default_factory=list)
    issues: List[CodeReviewIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    learning_points: List[str] = field(default_factory=list)
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    confidence_score: float = 1.0  # How confident the AI is in this analysis


@dataclass
class CodeReviewContext:
    """Context for code review analysis."""
    code: str
    language: str = "python"
    project_description: Optional[str] = None
    user_level: str = "intermediate"
    topics: List[str] = field(default_factory=list)
    expected_algorithm: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    previous_reviews: Optional[List[CodeReviewResult]] = None


class CodeReviewAgent:
    """AI agent that provides comprehensive code review for DSA implementations."""

    def __init__(self, ai_framework: AIFramework):
        """
        Initialize the Code Review Agent.

        Args:
            ai_framework: AI Framework for code analysis
        """
        self._ai_framework = ai_framework
        self._logger = logging.getLogger(__name__)

        # DSA-specific knowledge base
        self._dsa_patterns = self._load_dsa_patterns()
        self._common_mistakes = self._load_common_mistakes()
        self._complexity_indicators = self._load_complexity_indicators()

    def _load_dsa_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load DSA pattern recognition rules."""
        return {
            "two_pointers": {
                "indicators": ["i += 1", "j -= 1", "left", "right", "while.*i.*j"],
                "complexity": "O(n)",
                "description": "Two pointers moving towards each other"
            },
            "sliding_window": {
                "indicators": ["window", "left.*=.*right", "max.*window", "min.*window"],
                "complexity": "O(n)",
                "description": "Maintains window of elements for subarray problems"
            },
            "binary_search": {
                "indicators": ["mid.*=.*left.*right", "while.*left.*<=.*right", "low", "high"],
                "complexity": "O(log n)",
                "description": "Divide and conquer search in sorted array"
            },
            "dynamic_programming": {
                "indicators": ["dp.*=", "memo", "cache", "tabulation"],
                "complexity": "Varies",
                "description": "Solving complex problems by breaking into subproblems"
            },
            "dfs_backtracking": {
                "indicators": ["def.*dfs", "backtrack", "recursion", "visited"],
                "complexity": "Exponential",
                "description": "Exploring all possible solutions with pruning"
            },
            "greedy": {
                "indicators": ["max.*", "min.*", "sort.*", "priority"],
                "complexity": "Varies",
                "description": "Making locally optimal choices"
            }
        }

    def _load_common_mistakes(self) -> Dict[str, Dict[str, Any]]:
        """Load common DSA implementation mistakes."""
        return {
            "off_by_one": {
                "pattern": r"range\(len\([^)]+\)\)",
                "description": "Off-by-one errors in array indexing",
                "severity": ReviewSeverity.MAJOR,
                "fix": "Check array bounds and loop conditions"
            },
            "missing_base_case": {
                "pattern": r"def.*recursion.*:",
                "description": "Recursive function missing base case",
                "severity": ReviewSeverity.CRITICAL,
                "fix": "Add proper base case to prevent infinite recursion"
            },
            "inefficient_nested_loops": {
                "pattern": r"for.*in.*:\s*for.*in.*:",
                "description": "Nested loops creating O(n²) complexity unnecessarily",
                "severity": ReviewSeverity.MAJOR,
                "fix": "Consider using hash maps, sorting, or two-pointer techniques"
            },
            "unnecessary_sorting": {
                "pattern": r"\.sort\(\)",
                "description": "Unnecessary sorting when other approaches exist",
                "severity": ReviewSeverity.MINOR,
                "fix": "Consider hash maps or other data structures"
            },
            "mutable_defaults": {
                "pattern": r"def.*=.*\[\]",
                "description": "Mutable default arguments",
                "severity": ReviewSeverity.MINOR,
                "fix": "Use None as default and create new list inside function"
            }
        }

    def _load_complexity_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Load complexity analysis indicators."""
        return {
            "O(1)": ["constant", "single operation"],
            "O(log n)": ["binary search", "divide and conquer", "tree height"],
            "O(n)": ["single loop", "linear traversal"],
            "O(n log n)": ["sorting", "divide and conquer with linear work"],
            "O(n²)": ["nested loops", "bubble sort", "insertion sort"],
            "O(2^n)": ["exponential", "subsets", "combinations"],
            "O(n!)": ["permutations", "brute force arrangements"]
        }

    async def review_code(
        self,
        context: CodeReviewContext
    ) -> CodeReviewResult:
        """
        Perform comprehensive code review analysis.

        Args:
            context: Code review context with code and metadata

        Returns:
            Complete code review result with analysis and feedback
        """
        try:
            self._logger.info(f"Starting code review for {len(context.code)} characters of code")

            # Perform multi-stage analysis
            static_analysis = await self._static_code_analysis(context)
            algorithmic_analysis = await self._algorithmic_correctness_analysis(context)
            efficiency_analysis = await self._efficiency_analysis(context)
            educational_analysis = await self._educational_feedback_analysis(context)

            # Combine all analyses
            all_issues = (static_analysis + algorithmic_analysis +
                         efficiency_analysis + educational_analysis)

            # Calculate overall score
            overall_score, grade = self._calculate_overall_score(all_issues, context)

            # Generate summary and recommendations
            summary = await self._generate_review_summary(context, overall_score, all_issues)
            strengths = self._identify_strengths(context, all_issues)
            suggestions = self._generate_suggestions(all_issues, context)
            learning_points = self._extract_learning_points(all_issues, context)

            # Estimate complexity if not already done
            time_complexity, space_complexity = await self._estimate_complexity(context)

            result = CodeReviewResult(
                overall_score=overall_score,
                grade=grade,
                summary=summary,
                strengths=strengths,
                issues=all_issues,
                suggestions=suggestions,
                learning_points=learning_points,
                time_complexity=time_complexity,
                space_complexity=space_complexity,
                confidence_score=0.85  # AI confidence in analysis
            )

            self._logger.info(f"Code review completed with score {overall_score:.1f} ({grade})")
            return result

        except Exception as e:
            self._logger.error(f"Error during code review: {e}")
            return CodeReviewResult(
                overall_score=50.0,
                grade="C",
                summary="Code review encountered an error. Please check your code syntax and try again.",
                issues=[],
                confidence_score=0.0
            )

    async def _static_code_analysis(
        self,
        context: CodeReviewContext
    ) -> List[CodeReviewIssue]:
        """Perform static analysis of code for common issues."""
        issues = []

        if context.language.lower() == "python":
            issues.extend(self._analyze_python_code(context.code))

        # Check for common DSA mistakes
        for mistake_name, mistake_info in self._common_mistakes.items():
            if re.search(mistake_info["pattern"], context.code, re.MULTILINE):
                issues.append(CodeReviewIssue(
                    category=ReviewCategory.CORRECTNESS,
                    severity=mistake_info["severity"],
                    title=f"Potential {mistake_name.replace('_', ' ')}",
                    description=mistake_info["description"],
                    suggestion=mistake_info["fix"],
                    learning_insight=f"Understanding and avoiding {mistake_name.replace('_', ' ')} is crucial for reliable DSA implementations."
                ))

        return issues

    def _analyze_python_code(self, code: str) -> List[CodeReviewIssue]:
        """Analyze Python code for common issues."""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [CodeReviewIssue(
                category=ReviewCategory.CORRECTNESS,
                severity=ReviewSeverity.CRITICAL,
                title="Syntax Error",
                description=f"Code contains syntax error: {e.msg}",
                code_location=f"Line {e.lineno}",
                suggestion="Fix the syntax error before proceeding with algorithmic analysis.",
                learning_insight="Syntax errors prevent code execution. Always check for proper Python syntax."
            )]

        # Check for common Python DSA issues
        issues.extend(self._check_function_structure(tree))
        issues.extend(self._check_variable_naming(tree))
        issues.extend(self._check_error_handling(tree))

        return issues

    def _check_function_structure(self, tree: ast.AST) -> List[CodeReviewIssue]:
        """Check function structure and organization."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for missing docstrings
                if not ast.get_docstring(node):
                    issues.append(CodeReviewIssue(
                        category=ReviewCategory.STYLE,
                        severity=ReviewSeverity.INFO,
                        title="Missing Docstring",
                        description=f"Function '{node.name}' lacks a docstring",
                        code_location=f"def {node.name}",
                        suggestion="Add a docstring explaining the function's purpose, parameters, and return value.",
                        learning_insight="Good documentation helps others understand your code and improves maintainability."
                    ))

                # Check function length (simple heuristic)
                if len(node.body) > 20:
                    issues.append(CodeReviewIssue(
                        category=ReviewCategory.STYLE,
                        severity=ReviewSeverity.MINOR,
                        title="Long Function",
                        description=f"Function '{node.name}' is quite long ({len(node.body)} statements)",
                        code_location=f"def {node.name}",
                        suggestion="Consider breaking this function into smaller, more focused functions.",
                        learning_insight="Shorter functions are easier to understand, test, and maintain."
                    ))

        return issues

    def _check_variable_naming(self, tree: ast.AST) -> List[CodeReviewIssue]:
        """Check variable naming conventions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                # Check for single-letter variable names (except loop variables)
                if len(node.id) == 1 and node.id not in ['i', 'j', 'k', 'x', 'y', 'n']:
                    issues.append(CodeReviewIssue(
                        category=ReviewCategory.STYLE,
                        severity=ReviewSeverity.INFO,
                        title="Unclear Variable Name",
                        description=f"Single-letter variable name '{node.id}' makes code hard to understand",
                        code_location=node.id,
                        suggestion="Use descriptive variable names that explain the variable's purpose.",
                        learning_insight="Clear variable names make your code self-documenting and easier to debug."
                    ))

        return issues

    def _check_error_handling(self, tree: ast.AST) -> List[CodeReviewIssue]:
        """Check for proper error handling."""
        issues = []

        # Look for potential index errors
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                # This is a simplified check - could be enhanced
                issues.append(CodeReviewIssue(
                    category=ReviewCategory.EDGE_CASES,
                    severity=ReviewSeverity.MINOR,
                    title="Potential Index Error",
                    description="Array/list access without bounds checking",
                    suggestion="Add bounds checking or handle IndexError exceptions.",
                    learning_insight="Always validate array indices to prevent runtime errors."
                ))
                break  # Only report once

        return issues

    async def _algorithmic_correctness_analysis(
        self,
        context: CodeReviewContext
    ) -> List[CodeReviewIssue]:
        """Analyze algorithmic correctness using AI."""
        if not context.code.strip():
            return []

        prompt = f"""
Analyze this DSA implementation for algorithmic correctness. Focus on:

1. **Algorithm Logic**: Is the core algorithm implemented correctly?
2. **Problem Solving**: Does it solve the intended problem?
3. **Edge Cases**: How does it handle edge cases?
4. **Correctness Proof**: Can you verify the algorithm's correctness?

Code to analyze:
```python
{context.code}
```

Context:
- Topics: {', '.join(context.topics)}
- Expected Algorithm: {context.expected_algorithm or 'General DSA problem'}
- User Level: {context.user_level}

Provide specific feedback on algorithmic correctness. If there are errors, explain what's wrong and how to fix it. If correct, acknowledge the good algorithmic thinking.

Focus on the algorithm logic, not code style.
"""

        try:
            request = GenerationRequest(
                prompt=prompt,
                max_tokens=600,
                temperature=0.2  # Low temperature for factual analysis
            )

            response = await self._ai_framework.generate(request)
            analysis = response.content.strip()

            # Parse the AI analysis into structured issues
            return self._parse_algorithm_analysis(analysis, context)

        except Exception as e:
            self._logger.error(f"Error in algorithmic analysis: {e}")
            return []

    def _parse_algorithm_analysis(
        self,
        analysis: str,
        context: CodeReviewContext
    ) -> List[CodeReviewIssue]:
        """Parse AI algorithmic analysis into structured issues."""
        issues = []

        # Simple parsing - could be enhanced with more sophisticated NLP
        analysis_lower = analysis.lower()

        if "correct" in analysis_lower and "logic" in analysis_lower:
            # Algorithm appears correct
            issues.append(CodeReviewIssue(
                category=ReviewCategory.CORRECTNESS,
                severity=ReviewSeverity.INFO,
                title="Algorithm Logic Appears Correct",
                description="The core algorithmic approach seems sound based on the analysis.",
                learning_insight="Good algorithmic thinking! Continue refining the implementation details."
            ))
        elif "error" in analysis_lower or "wrong" in analysis_lower or "incorrect" in analysis_lower:
            # Algorithm has issues
            issues.append(CodeReviewIssue(
                category=ReviewCategory.CORRECTNESS,
                severity=ReviewSeverity.MAJOR,
                title="Algorithmic Logic Issue",
                description="The algorithm analysis detected potential logic errors.",
                suggestion="Review the algorithmic approach and verify it solves the problem correctly.",
                learning_insight="Algorithmic correctness is the foundation. Double-check your problem-solving approach."
            ))

        # Add the detailed analysis as additional context
        issues.append(CodeReviewIssue(
            category=ReviewCategory.CORRECTNESS,
            severity=ReviewSeverity.INFO,
            title="Detailed Algorithm Analysis",
            description=analysis[:300] + "..." if len(analysis) > 300 else analysis,
            learning_insight="Study algorithmic analysis to improve your problem-solving skills."
        ))

        return issues

    async def _efficiency_analysis(
        self,
        context: CodeReviewContext
    ) -> List[CodeReviewIssue]:
        """Analyze code efficiency and complexity."""
        issues = []

        # Analyze loops and nested structures
        loop_count = len(re.findall(r'\bfor\b|\bwhile\b', context.code))
        nested_loop_count = len(re.findall(r'(\s+)for.*:\s*\n\1\s*for', context.code))

        if nested_loop_count > 0:
            issues.append(CodeReviewIssue(
                category=ReviewCategory.EFFICIENCY,
                severity=ReviewSeverity.MINOR,
                title="Nested Loops Detected",
                description=f"Found {nested_loop_count} nested loop(s) which may create O(n²) complexity",
                suggestion="Consider optimization techniques like hash maps, sorting, or two-pointer approaches.",
                learning_insight="Understanding time complexity helps you choose the most efficient algorithmic approach."
            ))

        # Check for obvious inefficiencies
        if "sort()" in context.code and loop_count > 1:
            issues.append(CodeReviewIssue(
                category=ReviewCategory.EFFICIENCY,
                severity=ReviewSeverity.MINOR,
                title="Potential Sorting Optimization",
                description="Sorting followed by loops may indicate optimization opportunities",
                suggestion="Consider if sorting is necessary, or if a different data structure would be more efficient.",
                learning_insight="Sorting has O(n log n) complexity - sometimes you can avoid it with clever algorithms."
            ))

        return issues

    async def _educational_feedback_analysis(
        self,
        context: CodeReviewContext
    ) -> List[CodeReviewIssue]:
        """Provide educational feedback and learning insights."""
        issues = []

        # Analyze DSA pattern usage
        pattern_usage = self._analyze_pattern_usage(context.code)

        if pattern_usage:
            for pattern_name, usage_info in pattern_usage.items():
                if usage_info["correct"]:
                    issues.append(CodeReviewIssue(
                        category=ReviewCategory.DSA_PATTERNS,
                        severity=ReviewSeverity.INFO,
                        title=f"Good Use of {pattern_name.replace('_', ' ').title()}",
                        description=f"Correctly implemented {usage_info['description']}",
                        suggestion="Continue practicing this pattern - you're using it well!",
                        dsa_concept=pattern_name,
                        learning_insight=f"Mastering {pattern_name.replace('_', ' ')} will help you solve many similar problems efficiently."
                    ))
                else:
                    issues.append(CodeReviewIssue(
                        category=ReviewCategory.DSA_PATTERNS,
                        severity=ReviewSeverity.MINOR,
                        title=f"{pattern_name.replace('_', ' ').title()} Pattern Usage",
                        description=f"Potential improvement in {usage_info['description']} implementation",
                        suggestion="Review the standard implementation of this pattern.",
                        dsa_concept=pattern_name,
                        learning_insight=f"Understanding {pattern_name.replace('_', ' ')} deeply will unlock many algorithmic solutions."
                    ))

        # Add general educational feedback
        issues.append(CodeReviewIssue(
            category=ReviewCategory.TESTING,
            severity=ReviewSeverity.INFO,
            title="Testing Recommendation",
            description="Consider adding more test cases, especially edge cases",
            suggestion="Test with empty arrays, single elements, and boundary conditions.",
            learning_insight="Comprehensive testing builds confidence in your algorithmic solutions."
        ))

        return issues

    def _analyze_pattern_usage(self, code: str) -> Dict[str, Dict[str, Any]]:
        """Analyze usage of DSA patterns in code."""
        pattern_usage = {}

        for pattern_name, pattern_info in self._dsa_patterns.items():
            indicators = pattern_info["indicators"]
            matches = sum(1 for indicator in indicators if indicator.lower() in code.lower())

            if matches > 0:
                # Simple correctness heuristic - could be enhanced
                correct = matches >= len(indicators) * 0.5  # At least half the indicators
                pattern_usage[pattern_name] = {
                    "description": pattern_info["description"],
                    "correct": correct,
                    "matches": matches,
                    "complexity": pattern_info["complexity"]
                }

        return pattern_usage

    def _calculate_overall_score(
        self,
        issues: List[CodeReviewIssue],
        context: CodeReviewContext
    ) -> Tuple[float, str]:
        """Calculate overall code review score."""
        base_score = 85.0  # Start with B grade

        # Deduct points for issues
        severity_penalties = {
            ReviewSeverity.CRITICAL: -25,
            ReviewSeverity.MAJOR: -15,
            ReviewSeverity.MINOR: -5,
            ReviewSeverity.INFO: -1
        }

        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 0)
            base_score += penalty

        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, base_score))

        # Convert to letter grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return score, grade

    async def _generate_review_summary(
        self,
        context: CodeReviewContext,
        score: float,
        issues: List[CodeReviewIssue]
    ) -> str:
        """Generate a comprehensive review summary."""
        critical_count = len([i for i in issues if i.severity == ReviewSeverity.CRITICAL])
        major_count = len([i for i in issues if i.severity == ReviewSeverity.MAJOR])

        if critical_count > 0:
            summary = f"This implementation has {critical_count} critical issue(s) that prevent it from working correctly. Focus on fixing these first."
        elif major_count > 0:
            summary = f"The algorithm has {major_count} major logic issue(s) that need attention. The core approach may need revision."
        elif score >= 80:
            summary = "Well-implemented solution! The algorithm is sound with room for minor optimizations and style improvements."
        else:
            summary = "Solid foundation with several areas for improvement. Focus on the algorithmic logic and efficiency suggestions."

        return summary

    def _identify_strengths(
        self,
        context: CodeReviewContext,
        issues: List[CodeReviewIssue]
    ) -> List[str]:
        """Identify strengths in the code."""
        strengths = []

        # Code structure analysis
        if "def " in context.code and "return" in context.code:
            strengths.append("Good function structure with clear input/output")

        # DSA pattern usage
        pattern_usage = self._analyze_pattern_usage(context.code)
        for pattern_name in pattern_usage:
            strengths.append(f"Uses {pattern_name.replace('_', ' ')} pattern appropriately")

        # Error handling
        if "try:" in context.code or "except" in context.code:
            strengths.append("Includes error handling")

        # Documentation
        if '"""' in context.code or "'''" in context.code:
            strengths.append("Includes documentation/docstrings")

        # Default strengths for any submission
        if not strengths:
            strengths = [
                "Attempted to solve the problem programmatically",
                "Shows understanding of basic programming concepts"
            ]

        return strengths

    def _generate_suggestions(
        self,
        issues: List[CodeReviewIssue],
        context: CodeReviewContext
    ) -> List[str]:
        """Generate actionable suggestions."""
        suggestions = []

        # Group suggestions by category
        category_suggestions = {}
        for issue in issues:
            if issue.category not in category_suggestions:
                category_suggestions[issue.category] = []
            if issue.suggestion:
                category_suggestions[issue.category].append(issue.suggestion)

        # Convert to readable suggestions
        for category, cats in category_suggestions.items():
            if cats:
                suggestions.extend(cats[:2])  # Limit to 2 per category

        # Add general suggestions if needed
        if len(suggestions) < 3:
            suggestions.extend([
                "Add comprehensive test cases covering edge cases",
                "Consider time and space complexity optimization",
                "Improve variable naming for better readability",
                "Add docstrings to explain function purposes"
            ])

        return suggestions[:5]  # Limit to 5 suggestions

    def _extract_learning_points(
        self,
        issues: List[CodeReviewIssue],
        context: CodeReviewContext
    ) -> List[str]:
        """Extract key learning points from the review."""
        learning_points = []

        # Extract insights from issues
        for issue in issues:
            if issue.learning_insight:
                learning_points.append(issue.learning_insight)

        # Add pattern-specific learning
        pattern_usage = self._analyze_pattern_usage(context.code)
        for pattern_name in pattern_usage:
            learning_points.append(f"Practice implementing {pattern_name.replace('_', ' ')} pattern correctly")

        # Ensure we have some learning points
        if not learning_points:
            learning_points = [
                "Focus on algorithmic correctness before optimization",
                "Test your code thoroughly with various inputs",
                "Understand the problem requirements completely before coding",
                "Practice explaining your algorithm to others",
                "Study common DSA patterns and when to apply them"
            ]

        return list(set(learning_points))[:5]  # Remove duplicates, limit to 5

    async def _estimate_complexity(
        self,
        context: CodeReviewContext
    ) -> Tuple[Optional[str], Optional[str]]:
        """Estimate time and space complexity."""
        # Simple heuristic-based estimation
        code = context.code

        # Time complexity estimation
        if "for" in code and "for" in code.split("for")[1]:  # Nested loops
            time_complexity = "O(n²)"
        elif "sort" in code or "sorted" in code:
            time_complexity = "O(n log n)"
        elif "for" in code and ("binary" in code.lower() or "mid" in code):
            time_complexity = "O(log n)"
        elif "for" in code or "while" in code:
            time_complexity = "O(n)"
        else:
            time_complexity = "O(1)"

        # Space complexity estimation
        if "dp" in code.lower() or "memo" in code.lower():
            space_complexity = "O(n)"  # Usually for arrays/memoization
        elif "dict" in code or "set" in code or "{}" in code:
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

        return time_complexity, space_complexity
