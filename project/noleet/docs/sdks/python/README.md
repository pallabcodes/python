# NoLeet Python SDK

The official Python SDK for the NoLeet API, providing easy access to AI-powered coding project recommendations and intelligent learning tools.

## Installation

```bash
pip install noleet
```

## Quick Start

```python
from noleet import NoLeet

# Initialize client
client = NoLeet(api_key="your_jwt_token")

# Get AI-powered project recommendations
recommendations = client.projects.recommend(limit=5)

for rec in recommendations:
    print(f"Project: {rec.project.title}")
    print(f"Score: {rec.score:.2f}")
    print(f"AI Reasoning: {rec.reasoning}")
    print("---")
```

## Authentication

The SDK supports JWT token authentication:

```python
from noleet import NoLeet

# Using JWT token
client = NoLeet(api_key="your_jwt_token")

# Or authenticate with username/password
client = NoLeet()
client.auth.login(username="your_username", password="your_password")
```

## Core Features

### Project Management

```python
# List projects with filtering
projects = client.projects.list(
    difficulty="medium",
    tags=["algorithms", "data-structures"],
    limit=20
)

# Get project details
project = client.projects.get(project_id=123)

# Create new project
new_project = client.projects.create(
    title="Advanced Graph Algorithms",
    description="Deep dive into graph theory and algorithms",
    difficulty="hard",
    tags=["graphs", "algorithms", "advanced"],
    content="# Advanced Graph Algorithms\n\n..."
)

# Update project
updated = client.projects.update(
    project_id=123,
    title="Updated Title",
    tags=["graphs", "algorithms", "updated"]
)
```

### AI-Powered Recommendations

```python
# Get personalized recommendations
recommendations = client.projects.recommend(
    limit=10,
    include_explanations=True
)

# Recommendations include AI reasoning
for rec in recommendations:
    print(f"🎯 {rec.project.title}")
    print(f"📊 Score: {rec.score:.2f}")
    print(f"🤖 AI Says: {rec.reasoning}")
    print(f"🏷️  Tags: {', '.join(rec.project.tags)}")
    print("---")
```

### Question Analysis

```python
# Analyze coding questions with AI
analysis = client.questions.analyze(
    title="Implement Binary Search Tree",
    content="""
    Implement a binary search tree with insert, delete, and search operations.
    The tree should maintain BST properties.
    """,
    tags=["data-structures", "trees", "algorithms"]
)

print(f"Difficulty: {analysis.difficulty}")
print(f"Quality Score: {analysis.quality_score:.2f}")
print(f"Topics: {', '.join(analysis.topics)}")
print(f"Sentiment: {analysis.sentiment}")
print(f"AI Reasoning: {analysis.reasoning}")
```

### Agent Monitoring

```python
# List available AI agents
agents = client.agents.list()

for agent in agents:
    print(f"🤖 {agent.name} ({agent.type})")
    print(f"📊 Status: {agent.status}")
    print(f"⚙️  Config: {agent.config}")
    print("---")

# Monitor agent in real-time
status = client.agents.status("project_recommendation_agent")

print(f"Status: {status.status}")
print(f"Progress: {status.progress}%")
print(f"Current Task: {status.current_task}")
print(f"Average Execution Time: {status.average_execution_time}s")
```

### Research Integration

```python
# Search academic papers
papers = client.research.search_papers(
    query="graph algorithms optimization",
    limit=5,
    year_from=2020
)

for paper in papers:
    print(f"📄 {paper.title}")
    print(f"👥 Authors: {', '.join(paper.authors)}")
    print(f"📅 Published: {paper.published_date}")
    print(f"🔗 {paper.url}")
    print("---")

# Analyze research paper with AI
analysis = client.research.analyze_paper(
    paper_url="https://arxiv.org/abs/2001.12345",
    focus_areas=["algorithms", "complexity"]
)

print("Paper Analysis:")
print(f"Summary: {analysis.summary}")
print("Key Algorithms:")
for algo in analysis.algorithms:
    print(f"  • {algo.name}: {algo.description}")
    print(f"    Complexity: {algo.complexity}")
```

## Advanced Usage

### Async Operations

```python
import asyncio

async def analyze_multiple_questions():
    questions = [
        {"title": "Two Sum", "content": "...", "tags": ["array"]},
        {"title": "Valid Parentheses", "content": "...", "tags": ["stack"]},
        {"title": "Merge Intervals", "content": "...", "tags": ["array"]}
    ]

    # Analyze multiple questions concurrently
    tasks = [
        client.questions.analyze(**q) for q in questions
    ]

    results = await asyncio.gather(*tasks)

    for question, analysis in zip(questions, results):
        print(f"{question['title']}: {analysis.difficulty} ({analysis.quality_score:.2f})")

asyncio.run(analyze_multiple_questions())
```

### Streaming Responses

```python
# Get real-time agent progress
async def monitor_agent_progress(agent_name):
    async for status in client.agents.stream_status(agent_name):
        print(f"Progress: {status.progress}% - {status.current_task}")

        if status.status == "completed":
            break

# Usage
asyncio.run(monitor_agent_progress("project_recommendation_agent"))
```

### Batch Operations

```python
# Batch create multiple projects
project_data = [
    {
        "title": "Array Algorithms",
        "difficulty": "easy",
        "tags": ["arrays", "algorithms"]
    },
    {
        "title": "String Manipulation",
        "difficulty": "easy",
        "tags": ["strings", "algorithms"]
    }
]

created_projects = client.projects.batch_create(project_data)
print(f"Created {len(created_projects)} projects")
```

