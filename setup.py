#!/usr/bin/env python
"""
Setup script for the Governance Token Distribution Analyzer.

This file is only needed for backward compatibility with older versions of pip.
Modern installation should use the pyproject.toml file directly.
"""

from setuptools import setup, find_packages

setup(
    name="governance_token_analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Dependencies are specified in requirements.txt
    ],
)
