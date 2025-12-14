"""Setup script for Acquisitor."""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name="acquisitor",
    version="0.1.0",
    description="AI-powered tool for identifying acquisition opportunities through relative product development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Acquisitor Team",
    author_email="team@acquisitor.dev",
    url="https://github.com/acquisitor/acquisitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "acquisitor=cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
