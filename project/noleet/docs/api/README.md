# NoLeet API Documentation

Welcome to the NoLeet API! This comprehensive API provides access to AI-powered coding project recommendations, intelligent question analysis, and advanced learning tools.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [API Endpoints](#api-endpoints)
- [SDKs](#sdks)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Webhooks](#webhooks)

## Overview

The NoLeet API is organized around REST principles and uses JSON for request/response payloads. All API requests must be made over HTTPS.

### Base URL
```
https://api.noleet.ai
```

### Content Type
All requests should include the `Content-Type: application/json` header.

### Response Format
All responses are returned in JSON format with consistent error handling.

## Authentication

The NoLeet API uses JWT (JSON Web Tokens) for authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Getting Started

1. **Register an account** or **login** to get a JWT token
2. **Use the token** in all subsequent API requests
3. **Refresh tokens** before they expire (1 hour)

### Example Authentication Flow

```bash
# 1. Register new account
curl -X POST "https://api.noleet.ai/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password_123"
  }'

# 2. Login to get token
curl -X POST "https://api.noleet.ai/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password_123"
  }'
# Response: {"access_token": "eyJ0eXAi...", "token_type": "bearer", "expires_in": 3600}

# 3. Use token in API requests
curl -H "Authorization: Bearer eyJ0eXAi..." \
     "https://api.noleet.ai/projects/recommend"
```

## Rate Limiting

API requests are rate limited to ensure fair usage:

- **Authenticated users**: 1,000 requests per hour
- **Anonymous users**: 100 requests per hour

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

When you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

## API Endpoints

### Core Endpoints

#### Projects
- `GET /projects` - List projects with filtering and pagination
- `POST /projects` - Create a new project
- `GET /projects/recommend` - **AI-powered project recommendations**
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project

#### Questions
- `GET /questions` - List coding questions
- `POST /questions/analyze` - **AI-powered question analysis**

#### AI Agents
- `GET /agents` - List available AI agents
- `GET /agents/{name}/status` - Get real-time agent status

#### User Management
- `GET /users/profile` - Get user profile and preferences
- `PUT /users/profile` - Update user profile

#### Research
- `GET /research/papers` - Search academic papers
- `POST /research/analyze-paper` - **AI-powered paper analysis**

### AI-Powered Features

NoLeet includes several AI-powered endpoints that leverage our multi-agent system:

#### Project Recommendations
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://api.noleet.ai/projects/recommend?limit=5&include_explanations=true"
```

**Features:**
- Analyzes user interaction history
- Considers skill level and learning goals
- Uses semantic matching with embeddings
- Provides AI-generated reasoning

#### Question Analysis
```bash
curl -X POST "https://api.noleet.ai/questions/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Two Sum",
    "content": "Given an array of integers, return indices of two numbers that add up to target.",
    "tags": ["array", "hash-table"]
  }'
```

**Analysis includes:**
- Difficulty assessment (easy/medium/hard)
- Topic categorization
- Quality scoring
- Sentiment analysis

#### Research Paper Analysis
```bash
curl -X POST "https://api.noleet.ai/research/analyze-paper" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_url": "https://arxiv.org/abs/2001.12345",
    "focus_areas": ["algorithms", "complexity"]
  }'
```

**Extracts:**
- Paper summary and key contributions
- Algorithm implementations
- Complexity analysis
- Related topics and applications

## SDKs

### Python SDK

```python
from noleet import NoLeet

# Initialize client
client = NoLeet(api_key="your_jwt_token")

# Get AI-powered recommendations
recommendations = client.projects.recommend(limit=5)
for rec in recommendations:
    print(f"{rec.project.title} (score: {rec.score:.2f})")
    print(f"Reasoning: {rec.reasoning}")

# Analyze a question
analysis = client.questions.analyze(
    title="Two Sum",
    content="Given an array of integers...",
    tags=["array", "hash-table"]
)
print(f"Difficulty: {analysis.difficulty}")
print(f"Topics: {', '.join(analysis.topics)}")
print(f"Quality Score: {analysis.quality_score}")
```

### JavaScript SDK

```javascript
import { NoLeet } from 'noleet-sdk';

// Initialize client
const client = new NoLeet({ apiKey: 'your_jwt_token' });

// Get recommendations
const recommendations = await client.projects.getRecommendations({
  limit: 5,
  includeExplanations: true
});

recommendations.forEach(rec => {
  console.log(`${rec.project.title} (score: ${rec.score})`);
  console.log(`Reasoning: ${rec.reasoning}`);
});

// Analyze question
const analysis = await client.questions.analyze({
  title: 'Two Sum',
  content: 'Given an array of integers...',
  tags: ['array', 'hash-table']
});

console.log(`Difficulty: ${analysis.difficulty}`);
console.log(`Quality Score: ${analysis.quality_score}`);
```

### Go SDK

```go
package main

import (
    "fmt"
    "github.com/noleet/noleet-go"
)

func main() {
    client := noleet.NewClient("your_jwt_token")

    // Get recommendations
    recommendations, err := client.Projects.Recommend(&noleet.RecommendOptions{
        Limit: 5,
        IncludeExplanations: true,
    })
    if err != nil {
        panic(err)
    }

    for _, rec := range recommendations {
        fmt.Printf("%s (score: %.2f)\n", rec.Project.Title, rec.Score)
        fmt.Printf("Reasoning: %s\n", rec.Reasoning)
    }
}
```

## Examples

### Complete User Journey

```python
import asyncio
from noleet import NoLeet

