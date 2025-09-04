#!/usr/bin/env python3
"""
Setup script for Carbon-Aware FinOps package.
"""

from setuptools import setup, find_packages
import os

# Read requirements
def read_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="carbon-aware-finops",
    version="1.0.0",
    author="Carbon-Aware FinOps Team",
    description="Carbon-aware financial operations and resource optimization for AWS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements('requirements.txt') if os.path.exists('requirements.txt') else [],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=22.0',
            'flake8>=4.0',
            'mypy>=0.950',
            'types-requests',
            'types-PyYAML',
        ],
    },
    entry_points={
        'console_scripts': [
            'carbon-dashboard=src.reporting.thesis_dashboard:main',
        ],
    },
    package_data={
        'src': ['config/*.yaml'],
    },
    include_package_data=True,
)