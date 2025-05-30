#!/usr/bin/env python3
"""
Setup script for Property Management Automation Suite
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read the requirements file
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read version from VERSION file
version = "1.2.0"  # fallback version
version_file = this_directory / "VERSION"
if version_file.exists():
    version = version_file.read_text().strip()

setup(
    name="property-management-automation",
    version=version,
    author="Property Management Automation Team",
    author_email="automation@example.com",
    description="Comprehensive automation system for vacation rental property management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/blindermanupwork/property-management-automation",
    project_urls={
        "Bug Reports": "https://github.com/blindermanupwork/property-management-automation/issues",
        "Source": "https://github.com/blindermanupwork/property-management-automation",
        "Documentation": "https://github.com/blindermanupwork/property-management-automation/blob/main/README.md",
    },
    
    # Package discovery
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Include non-Python files
    include_package_data=True,
    package_data={
        "automation": ["*.md", "*.txt", "*.json"],
    },
    
    # Dependencies
    install_requires=requirements,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "run-automation=automation.scripts.run_automation:main",
            "evolve-scraper=automation.scripts.evolve_scraper:main",
            "csv-processor=automation.scripts.csv_processor:main",
            "ics-sync=automation.scripts.ics_sync:main",
            "gmail-downloader=automation.scripts.gmail_downloader:main",
        ],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    
    # Keywords for PyPI search
    keywords="automation property-management vacation-rental airtable csv ics calendar",
    
    # Extra dependencies for development
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "pre-commit>=2.0",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-mock>=3.0",
        ],
    },
    
    # Minimum setuptools version
    setup_requires=["setuptools>=45", "wheel"],
    
    # ZIP safe
    zip_safe=False,
)