# Data Gathering System

## Overview

The data gathering system collects DSA questions from various public sources and categorizes them by topics. This enables NoLeet to build a comprehensive database of real interview questions.

## Architecture

### Components

1. **Base Scraper** (`base_scraper.py`): Abstract base class for all scrapers
2. **LeetCode Scraper** (`leetcode_scraper.py`): Scrapes LeetCode discussions
3. **Reddit Scraper** (`reddit_scraper.py`): Scrapes Reddit posts
4. **Question Processor** (`processor.py`): Categorizes questions by DSA topics
5. **Coordinator** (`coordinator.py`): Coordinates gathering from all sources

## Usage

### CLI Command

```bash
python3 -m noleet.cli.main data gather --max-results 50
```

### Programmatic Usage

```python
from pathlib import Path
from noleet.data_gathering.coordinator import DataGatheringCoordinator

coordinator = DataGatheringCoordinator(Path("./data"))
categorized = coordinator.gather_all_sources(max_results_per_source=50)
```

## Data Sources

### LeetCode

- **Target Tags**: amazon-oa, google-interview, facebook-interview, etc.
- **Method**: Scrapes discussion posts tagged with interview questions
- **Output**: Questions with titles, content, tags, difficulty

### Reddit

- **Target Subreddits**: r/leetcode, r/cscareerquestions, r/ExperiencedDevs
- **Search Terms**: "amazon oa", "google interview", "top 150", "blind 75"
- **Method**: Searches subreddits for relevant posts
- **Output**: Questions extracted from post titles and content

## Question Processing

### Topic Categorization

Questions are automatically categorized using keyword matching:

- **Dynamic Programming**: "dp", "dynamic programming", "memoization"
- **Sliding Window**: "sliding window", "two pointers", "subarray"
- **Merge Intervals**: "merge intervals", "interval", "overlapping"
- And 16 more topics...

### Storage

Collected data is stored in JSON format:

- `questions.json`: All collected questions
- `categorized_questions.json`: Questions grouped by topic

## Extending the System

### Adding New Scrapers

1. Inherit from `BaseScraper`
2. Implement the `scrape()` method
3. Return list of `QuestionMetadata` objects
4. Register in `DataGatheringCoordinator`

### Example

```python
class CustomScraper(BaseScraper):
    def __init__(self):
        super().__init__("custom_source")
    
    def scrape(self, **kwargs) -> List[QuestionMetadata]:
        # Implementation
        return questions
```

## Future Enhancements

- Medium article scraper
- YouTube video description scraper
- GitHub repository scraper for "top 150" sheets
- ML-based topic classification
- Duplicate detection
- Quality scoring

