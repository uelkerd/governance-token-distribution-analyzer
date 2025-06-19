"""API Client for Governance Token Distribution Analyzer.

This module provides a unified interface for fetching governance token data
from various blockchain APIs including Etherscan, The Graph, and Alchemy.

This file is maintained for backward compatibility and imports from the api_client package.
"""

from .api_client.base_client import APIClient

# Re-export the APIClient class for backward compatibility
__all__ = ["APIClient"]
