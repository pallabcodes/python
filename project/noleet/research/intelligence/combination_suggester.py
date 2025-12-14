"""LLM-powered research paper combination suggester."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from ...llm.llm_factory import LLMFactory
from ...llm.llm_config import LLMConfig


@dataclass
class PaperCombination:
    """Suggested combination of research papers."""
    papers: List[str]  # Paper titles
    combination_type: str  # 'sequential', 'parallel', 'hybrid', 'complementary'
    synergy_score: float  # 0.0-1.0
    combined_algorithm: str
    implementation_approach: str
    complexity_improvement: str
    use_cases: List[str]
    confidence_score: float  # 0.0-1.0
    reasoning: str


@dataclass
class CombinationAnalysis:
    """Analysis of paper combinations."""
    combinations: List[PaperCombination]
    total_papers_analyzed: int
    combinations_found: int
    average_synergy_score: float
    analysis_summary: str


class CombinationSuggester:
    """Uses LLM to suggest combinations of multiple research papers for enhanced algorithms."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize combination suggester.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)

        # Combination analysis prompts
        self._combination_prompt = self._build_combination_prompt()
        self._pairwise_analysis_prompt = self._build_pairwise_analysis_prompt()

    def _build_combination_prompt(self) -> str:
        """Build the paper combination analysis prompt."""
        return """You are an expert at synthesizing multiple research papers to create novel algorithmic approaches. Analyze these research papers and suggest how they can be combined.

Papers to analyze:
{papers_description}

Find meaningful combinations of 2-3 papers that can create:
1. **Sequential combinations**: One paper's algorithm followed by another's
2. **Parallel combinations**: Running algorithms simultaneously with different inputs
3. **Hybrid approaches**: Merging techniques from different papers
4. **Complementary methods**: Papers that solve different aspects of the same problem

For each combination, provide:

1. **Papers Involved**: Which papers are being combined
2. **Combination Type**: sequential/parallel/hybrid/complementary
3. **Synergy Score**: 0.0-1.0 indicating the power of the combination
4. **Combined Algorithm**: Name and description of the resulting algorithm
5. **Implementation Approach**: How to implement the combination
6. **Complexity Improvement**: Expected performance gains
7. **Use Cases**: Where this combination would be valuable
8. **Confidence Score**: How confident you are in this combination (0.0-1.0)
9. **Reasoning**: Why this combination makes sense

Return as JSON array of combination objects with these exact keys:
papers, combination_type, synergy_score, combined_algorithm, implementation_approach, complexity_improvement, use_cases, confidence_score, reasoning

Find 3-5 most promising combinations. Focus on combinations that create genuinely novel approaches."""

    def _build_pairwise_analysis_prompt(self) -> str:
        """Build the pairwise paper analysis prompt."""
        return """Analyze the relationship between these two research papers:

Paper 1: {paper1_title}
Algorithms: {paper1_algorithms}
Key Insights: {paper1_insights}

Paper 2: {paper2_title}
Algorithms: {paper2_algorithms}
Key Insights: {paper2_insights}

Determine if and how these papers can be combined. Consider:
- Algorithmic compatibility
- Complementary strengths
- Sequential application possibilities
- Hybrid technique creation
- Performance improvement potential

Return JSON with: can_combine (boolean), combination_type, synergy_score, reasoning"""

    def suggest_combinations(
        self,
        papers: List[Dict[str, Any]],
        max_combinations: int = 5
    ) -> CombinationAnalysis:
        """
        Suggest combinations of research papers using LLM analysis.

        Args:
            papers: List of paper dictionaries with analysis
            max_combinations: Maximum combinations to suggest

        Returns:
            Analysis of paper combinations
        """
        if len(papers) < 2:
            return CombinationAnalysis(
                combinations=[],
                total_papers_analyzed=len(papers),
                combinations_found=0,
                average_synergy_score=0.0,
                analysis_summary="Need at least 2 papers for combinations"
            )

        try:
            # Prepare papers description
            papers_description = self._format_papers_for_analysis(papers)

            # Get LLM combination suggestions
            prompt = self._combination_prompt.format(papers_description=papers_description)

            llm = self._llm_factory.create_llm()
            response = llm.generate(
                prompt=prompt,
                temperature=0.3,  # Moderate creativity for combination ideation
                max_tokens=1500
            )

            # Parse combinations
            combinations_data = self._parse_combination_response(response)

            # Convert to Combination objects
            combinations = []
            for combo_data in combinations_data[:max_combinations]:
                try:
                    combination = PaperCombination(
                        papers=combo_data.get("papers", []),
                        combination_type=combo_data.get("combination_type", "hybrid"),
                        synergy_score=float(combo_data.get("synergy_score", 0.0)),
                        combined_algorithm=combo_data.get("combined_algorithm", "Combined Algorithm"),
                        implementation_approach=combo_data.get("implementation_approach", ""),
                        complexity_improvement=combo_data.get("complexity_improvement", ""),
                        use_cases=combo_data.get("use_cases", []),
                        confidence_score=float(combo_data.get("confidence_score", 0.0)),
                        reasoning=combo_data.get("reasoning", "")
                    )
                    combinations.append(combination)

                except Exception as e:
                    self._logger.warning(f"Failed to process combination data: {e}")
                    continue

            # Calculate statistics
            synergy_scores = [c.synergy_score for c in combinations]
            average_synergy = sum(synergy_scores) / len(synergy_scores) if synergy_scores else 0.0

            analysis_summary = f"Found {len(combinations)} paper combinations from {len(papers)} papers with average synergy score {average_synergy:.2f}"

            return CombinationAnalysis(
                combinations=combinations,
                total_papers_analyzed=len(papers),
                combinations_found=len(combinations),
                average_synergy_score=average_synergy,
                analysis_summary=analysis_summary
            )

        except Exception as e:
            self._logger.error(f"Failed to suggest paper combinations: {e}")
            return CombinationAnalysis(
                combinations=[],
                total_papers_analyzed=len(papers),
                combinations_found=0,
                average_synergy_score=0.0,
                analysis_summary=f"Combination analysis failed: {e}"
            )

    def _format_papers_for_analysis(self, papers: List[Dict[str, Any]]) -> str:
        """Format papers for LLM analysis."""
        formatted_papers = []

        for i, paper in enumerate(papers, 1):
            title = paper.get("title", f"Paper {i}")
            algorithms = paper.get("algorithms_extracted", [])
            alg_names = [alg.get("name", "Unknown") for alg in algorithms] if algorithms else ["General research"]

            # Get key contributions or fallback
            contributions = paper.get("key_contributions", [])
            if not contributions and algorithms:
                contributions = [f"Algorithm: {alg.get('name', 'Unknown')}" for alg in algorithms[:2]]

            formatted_paper = f"""Paper {i}: {title}
  Algorithms: {', '.join(alg_names)}
  Key Contributions: {'; '.join(contributions[:2]) if contributions else 'Research contributions'}
  Relevance Score: {paper.get('code_relevance_score', 0.5):.2f}"""

            formatted_papers.append(formatted_paper)

        return "\n\n".join(formatted_papers)

    def _parse_combination_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM combination response."""
        try:
            import json

            # Try to extract JSON array from response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing entire response as JSON
                return json.loads(response) if response.strip().startswith("[") else []

        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse combination response: {e}")
            self._logger.debug(f"Raw response: {response}")
            return []

    def analyze_pairwise_relationships(
        self,
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze pairwise relationships between all papers.

        Args:
            papers: List of paper dictionaries

        Returns:
            List of pairwise relationship analyses
        """
        relationships = []

        # Analyze each pair
        for i in range(len(papers)):
            for j in range(i + 1, len(papers)):
                paper1 = papers[i]
                paper2 = papers[j]

                try:
                    # Get algorithms and insights
                    paper1_algorithms = [alg.get("name", "Unknown") for alg in paper1.get("algorithms_extracted", [])]
                    paper2_algorithms = [alg.get("name", "Unknown") for alg in paper2.get("algorithms_extracted", [])]

                    paper1_insights = paper1.get("key_contributions", [])
                    paper2_insights = paper2.get("key_contributions", [])

                    # Analyze relationship
                    prompt = self._pairwise_analysis_prompt.format(
                        paper1_title=paper1["title"],
                        paper1_algorithms=", ".join(paper1_algorithms) if paper1_algorithms else "General algorithms",
                        paper1_insights="; ".join(paper1_insights) if paper1_insights else "Research insights",
                        paper2_title=paper2["title"],
                        paper2_algorithms=", ".join(paper2_algorithms) if paper2_algorithms else "General algorithms",
                        paper2_insights="; ".join(paper2_insights) if paper2_insights else "Research insights"
                    )

                    llm = self._llm_factory.create_llm()
                    response = llm.generate(
                        prompt=prompt,
                        temperature=0.1,
                        max_tokens=400
                    )

                    # Parse relationship
                    try:
                        import json
                        start_idx = response.find("{")
                        end_idx = response.rfind("}") + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            relationship_data = json.loads(response[start_idx:end_idx])

                            relationships.append({
                                "paper1": paper1["title"],
                                "paper2": paper2["title"],
                                "can_combine": relationship_data.get("can_combine", False),
                                "combination_type": relationship_data.get("combination_type", "none"),
                                "synergy_score": float(relationship_data.get("synergy_score", 0.0)),
                                "reasoning": relationship_data.get("reasoning", ""),
                                "analysis_method": "llm_pairwise"
                            })

                    except Exception as e:
                        self._logger.debug(f"Failed to parse pairwise relationship: {e}")

                except Exception as e:
                    self._logger.warning(f"Failed to analyze relationship between {paper1['title']} and {paper2['title']}: {e}")

        return relationships

    def suggest_best_combinations(
        self,
        papers: List[Dict[str, Any]],
        min_synergy_score: float = 0.6,
        max_suggestions: int = 3
    ) -> List[PaperCombination]:
        """
        Suggest the best paper combinations based on synergy scores.

        Args:
            papers: List of analyzed papers
            min_synergy_score: Minimum synergy score to consider
            max_suggestions: Maximum combinations to return

        Returns:
            Best combination suggestions
        """
        # Get all possible combinations
        analysis = self.suggest_combinations(papers, max_combinations=10)

        # Filter by synergy score
        high_synergy_combinations = [
            combo for combo in analysis.combinations
            if combo.synergy_score >= min_synergy_score
        ]

        # Sort by synergy score and confidence
        sorted_combinations = sorted(
            high_synergy_combinations,
            key=lambda x: (x.synergy_score * 0.7 + x.confidence_score * 0.3),
            reverse=True
        )

        return sorted_combinations[:max_suggestions]

    def generate_combination_report(
        self,
        papers: List[Dict[str, Any]],
        combinations: List[PaperCombination]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report on paper combinations.

        Args:
            papers: Original papers
            combinations: Suggested combinations

        Returns:
            Combination report
        """
        report = {
            "summary": {
                "total_papers": len(papers),
                "total_combinations": len(combinations),
                "high_synergy_combinations": len([c for c in combinations if c.synergy_score >= 0.7]),
                "average_synergy": sum(c.synergy_score for c in combinations) / len(combinations) if combinations else 0.0
            },
            "combinations_by_type": {},
            "top_combinations": [],
            "paper_involvement": {},
            "recommendations": []
        }

        # Analyze combinations by type
        type_counts = {}
        for combo in combinations:
            combo_type = combo.combination_type
            type_counts[combo_type] = type_counts.get(combo_type, 0) + 1

            # Track paper involvement
            for paper_title in combo.papers:
                if paper_title not in report["paper_involvement"]:
                    report["paper_involvement"][paper_title] = []
                report["paper_involvement"][paper_title].append({
                    "combination_type": combo_type,
                    "synergy_score": combo.synergy_score
                })

        report["combinations_by_type"] = type_counts

        # Get top combinations
        top_combinations = sorted(combinations, key=lambda x: x.synergy_score, reverse=True)[:5]
        report["top_combinations"] = [
            {
                "papers": combo.papers,
                "type": combo.combination_type,
                "synergy_score": combo.synergy_score,
                "combined_algorithm": combo.combined_algorithm,
                "confidence": combo.confidence_score
            }
            for combo in top_combinations
        ]

        # Generate recommendations
        if combinations:
            best_combo = max(combinations, key=lambda x: x.synergy_score)
            report["recommendations"] = [
                f"Focus on {best_combo.combination_type} combinations - highest synergy potential",
                f"Prioritize papers: {', '.join(set(p for c in combinations for p in c.papers))}",
                f"Target use cases: {', '.join(set(u for c in combinations for u in c.use_cases[:2]))}"
            ]

        return report
