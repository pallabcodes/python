# NoLeet

A production-grade platform that transforms DSA learning from soul-sucking LeetCode grinding into building real-world products that impress Google engineers.

## Vision

We teach DSA through building tangible products, not solving abstract problems. Every concept learned is immediately applied to create something impressive.

## Core Concept

1. **Select Topics**: Choose DSA concepts (e.g., "DP", "DP + Sliding Window")
2. **Get Projects**: System suggests projects heavily relying on your selected topics
3. **Build Step-by-Step**: Each project broken into plain-English tasks with DSA involvement percentages
4. **Showcase**: Build products that turn heads at Google

## Quick Start

### Installation

```bash
cd project
python3 -m noleet.setup_data
```

### Usage

**List available topics:**
```bash
python3 -m noleet.cli.main topics
```

**Find projects by topics:**
```bash
python3 -m noleet.cli.main find dynamic_programming sliding_window merge_intervals
```

**View project details:**
```bash
python3 -m noleet.cli.main show real_time_analytics_engine
```

## Architecture

- **CLI First**: Command-line interface for power users
- **Web Later**: Web application for broader audience
- **Research-Backed**: Integrates cutting-edge research papers and custom algorithms
- **Production-Grade**: Google SDE-3 level code quality

## Project Structure

```
noleet/
├── core/                    # Core data models and domain logic
├── matching/                # Project matching engine
├── curation/                # Project curation and research integration
├── cli/                     # CLI interface
├── storage/                 # Data persistence layer
├── examples/                # Example projects and demos
└── ARCHITECTURE.md          # Detailed architecture documentation
```

## Key Features

### Topic-Based Project Matching

Select one or multiple DSA topics, and the system finds projects that heavily rely on those concepts.

### Plain English Tasks

Every task and subtask is written in simple, clear language - no technical jargon barriers.

### DSA Involvement Tracking

See exactly which DSA concepts are used in each task/subtask and to what percentage.

### Research Integration

Projects reference research papers, open-source implementations, and custom algorithm modifications.

### Production-Grade Quality

Every component follows Google SDE-3 standards:
- Maximum 200 lines per file
- Maximum 50 lines per function
- Comprehensive error handling
- Full type safety
- Production-ready logging

## Uniqueness

NoLeet stands out by:

1. **Research-Backed**: Integrates multiple research papers, mixing and matching techniques
2. **Custom Algorithms**: Support for rare, modified, and customized algorithms
3. **Real-World Focus**: Every project builds something tangible, not abstract problems
4. **Plain English**: All instructions in simple language, accessible to all skill levels

## Contributing

This is an internal product. Contributions should:
- Follow Google SDE-3 production standards
- Maintain file/function size limits
- Include comprehensive tests
- Document research references
- Use plain English for user-facing content

## Data Gathering

NoLeet includes a comprehensive data gathering system to collect DSA questions from public sources:

```bash
# Gather questions from LeetCode, Reddit, etc.
python3 -m noleet.cli.main data gather --max-results 50
```

See [DATA_GATHERING.md](DATA_GATHERING.md) for details.

## Research Integration

Integrate research papers and algorithms into projects:

- Parse research papers (PDF, text)
- Extract algorithms and techniques
- Match papers to projects based on topics
- Suggest paper combinations
- Track custom modifications

See [RESEARCH_INTEGRATION.md](RESEARCH_INTEGRATION.md) for details.

## Future Enhancements

- Web interface (REST API + frontend)
- More project templates
- GitHub integration
- Progress tracking
- Community contributions
- Medium/YouTube scrapers
- ML-based topic classification

