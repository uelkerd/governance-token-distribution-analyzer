"""
Governance Token Analyzer - A tool for analyzing governance token distributions.

This package provides tools to analyze and compare governance token distributions
across different protocols such as Compound, Uniswap, and Aave.
"""

from . import core
from . import protocols
from . import visualization

__version__ = "0.1.0"
__author__ = "Governance Token Analyzer Team"

__all__ = ["core", "protocols", "visualization"]