### Error Handling

```python
from noleet.exceptions import NoLeetError, AuthenticationError, RateLimitError

try:
    recommendations = client.projects.recommend(limit=100)
except AuthenticationError:
    print("Token expired, please re-authenticate")
    client.auth.refresh_token()
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
    time.sleep(e.retry_after)
    # Retry request
except NoLeetError as e:
    print(f"API Error: {e.message}")
```

### Configuration

```python
from noleet import NoLeet

# Custom configuration
client = NoLeet(
    api_key="your_token",
    base_url="https://api.noleet.ai",  # Default
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Retry failed requests
    user_agent="MyApp/1.0"
)

# Environment variables
import os
os.environ["NOLEET_API_KEY"] = "your_token"
os.environ["NOLEET_BASE_URL"] = "https://staging-api.noleet.ai"

# Now you can initialize without parameters
client = NoLeet()
```

## Data Models

### Project

```python
@dataclass
class Project:
    id: int
    title: str
    slug: str
    description: str
    content: str
    difficulty: Literal["easy", "medium", "hard"]
    status: Literal["draft", "published", "archived"]
    author: User
    category: Optional[Category]
    tags: List[str]
    metadata: Dict[str, Any]
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
```

### Recommendation

```python
@dataclass
class Recommendation:
    project: Project
    score: float  # 0.0 to 1.0
    reasoning: str  # AI-generated explanation
    agent_used: str  # Which agent made this recommendation
```

### QuestionAnalysis

```python
@dataclass
class QuestionAnalysis:
    difficulty: Literal["easy", "medium", "hard"]
    topics: List[str]
    quality_score: float  # 0.0 to 1.0
    sentiment: Literal["positive", "neutral", "negative"]
    reasoning: str  # AI analysis explanation
    suggested_tags: List[str]
    estimated_solve_time: int  # minutes
```

## Rate Limiting

The SDK automatically handles rate limiting:

```python
# SDK will automatically wait when rate limited
recommendations = client.projects.recommend(limit=1000)  # May take time due to rate limits

# Check rate limit status
limits = client.rate_limits()
print(f"Requests remaining: {limits.remaining}")
print(f"Reset time: {limits.reset_time}")
```

## Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# SDK will now log all requests and responses
client = NoLeet(api_key="your_token")
```

## Examples

### Building a Learning Dashboard

```python
from noleet import NoLeet
from datetime import datetime, timedelta

def create_learning_dashboard():
    client = NoLeet(api_key="your_token")

    # Get user's learning profile
    profile = client.users.profile()

    print(f"👋 Welcome back, {profile.username}!")
    print(f"🎯 Current focus: {profile.preferences.get('difficulty_preference', 'mixed')}")

    # Get recent activity
    recent_projects = client.projects.list(
        limit=5,
        sort_by="created_at",
        sort_order="desc"
    )

    print("\n📚 Recent Projects:")
    for project in recent_projects:
        print(f"  • {project.title} ({project.difficulty}) - {project.view_count} views")

    # Get AI recommendations
    recommendations = client.projects.recommend(limit=3)

    print("\n🤖 AI Recommendations:")
    for rec in recommendations:
        print(f"  • {rec.project.title} (score: {rec.score:.1f})")
        print(f"    💭 {rec.reasoning}")

    # Analyze learning progress
    # (This would require additional API endpoints for progress tracking)
    print("\n📊 Learning Progress:")
    print("  Keep up the great work! You're making excellent progress.")

if __name__ == "__main__":
    create_learning_dashboard()
```

### Automated Question Curation

```python
from noleet import NoLeet
import time

def curate_questions():
    client = NoLeet(api_key="your_token")

    # Get questions pending review
    pending_questions = client.questions.list(
        status="pending",
        limit=10
    )

    print(f"Found {len(pending_questions)} questions pending review")

    curated_questions = []

    for question in pending_questions:
        print(f"\nAnalyzing: {question.title}")

        # Use AI to analyze the question
        analysis = client.questions.analyze(
            title=question.title,
            content=question.content,
            tags=question.tags
        )

        print(f"  Difficulty: {analysis.difficulty}")
        print(f"  Quality: {analysis.quality_score:.2f}")
        print(f"  Topics: {', '.join(analysis.topics)}")

        # Auto-approve high-quality questions
        if analysis.quality_score >= 0.8:
            client.questions.update_status(
                question_id=question.id,
                status="approved",
                difficulty=analysis.difficulty,
                tags=analysis.suggested_tags
            )
            curated_questions.append(question)
            print("  ✅ Auto-approved")
        else:
            print("  ⏳ Needs manual review")

        # Respect rate limits
        time.sleep(1)

    print(f"\nCurated {len(curated_questions)} questions automatically")

if __name__ == "__main__":
    curate_questions()
```

## Contributing

We welcome contributions to the NoLeet Python SDK!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This SDK is released under the MIT License. See LICENSE for details.

## Support

- **Documentation**: [docs.noleet.ai/python-sdk](https://docs.noleet.ai/python-sdk)
- **Issues**: [github.com/noleet/noleet-python-sdk/issues](https://github.com/noleet/noleet-python-sdk/issues)
- **Community**: [community.noleet.ai](https://community.noleet.ai)
- **Email**: python-sdk@noleet.ai
