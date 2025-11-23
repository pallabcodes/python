"""Code Scaffolding Agent - Auto-generates project boilerplate and starter code."""

import asyncio
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from noleet.core.models import Project
from aiframework import AIFramework
from aiframework.types import GenerationRequest


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"


class Framework(Enum):
    """Supported frameworks/libraries."""
    # Python
    FLASK = "flask"
    DJANGO = "django"
    FASTAPI = "fastapi"
    NUMPY = "numpy"
    PANDAS = "pandas"

    # JavaScript
    REACT = "react"
    VUE = "vue"
    EXPRESS = "express"
    NODE = "node"

    # Java
    SPRING = "spring"
    ANDROID = "android"

    # General
    NONE = "none"


@dataclass
class ScaffoldingContext:
    """Context for code scaffolding generation."""
    project: Project
    user_level: str  # beginner, intermediate, advanced
    preferred_language: Optional[Language] = None
    preferred_framework: Optional[Framework] = None
    career_focus: Optional[str] = None
    time_available: str = "medium"  # short, medium, long
    include_tests: bool = True
    include_docs: bool = True
    project_complexity: str = "medium"  # simple, medium, complex


@dataclass
class ScaffoldedFile:
    """Represents a generated file in the scaffold."""
    path: str
    content: str
    description: str
    language: Language
    executable: bool = False
    is_template: bool = False


@dataclass
class ProjectScaffold:
    """Complete project scaffolding with all files and structure."""
    project_name: str
    description: str
    language: Language
    framework: Framework
    files: List[ScaffoldedFile] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)  # package -> version
    setup_instructions: List[str] = field(default_factory=list)
    run_instructions: List[str] = field(default_factory=list)


