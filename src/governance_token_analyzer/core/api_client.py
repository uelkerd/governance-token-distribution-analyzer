"""
API Client Module for governance token data collection.

This module provides utilities for fetching data from various blockchain APIs
including Etherscan, The Graph, and protocol-specific endpoints.
"""

import os
import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import time
import random
from .config import Config, ETHERSCAN_API_KEY, ETHERSCAN_BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default API keys (should be set through environment variables)
DEFAULT_ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
DEFAULT_INFURA_API_KEY = os.environ.get("INFURA_API_KEY", "")
DEFAULT_GRAPH_API_KEY = os.environ.get("GRAPH_API_KEY", "")
ETHPLORER_API_URL = "https://api.ethplorer.io"
DEFAULT_ETHPLORER_API_KEY = os.environ.get("ETHPLORER_API_KEY", "freekey")

# API endpoints
ETHERSCAN_API_URL = "https://api.etherscan.io/api"
INFURA_API_URL = f"https://mainnet.infura.io/v3/{DEFAULT_INFURA_API_KEY}"

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

# GraphQL endpoints
GRAPHQL_ENDPOINTS = {
    "compound": "https://api.thegraph.com/subgraphs/name/compound-finance/compound-governance",
    "uniswap": "https://api.thegraph.com/subgraphs/name/uniswap/governance",
    "aave": "https://api.thegraph.com/subgraphs/name/aave/governance",
}

