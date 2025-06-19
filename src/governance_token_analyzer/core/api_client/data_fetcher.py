"""Data Fetcher for Governance Token Distribution Analyzer.

This module provides data fetching functionality for retrieving token holder
and governance data from various APIs.
"""

import logging
from typing import Any, Dict, List

from .base_client import TOKEN_ADDRESSES

# Configure logging
logger = logging.getLogger(__name__)


class DataFetcher:
    """Data fetcher for retrieving token holder and governance data."""

    def __init__(self, parent_client=None):
        """Initialize the Data Fetcher.

        Args:
            parent_client: Parent APIClient instance
        """
        self.parent_client = parent_client

    def get_token_holder_data(
        self, protocol: str, limit: int = 100, use_real_data: bool = True
    ) -> List[Dict[str, Any]]:
        """Get token holder data for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            limit: Maximum number of holders to return
            use_real_data: Whether to use real data or simulated data

        Returns:
            List of token holder dictionaries
        """
        if protocol.lower() not in TOKEN_ADDRESSES:
            raise ValueError(f"Unsupported protocol: {protocol}")

        token_address = TOKEN_ADDRESSES[protocol.lower()]

        if use_real_data:
            # Import here to avoid circular imports
            from .ethereum_client import EthereumClient

            ethereum_client = EthereumClient(self.parent_client)
            return ethereum_client.fetch_token_holders_with_fallback(protocol, token_address, limit)
        # Use simulated data
        from .ethereum_client import EthereumClient

        ethereum_client = EthereumClient(self.parent_client)
        return ethereum_client.generate_sample_holder_data(protocol, limit)

    @staticmethod
    def normalize_holder_balances(holders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize token holder balances to ensure consistent format.

        Args:
            holders: List of token holder dictionaries

        Returns:
            List of normalized token holder dictionaries
        """
        normalized = []

        for holder in holders:
            # Ensure balance is a float
            balance = holder.get("balance", 0)
            if isinstance(balance, str):
                try:
                    balance = float(balance)
                except (ValueError, TypeError):
                    balance = 0

            # Ensure percentage is a float
            percentage = holder.get("percentage", 0)
            if isinstance(percentage, str):
                try:
                    percentage = float(percentage)
                except (ValueError, TypeError):
                    percentage = 0

            normalized.append(
                {
                    "address": holder.get("address", ""),
                    "balance": balance,
                    "percentage": percentage,
                }
            )

        return normalized
