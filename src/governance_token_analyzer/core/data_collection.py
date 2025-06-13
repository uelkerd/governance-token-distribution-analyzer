"""Data Collection Module for the Governance Token Analyzer.

This module handles collecting and managing data from multiple DeFi governance protocols.
It provides a unified interface for accessing token holder, proposal, and voting data.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..protocols import aave, compound, uniswap
from .api_client import APIClient

# Configure logging
logger = logging.getLogger(__name__)

# Define supported protocols
SUPPORTED_PROTOCOLS = ["compound", "uniswap", "aave"]


class DataCollectionManager:
    """Manager for collecting and storing governance token data."""

    def __init__(self, data_dir: str = None):
        """Initialize the data collection manager.

        Args:
            data_dir: Directory to store collected data

        """
        self.api_client = APIClient()

        # Set up data directory
        if data_dir is None:
            # Default to a data directory in the user's home directory
            self.data_dir = os.path.join(os.path.expanduser("~"), ".governance_token_analyzer", "data")
        else:
            self.data_dir = data_dir

        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)

        # Create protocol-specific directories
        for protocol in SUPPORTED_PROTOCOLS:
            os.makedirs(os.path.join(self.data_dir, protocol), exist_ok=True)

    def collect_protocol_data(
        self,
        protocol: str,
        use_cache: bool = True,
        use_real_data: bool = False,
        cache_ttl: int = 3600,
    ) -> Dict[str, Any]:
        """Collect data for a specific protocol.

        Args:
            protocol: Protocol name ('compound', 'uniswap', 'aave')
            use_cache: Whether to use cached data if available and not expired
            use_real_data: Whether to use real data from APIs (vs. sample data)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)

        Returns:
            Dictionary containing protocol data

        """
        if protocol not in SUPPORTED_PROTOCOLS:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Check if we have cached data that's still valid
        if use_cache:
            cached_data = self._load_cached_data(protocol)
            if cached_data and self._is_cache_valid(cached_data, cache_ttl):
                logger.info(f"Using cached data for {protocol}")
                return cached_data

        # If no valid cache, fetch fresh data
        logger.info(f"Collecting fresh data for {protocol} (use_real_data={use_real_data})")

        # Get data based on protocol
        if protocol == "compound":
            data = (
                compound.get_sample_data() if not use_real_data else self.api_client.get_protocol_data(protocol, True)
            )
        elif protocol == "uniswap":
            data = uniswap.get_sample_data() if not use_real_data else self.api_client.get_protocol_data(protocol, True)
        elif protocol == "aave":
            data = aave.get_sample_data() if not use_real_data else self.api_client.get_protocol_data(protocol, True)

        # Add metadata
        data["metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "protocol": protocol,
            "source": "sample_data" if not use_real_data else "api_client",
            "is_real_data": use_real_data,
        }

        # Save to cache
        self._save_cached_data(protocol, data)

        return data

    def collect_all_protocols(
        self, use_cache: bool = True, use_real_data: bool = False, cache_ttl: int = 3600
    ) -> Dict[str, Dict[str, Any]]:
        """Collect data for all supported protocols.

        Args:
            use_cache: Whether to use cached data if available and not expired
            use_real_data: Whether to use real data from APIs (vs. sample data)
            cache_ttl: Cache time-to-live in seconds

        Returns:
            Dictionary mapping protocol names to their data

        """
        all_data = {}

        for protocol in SUPPORTED_PROTOCOLS:
            try:
                data = self.collect_protocol_data(protocol, use_cache, use_real_data, cache_ttl)
                all_data[protocol] = data
            except Exception as e:
                logger.error(f"Error collecting data for {protocol}: {e}")
                all_data[protocol] = {"error": str(e)}

        return all_data

    def get_token_holders(
        self,
        protocol: str,
        limit: int = 100,
        use_cache: bool = True,
        use_real_data: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get token holders for a specific protocol.

        Args:
            protocol: Protocol name
            limit: Maximum number of holders to return
            use_cache: Whether to use cached data
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of token holder dictionaries

        """
        # Get data from cache or API
        data = self.collect_protocol_data(protocol, use_cache, use_real_data)

        # Extract and limit token holders
        holders = data.get("token_holders", [])
        return holders[:limit]

    def get_governance_proposals(
        self,
        protocol: str,
        limit: int = 10,
        use_cache: bool = True,
        use_real_data: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get governance proposals for a specific protocol.

        Args:
            protocol: Protocol name
            limit: Maximum number of proposals to return
            use_cache: Whether to use cached data
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of proposal dictionaries

        """
        # Get data from cache or API
        data = self.collect_protocol_data(protocol, use_cache, use_real_data)

        # Extract and limit proposals
        proposals = data.get("proposals", [])
        return proposals[:limit]

    def get_governance_votes(
        self,
        protocol: str,
        proposal_id: int,
        use_cache: bool = True,
        use_real_data: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get votes for a specific governance proposal.

        Args:
            protocol: Protocol name
            proposal_id: ID of the proposal
            use_cache: Whether to use cached data
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of vote dictionaries

        """
        # Get data from cache or API
        data = self.collect_protocol_data(protocol, use_cache, use_real_data)

        # Extract votes for the specific proposal
        all_votes = data.get("votes", [])
        proposal_votes = [v for v in all_votes if v.get("proposal_id") == proposal_id]

        return proposal_votes

    def _load_cached_data(self, protocol: str) -> Optional[Dict[str, Any]]:
        """Load cached data for a protocol if it exists."""
        cache_file = os.path.join(self.data_dir, protocol, "data.json")

        try:
            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cached data for {protocol}: {e}")

        return None

    def _save_cached_data(self, protocol: str, data: Dict[str, Any]) -> bool:
        """Save data to cache for a protocol."""
        cache_file = os.path.join(self.data_dir, protocol, "data.json")

        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving cached data for {protocol}: {e}")
            return False

    def _is_cache_valid(self, data: Dict[str, Any], ttl: int) -> bool:
        """Check if cached data is still valid based on TTL."""
        # Extract last updated timestamp
        metadata = data.get("metadata", {})
        last_updated_str = metadata.get("last_updated")

        if not last_updated_str:
            return False

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            now = datetime.now()

            # Calculate age of cache in seconds
            age = (now - last_updated).total_seconds()

            # Cache is valid if age is less than TTL
            return age < ttl

        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