# Protocol specific information for sample data generation
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

    def __init__(
        self,
        etherscan_api_key: str = DEFAULT_ETHERSCAN_API_KEY,
        infura_api_key: str = DEFAULT_INFURA_API_KEY,
        graph_api_key: str = DEFAULT_GRAPH_API_KEY,
    ):
        """
        Initialize the API client with API keys.

        Args:
            etherscan_api_key: Etherscan API key
            infura_api_key: Infura API key
            graph_api_key: The Graph API key
        """
        self.etherscan_api_key = etherscan_api_key
        self.infura_api_key = infura_api_key
        self.graph_api_key = graph_api_key
        self.session = requests.Session()

        # Configure logging
        self.logger = logging.getLogger(__name__)

    def get_token_holders(
        self, protocol: str, limit: int = 100, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get token holders for a specific protocol.

        Args:
            protocol: Protocol name ('compound', 'uniswap', 'aave')
            limit: Number of holders to retrieve
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of token holder dictionaries
        """
        if protocol not in TOKEN_ADDRESSES:
            raise ValueError(f"Unsupported protocol: {protocol}")

        try:
            if use_real_data:
                # Implement real API call to get token holders
                token_address = TOKEN_ADDRESSES[protocol]
                return self._fetch_token_holders(protocol, token_address, limit)
            else:
                # Generate sample data for testing
                return self._generate_sample_holder_data(protocol, limit)

        except Exception as e:
            logger.error(f"Error fetching token holders for {protocol}: {e}")
            return []

    def get_governance_proposals(
        self, protocol: str, limit: int = 10, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get governance proposals for a specific protocol.

        Args:
            protocol: Protocol name ('compound', 'uniswap', 'aave')
            limit: Number of proposals to retrieve
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of proposal dictionaries
        """
        if protocol not in GRAPHQL_ENDPOINTS:
            raise ValueError(f"Unsupported protocol: {protocol}")

        try:
            if use_real_data:
                # Implement real API call to get governance proposals
                return self._fetch_governance_proposals(protocol, limit)
            else:
                # Generate sample data for testing
                return self._generate_sample_proposal_data(protocol, limit)

        except Exception as e:
            logger.error(f"Error fetching governance proposals for {protocol}: {e}")
            return []

    def get_governance_votes(
        self, protocol: str, proposal_id: int, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get votes for a specific governance proposal.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            proposal_id: ID of the proposal
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of vote dictionaries
        """
        if protocol not in GRAPHQL_ENDPOINTS:
            raise ValueError(f"Unsupported protocol: {protocol}")

        try:
            if use_real_data:
                # Implement real API call to get governance votes
                return self._fetch_governance_votes(protocol, proposal_id)
            else:
                # Generate sample data for testing
                return self._generate_sample_vote_data(protocol, proposal_id)

        except Exception as e:
            logger.error(
                f"Error fetching votes for proposal {proposal_id} in {protocol}: {e}"
            )
            return []

    def get_protocol_data(
        self, protocol: str, use_real_data: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive data for a protocol including token holders, proposals, and votes.

        Args:
            protocol: Protocol name ('compound', 'uniswap', 'aave')
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            Dictionary containing protocol data
        """
        if protocol not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Get protocol info for sample data generation
        info = PROTOCOL_INFO[protocol]

        # Collect holders, proposals, and votes
        holders = self.get_token_holders(
            protocol, limit=100, use_real_data=use_real_data
        )
        proposals = self.get_governance_proposals(
            protocol, limit=10, use_real_data=use_real_data
        )

        # Collect votes for each proposal
        all_votes = []
        for proposal in proposals:
            proposal_id = proposal["id"]
            votes = self.get_governance_votes(
                protocol, proposal_id, use_real_data=use_real_data
            )
            all_votes.extend(votes)

        # Calculate participation metrics
        participation_rate = self._calculate_participation_rate(proposals)

        # Build the full protocol data dictionary
        return {
            "protocol": protocol,
            "token_symbol": info["token_symbol"],
            "token_name": info["token_name"],
            "total_supply": info["total_supply"],
            "token_holders": holders,
            "proposals": proposals,
            "votes": all_votes,
            "participation_rate": participation_rate,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_participation_rate(self, proposals: List[Dict[str, Any]]) -> float:
        """
        Calculate the participation rate based on proposal votes.

        Args:
            proposals: List of proposal dictionaries

        Returns:
            Float representing participation rate (0-1)
        """
        if not proposals:
            return 0.0

        participation_sum = 0.0
        for proposal in proposals:
            if "participation_rate" in proposal:
                participation_sum += proposal["participation_rate"]

        return participation_sum / len(proposals)

    def _generate_sample_holder_data(
        self, protocol: str, count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate sample token holder data for testing.

        Args:
            protocol: Protocol name
            count: Number of holders to generate

        Returns:
            List of sample token holder dictionaries
        """
        info = PROTOCOL_INFO[protocol]
        total_supply = info["total_supply"]

        # Generate a power-law distribution of token balances
        balances = self._generate_power_law_distribution(count, total_supply)

        # Create sample addresses
        holders = []
        for i in range(count):
            # Use a deterministic address based on index
            address = f"0x{i + 1:040x}"

            # For the top holders, use "known" whale addresses if available
            if i < len(info.get("whale_addresses", [])):
                address = info["whale_addresses"][i]

            balance = balances[i]
            percentage = balance / total_supply

            holders.append(
                {
                    "protocol": protocol,
                    "address": address,
                    "balance": balance,
                    "percentage": percentage,
                    "label": f"Whale {i + 1}" if i < 5 else f"Holder {i + 1}",
                    "is_contract": i % 5 == 0,  # Every 5th holder is a contract
                    "last_updated": datetime.now().isoformat(),
                }
            )

        return holders

    def _generate_power_law_distribution(
        self, count: int, total: float, alpha: float = 1.5
    ) -> List[float]:
        """
        Generate a power-law distribution of values.

        Args:
            count: Number of values to generate
            total: Sum of all values
            alpha: Power law exponent (higher = more concentrated)

        Returns:
            List of values following a power-law distribution
        """
        # Generate raw power-law values
        values = [1.0 / ((i + 1) ** alpha) for i in range(count)]

        # Normalize to the total
        total_raw = sum(values)
        normalized = [v * total / total_raw for v in values]

        return normalized

    def _generate_sample_proposal_data(
        self, protocol: str, count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate sample governance proposal data for testing.

        Args:
            protocol: Protocol name
            count: Number of proposals to generate

        Returns:
            List of sample proposal dictionaries
        """
        proposals = []

        # Common proposal templates for each protocol
        template_titles = {
            "compound": [
                "Add Market Support for {asset}",
                "Adjust {asset} Collateral Factor",
                "Update Liquidation Parameters",
                "Implement {feature} for Protocol Security",
                "Reduce Reserve Factor for {asset}",
                "Update Oracle Implementation",
                "Approve Grants Program Funding",
            ],
            "uniswap": [
                "Deploy Uniswap v{version} on {chain}",
                "Adjust Fee Tier for {pair} Pool",
                "Allocate UNI for {program} Program",
                "Update Protocol Fee Switch",
                "Implement Cross-Chain Bridge Integration",
                "Launch {feature} for Improved Liquidity",
                "Authorize {amount} UNI for Development Fund",
            ],
            "aave": [
                "List {asset} as Collateral",
                "Update Interest Rate Strategy for {asset}",
                "Adjust Loan-to-Value Ratio for {asset}",
                "Deploy Aave on {chain}",
                "Implement {feature} for Risk Management",
                "Allocate Ecosystem Reserve Funds",
                "Update Oracle Price Feeds",
            ],
        }

        assets = ["ETH", "USDC", "DAI", "WBTC", "LINK", "UNI", "COMP", "AAVE", "MKR"]
        chains = ["Arbitrum", "Optimism", "Polygon", "Base", "Avalanche", "zkSync"]
        features = [
            "Flash Loans",
            "Isolation Mode",
            "Safety Module",
            "Liquidity Mining",
            "Governance Delegation",
        ]

        for i in range(count):
            # Select a random template and fill in variables
            templates = template_titles.get(protocol, template_titles["compound"])
            title_template = random.choice(templates)

            # Replace template variables
            title = title_template.format(
                asset=random.choice(assets),
                chain=random.choice(chains),
                feature=random.choice(features),
                version=random.choice(["3", "4"]),
                pair=f"{random.choice(assets)}-{random.choice(assets)}",
                program=random.choice(["Ecosystem", "Developer", "Community"]),
                amount=f"{random.randint(10, 100)}M",
            )

            # Create a detailed description
            description = (
                f"This proposal aims to {title.lower()}. "
                f"The implementation includes several key components that will benefit the protocol by "
                f"enhancing security, improving capital efficiency, and attracting more users."
            )

            # Generate random proposal details
            proposal_id = i + 1
            created_date = datetime.now() - timedelta(days=random.randint(1, 365))
            end_date = created_date + timedelta(days=random.randint(3, 14))

            # Randomize proposal state based on end date
            if end_date > datetime.now():
                state = random.choice(["active", "pending"])
            else:
                state = random.choice(["executed", "defeated", "expired", "succeeded"])

            # Generate random vote counts
            for_votes = random.randint(100000, 10000000)
            against_votes = random.randint(10000, for_votes)
            abstain_votes = random.randint(5000, 100000)
            total_votes = for_votes + against_votes + abstain_votes

            # Calculate participation rate (0-1)
            info = PROTOCOL_INFO[protocol]
            participation_rate = total_votes / info["total_supply"]

            # Create the proposal object
            proposals.append(
                {
                    "protocol": protocol,
                    "id": proposal_id,
                    "title": title,
                    "description": description,
                    "proposer": random.choice(
                        info.get(
                            "whale_addresses", [f"0x{random.getrandbits(160):040x}"]
                        )
                    ),
                    "created_at": created_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "state": state,
                    "for_votes": for_votes,
                    "against_votes": against_votes,
                    "abstain_votes": abstain_votes,
                    "total_votes": total_votes,
                    "participation_rate": participation_rate,
                    "quorum_reached": total_votes
                    > (info["total_supply"] * 0.04),  # 4% quorum
                }
            )

        return proposals

    def _generate_sample_vote_data(
        self, protocol: str, proposal_id: int
    ) -> List[Dict[str, Any]]:
        """
        Generate sample governance vote data for testing.

        Args:
            protocol: Protocol name
            proposal_id: Proposal ID

        Returns:
            List of sample vote dictionaries
        """
        info = PROTOCOL_INFO[protocol]

        # Generate between 50-200 votes for this proposal
        vote_count = random.randint(50, 200)
        votes = []

        # Possible vote choices
        choices = ["for", "against", "abstain"]
        weights = [0.7, 0.2, 0.1]  # Most votes are "for" in sample data

        # Generate random addresses or use whale addresses for top votes
        for i in range(vote_count):
            # For top voters, use whale addresses
            if i < len(info.get("whale_addresses", [])):
                voter = info["whale_addresses"][i]
            else:
                voter = f"0x{random.getrandbits(160):040x}"

            # Determine vote choice weighted by the probabilities
            vote_choice = random.choices(choices, weights=weights)[0]

            # Generate vote power - whales have more voting power
            if i < 5:  # Top 5 voters
                vote_power = random.uniform(0.01, 0.1) * info["total_supply"]
            elif i < 20:  # Next 15 voters
                vote_power = random.uniform(0.001, 0.01) * info["total_supply"]
            else:  # Remaining voters
                vote_power = random.uniform(0.0001, 0.001) * info["total_supply"]

            # Create vote object
            votes.append(
                {
                    "protocol": protocol,
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "vote_choice": vote_choice,
                    "vote_power": vote_power,
                    "vote_weight": vote_power / info["total_supply"],
                    "voted_at": (
                        datetime.now() - timedelta(days=random.randint(1, 14))
                    ).isoformat(),
                    "tx_hash": f"0x{random.getrandbits(256):064x}",
                }
            )

        return votes

    def _fetch_token_holders(
        self, protocol: str, token_address: str, limit: int
    ) -> List[Dict[str, Any]]:
        """
        Placeholder for real API implementation to fetch token holders.
        Currently returns sample data.

        Args:
            protocol: Protocol name
            token_address: Token contract address
            limit: Number of holders to retrieve

        Returns:
            List of token holder dictionaries
        """
        # In a real implementation, this would call protocol-specific APIs
        # For now, return sample data
        logger.warning(
            f"Using sample data for {protocol} token holders (real API not implemented)"
        )
        return self._generate_sample_holder_data(protocol, limit)

    def _fetch_governance_proposals(
        self, protocol: str, limit: int
    ) -> List[Dict[str, Any]]:
        """
        Placeholder for real API implementation to fetch governance proposals.
        Currently returns sample data.

        Args:
            protocol: Protocol name
            limit: Number of proposals to retrieve

        Returns:
            List of proposal dictionaries
        """
        # In a real implementation, this would call protocol-specific APIs
        # For now, return sample data
        logger.warning(
            f"Using sample data for {protocol} proposals (real API not implemented)"
        )
        return self._generate_sample_proposal_data(protocol, limit)

    def _fetch_governance_votes(
        self, protocol: str, proposal_id: int
    ) -> List[Dict[str, Any]]:
        """
        Placeholder for real API implementation to fetch governance votes.
        Currently returns sample data.

        Args:
            protocol: Protocol name
            proposal_id: Proposal ID

        Returns:
            List of vote dictionaries
        """
        # In a real implementation, this would call protocol-specific APIs
        # For now, return sample data
        logger.warning(
            f"Using sample data for {protocol} votes (real API not implemented)"
        )
        return self._generate_sample_vote_data(protocol, proposal_id)

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Etherscan API.

        Args:
            params (Dict[str, Any]): Parameters for the API request.

        Returns:
            Dict[str, Any]: API response as a dictionary.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        # Add API key to parameters
        params["apikey"] = self.etherscan_api_key

        try:
            # Make the request
            response = requests.get(ETHERSCAN_API_URL, params=params)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses

            # Parse response
            data = response.json()

            # Check for API errors
            if data.get("status") == "0":
                error_message = data.get("message", "Unknown API error")
                logger.error(f"API error: {error_message}")
                return {"error": error_message}

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def get_token_supply(self, token_address: str) -> Dict[str, Any]:
        """
        Get the total supply of a token.

        Args:
            token_address (str): The Ethereum address of the token.

        Returns:
            Dict[str, Any]: Token supply information.
        """
        params = {
            "module": "stats",
            "action": "tokensupply",
            "contractaddress": token_address,
        }

        return self._make_request(params)

    def get_etherscan_token_holders(
        self, token_address: str, page: int = 1, offset: int = 100
    ) -> Dict[str, Any]:
        """
        Get a list of token holders from Etherscan.

        Note: This requires a paid Etherscan API key for the tokenholderslist endpoint.
        For the free tier, we'll simulate this with a limited list of holders.

        Args:
            token_address (str): The Ethereum address of the token.
            page (int, optional): Page number for pagination. Defaults to 1.
            offset (int, optional): Number of results per page. Defaults to 100.

        Returns:
            Dict[str, Any]: List of token holders.
        """
        # For free tier API, we'll use account/txlist to get transactions and simulate holder data
        # In a real implementation with a paid API key, use the tokenholderlist endpoint

        # Attempt to use the token holder list endpoint first
        params = {
            "module": "token",
            "action": "tokenholderlist",
            "contractaddress": token_address,
            "page": page,
            "offset": offset,
        }

        try:
            result = self._make_request(params)
            if "result" in result and not isinstance(result["result"], str):
                return result
        except Exception as e:
            logger.warning(f"Token holder list endpoint failed: {str(e)}")

        # Fallback to simulated data if the API call doesn't work
        logger.info(
            "Using simulated token holder data (API requires paid tier for actual data)"
        )

        # Generate simulated holder data for testing
        simulated_data = self._generate_simulated_holders(token_address, page, offset)
        return simulated_data

    def _generate_simulated_holders(
        self, token_address: str, page: int, offset: int
    ) -> Dict[str, Any]:
        """
        Generate simulated token holder data for testing purposes.

        Args:
            token_address: The token contract address
            page: Page number
            offset: Number of results per page

        Returns:
            Simulated API response with token holders
        """
        # Get the total supply to make realistic percentages
        supply_response = self.get_token_supply(token_address)
        total_supply = int(supply_response.get("result", "10000000000000000000000000"))

        # Create simulated holders with a realistic distribution
        # - A few large holders (whales)
        # - Some medium holders (institutions)
        # - Many small holders (retail)

        # Determine start index based on page and offset
        start_idx = (page - 1) * offset

        # Create holder addresses - we'll use deterministic addresses based on index
        holders = []

        # Simulated distribution parameters
        whale_count = 5
        institution_count = 20
        retail_base = 1000

        # Generate holder data
        for i in range(start_idx, start_idx + offset):
            if i >= whale_count + institution_count + retail_base:
                break

            address = f"0x{i:040x}"  # Generate deterministic address

            # Determine holder type and allocate tokens accordingly
            if i < whale_count:
                # Whale - holds 5-15% of supply
                pct = 5 + (i * 2)  # 5%, 7%, 9%, 11%, 13%
                quantity = int(total_supply * pct / 100)
            elif i < whale_count + institution_count:
                # Institution - holds 0.5-2% of supply
                pct = 0.5 + ((i - whale_count) * 0.075)
                quantity = int(total_supply * pct / 100)
            else:
                # Retail - holds smaller amounts
                idx = i - whale_count - institution_count
                pct = 0.1 * (0.9**idx)  # Exponential decay
                quantity = int(total_supply * pct / 100)

            holders.append(
                {
                    "TokenHolderAddress": address,
                    "TokenHolderQuantity": str(quantity),
                    "balance": str(quantity),  # Adding this field for compatibility
                    "TokenHolderPercentage": str(pct),
                }
            )

            if len(holders) >= offset:
                break

        return {"status": "1", "message": "OK", "result": holders}

    def get_token_balance(self, token_address: str, address: str) -> Dict[str, Any]:
        """
        Get the token balance for a specific address.

        Args:
            token_address (str): The Ethereum address of the token.
            address (str): The Ethereum address to check balance for.

        Returns:
            Dict[str, Any]: Token balance information.
        """
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": token_address,
            "address": address,
            "tag": "latest",
        }

        return self._make_request(params)


class TheGraphAPI:
    """Client for interacting with The Graph API."""

    def __init__(self, subgraph_url: str):
        """
        Initialize The Graph API client.

        Args:
            subgraph_url (str): URL of the subgraph to query.
        """
        self.subgraph_url = subgraph_url

    def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the subgraph.

        Args:
            query (str): GraphQL query.
            variables (Dict[str, Any], optional): Variables for the query.

        Returns:
            Dict[str, Any]: Query results.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(self.subgraph_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL query failed: {str(e)}")
            raise
