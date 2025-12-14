"""LLM-powered algorithm extractor from research papers."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..paper_parser import Algorithm
from ...llm.llm_factory import LLMFactory
from ...llm.llm_config import LLMConfig


@dataclass
class ExtractedAlgorithm:
    """Detailed algorithm extracted using LLM analysis."""
    name: str
    description: str
    pseudocode: str
    time_complexity: str
    space_complexity: str
    key_insights: List[str]
    implementation_notes: List[str]
    test_cases: List[Dict[str, Any]]
    edge_cases: List[str]
    optimization_opportunities: List[str]
    confidence_score: float  # 0.0-1.0
    extraction_method: str   # 'llm_direct', 'llm_reasoning', 'fallback'


class AlgorithmExtractorLLM:
    """Uses LLM to extract and analyze algorithms from research papers."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize LLM-powered algorithm extractor.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)

        # Extraction prompts
        self._extraction_prompt = self._build_extraction_prompt()
        self._refinement_prompt = self._build_refinement_prompt()

    def _build_extraction_prompt(self) -> str:
        """Build the algorithm extraction prompt."""
        return """You are an expert algorithm researcher and competitive programmer. Extract and analyze algorithms from this research paper content.

Paper Content: {content}

Focus on the most important algorithms presented in this paper. For each algorithm, extract:

1. **Name**: Clear, descriptive algorithm name
2. **Description**: What the algorithm does and its purpose
3. **Pseudocode**: Step-by-step algorithmic description (not code)
4. **Time Complexity**: Big O notation with explanation
5. **Space Complexity**: Memory requirements analysis
6. **Key Insights**: Important algorithmic insights or innovations
7. **Implementation Notes**: Critical implementation details
8. **Test Cases**: 2-3 example inputs/outputs
9. **Edge Cases**: Important edge cases to handle
10. **Optimizations**: Performance improvement opportunities

Be precise and technical. Focus on algorithms that would be valuable for:
- Coding interviews
- System design
- Performance-critical applications

Return as JSON array of algorithm objects with these exact keys:
name, description, pseudocode, time_complexity, space_complexity, key_insights (array), implementation_notes (array), test_cases (array of objects with input/output), edge_cases (array), optimization_opportunities (array)

Extract 1-3 most important algorithms. If no clear algorithms, return empty array."""

    def _build_refinement_prompt(self) -> str:
        """Build the algorithm refinement prompt."""
        return """You are refining an algorithm extracted from research. Improve and validate the following algorithm details:

Algorithm: {algorithm_json}

Review and improve:
1. **Accuracy**: Ensure pseudocode correctly represents the algorithm
2. **Completeness**: Add missing implementation details
3. **Clarity**: Make descriptions more precise
4. **Test Cases**: Add more comprehensive examples
5. **Edge Cases**: Identify additional edge cases
6. **Optimizations**: Suggest practical improvements

Return the refined algorithm as JSON with the same structure, enhanced where appropriate."""

    def extract_algorithms_llm(
        self,
        paper_title: str,
        paper_content: str,
        existing_algorithms: Optional[List[Algorithm]] = None
    ) -> List[ExtractedAlgorithm]:
        """
        Extract algorithms from paper using LLM analysis.

        Args:
            paper_title: Title of the research paper
            paper_content: Full paper content
            existing_algorithms: Previously extracted algorithms (optional)

        Returns:
            List of detailed algorithm extractions
        """
        try:
            # Prepare content (truncate if too long)
            content_to_analyze = paper_content
            if len(content_to_analyze) > 12000:
                content_to_analyze = content_to_analyze[:12000] + "...[content truncated]"

            # Include existing algorithms in context if available
            context_addition = ""
            if existing_algorithms:
                existing_names = [alg.name for alg in existing_algorithms]
                context_addition = f"\n\nPreviously identified algorithms: {', '.join(existing_names)}. Focus on extracting these or finding additional important algorithms."

            # Format extraction prompt
            prompt = self._extraction_prompt.format(content=content_to_analyze + context_addition)

            # Get LLM extraction
            llm = self._llm_factory.create_llm()
            response = llm.generate(
                prompt=prompt,
                temperature=0.2,  # Moderate temperature for creativity but consistency
                max_tokens=2000
            )

            # Parse algorithms
            algorithms_data = self._parse_extraction_response(response)

            # Convert to ExtractedAlgorithm objects
            extracted_algorithms = []
            for alg_data in algorithms_data:
                try:
                    algorithm = ExtractedAlgorithm(
                        name=alg_data.get("name", "Unknown Algorithm"),
                        description=alg_data.get("description", "Algorithm description"),
                        pseudocode=alg_data.get("pseudocode", "Pseudocode not available"),
                        time_complexity=alg_data.get("time_complexity", "O(?)"),
                        space_complexity=alg_data.get("space_complexity", "O(?)"),
                        key_insights=alg_data.get("key_insights", []),
                        implementation_notes=alg_data.get("implementation_notes", []),
                        test_cases=alg_data.get("test_cases", []),
                        edge_cases=alg_data.get("edge_cases", []),
                        optimization_opportunities=alg_data.get("optimization_opportunities", []),
                        confidence_score=0.8,  # Default high confidence for LLM extraction
                        extraction_method="llm_direct"
                    )
                    extracted_algorithms.append(algorithm)

                except Exception as e:
                    self._logger.warning(f"Failed to process algorithm data: {e}")
                    continue

            # Refine algorithms if we got any
            if extracted_algorithms:
                extracted_algorithms = self._refine_algorithms(extracted_algorithms)

            return extracted_algorithms

        except Exception as e:
            self._logger.error(f"Failed to extract algorithms from {paper_title}: {e}")
            return self._fallback_extraction(paper_title, existing_algorithms or [])

    def _parse_extraction_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM extraction response."""
        try:
            import json

            # Try to extract JSON array from response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing as single object in array
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = f"[{response[start_idx:end_idx]}]"
                    return json.loads(json_str)

            # Try parsing entire response as JSON
            return json.loads(response) if response.strip().startswith("[") else [json.loads(response)]

        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse algorithm extraction response: {e}")
            self._logger.debug(f"Raw response: {response}")
            return []

    def _refine_algorithms(self, algorithms: List[ExtractedAlgorithm]) -> List[ExtractedAlgorithm]:
        """Refine extracted algorithms using additional LLM analysis."""
        refined_algorithms = []

        for algorithm in algorithms:
            try:
                # Convert algorithm back to dict for refinement
                alg_dict = {
                    "name": algorithm.name,
                    "description": algorithm.description,
                    "pseudocode": algorithm.pseudocode,
                    "time_complexity": algorithm.time_complexity,
                    "space_complexity": algorithm.space_complexity,
                    "key_insights": algorithm.key_insights,
                    "implementation_notes": algorithm.implementation_notes,
                    "test_cases": algorithm.test_cases,
                    "edge_cases": algorithm.edge_cases,
                    "optimization_opportunities": algorithm.optimization_opportunities,
                }

                # Format refinement prompt
                prompt = self._refinement_prompt.format(algorithm_json=json.dumps(alg_dict, indent=2))

                # Get refinement
                llm = self._llm_factory.create_llm()
                response = llm.generate(
                    prompt=prompt,
                    temperature=0.1,  # Low temperature for refinement
                    max_tokens=1000
                )

                # Parse refined algorithm
                try:
                    import json
                    start_idx = response.find("{")
                    end_idx = response.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        refined_data = json.loads(response[start_idx:end_idx])

                        # Update algorithm with refined data
                        algorithm.description = refined_data.get("description", algorithm.description)
                        algorithm.pseudocode = refined_data.get("pseudocode", algorithm.pseudocode)
                        algorithm.time_complexity = refined_data.get("time_complexity", algorithm.time_complexity)
                        algorithm.space_complexity = refined_data.get("space_complexity", algorithm.space_complexity)
                        algorithm.key_insights = refined_data.get("key_insights", algorithm.key_insights)
                        algorithm.implementation_notes = refined_data.get("implementation_notes", algorithm.implementation_notes)
                        algorithm.test_cases = refined_data.get("test_cases", algorithm.test_cases)
                        algorithm.edge_cases = refined_data.get("edge_cases", algorithm.edge_cases)
                        algorithm.optimization_opportunities = refined_data.get("optimization_opportunities", algorithm.optimization_opportunities)
                        algorithm.extraction_method = "llm_reasoning"

                except Exception as e:
                    self._logger.debug(f"Failed to refine algorithm {algorithm.name}: {e}")
                    # Keep original algorithm

            except Exception as e:
                self._logger.warning(f"Failed to refine algorithm {algorithm.name}: {e}")

            refined_algorithms.append(algorithm)

        return refined_algorithms

    def _fallback_extraction(
        self,
        paper_title: str,
        existing_algorithms: List[Algorithm]
    ) -> List[ExtractedAlgorithm]:
        """Provide fallback algorithm extraction."""
        fallback_algorithms = []

        # Convert existing algorithms to ExtractedAlgorithm format
        for alg in existing_algorithms:
            fallback_algorithm = ExtractedAlgorithm(
                name=alg.name,
                description=alg.description or f"Algorithm {alg.name} from {paper_title}",
                pseudocode=alg.pseudocode or "Pseudocode not available",
                time_complexity=str(alg.complexity) if alg.complexity else "O(?)",
                space_complexity="O(?)",  # Not available in basic Algorithm
                key_insights=[],
                implementation_notes=[],
                test_cases=[],
                edge_cases=[],
                optimization_opportunities=[],
                confidence_score=0.4,
                extraction_method="fallback"
            )
            fallback_algorithms.append(fallback_algorithm)

        if not fallback_algorithms:
            # Create a generic algorithm if none exist
            fallback_algorithm = ExtractedAlgorithm(
                name="Research Algorithm",
                description=f"Algorithm extracted from paper: {paper_title}",
                pseudocode="Algorithm details not available",
                time_complexity="O(?)",
                space_complexity="O(?)",
                key_insights=["Research contribution"],
                implementation_notes=["Requires further analysis"],
                test_cases=[],
                edge_cases=[],
                optimization_opportunities=[],
                confidence_score=0.2,
                extraction_method="fallback"
            )
            fallback_algorithms.append(fallback_algorithm)

        return fallback_algorithms

    def extract_algorithm_details(
        self,
        algorithm_name: str,
        paper_content: str
    ) -> Optional[ExtractedAlgorithm]:
        """
        Extract detailed information about a specific algorithm.

        Args:
            algorithm_name: Name of the algorithm to focus on
            paper_content: Full paper content

        Returns:
            Detailed algorithm extraction or None
        """
        try:
            prompt = f"""Extract detailed information about the algorithm "{algorithm_name}" from this research paper.

