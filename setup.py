#!/usr/bin/env python3
"""
AgentOS Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text().splitlines() 
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="agentos",
    version="1.0.0",
    description="Production AI Agent Runtime with Memory and Safe Tool Sandboxing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AgentOS Team",
    author_email="team@agentos.dev",
    url="https://github.com/agentos/agentos",
    packages=find_packages(),
    py_modules=[
        "agentos", "cli_agent", "answerer", "config", 
        "db", "threader", "utils", "isolate"
    ],
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0"],
        "docker": ["docker>=6.0.0"],
    },
    entry_points={
        "console_scripts": [
            "agentos=agentos:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    keywords="ai agent llm automation cli runtime",
    project_urls={
        "Bug Reports": "https://github.com/agentos/agentos/issues",
        "Source": "https://github.com/agentos/agentos",
        "Documentation": "https://docs.agentos.dev",
    },
)