"""
Setup script for AI Framework

Install with: pip install -e .
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aiframework",
    version="1.0.0",
    author="AI Engineer Framework",
    author_email="framework@ai-engineer.dev",
    description="Production-Ready AI Library for Developers - Multi-Provider LLM Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aiframework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "asyncio",
        "typing",
        "pathlib",
        "logging",
        "dataclasses",
        "json",
        "time",
        "collections",
        # Optional dependencies for enhanced functionality
        "aiofiles;python_version>='3.7'",  # For file operations
        "pydantic>=1.8.0",  # For data validation (optional)
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.14.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.800",
            "sphinx>=4.0.0",  # For documentation
            "sphinx-rtd-theme>=0.5.0",
        ],
        "web": [
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
            "starlette>=0.14.0",
        ],
        "monitoring": [
            "prometheus-client>=0.11.0",
            "grafana-api>=1.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "aiframework-dev=aiframework.development:create_project",
            "aiframework-quick=aiframework.development:quick_ai",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