Paper Content: {paper_content[:8000]}...

Provide comprehensive details including:
- Exact pseudocode or algorithmic steps
- Precise time and space complexity
- Key algorithmic insights
- Implementation challenges
- Test cases with specific examples
- Important edge cases
- Optimization techniques

Return as JSON with the same structure as before."""

            llm = self._llm_factory.create_llm()
            response = llm.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=1500
            )

            # Parse and return single algorithm
            algorithms_data = self._parse_extraction_response(response)
            if algorithms_data:
                alg_data = algorithms_data[0]
                return ExtractedAlgorithm(
                    name=alg_data.get("name", algorithm_name),
                    description=alg_data.get("description", ""),
                    pseudocode=alg_data.get("pseudocode", ""),
                    time_complexity=alg_data.get("time_complexity", "O(?)"),
                    space_complexity=alg_data.get("space_complexity", "O(?)"),
                    key_insights=alg_data.get("key_insights", []),
                    implementation_notes=alg_data.get("implementation_notes", []),
                    test_cases=alg_data.get("test_cases", []),
                    edge_cases=alg_data.get("edge_cases", []),
                    optimization_opportunities=alg_data.get("optimization_opportunities", []),
                    confidence_score=0.9,
                    extraction_method="llm_focused"
                )

        except Exception as e:
            self._logger.error(f"Failed to extract details for algorithm {algorithm_name}: {e}")

        return None
