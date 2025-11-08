#!/usr/bin/env python3
"""Setup configuration for AgentOS"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "MD" / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="agentos",
    version="1.0.0",
    description="Production AI Agent Runtime System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AgentOS Team",
    author_email="support@agentos.com",
    url="https://github.com/agents-os/agentos",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "agentos=agentos.agentos:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        # "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agent llm automation orchestration",
)