class CodeScaffoldingAgent:
    """Agent that generates complete project boilerplate and starter code."""

    def __init__(self, ai_framework: AIFramework):
        """
        Initialize the Code Scaffolding Agent.

        Args:
            ai_framework: AI Framework instance for code generation
        """
        self._ai_framework = ai_framework
        self._logger = logging.getLogger(__name__)

        # Template storage
        self._templates: Dict[str, Dict[str, str]] = {}

    async def generate_scaffold(
        self,
        context: ScaffoldingContext
    ) -> ProjectScaffold:
        """
        Generate complete project scaffolding based on context.

        Args:
            context: Scaffolding context with project and user preferences

        Returns:
            Complete project scaffold with all files and instructions
        """
        try:
            self._logger.info(
                f"Generating scaffold for project: {context.project.name} "
                f"(language: {context.preferred_language}, level: {context.user_level})"
            )

            # Determine optimal language and framework
            language, framework = await self._determine_tech_stack(context)

            # Create scaffold structure
            scaffold = ProjectScaffold(
                project_name=self._sanitize_name(context.project.name),
                description=context.project.description,
                language=language,
                framework=framework
            )

            # Generate core project files
            await self._generate_core_files(scaffold, context)

            # Generate framework-specific files
            await self._generate_framework_files(scaffold, context)

            # Generate tests if requested
            if context.include_tests:
                await self._generate_test_files(scaffold, context)

            # Generate documentation if requested
            if context.include_docs:
                await self._generate_documentation(scaffold, context)

            # Generate configuration files
            await self._generate_config_files(scaffold, context)

            # Set up dependencies and instructions
            await self._setup_dependencies(scaffold, context)
            self._generate_setup_instructions(scaffold, context)

            self._logger.info(
                f"Generated scaffold with {len(scaffold.files)} files "
                f"and {len(scaffold.directories)} directories"
            )

            return scaffold

        except Exception as e:
            self._logger.error(f"Failed to generate scaffold: {e}")
            raise

    async def _determine_tech_stack(
        self,
        context: ScaffoldingContext
    ) -> Tuple[Language, Framework]:
        """
        Determine the optimal language and framework based on context.

        Args:
            context: Scaffolding context

        Returns:
            Tuple of (language, framework)
        """
        # Default to Python for DSA projects
        if not context.preferred_language:
            context.preferred_language = Language.PYTHON

        language = context.preferred_language

        # Determine framework based on project type and user preferences
        framework = await self._recommend_framework(context, language)

        return language, framework

    async def _recommend_framework(
        self,
        context: ScaffoldingContext,
        language: Language
    ) -> Framework:
        """
        Recommend appropriate framework based on context.

        Args:
            context: Scaffolding context
            language: Selected programming language

        Returns:
            Recommended framework
        """
        if context.preferred_framework:
            return context.preferred_framework

        # Framework recommendations based on project type and user level
        project_name = context.project.name.lower()
        project_desc = context.project.description.lower()

        if language == Language.PYTHON:
            if "web" in project_name or "api" in project_desc:
                if context.user_level == "beginner":
                    return Framework.FLASK  # Simpler for beginners
                else:
                    return Framework.FASTAPI  # Modern async framework
            elif "data" in project_desc or "analysis" in project_desc:
                return Framework.PANDAS  # Data processing
            else:
                return Framework.NONE  # Standard library only

        elif language == Language.JAVASCRIPT:
            if "web" in project_name or "frontend" in project_desc:
                return Framework.REACT
            elif "api" in project_desc or "backend" in project_desc:
                return Framework.EXPRESS
            else:
                return Framework.NODE

        elif language == Language.JAVA:
            if "android" in project_desc or "mobile" in project_desc:
                return Framework.ANDROID
            else:
                return Framework.SPRING

        # Default to no framework
        return Framework.NONE

    async def _generate_core_files(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Generate core project files."""

        # Main application file
        main_file = await self._generate_main_file(scaffold, context)
        scaffold.files.append(main_file)

        # README
        readme = await self._generate_readme(scaffold, context)
        scaffold.files.append(readme)

        # Requirements/dependencies file
        if scaffold.language == Language.PYTHON:
            requirements = ScaffoldedFile(
                path="requirements.txt",
                content=self._get_requirements_content(scaffold),
                description="Python dependencies",
                language=Language.PYTHON
            )
            scaffold.files.append(requirements)

    async def _generate_main_file(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> ScaffoldedFile:
        """Generate the main application file."""

        # Generate appropriate main file content based on language and framework
        if scaffold.language == Language.PYTHON:
            if scaffold.framework == Framework.FASTAPI:
                content = await self._generate_fastapi_main(context)
            elif scaffold.framework == Framework.FLASK:
                content = await self._generate_flask_main(context)
            else:
                content = await self._generate_python_main(context)

            filename = "main.py"

        elif scaffold.language == Language.JAVASCRIPT:
            if scaffold.framework == Framework.REACT:
                content = await self._generate_react_main(context)
                filename = "src/App.js"
            elif scaffold.framework == Framework.EXPRESS:
                content = await self._generate_express_main(context)
                filename = "server.js"
            else:
                content = await self._generate_nodejs_main(context)
                filename = "app.js"

        else:
            # Generic main file for other languages
            content = await self._generate_generic_main(context, scaffold.language)
            filename = f"main.{scaffold.language.value}"

        return ScaffoldedFile(
            path=filename,
            content=content,
            description="Main application file",
            language=scaffold.language,
            executable=True
        )

    async def _generate_fastapi_main(self, context: ScaffoldingContext) -> str:
        """Generate FastAPI main application."""
        prompt = f"""
Generate a FastAPI application starter for a DSA project: "{context.project.name}"

Project Description: {context.project.description}

Requirements:
- Use FastAPI for the web framework
- Include basic project structure for {context.project.name}
- Add appropriate DSA-related endpoints
- Include error handling and logging
- Add basic documentation with OpenAPI/Swagger
- User level: {context.user_level}
- Keep it simple but functional

Return only the Python code, no explanations.
"""

        request = GenerationRequest(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3
        )

        response = await self._ai_framework.generate(request)
        return response.content.strip()

    async def _generate_flask_main(self, context: ScaffoldingContext) -> str:
        """Generate Flask main application."""
        prompt = f"""
Generate a Flask application starter for a DSA project: "{context.project.name}"

Project Description: {context.project.description}

Requirements:
- Use Flask for the web framework
- Include basic project structure
- Add appropriate DSA-related routes
- Include error handling
- User level: {context.user_level}
- Keep it educational and simple

Return only the Python code, no explanations.
"""

        request = GenerationRequest(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3
        )

        response = await self._ai_framework.generate(request)
        return response.content.strip()

    async def _generate_python_main(self, context: ScaffoldingContext) -> str:
        """Generate basic Python main file."""
        base_code = f'''"""
{context.project.name} - DSA Project Implementation

{context.project.description}

This is an auto-generated starter template for {context.user_level} level developers.
"""

import logging
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {self._sanitize_class_name(context.project.name)}:
    """
    Main class for {context.project.name} implementation.

    This class provides the core functionality for the DSA project.
    """

    def __init__(self):
        """Initialize the project class."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing {context.project.name}")

    def run_example(self) -> None:
        """
        Run a basic example of the DSA implementation.

        This method demonstrates the core algorithm/concept.
        """
        self.logger.info("Running example...")

        # TODO: Implement the core DSA algorithm here
        # This is where you'll implement {context.project.name}

        print(f"🚀 {context.project.name} Example")
        print("=" * 50)

        # Example implementation placeholder
        result = self._core_algorithm()
        print(f"Result: {{result}}")

        self.logger.info("Example completed")

    def _core_algorithm(self) -> Any:
        """
        Core DSA algorithm implementation.

        Returns:
            Result of the algorithm
        """
        # TODO: Replace with actual DSA implementation
        return "Hello, DSA World!"

    def run_tests(self) -> bool:
        """
        Run basic tests to verify implementation.

        Returns:
            True if all tests pass, False otherwise
        """
        self.logger.info("Running tests...")

        # TODO: Add comprehensive tests
        print("\\n🧪 Running Tests...")
        print("-" * 30)

        try:
            # Basic functionality test
            result = self._core_algorithm()
            assert result is not None, "Algorithm should return a result"

            print("✅ Basic functionality test passed")
            return True

        except Exception as e:
            print(f"❌ Test failed: {{e}}")
            return False


