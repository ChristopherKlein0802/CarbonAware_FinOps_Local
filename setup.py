from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="carbon-aware-finops",
    version="0.1.0",
    author="Christopher Klein",
    author_email="your.email@example.com",
    description="Carbon-Aware FinOps Framework for AWS EC2 optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ChristopherKlein0802/CarbonAware_FinOps_Local",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.28.0",
        "pandas>=2.1.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "loguru>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "carbon-finops=src.cli:main",
        ],
    },
)