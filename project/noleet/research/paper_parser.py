"""Parser for research papers to extract algorithms and techniques."""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from pathlib import Path

from noleet.core.models import Topic


@dataclass
class Algorithm:
    """Represents an algorithm extracted from a research paper."""
    
    name: str
    description: str
    complexity: Optional[str] = None
    topics: Set[Topic] = field(default_factory=set)
    pseudocode: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class ResearchPaper:
    """Represents a parsed research paper."""
    
    title: str
    authors: List[str]
    url: Optional[str] = None
    file_path: Optional[str] = None
    abstract: str = ""
    algorithms: List[Algorithm] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    data_structures: List[str] = field(default_factory=list)
    topics: Set[Topic] = field(default_factory=set)
    custom_modifications: str = ""
    github_repo: Optional[str] = None


class ResearchPaperParser:
    """Parser for extracting algorithms and techniques from research papers."""
    
    ALGORITHM_PATTERNS = [
        r"algorithm\s+(\w+)",
        r"(\w+)\s+algorithm",
        r"procedure\s+(\w+)",
        r"function\s+(\w+)"
    ]
    
    COMPLEXITY_PATTERNS = [
        r"O\(([^)]+)\)",
        r"time complexity[:\s]+O\(([^)]+)\)",
        r"space complexity[:\s]+O\(([^)]+)\)"
    ]
    
    def __init__(self) -> None:
        """Initialize parser."""
        self._logger = logging.getLogger(__name__)
    
    def parse_paper(
        self,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        url: Optional[str] = None
    ) -> ResearchPaper:
        """
        Parse a research paper.
        
        Args:
            file_path: Path to paper file
            content: Paper content as string
            title: Paper title
            authors: List of authors
            url: URL to paper
            
        Returns:
            Parsed research paper
        """
        if file_path:
            content = self._read_file(file_path)
        
        if not content:
            raise ValueError("No content provided for parsing")
        
        paper = ResearchPaper(
            title=title or self._extract_title(content),
            authors=authors or self._extract_authors(content),
            url=url,
            file_path=file_path,
            abstract=self._extract_abstract(content)
        )
        
        paper.algorithms = self._extract_algorithms(content)
        paper.techniques = self._extract_techniques(content)
        paper.data_structures = self._extract_data_structures(content)
        paper.topics = self._identify_topics(content, paper.algorithms)
        
        self._logger.info(
            f"Parsed paper: {paper.title}",
            extra={
                "title": paper.title,
                "algorithm_count": len(paper.algorithms),
                "technique_count": len(paper.techniques),
                "topic_count": len(paper.topics)
            }
        )
        
        return paper
    
    def _read_file(self, file_path: str) -> str:
        """Read file content."""
        path = Path(file_path)
        
        if not path.exists():
            self._logger.error(f"File not found: {file_path}")
            return ""
        
        try:
            if path.suffix.lower() == ".pdf":
                return self._read_pdf(path)
            else:
                return path.read_text(encoding="utf-8")
        except Exception as e:
            self._logger.error(
                f"Failed to read file {file_path}: {e}",
                exc_info=True
            )
            return ""
    
    def _read_pdf(self, path: Path) -> str:
        """Read PDF file content."""
        try:
            import PyPDF2
            with open(path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            self._logger.warning("PyPDF2 not available, cannot read PDF")
            return ""
        except Exception as e:
            self._logger.error(f"Failed to read PDF: {e}")
            return ""
    
    def _extract_title(self, content: str) -> str:
        """Extract paper title."""
        lines = content.split("\n")[:10]
        for line in lines:
            if len(line) > 20 and len(line) < 200:
                return line.strip()
        return "Untitled Paper"
    
    def _extract_authors(self, content: str) -> List[str]:
        """Extract authors."""
        authors: List[str] = []
        
        pattern = r"authors?[:\s]+([^\n]+)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            author_text = match.group(1)
            authors = [a.strip() for a in author_text.split(",")]
        
        return authors[:10]
    
    def _extract_abstract(self, content: str) -> str:
        """Extract abstract."""
        pattern = r"abstract[:\s]+([^\n]+(?:\n(?!introduction|1\.)[^\n]+)*)"
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""
    
    def _extract_algorithms(self, content: str) -> List[Algorithm]:
        """Extract algorithms from content."""
        algorithms: List[Algorithm] = []
        
        for pattern in self.ALGORITHM_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                algo_name = match.group(1)
                if algo_name.lower() not in ["the", "a", "an", "is", "are"]:
                    algo = self._extract_algorithm_details(content, algo_name, match.start())
                    if algo:
                        algorithms.append(algo)
        
        return algorithms
    
    def _extract_algorithm_details(
        self,
        content: str,
        name: str,
        start_pos: int
    ) -> Optional[Algorithm]:
        """Extract details for a specific algorithm."""
        end_pos = min(start_pos + 2000, len(content))
        section = content[start_pos:end_pos]
        
        description = self._extract_description(section)
        complexity = self._extract_complexity(section)
        pseudocode = self._extract_pseudocode(section)
        
        if not description and not pseudocode:
            return None
        
        return Algorithm(
            name=name,
            description=description,
            complexity=complexity,
            pseudocode=pseudocode
        )
    
    def _extract_description(self, section: str) -> str:
        """Extract algorithm description."""
        sentences = section.split(".")[:3]
        return ". ".join(sentences).strip()
    
    def _extract_complexity(self, section: str) -> Optional[str]:
        """Extract time/space complexity."""
        for pattern in self.COMPLEXITY_PATTERNS:
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_pseudocode(self, section: str) -> Optional[str]:
        """Extract pseudocode."""
        pattern = r"(?:algorithm|procedure|function)[\s\S]{0,500}"
        match = re.search(pattern, section, re.IGNORECASE)
        return match.group(0) if match else None
    
    def _extract_techniques(self, content: str) -> List[str]:
        """Extract techniques mentioned."""
        techniques: List[str] = []
        
        technique_keywords = [
            "optimization", "heuristic", "approximation", "greedy",
            "dynamic programming", "divide and conquer", "backtracking"
        ]
        
        for keyword in technique_keywords:
            if keyword.lower() in content.lower():
                techniques.append(keyword)
        
        return list(set(techniques))
    
    def _extract_data_structures(self, content: str) -> List[str]:
        """Extract data structures mentioned."""
        structures: List[str] = []
        
        ds_keywords = [
            "tree", "graph", "heap", "trie", "hash table", "array",
            "linked list", "stack", "queue", "set", "map"
        ]
        
        for keyword in ds_keywords:
            if keyword.lower() in content.lower():
                structures.append(keyword)
        
        return list(set(structures))
    
    def _identify_topics(
        self,
        content: str,
        algorithms: List[Algorithm]
    ) -> Set[Topic]:
        """Identify DSA topics from content and algorithms."""
        topics: Set[Topic] = set()
        
        content_lower = content.lower()
        
        topic_mappings = {
            Topic.DYNAMIC_PROGRAMMING: ["dynamic programming", "dp", "memoization"],
            Topic.GREEDY: ["greedy", "greedy algorithm"],
            Topic.BACKTRACKING: ["backtrack", "backtracking"],
            Topic.GRAPH_TRAVERSAL: ["graph", "dfs", "bfs"],
            Topic.TREE_TRAVERSAL: ["tree", "binary tree", "bst"],
            Topic.HEAP: ["heap", "priority queue"],
            Topic.TRIE: ["trie", "prefix tree"],
            Topic.HASH_TABLE: ["hash", "hashmap", "hash table"]
        }
        
        for topic, keywords in topic_mappings.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.add(topic)
        
        return topics

