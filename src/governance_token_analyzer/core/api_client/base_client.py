"""Base API Client for Governance Token Distribution Analyzer.

This module provides the core APIClient class with common functionality
for all API interactions.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default API keys (should be set through environment variables)
DEFAULT_ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
DEFAULT_INFURA_API_KEY = os.environ.get("INFURA_API_KEY", "")
DEFAULT_ALCHEMY_API_KEY = os.environ.get("ALCHEMY_API_KEY", "")
DEFAULT_GRAPH_API_KEY = os.environ.get("GRAPH_API_KEY", "")
DEFAULT_ETHPLORER_API_KEY = os.environ.get("ETHPLORER_API_KEY", "freekey")

# API endpoints
ETHERSCAN_API_URL = "https://api.etherscan.io/api"
INFURA_API_URL = f"https://mainnet.infura.io/v3/{DEFAULT_INFURA_API_KEY}"
ALCHEMY_API_URL = f"https://eth-mainnet.g.alchemy.com/v2/{DEFAULT_ALCHEMY_API_KEY}"
ETHPLORER_API_URL = "https://api.ethplorer.io"

# Token contract addresses
TOKEN_ADDRESSES = {
    "compound": "0xc00e94Cb662C3520282E6f5717214004A7f26888",  # COMP
    "uniswap": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # UNI
    "aave": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",  # AAVE
}

# Governance contract addresses
GOVERNANCE_ADDRESSES = {
    "compound": "0xc0Da02939E1441F497fd74F78cE7Decb17B66529",
    "uniswap": "0x408ED6354d4973f66138C91495F2f2FCbd8724C3",
    "aave": "0xEC568fffba86c094cf06b22134B23074DFE2252c",
}

# GraphQL endpoints with API key authentication
GRAPHQL_ENDPOINTS = {
    "compound": "https://gateway-arbitrum.network.thegraph.com/api/{api_key}/subgraphs/id/3HrWdYr48tFPTjkqxYN6KJprj29EzU9L9pjJZu6qk3Xr",
    "uniswap": "https://gateway-arbitrum.network.thegraph.com/api/{api_key}/subgraphs/id/EUTy9RtugEz9Uy5BPUgc3Qvgh4VE3dP5B7URNQDB5mf4",
    "aave": "https://gateway-arbitrum.network.thegraph.com/api/{api_key}/subgraphs/id/8NzKywjhXbUFnEVPn5v8QyZYWj7KAhJGE7jHW8TvK2m",
}

# GraphQL queries for different protocols
GOVERNANCE_QUERIES = {
    "compound": """
        query GetProposals($first: Int!, $skip: Int!) {
            proposals(first: $first, skip: $skip, orderBy: id, orderDirection: desc) {
                id
                title
                description
                proposer
                targets
                values
                signatures
                calldatas
                startBlock
                endBlock
                forVotes
                againstVotes
                abstainVotes
                canceled
                queued
                executed
                eta
                createdAt
                updatedAt
            }
        }
    """,
    "uniswap": """
        query GetProposals($first: Int!, $skip: Int!) {
            proposals(first: $first, skip: $skip, orderBy: id, orderDirection: desc) {
                id
                title
                description
                proposer
                targets
                values
                signatures
                calldatas
                startBlock
                endBlock
                forVotes
                againstVotes
                abstainVotes
                canceled
                queued
                executed
                eta
                createdAt
                updatedAt
            }
        }
    """,
    "aave": """
        query GetProposals($first: Int!, $skip: Int!) {
            proposals(first: $first, skip: $skip, orderBy: id, orderDirection: desc) {
                id
                title
                description
                proposer
                targets
                values
                signatures
                calldatas
                startBlock
                endBlock
                forVotes
                againstVotes
                abstainVotes
                canceled
                queued
                executed
                eta
                createdAt
                updatedAt
            }
        }
    """,
}

VOTE_QUERIES = {
    "compound": """
        query GetVotes($proposalId: String!) {
            votes(where: {proposal: $proposalId}, first: 1000, orderBy: votingPower, orderDirection: desc) {
                id
                voter
                support
                votingPower
                reason
                blockNumber
                blockTimestamp
                transactionHash
            }
        }
    """,
    "uniswap": """
        query GetVotes($proposalId: String!) {
            votes(where: {proposal: $proposalId}, first: 1000, orderBy: votingPower, orderDirection: desc) {
                id
                voter
                support
                votingPower
                reason
                blockNumber
                blockTimestamp
                transactionHash
            }
        }
    """,
    "aave": """
        query GetVotes($proposalId: String!) {
            votes(where: {proposal: $proposalId}, first: 1000, orderBy: votingPower, orderDirection: desc) {
                id
                voter
                support
                votingPower
                reason
                blockNumber
                blockTimestamp
                transactionHash
            }
        }
    """,
}

# Protocol specific information
PROTOCOL_INFO = {
    "compound": {
        "token_symbol": "COMP",
        "token_name": "Compound",
        "total_supply": 10000000,  # 10 million COMP
        "decimals": 18,
        "proposal_threshold": 65000,  # COMP needed to submit a proposal
        "whale_addresses": [
            "0x6626593c237f530d15ae9980a95ef938ac15c35c",  # Compound Treasury
            "0xc00e94cb662c3520282e6f5717214004a7f26888",  # Compound Comptroller
            "0x2775b1c75658be0f640272ccb8c72ac986009e38",  # Binance
        ],
    },
    "uniswap": {
        "token_symbol": "UNI",
        "token_name": "Uniswap",
        "total_supply": 1000000000,  # 1 billion UNI
        "decimals": 18,
        "proposal_threshold": 10000000,  # UNI needed to submit a proposal
        "whale_addresses": [
            "0x1a9c8182c09f50c8318d769245bea52c32be35bc",  # Uniswap Treasury
            "0x4750c43867ef5f89869132eccf19b9b6c4286e1a",  # Binance
            "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0",  # Uniswap Team
        ],
    },
    "aave": {
        "token_symbol": "AAVE",
        "token_name": "Aave",
        "total_supply": 16000000,  # 16 million AAVE
        "decimals": 18,
        "proposal_threshold": 80000,  # AAVE needed to submit a proposal
        "whale_addresses": [
            "0x25f2226b597e8f9514b3f68f00f494cf4f286491",  # Aave Ecosystem Reserve
            "0xbe8e3e3618f7474f8cb1d074a26affef007e98fb",  # Binance
            "0x4da27a545c0c5b758a6ba100e3a049001de870f5",  # Staked Aave
        ],
    },
}


class APIClient:
    """Client for interacting with various blockchain APIs for governance token analysis."""

    def __init__(self):
        """Initialize the API client with configuration from environment variables."""
        # API Keys
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY", DEFAULT_ETHERSCAN_API_KEY)
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY", DEFAULT_ALCHEMY_API_KEY)
        self.graph_api_key = os.getenv("GRAPH_API_KEY", DEFAULT_GRAPH_API_KEY)
        self.moralis_api_key = os.getenv("MORALIS_API_KEY", "")
        self.ethplorer_api_key = os.getenv("ETHPLORER_API_KEY", DEFAULT_ETHPLORER_API_KEY)

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests

        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "GovernanceTokenAnalyzer/1.0"})

        logger.info("APIClient initialized with available API keys:")
        logger.info(f"  Etherscan: {'✓' if self.etherscan_api_key else '✗'}")
        logger.info(f"  Alchemy: {'✓' if self.alchemy_api_key else '✗'}")
        logger.info(f"  The Graph: {'✓' if self.graph_api_key else '✗'}")
        logger.info(f"  Moralis: {'✓' if self.moralis_api_key else '✗'}")
        logger.info(f"  Ethplorer: {'✓' if self.ethplorer_api_key else '✗'}")

        # Initialize The Graph clients for each protocol
        self.graph_clients = {}
        if self.graph_api_key:
            from .graph_client import TheGraphAPI

            for protocol, endpoint_template in GRAPHQL_ENDPOINTS.items():
                endpoint = endpoint_template.format(api_key=self.graph_api_key)
                self.graph_clients[protocol] = TheGraphAPI(endpoint)

    def get_token_holders(self, protocol: str, limit: int = 100, use_real_data: bool = True) -> List[Dict[str, Any]]:
        """Get token holders for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            limit: Maximum number of holders to return
            use_real_data: Whether to use real data or simulated data

        Returns:
            List of token holder dictionaries
        """
        from .data_fetcher import DataFetcher

        data_fetcher = DataFetcher(self)
        return data_fetcher.get_token_holder_data(protocol, limit, use_real_data)

    def get_governance_proposals(
        self, protocol: str, limit: int = 10, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """Get governance proposals for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            limit: Maximum number of proposals to return
            use_real_data: Whether to use real data or simulated data

        Returns:
            List of governance proposal dictionaries
        """
        from .protocol_client import ProtocolClient

        protocol_client = ProtocolClient(self)
        return protocol_client.get_proposal_data(protocol, limit, use_real_data)

    def get_governance_votes(
        self, protocol: str, proposal_id: int, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """Get governance votes for a specific proposal.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            proposal_id: ID of the proposal to get votes for
            use_real_data: Whether to use real data or simulated data

        Returns:
            List of vote dictionaries
        """
        from .protocol_client import ProtocolClient

        protocol_client = ProtocolClient(self)
        return protocol_client.get_votes_data(protocol, proposal_id, use_real_data)

    def get_protocol_data(self, protocol: str, use_real_data: bool = False) -> Dict[str, Any]:
        """Get comprehensive data for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            use_real_data: Whether to use real data or simulated data

        Returns:
            Dictionary containing token holders, proposals, and protocol info
        """
        # Validate protocol
        if protocol.lower() not in TOKEN_ADDRESSES:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Get token holders
        holders = self.get_token_holders(protocol, limit=100, use_real_data=use_real_data)

        # Get governance proposals
        proposals = self.get_governance_proposals(protocol, limit=10, use_real_data=use_real_data)

        # Get protocol information
        protocol_info = PROTOCOL_INFO.get(protocol.lower(), {})

        # Calculate holder concentration
        holder_concentration = self._calculate_holder_concentration(holders, protocol_info)

        # Calculate participation rate
        participation_rate = self._calculate_participation_rate(proposals)

        return {
            "token_holders": holders,
            "governance_proposals": proposals,
            "protocol_info": protocol_info,
            "metrics": {
                "holder_concentration": holder_concentration,
                "participation_rate": participation_rate,
            },
        }

    @staticmethod
    def _calculate_holder_concentration(holders: List[Dict[str, Any]], protocol_info: Dict[str, Any]) -> float:
        """Calculate holder concentration (percentage held by top 10 holders).

        Args:
            holders: List of token holder dictionaries
            protocol_info: Protocol information dictionary

        Returns:
            Holder concentration percentage (0-100)
        """
        if not holders:
            return 0.0

        # Sort holders by balance
        sorted_holders = sorted(holders, key=lambda x: float(x.get("balance", 0)), reverse=True)

        # Get top 10 holders
        top_holders = sorted_holders[:10]

        # Calculate total balance of top holders
        top_balance = sum(float(holder.get("balance", 0)) for holder in top_holders)

        # Calculate total supply
        total_supply = protocol_info.get("total_supply", 0)

        # Calculate concentration
        concentration = (top_balance / total_supply) * 100 if total_supply > 0 else 0

        return min(concentration, 100.0)  # Cap at 100%

    @staticmethod
    def _calculate_participation_rate(proposals: List[Dict[str, Any]]) -> float:
        """Calculate governance participation rate.

        Args:
            proposals: List of governance proposal dictionaries

        Returns:
            Participation rate percentage (0-100)
        """
        if not proposals:
            return 0.0

        # Calculate total votes across all proposals
        total_votes = sum(
            int(proposal.get("forVotes", 0))
            + int(proposal.get("againstVotes", 0))
            + int(proposal.get("abstainVotes", 0))
            for proposal in proposals
        )

        # Calculate average votes per proposal
        avg_votes = total_votes / len(proposals) if proposals else 0

        # Normalize to percentage (assuming 10% participation is typical)
        participation_rate = min((avg_votes / 1000000) * 100, 100.0)

        return participation_rate

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a rate-limited API request.

        Args:
            params: Request parameters

        Returns:
            API response as dictionary
        """
        # Implement rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

        # Make the request
        try:
            response = self.session.get(params.get("url", ""), params=params.get("params", {}))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e), "status": "error"}
