"""
GUARDIAN Setup Script
This provides backwards compatibility with older pip versions
and standard Python packaging tools.

For modern installations, use:
    pip install -e .

Which will use pyproject.toml automatically.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="guardian-solana",
    version="0.1.0",
    author="GUARDIAN Team",
    author_email="security@guardian.sol",
    description="Autonomous multi-agent security infrastructure for Solana",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sugusdaddy/GUARDIAN",
    project_urls={
        "Bug Tracker": "https://github.com/Sugusdaddy/GUARDIAN/issues",
        "Documentation": "https://github.com/Sugusdaddy/GUARDIAN/tree/main/docs",
        "Source Code": "https://github.com/Sugusdaddy/GUARDIAN",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.18.0",
        "solana>=0.32.0",
        "solders>=0.20.0",
        "anchorpy>=0.19.0",
        "httpx>=0.26.0",
        "aiohttp>=3.9.0",
        "python-dotenv>=1.0.0",
        "structlog>=24.1.0",
        "rich>=13.7.0",
        "sentence-transformers>=2.3.0",
        "scikit-learn>=1.4.0",
        "numpy>=1.26.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "isort>=5.13.0",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "guardian=cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
