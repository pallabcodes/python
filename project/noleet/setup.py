"""Setup script for NoLeet package."""

from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="noleet",
    version="0.1.0",
    description="AI-powered DSA learning through real-world projects",
    author="AI Engineer",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "noleet=noleet.cli.main:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
