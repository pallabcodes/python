"""LLM-powered research paper analyzer."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from ..paper_parser import ResearchPaper
from ...llm.llm_factory import LLMFactory
from ...llm.llm_config import LLMConfig


@dataclass
class LLMPaperAnalysis:
    """LLM-powered analysis of a research paper."""
    paper_title: str
    key_contributions: List[str]
    algorithms_extracted: List[Dict[str, Any]]
    complexity_analysis: Dict[str, str]
    practical_applications: List[str]
    code_relevance_score: float  # 0.0-1.0
    implementation_difficulty: str  # easy, medium, hard
    confidence_score: float  # 0.0-1.0
    reasoning: str


class PaperAnalyzerLLM:
    """Uses LLM to deeply analyze research papers for algorithmic insights."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize LLM-powered paper analyzer.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)

        # Analysis prompts
        self._analysis_prompt = self._build_analysis_prompt()

    def _build_analysis_prompt(self) -> str:
        """Build the comprehensive paper analysis prompt."""
        return """You are an expert computer scientist and algorithm researcher. Analyze this research paper and provide a detailed technical assessment.

Paper Title: {title}
Abstract/Content: {content}

Provide a comprehensive analysis covering:

1. **Key Contributions**: What are the 3-5 most important contributions of this paper?

2. **Algorithms Extracted**: Identify specific algorithms with:
   - Name and brief description
   - Time/space complexity
   - Key algorithmic insights
   - Implementation considerations

3. **Complexity Analysis**: For each major algorithm:
   - Best/worst/average case complexity
   - Space complexity
   - Practical performance considerations

4. **Practical Applications**: How can these algorithms be applied to:
   - Coding interview problems
   - Real-world software systems
   - Performance-critical applications

5. **Code Relevance**: Rate how relevant this is to coding interviews/problems (0.0-1.0)

6. **Implementation Difficulty**: easy/medium/hard based on:
   - Algorithmic complexity
   - Data structure requirements
   - Edge case handling

7. **Confidence Score**: How confident are you in this analysis (0.0-1.0)?

8. **Reasoning**: Brief explanation of your analysis methodology

Format your response as valid JSON with these exact keys:
key_contributions (array), algorithms_extracted (array of objects), complexity_analysis (object), practical_applications (array), code_relevance_score (float), implementation_difficulty (string), confidence_score (float), reasoning (string)

Be specific and technical in your analysis. Focus on algorithmic details that would be valuable for coding interviews and software development."""

    def analyze_paper_llm(
        self,
        paper: ResearchPaper,
        full_content: Optional[str] = None
    ) -> LLMPaperAnalysis:
        """
        Perform deep LLM-powered analysis of a research paper.

        Args:
            paper: Research paper object
            full_content: Full paper content (if available)

        Returns:
            Comprehensive LLM analysis
        """
        try:
            # Prepare content for analysis
            content_to_analyze = full_content or paper.abstract or "No full content available"

            # Truncate if too long (LLM context limits)
            if len(content_to_analyze) > 8000:
                content_to_analyze = content_to_analyze[:8000] + "...[truncated]"

            # Format prompt
            prompt = self._analysis_prompt.format(
                title=paper.title,
                content=content_to_analyze
            )

            # Get LLM analysis
            llm = self._llm_factory.create_llm()
            response = llm.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1500
            )

            # Parse and validate response
            analysis_data = self._parse_llm_response(response)

            return LLMPaperAnalysis(
                paper_title=paper.title,
                key_contributions=analysis_data.get("key_contributions", []),
                algorithms_extracted=analysis_data.get("algorithms_extracted", []),
                complexity_analysis=analysis_data.get("complexity_analysis", {}),
                practical_applications=analysis_data.get("practical_applications", []),
                code_relevance_score=float(analysis_data.get("code_relevance_score", 0.5)),
                implementation_difficulty=analysis_data.get("implementation_difficulty", "medium"),
                confidence_score=float(analysis_data.get("confidence_score", 0.5)),
                reasoning=analysis_data.get("reasoning", "LLM analysis completed")
            )

        except Exception as e:
            self._logger.error(f"Failed to analyze paper {paper.title}: {e}")
            return self._fallback_analysis(paper)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data."""
        try:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return self._validate_analysis_data(json.loads(json_str))
            else:
                # Try parsing entire response as JSON
                return self._validate_analysis_data(json.loads(response))

        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse LLM response as JSON: {e}")
            self._logger.debug(f"Raw response: {response}")

            # Return default structure
            return self._get_default_analysis_structure()

    def _validate_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean analysis data."""
        validated = {}

        # Validate arrays
        validated["key_contributions"] = data.get("key_contributions", [])
        validated["algorithms_extracted"] = data.get("algorithms_extracted", [])
        validated["practical_applications"] = data.get("practical_applications", [])

        # Validate objects
        validated["complexity_analysis"] = data.get("complexity_analysis", {})

        # Validate floats
        for key in ["code_relevance_score", "confidence_score"]:
            value = data.get(key, 0.5)
            validated[key] = max(0.0, min(1.0, float(value)))

        # Validate strings
        validated["implementation_difficulty"] = data.get("implementation_difficulty", "medium")
        if validated["implementation_difficulty"] not in ["easy", "medium", "hard"]:
            validated["implementation_difficulty"] = "medium"

        validated["reasoning"] = str(data.get("reasoning", "Analysis completed"))

        return validated

    def _get_default_analysis_structure(self) -> Dict[str, Any]:
        """Get default analysis structure when parsing fails."""
        return {
            "key_contributions": ["Paper analysis completed"],
            "algorithms_extracted": [],
            "complexity_analysis": {},
            "practical_applications": ["General algorithmic applications"],
            "code_relevance_score": 0.5,
            "implementation_difficulty": "medium",
            "confidence_score": 0.3,
            "reasoning": "Fallback analysis due to parsing error"
        }

    def _fallback_analysis(self, paper: ResearchPaper) -> LLMPaperAnalysis:
        """Provide fallback analysis when LLM fails."""
        return LLMPaperAnalysis(
            paper_title=paper.title,
            key_contributions=["Research paper analysis"],
            algorithms_extracted=[],
            complexity_analysis={},
            practical_applications=["Algorithmic research applications"],
            code_relevance_score=0.5,
            implementation_difficulty="medium",
            confidence_score=0.3,
            reasoning="Fallback analysis due to LLM failure"
        )

    def batch_analyze_papers(
        self,
        papers: List[ResearchPaper],
        max_concurrent: int = 3
    ) -> List[LLMPaperAnalysis]:
        """
        Analyze multiple papers with controlled concurrency.

        Args:
            papers: List of research papers to analyze
            max_concurrent: Maximum concurrent analyses

        Returns:
            List of analysis results
        """
        import asyncio

        async def analyze_single(paper: ResearchPaper) -> LLMPaperAnalysis:
            # Run in thread pool to avoid blocking
            import concurrent.futures
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(
                    executor, self.analyze_paper_llm, paper
                )

        async def analyze_batch():
            semaphore = asyncio.Semaphore(max_concurrent)
            results = []

            async def analyze_with_semaphore(paper: ResearchPaper):
                async with semaphore:
                    return await analyze_single(paper)

            tasks = [analyze_with_semaphore(paper) for paper in papers]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self._logger.warning(f"Analysis failed for paper {papers[i].title}: {result}")
                    final_results.append(self._fallback_analysis(papers[i]))
                else:
                    final_results.append(result)

            return final_results

        # Run async analysis
        import asyncio
        return asyncio.run(analyze_batch())