async def user_journey():
    client = NoLeet(api_key="your_token")

    # 1. Get personalized recommendations
    recommendations = await client.projects.recommend(limit=3)
    print("Recommended projects:")
    for rec in recommendations:
        print(f"• {rec.project.title} - {rec.reasoning}")

    # 2. Explore a project
    project = await client.projects.get(recommendations[0].project.id)
    print(f"\nExploring: {project.title}")
    print(f"Difficulty: {project.difficulty}")
    print(f"Tags: {', '.join(project.tags)}")

    # 3. Analyze a coding question
    analysis = await client.questions.analyze(
        title="Implement Binary Search",
        content="Write a function that implements binary search on a sorted array.",
        tags=["algorithms", "search"]
    )
    print(f"\nQuestion Analysis:")
    print(f"Difficulty: {analysis.difficulty}")
    print(f"Topics: {', '.join(analysis.topics)}")
    print(f"Quality: {analysis.quality_score:.2f}")

    # 4. Search for relevant research
    papers = await client.research.search_papers(
        query="binary search algorithms optimization",
        limit=2
    )
    print(f"\nRelevant Research:")
    for paper in papers:
        print(f"• {paper.title} by {', '.join(paper.authors)}")

asyncio.run(user_journey())
```

### Real-time Agent Monitoring

```python
import asyncio
from noleet import NoLeet

async def monitor_agents():
    client = NoLeet(api_key="your_token")

    # Get all agents
    agents = await client.agents.list()
    print("Available AI Agents:")
    for agent in agents:
        print(f"• {agent.name} ({agent.type}) - {agent.status}")

    # Monitor specific agent
    while True:
        status = await client.agents.get_status("project_recommendation_agent")
        print(f"Agent Status: {status.status} ({status.progress}%)")

        if status.status == "completed":
            break

        await asyncio.sleep(1)

asyncio.run(monitor_agents())
```

### Batch Question Processing

```python
import asyncio
from noleet import NoLeet

async def batch_analyze_questions():
    client = NoLeet(api_key="your_token")

    questions = [
        {
            "title": "Two Sum",
            "content": "Given an array of integers, return indices of two numbers that add up to target.",
            "tags": ["array", "hash-table"]
        },
        {
            "title": "Valid Parentheses",
            "content": "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.",
            "tags": ["string", "stack"]
        }
    ]

    # Analyze multiple questions
    results = await asyncio.gather(*[
        client.questions.analyze(**q) for q in questions
    ])

    for i, (question, analysis) in enumerate(zip(questions, results)):
        print(f"Question {i+1}: {question['title']}")
        print(f"  Difficulty: {analysis.difficulty}")
        print(f"  Quality Score: {analysis.quality_score:.2f}")
        print(f"  Topics: {', '.join(analysis.topics)}")
        print()

asyncio.run(batch_analyze_questions())
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid input data",
  "details": {
    "title": ["Title is required"],
    "difficulty": ["Must be one of: easy, medium, hard"]
  }
}
```

### Handling Errors in Code

```python
try:
    recommendations = client.projects.recommend(limit=10)
except NoLeetError as e:
    if e.status_code == 401:
        # Token expired, refresh authentication
        refresh_token()
    elif e.status_code == 429:
        # Rate limited, wait and retry
        time.sleep(60)
        retry_request()
    else:
        print(f"API Error: {e.message}")
```

## Webhooks

Webhooks allow you to receive real-time notifications about events in your NoLeet account.

### Supported Events

- `agent.completed` - AI agent finished processing
- `project.created` - New project published
- `question.analyzed` - Question analysis completed
- `user.activity` - User interaction logged

### Webhook Configuration

```bash
# Register webhook endpoint
curl -X POST "https://api.noleet.ai/webhooks" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/noleet",
    "events": ["agent.completed", "project.created"],
    "secret": "your_webhook_secret"
  }'
```

### Webhook Payload

```json
{
  "event": "agent.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "agent_name": "project_recommendation_agent",
    "run_id": "run_12345",
    "execution_time": 2.5,
    "result": {
      "recommendations_count": 5,
      "user_id": 123
    }
  },
  "signature": "sha256=..."
}
```

### Security

Webhook requests include an `X-NoLeet-Signature` header for verification:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

## Support

### Getting Help

1. **API Documentation**: Complete OpenAPI 3.0 specification available at `/docs`
2. **Interactive Explorer**: Try API endpoints directly at `/docs/interactive`
3. **Community Forums**: Join discussions at [community.noleet.ai](https://community.noleet.ai)
4. **Support Tickets**: Create tickets at [support.noleet.ai](https://support.noleet.ai)

### SDK Installation

```bash
# Python
pip install noleet

# JavaScript
npm install noleet-sdk

# Go
go get github.com/noleet/noleet-go
```

### Versioning

API versions are included in the URL path: `https://api.noleet.ai/v1/`

We follow semantic versioning and maintain backward compatibility within major versions.

### Changelog

#### v1.0.0 (Current)
- Initial release with AI-powered recommendations
- Multi-agent orchestration system
- Research paper analysis
- Comprehensive question analysis
- JWT authentication
- Rate limiting and security features

---

For more detailed information, visit the [interactive API documentation](https://api.noleet.ai/docs) or check the [GitHub repository](https://github.com/noleet/noleet).
