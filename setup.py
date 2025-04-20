# Rabbit/setup.py
#!/usr/bin/env python3 
"""Setup script for Rabbit SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="rabbit-sdk",
    version="0.1.0",
    author="Your Name",
    author_email="warrenkalunga96@gmail.com",
    description="A browser-based agent SDK for automating web tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wchisasa/rabbit-sdk",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "rabbit-agent=agent_task_loop:main",
        ],
    },
    include_package_data=True,
)