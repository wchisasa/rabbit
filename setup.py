# setup.py
from setuptools import setup, find_packages

setup(
    name='rabbit_sdk',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'playwright',
        # Add more dependencies here as needed 
    ],
    entry_points={
        'console_scripts': [
            # Optional: you could add a CLI command later
        ],
    },
)