def main():
    """Main entry point."""
    print(f"🎯 {{context.project.name}}")
    print(f"📚 DSA Learning Project")
    print("=" * 50)

    # Initialize the project
    project = {self._sanitize_class_name(context.project.name)}()

    # Run example
    project.run_example()

    # Run tests
    print("\\n" + "=" * 50)
    if project.run_tests():
        print("\\n🎉 All tests passed! Ready to implement your DSA solution.")
    else:
        print("\\n⚠️  Some tests failed. Check your implementation.")


if __name__ == "__main__":
    main()
'''

        return base_code

    async def _generate_readme(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> ScaffoldedFile:
        """Generate README file."""
        readme_content = f'''# {scaffold.project_name}

{scaffold.description}

## 🚀 Auto-Generated DSA Project

This project was automatically scaffolded for **{context.user_level}** level developers using NoLeet's AI Code Scaffolding Agent.

### 🎯 Project Overview

**Difficulty Level:** {context.project_complexity.title()}
**Target Audience:** {context.user_level.title()} developers
**Estimated Time:** {context.time_available.title()} timeframe

### 🛠️ Technology Stack

- **Language:** {scaffold.language.value.title()}
- **Framework:** {scaffold.framework.value.title() if scaffold.framework != Framework.NONE else 'None (Standard Library)'}

### 📁 Project Structure

