# Research Paper Integration System

## Overview

The research integration system enables NoLeet to extract algorithms and techniques from research papers and match them to projects. This is a key differentiator that allows mixing and matching multiple research papers.

## Architecture

### Components

1. **Paper Parser** (`paper_parser.py`): Extracts algorithms and techniques from papers
2. **Research Matcher** (`matcher.py`): Matches papers to projects
3. **Research Integrator** (`integrator.py`): Integrates papers into projects

## Features

### Algorithm Extraction

- Extracts algorithm names from papers
- Identifies time/space complexity
- Extracts pseudocode
- Identifies related techniques

### Topic Identification

- Maps paper content to DSA topics
- Identifies data structures mentioned
- Extracts techniques used

### Project Matching

- Matches papers to projects based on topics
- Suggests paper combinations
- Calculates match scores

### Integration

- Creates research references for projects
- Suggests custom modifications
- Tracks algorithm usage

## Usage

### Parsing a Paper

```python
from noleet.research.paper_parser import ResearchPaperParser

parser = ResearchPaperParser()
paper = parser.parse_paper(
    file_path="paper.pdf",
    title="Adaptive Windowing Algorithms",
    authors=["Author One", "Author Two"],
    url="https://example.com/paper"
)
```

### Matching Papers to Projects

```python
from noleet.research.matcher import ResearchMatcher
from noleet.storage.repository import ProjectRepository

matcher = ResearchMatcher()
repository = ProjectRepository(data_dir)
projects = repository.load_projects()

for project in projects:
    matching_papers = matcher.find_matching_papers(papers, project)
    combinations = matcher.suggest_paper_combinations(papers, project)
```

### Integrating Papers

```python
from noleet.research.integrator import ResearchIntegrator

integrator = ResearchIntegrator()
enhanced_project = integrator.integrate_papers_into_project(
    project=project,
    papers=matching_papers,
    custom_modifications="Extended for real-time processing"
)
```

## Paper Format Support

### Currently Supported

- **Text files**: Plain text, markdown
- **PDF files**: Requires PyPDF2 (optional)

### Future Support

- LaTeX source files
- HTML/Web pages
- ArXiv API integration
- Google Scholar integration

## Algorithm Extraction

### Patterns Detected

- Algorithm declarations: "Algorithm X", "Procedure Y"
- Complexity notation: "O(n log n)", "Time complexity: O(n)"
- Pseudocode blocks: Code-like sections

### Topic Mapping

Papers are analyzed for DSA topic keywords:
- Dynamic programming mentions
- Graph/tree algorithms
- Data structure usage
- Optimization techniques

## Matching Algorithm

### Score Calculation

1. **Topic Overlap** (50%): How many project topics match paper topics
2. **Algorithm Count** (30%): Number of algorithms in paper
3. **Technique Count** (20%): Number of techniques mentioned

### Combination Suggestions

- Finds papers that together cover all project topics
- Suggests 2-3 paper combinations
- Prioritizes complementary papers

## Custom Modifications

The system suggests modifications based on:

- Missing topics in papers
- Project difficulty level
- Number of algorithms to combine
- Production requirements

## Example Workflow

1. **Parse Papers**: Extract algorithms from multiple papers
2. **Match to Project**: Find papers relevant to project topics
3. **Suggest Combinations**: Find papers that work well together
4. **Integrate**: Add research references to project
5. **Customize**: Suggest modifications for project needs

## Future Enhancements

- Automatic algorithm implementation generation
- Code template creation from pseudocode
- Performance comparison between papers
- Citation network analysis
- Algorithm variant detection

