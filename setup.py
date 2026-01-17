#!/usr/bin/env python3
"""
Setup configuration for AgentOS

This file is maintained for backwards compatibility with older pip versions.
The primary configuration is in pyproject.toml.

Installation:
    pip install .                    # Basic installation
    pip install ".[full]"            # Full installation with all features
    pip install ".[openai,claude]"   # Specific LLM providers

For PyPI distribution:
    python -m build
    twine upload dist/*
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read version from VERSION file or __init__.py
version_file = Path(__file__).parent / "VERSION"
if version_file.exists():
    version = version_file.read_text(encoding="utf-8").strip()
else:
    version = "1.1.7"

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Core dependencies (minimal for basic functionality)
core_requirements = [
    "pyyaml>=6.0",
    "requests>=2.28.0",
    "python-dotenv>=1.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "click>=8.0.0",
]

# Optional dependencies
extras_require = {
    # LLM Providers
    "openai": ["openai>=1.0.0"],
    "claude": ["anthropic>=0.18.0"],
    "gemini": ["google-generativeai>=0.3.0"],
    "cohere": ["cohere>=4.0.0"],
    "ollama": ["ollama>=0.1.0"],
    "mcp": ["mcp>=0.1.0"],
    # All LLM providers
    "llm": [
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "google-generativeai>=0.3.0",
        "cohere>=4.0.0",
        "ollama>=0.1.0",
    ],
    # Web UI
    "web": [
        "flask>=2.3.0",
        "gunicorn>=21.0.0",
        "gevent>=23.0.0",
    ],
    # Desktop UI
    "desktop": [
        "pywebview>=4.4.0",
        "PyQt5>=5.15.0",
        "PyQtWebEngine>=5.15.0",
        "QtPy>=2.0.0",
    ],
    # Docker isolation
    "docker": ["docker>=6.0.0"],
    # Monitoring
    "monitoring": ["prometheus-client>=0.19.0"],
    # Development
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "build>=1.0.0",
        "twine>=4.0.0",
    ],
    # Full installation
    "full": [
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "google-generativeai>=0.3.0",
        "cohere>=4.0.0",
        "ollama>=0.1.0",
        "mcp>=0.1.0",
        "flask>=2.3.0",
        "gunicorn>=21.0.0",
        "gevent>=23.0.0",
        "pywebview>=4.4.0",
        "docker>=6.0.0",
        "prometheus-client>=0.19.0",
    ],
}

setup(
    name="agentos-ai",
    version=version,
    description="Production-Ready AI Agent Runtime - Automate everything with LLM-powered agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AgentOS Team",
    author_email="support@agentos.dev",
    url="https://agentos.sodeom.com/",
    project_urls={
        "Homepage": "https://agentos.sodeom.com/",
        "Documentation": "https://agentos.sodeom.com/docs",
        "Repository": "https://github.com/agents-os/agentos",
        "Issues": "https://github.com/agents-os/agentos/issues",
        "Changelog": "https://github.com/agents-os/agentos/blob/main/MD/CHANGELOG.md",
    },
    packages=find_packages(
        exclude=["tests", "tests.*", "examples", "installer", "uninstaller"]
    ),
    include_package_data=True,
    install_requires=core_requirements,
    extras_require=extras_require,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "agentos=agentos.agentos:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    keywords=[
        "ai",
        "agent",
        "llm",
        "automation",
        "orchestration",
        "chatbot",
        "openai",
        "claude",
        "gemini",
        "ollama",
        "gpt",
        "artificial-intelligence",
        "machine-learning",
    ],
    zip_safe=False,
)
