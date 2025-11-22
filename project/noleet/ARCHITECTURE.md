# NoLeet Architecture

## Overview

NoLeet is designed as a production-grade platform that transforms DSA learning through building real-world products. The architecture emphasizes modularity, extensibility, and the ability to integrate cutting-edge research.

## Core Principles

1. **Uniqueness First**: Every component designed to showcase innovative approaches
2. **Production-Grade**: Google SDE-3 level code quality throughout
3. **Research-Backed**: Integration points for research papers and custom algorithms
4. **Plain English**: All user-facing content in simple, clear language
5. **CLI First**: Command-line interface for power users, web later

## Architecture Layers

### 1. Core Domain Layer (`core/`)

**Purpose**: Domain models and business logic

**Components**:
- `models.py`: Core data models (Project, Task, Subtask, Topic, etc.)
- Domain entities with rich behavior
- Type-safe enums and dataclasses

**Key Models**:
- `Project`: Represents a complete project with tasks
- `Task`: A major milestone in a project
- `Subtask`: Granular steps within a task
- `DSAInvolvement`: Tracks which DSA concepts are used and to what degree
- `ResearchReference`: Links to research papers and implementations

### 2. Matching Engine (`matching/`)

**Purpose**: Intelligent project matching based on topic combinations

**Components**:
- `matcher.py`: Project matching algorithm
- Score-based ranking system
- Topic combination analysis

**Features**:
- Multi-topic matching
- Match score calculation
- Topic combination extraction

### 3. Storage Layer (`storage/`)

**Purpose**: Data persistence and retrieval

**Components**:
- `repository.py`: Project data repository
- JSON-based storage (extensible to database)
- Caching for performance

**Features**:
- Serialization/deserialization
- Project CRUD operations
- Data validation

### 4. Curation System (`curation/`)

**Purpose**: Project creation and curation tools

**Components**:
- `builder.py`: Builder pattern for project creation
- Research integration helpers
- Project validation

**Features**:
- Fluent API for project creation
- Research reference management
- DSA involvement tracking

### 5. CLI Interface (`cli/`)

**Purpose**: Command-line user interface

**Components**:
- `main.py`: CLI command handlers
- `entry_point.py`: Entry point script

**Commands**:
- `topics`: List available DSA topics
- `find <topics...>`: Find projects matching topics
- `show <project_id>`: Display project details

### 6. Examples (`examples/`)

**Purpose**: Sample projects and demonstrations

**Components**:
- `sample_projects.py`: Example projects
- Demonstrates the platform capabilities

## Data Flow

```
User Input (CLI)
    ↓
Topic Selection
    ↓
Matching Engine
    ↓
Repository (Load Projects)
    ↓
Filter & Rank Projects
    ↓
Display Results
    ↓
User Selects Project
    ↓
Display Tasks/Subtasks with DSA Involvement
```

## Extension Points

### Research Integration

The architecture provides clear extension points for research integration:

1. **Research References**: Projects can reference research papers
2. **Custom Algorithms**: Support for custom algorithm implementations
3. **Algorithm Modifications**: Track modifications to existing algorithms

### Storage Backends

Currently uses JSON files, but designed to support:
- SQL databases
- NoSQL databases
- Remote APIs

### Matching Algorithms

Current matching is score-based, but can be extended with:
- Machine learning models
- Collaborative filtering
- Content-based recommendations

## Uniqueness Mechanisms

### 1. Research Paper Integration

Projects can integrate multiple research papers, mixing and matching:
- Custom modifications to algorithms
- Combination of techniques from different papers
- Novel applications of existing research

### 2. Custom Data Structures

Support for custom data structures:
- Optimized for specific use cases
- Performance-critical implementations
- Memory-efficient designs

### 3. Algorithm Customization

- Modified algorithms for specific requirements
- Hybrid approaches combining multiple techniques
- Performance optimizations

## Performance Considerations

### Current Optimizations

1. **Caching**: Project data cached in memory
2. **Lazy Loading**: Projects loaded on demand
3. **Efficient Matching**: O(n) matching algorithm

### Future Optimizations

1. **Indexing**: Topic-based indexes for faster lookups
2. **Precomputation**: Pre-computed match scores
3. **Streaming**: Stream large project lists

## Testing Strategy

### Unit Tests

- Model validation
- Matching algorithm correctness
- Repository operations

### Integration Tests

- End-to-end CLI workflows
- Data persistence
- Project creation

### Performance Tests

- Matching performance with large datasets
- Storage I/O performance
- Memory usage

## Future Enhancements

### Web Interface

- REST API layer
- Web frontend
- Interactive project browser

### Advanced Features

- Project progress tracking
- Code template generation
- Integration with GitHub
- Community contributions

### Research Integration

- Automated research paper analysis
- Algorithm extraction from papers
- Custom algorithm generator

## File Size Compliance

All files follow strict size limits:
- Maximum 200 lines per file
- Maximum 50 lines per function
- Maximum 7 methods per class

This ensures maintainability and debuggability.

