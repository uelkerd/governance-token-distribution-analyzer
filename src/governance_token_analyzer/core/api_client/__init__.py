"""API Client package for Governance Token Distribution Analyzer.

This package provides a unified interface for fetching governance token data
from various blockchain APIs including Etherscan, The Graph, and Alchemy.
"""

from .base_client import APIClient
from .ethereum_client import EthereumClient
from .protocol_client import ProtocolClient
from .data_fetcher import DataFetcher
from .response_parser import ResponseParser
from .graph_client import TheGraphAPI

__all__ = [
    "APIClient",
    "EthereumClient",
    "ProtocolClient",
    "DataFetcher",
    "ResponseParser",
    "TheGraphAPI",
]