```
{scaffold.project_name}/
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── tests/                  # Test files
├── docs/                   # Documentation
└── README.md              # This file
```

### 🚀 Getting Started

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   ```bash
   python main.py
   ```

3. **Run Tests:**
   ```bash
   python -m pytest tests/
   ```

### 🎓 Learning Objectives

{chr(10).join(f"- {obj}" for obj in context.project.learning_outcomes[:5])}

### 🔧 Next Steps

1. **Implement the Core Algorithm** in `main.py`
2. **Add Comprehensive Tests** in the `tests/` directory
3. **Enhance Documentation** in the `docs/` directory
4. **Customize Based on Your Needs**

### 📚 DSA Concepts Covered

{chr(10).join(f"- {topic.replace('_', ' ').title()}" for topic in context.project.topics)}

### 🤝 Contributing

This is an auto-generated starter template. Feel free to modify and extend it based on your learning goals and project requirements.

### 📄 License

This project is part of your DSA learning journey. Use it to build impressive portfolio pieces!

---

**Generated by NoLeet AI Code Scaffolding Agent** 🤖
'''

        return ScaffoldedFile(
            path="README.md",
            content=readme_content,
            description="Project README and documentation",
            language=Language.PYTHON,  # Markdown is language-agnostic
            is_template=False
        )

    async def _generate_framework_files(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Generate framework-specific files."""
        # Framework-specific files would be generated here
        # For now, we'll keep it simple and focus on core functionality
        pass

    async def _generate_test_files(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Generate test files."""
        test_content = f'''"""
Tests for {scaffold.project_name}

Auto-generated test suite for {context.user_level} level DSA implementation.
"""

import pytest
from {scaffold.project_name.lower().replace(' ', '_')} import {self._sanitize_class_name(scaffold.project_name)}


class Test{self._sanitize_class_name(scaffold.project_name)}:
    """Test cases for the DSA project."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project = {self._sanitize_class_name(scaffold.project_name)}()

    def test_initialization(self):
        """Test that the project initializes correctly."""
        assert self.project is not None
        assert hasattr(self.project, 'run_example')
        assert hasattr(self.project, 'run_tests')

    def test_core_algorithm_returns_result(self):
        """Test that the core algorithm returns a result."""
        result = self.project._core_algorithm()
        assert result is not None

    def test_run_example_prints_output(self, capsys):
        """Test that run_example produces output."""
        self.project.run_example()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    # TODO: Add more specific test cases based on the actual DSA algorithm
    # def test_algorithm_correctness(self):
    #     """Test that the algorithm produces correct results."""
    #     # Add specific test cases for your DSA implementation
    #     pass

    # def test_edge_cases(self):
    #     """Test edge cases and error conditions."""
    #     # Add tests for edge cases
    #     pass

    # def test_performance(self):
    #     """Test algorithm performance."""
    #     # Add performance benchmarks
    #     pass
'''

        test_file = ScaffoldedFile(
            path=f"tests/test_{scaffold.project_name.lower().replace(' ', '_')}.py",
            content=test_content,
            description="Comprehensive test suite",
            language=Language.PYTHON
        )

        scaffold.files.append(test_file)
        scaffold.directories.append("tests")

    async def _generate_documentation(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Generate documentation files."""
        docs_content = f'''# {scaffold.project_name} - Technical Documentation

## Overview

{context.project.description}

This document provides technical details for implementing {scaffold.project_name}.

## Architecture

### Core Components

1. **Main Class**: `{self._sanitize_class_name(scaffold.project_name)}`
   - Handles the primary DSA algorithm implementation
   - Provides example usage and testing methods

2. **Algorithm Implementation**: `_core_algorithm()`
   - Contains the main DSA logic
   - Should be modified to implement the actual algorithm

3. **Testing Framework**: `tests/`
   - Comprehensive test suite
   - Includes basic functionality and correctness tests

## Implementation Guide

### Step 1: Understand the Problem
{context.project.description}

### Step 2: Plan Your Solution
- Break down the problem into smaller components
- Identify the DSA concepts and data structures needed
- Plan your algorithmic approach

### Step 3: Implement the Core Algorithm
Modify the `_core_algorithm()` method in `main.py`:

```python
def _core_algorithm(self) -> Any:
    # Your DSA implementation here
    pass
```

### Step 4: Add Comprehensive Tests
Extend the test file with specific test cases for your algorithm.

### Step 5: Optimize and Refine
- Analyze time and space complexity
- Optimize for better performance
- Add error handling and edge case management

## DSA Concepts Involved

{chr(10).join(f"### {topic.replace('_', ' ').title()}" for topic in context.project.topics)}

## Learning Objectives

{chr(10).join(f"- {obj}" for obj in context.project.learning_outcomes)}

## Next Steps

1. Implement the core algorithm
2. Add comprehensive tests
3. Optimize performance
4. Add error handling
5. Create additional features

## Resources

- Review the DSA concepts listed above
- Check algorithm complexity requirements
- Consider edge cases and input validation
- Test thoroughly before deployment

---

**Generated by NoLeet AI Code Scaffolding Agent** 🤖
'''

        docs_file = ScaffoldedFile(
            path="docs/technical_guide.md",
            content=docs_content,
            description="Technical implementation guide",
            language=Language.PYTHON,
            is_template=False
        )

        scaffold.files.append(docs_file)
        scaffold.directories.append("docs")

    async def _generate_config_files(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Generate configuration files."""
        # Generate .gitignore
        gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.coverage
.pytest_cache/
htmlcov/

# Distribution
dist/
build/
*.egg-info/
'''

        scaffold.files.append(ScaffoldedFile(
            path=".gitignore",
            content=gitignore_content,
            description="Git ignore file",
            language=Language.PYTHON
        ))

    async def _setup_dependencies(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Set up project dependencies."""
        # Basic Python dependencies
        scaffold.dependencies.update({
            "pytest": ">=7.0.0",
            "black": ">=22.0.0",
            "flake8": ">=4.0.0",
            "mypy": ">=1.0.0"
        })

        # Framework-specific dependencies
        if scaffold.framework == Framework.FASTAPI:
            scaffold.dependencies.update({
                "fastapi": ">=0.100.0",
                "uvicorn": ">=0.20.0"
            })
        elif scaffold.framework == Framework.FLASK:
            scaffold.dependencies.update({
                "flask": ">=2.0.0"
            })
        elif scaffold.framework == Framework.PANDAS:
            scaffold.dependencies.update({
                "pandas": ">=1.5.0",
                "numpy": ">=1.21.0"
            })

    def _generate_setup_instructions(
        self,
        scaffold: ProjectScaffold,
        context: ScaffoldingContext
    ) -> None:
        """Generate setup and run instructions."""
        scaffold.setup_instructions = [
            f"cd {scaffold.project_name}",
            "python -m venv venv",
            "source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
            "pip install -r requirements.txt",
            "python main.py"
        ]

        scaffold.run_instructions = [
            "python main.py  # Run the main application",
            "python -m pytest tests/  # Run tests",
            "python -c 'from main import *; project = DSAProject(); project.run_tests()'  # Quick test"
        ]

    def _get_requirements_content(self, scaffold: ProjectScaffold) -> str:
        """Generate requirements.txt content."""
        lines = []
        for package, version in scaffold.dependencies.items():
            lines.append(f"{package}{version}")
        return "\n".join(lines)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for use in code."""
        return name.lower().replace(" ", "_").replace("-", "_")

    def _sanitize_class_name(self, name: str) -> str:
        """Convert project name to valid class name."""
        # Remove special characters and title case
        clean_name = "".join(c for c in name if c.isalnum() or c == " ").title()
        return clean_name.replace(" ", "") + "Project"
