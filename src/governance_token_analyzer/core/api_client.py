"""API Client Module for governance token data collection.

This module provides utilities for fetching data from various blockchain APIs
including Etherscan, The Graph, and protocol-specific endpoints.
"""

import logging
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

# Configure logging
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
    """Client for fetching data from blockchain APIs."""

    def __init__(
        self,
        etherscan_api_key: str = DEFAULT_ETHERSCAN_API_KEY,
        infura_api_key: str = DEFAULT_INFURA_API_KEY,
        graph_api_key: str = DEFAULT_GRAPH_API_KEY,
    ):
        """Initialize the API client."""
        self.etherscan_api_key = etherscan_api_key
        self.infura_api_key = infura_api_key
        self.graph_api_key = graph_api_key
        self.session = requests.Session()

        # Check if keys are available
        if not self.etherscan_api_key:
            logger.warning(
                "No Etherscan API key provided. Set ETHERSCAN_API_KEY environment variable."
            )
        if not self.infura_api_key:
            logger.warning(
                "No Infura API key provided. Set INFURA_API_KEY environment variable."
            )

    def get_token_holders(
        self, protocol: str, limit: int = 100, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """Get token holders for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            limit: Number of holders to retrieve
            use_real_data: Whether to use real data from APIs (vs. sample data)

        Returns:
            List of token holder dictionaries
        """
        if protocol not in TOKEN_ADDRESSES:
            raise ValueError(f"Unsupported protocol: {protocol}")

        token_address = TOKEN_ADDRESSES[protocol]

        try:
            if use_real_data:
                # Implement real API call to get token holders
                return self._fetch_token_holders(protocol, token_address, limit)
            else:
                # Generate sample data for MVP
                return self._generate_sample_holder_data(protocol, limit)

        except Exception as e:
            logger.error(f"Error fetching token holders for {protocol}: {e}")
            return []

    def get_governance_proposals(
        self, protocol: str, limit: int = 10, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """Get governance proposals for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
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
                # Generate sample data for MVP
                return self._generate_sample_proposal_data(protocol, limit)

        except Exception as e:
            logger.error(f"Error fetching governance proposals for {protocol}: {e}")
            # Fall back to sample data when real API calls fail
            return self._generate_sample_proposal_data(protocol, limit)

    def get_governance_votes(
        self, protocol: str, proposal_id: int, use_real_data: bool = False
    ) -> List[Dict[str, Any]]:
        """Get votes for a specific governance proposal.

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
                # Generate sample data for MVP
                return self._generate_sample_vote_data(protocol, proposal_id)

        except Exception as e:
            logger.error(
                f"Error fetching votes for proposal {proposal_id} in {protocol}: {e}"
            )
            # Fall back to sample data when real API calls fail
            return self._generate_sample_vote_data(protocol, proposal_id)

    def get_protocol_data(
        self, protocol: str, use_real_data: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive data for a protocol including token holders, proposals, and votes.

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

    def _fetch_token_holders(
        self, protocol: str, token_address: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch token holders for a specific protocol using real API data.

        Args:
            protocol: Protocol name
            token_address: Token contract address
            limit: Number of holders to retrieve

        Returns:
            List of token holder dictionaries
        """
        logger.info(f"Fetching token holders for {protocol}")

        try:
            # Route to the appropriate protocol-specific method
            if protocol == "compound":
                return self._fetch_compound_token_holders(token_address, limit)
            elif protocol == "uniswap":
                return self._fetch_uniswap_token_holders(token_address, limit)
            elif protocol == "aave":
                return self._fetch_aave_token_holders(token_address, limit)
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")

        except Exception as e:
            logger.error(f"Error in _fetch_token_holders for {protocol}: {str(e)}")
            # Fallback to sample data
            logger.warning(f"Falling back to sample data for {protocol} token holders")
            return self._generate_sample_holder_data(protocol, limit)

    def _fetch_compound_token_holders(
        self, token_address: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch Compound token holders using Ethplorer API.

        Args:
            token_address: COMP token contract address
            limit: Number of holders to retrieve

        Returns:
            List of token holder dictionaries
        """
        logger.info("Fetching COMP token holders")
        holders = []

        try:
            # Use Ethplorer API to get top token holders
            url = f"{ETHPLORER_API_URL}/getTopTokenHolders/{token_address}"
            params = {"apiKey": DEFAULT_ETHPLORER_API_KEY, "limit": limit}

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "holders" in data:
                for holder in data["holders"]:
                    balance = float(holder["balance"]) / (10**18)  # Convert from wei
                    percentage = holder["share"]

                    # Get additional holder info from Etherscan
                    holder_info = self._get_address_info(holder["address"])

                    holders.append(
                        {
                            "protocol": "compound",
                            "address": holder["address"],
                            "balance": balance,
                            "percentage": percentage,
                            "label": holder_info.get("label", ""),
                            "is_contract": holder_info.get("is_contract", False),
                            "last_updated": datetime.now().isoformat(),
                        }
                    )

            return holders

        except requests.RequestException as e:
            logger.error(f"Error fetching COMP token holders: {str(e)}")
            # Fallback to sample data if API call fails
            logger.warning("Falling back to sample data for COMP token holders")
            return self._generate_sample_holder_data("compound", limit)

    def _get_address_info(self, address: str) -> Dict[str, Any]:
        """Get additional information about an Ethereum address.

        Args:
            address: Ethereum address

        Returns:
            Dictionary with address information
        """
        info = {"label": "", "is_contract": False}

        try:
            # Check if the address is a contract
            params = {
                "module": "proxy",
                "action": "eth_getCode",
                "address": address,
                "tag": "latest",
                "apikey": self.etherscan_api_key,
            }

            response = self.session.get(ETHERSCAN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # If code is more than "0x", it's a contract
            if data.get("result") and data["result"] != "0x":
                info["is_contract"] = True

            # Try to get label from Etherscan
            params = {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "page": 1,
                "offset": 1,
                "sort": "desc",
                "apikey": self.etherscan_api_key,
            }

            response = self.session.get(ETHERSCAN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # If there's a known label for this address
            if data.get("result") and len(data["result"]) > 0:
                if "tokenName" in data["result"][0]:
                    info["label"] = data["result"][0]["tokenName"]

            return info

        except requests.RequestException as e:
            logger.warning(f"Error getting address info: {str(e)}")
            return info

    def _fetch_uniswap_token_holders(
        self, token_address: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch Uniswap token holders using Ethplorer API.

        Args:
            token_address: UNI token contract address
            limit: Number of holders to retrieve

        Returns:
            List of token holder dictionaries
        """
        logger.info("Fetching UNI token holders")
        holders = []

        try:
            # Use Ethplorer API to get top token holders
            url = f"{ETHPLORER_API_URL}/getTopTokenHolders/{token_address}"
            params = {"apiKey": DEFAULT_ETHPLORER_API_KEY, "limit": limit}

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "holders" in data:
                for holder in data["holders"]:
                    balance = float(holder["balance"]) / (10**18)  # Convert from wei
                    percentage = holder["share"]

                    # Get additional holder info from Etherscan
                    holder_info = self._get_address_info(holder["address"])

                    holders.append(
                        {
                            "protocol": "uniswap",
                            "address": holder["address"],
                            "balance": balance,
                            "percentage": percentage,
                            "label": holder_info.get("label", ""),
                            "is_contract": holder_info.get("is_contract", False),
                            "last_updated": datetime.now().isoformat(),
                        }
                    )

            return holders

        except requests.RequestException as e:
            logger.error(f"Error fetching UNI token holders: {str(e)}")
            # Fallback to sample data if API call fails
            logger.warning("Falling back to sample data for UNI token holders")
            return self._generate_sample_holder_data("uniswap", limit)

    def _fetch_aave_token_holders(
        self, token_address: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch Aave token holders using Ethplorer API.

        Args:
            token_address: AAVE token contract address
            limit: Number of holders to retrieve

        Returns:
            List of token holder dictionaries
        """
        logger.info("Fetching AAVE token holders")
        holders = []

        try:
            # Use Ethplorer API to get top token holders
            url = f"{ETHPLORER_API_URL}/getTopTokenHolders/{token_address}"
            params = {"apiKey": DEFAULT_ETHPLORER_API_KEY, "limit": limit}

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "holders" in data:
                for holder in data["holders"]:
                    balance = float(holder["balance"]) / (10**18)  # Convert from wei
                    percentage = holder["share"]

                    # Get additional holder info from Etherscan
                    holder_info = self._get_address_info(holder["address"])

                    holders.append(
                        {
                            "protocol": "aave",
                            "address": holder["address"],
                            "balance": balance,
                            "percentage": percentage,
                            "label": holder_info.get("label", ""),
                            "is_contract": holder_info.get("is_contract", False),
                            "last_updated": datetime.now().isoformat(),
                        }
                    )

            return holders

        except requests.RequestException as e:
            logger.error(f"Error fetching AAVE token holders: {str(e)}")
            # Fallback to sample data if API call fails
            logger.warning("Falling back to sample data for AAVE token holders")
            return self._generate_sample_holder_data("aave", limit)

    def _fetch_governance_proposals(
        self, protocol: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch governance proposals for a specific protocol using real API data.

        Args:
            protocol: Protocol name
            limit: Number of proposals to retrieve

        Returns:
            List of proposal dictionaries
        """
        logger.info(f"Fetching governance proposals for {protocol}")

        # Route to protocol-specific fetch method
        if protocol == "compound":
            return self._fetch_compound_proposals(limit)
        elif protocol == "uniswap":
            return self._fetch_uniswap_proposals(limit)
        elif protocol == "aave":
            return self._fetch_aave_proposals(limit)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    def _fetch_compound_proposals(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch Compound governance proposals using GraphQL.

        Args:
            limit: Number of proposals to retrieve

        Returns:
            List of proposal dictionaries
        """
        logger.info("Fetching Compound governance proposals")
        proposals = []

        try:
            # Define the GraphQL query for Compound proposals
            query = (
                """
            query {
              proposals(first: %d, orderBy: id, orderDirection: desc) {
                id
                description
                targets
                values
                signatures
                calldatas
                startBlock
                endBlock
                state
                proposer {
                  id
                }
                forVotes
                againstVotes
                abstainVotes
              }
            }
            """
                % limit
            )

            # Call the GraphQL endpoint
            url = GRAPHQL_ENDPOINTS["compound"]
            response = self.session.post(url, json={"query": query})
            response.raise_for_status()
            data = response.json()

            if "data" in data and "proposals" in data["data"]:
                for proposal_data in data["data"]["proposals"]:
                    # Get proposal state in human-readable form
                    state = proposal_data.get("state", "UNKNOWN")
                    state_map = {
                        "PENDING": "Pending",
                        "ACTIVE": "Active",
                        "CANCELED": "Canceled",
                        "DEFEATED": "Defeated",
                        "SUCCEEDED": "Succeeded",
                        "QUEUED": "Queued",
                        "EXPIRED": "Expired",
                        "EXECUTED": "Executed",
                    }

                    # Parse description to get title
                    description = proposal_data.get("description", "")
                    title = (
                        description.split("\n")[0]
                        if description
                        else f"Proposal {proposal_data.get('id', 'Unknown')}"
                    )

                    # Parse votes
                    for_votes = float(proposal_data.get("forVotes", "0")) / (10**18)
                    against_votes = float(proposal_data.get("againstVotes", "0")) / (
                        10**18
                    )
                    abstain_votes = float(proposal_data.get("abstainVotes", "0")) / (
                        10**18
                    )
                    total_votes = for_votes + against_votes + abstain_votes

                    # Calculate vote percentages
                    for_percentage = (
                        (for_votes / total_votes * 100) if total_votes > 0 else 0
                    )
                    against_percentage = (
                        (against_votes / total_votes * 100) if total_votes > 0 else 0
                    )
                    abstain_percentage = (
                        (abstain_votes / total_votes * 100) if total_votes > 0 else 0
                    )

                    proposal = {
                        "protocol": "compound",
                        "id": int(proposal_data.get("id", 0)),
                        "title": title,
                        "description": description,
                        "proposer": proposal_data.get("proposer", {}).get("id", ""),
                        "status": state_map.get(state, state),
                        "start_block": int(proposal_data.get("startBlock", 0)),
                        "end_block": int(proposal_data.get("endBlock", 0)),
                        "for_votes": for_votes,
                        "against_votes": against_votes,
                        "abstain_votes": abstain_votes,
                        "for_percentage": for_percentage,
                        "against_percentage": against_percentage,
                        "abstain_percentage": abstain_percentage,
                        "total_votes": total_votes,
                        "created_at": datetime.now().isoformat(),  # Placeholder as not available in data
                    }

                    proposals.append(proposal)

            return proposals

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"Error fetching Compound governance proposals: {str(e)}")
            # Fallback to sample data if API call fails
            logger.warning(
                "Falling back to sample data for Compound governance proposals"
            )
            return self._generate_sample_proposal_data("compound", limit)

    def _fetch_uniswap_proposals(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch Uniswap governance proposals using GraphQL.

        Args:
            limit: Number of proposals to retrieve

        Returns:
            List of proposal dictionaries
        """
        logger.info("Fetching Uniswap governance proposals")
        proposals = []

        try:
            # Define the GraphQL query for Uniswap proposals
            query = (
                """
            query {
              proposals(first: %d, orderBy: createdTimestamp, orderDirection: desc) {
                id
                proposer
                description
                status
                targets
                values
                signatures
                calldatas
                createdTimestamp
                startBlock
                endBlock
                forVotes
                againstVotes
                abstainVotes
                quorumVotes
              }
            }
            """
                % limit
            )

            # Call the GraphQL endpoint
            url = GRAPHQL_ENDPOINTS["uniswap"]
            response = self.session.post(url, json={"query": query})
            response.raise_for_status()
            data = response.json()

            if "data" in data and "proposals" in data["data"]:
                for proposal_data in data["data"]["proposals"]:
                    # Get proposal state in human-readable form
                    status = proposal_data.get("status", "UNKNOWN")
                    status_map = {
                        "PENDING": "Pending",
                        "ACTIVE": "Active",
                        "CANCELED": "Canceled",
                        "DEFEATED": "Defeated",
                        "SUCCEEDED": "Succeeded",
                        "QUEUED": "Queued",
                        "EXPIRED": "Expired",
                        "EXECUTED": "Executed",
                    }

                    # Parse description to get title
                    description = proposal_data.get("description", "")
                    title = (
                        description.split("\n")[0]
                        if description
                        else f"Proposal {proposal_data.get('id', 'Unknown')}"
                    )

                    # Parse votes
                    for_votes = float(proposal_data.get("forVotes", "0")) / (10**18)
                    against_votes = float(proposal_data.get("againstVotes", "0")) / (
                        10**18
                    )
                    abstain_votes = float(proposal_data.get("abstainVotes", "0")) / (
                        10**18
                    )
                    total_votes = for_votes + against_votes + abstain_votes

                    # Calculate vote percentages
                    for_percentage = (
                        (for_votes / total_votes * 100) if total_votes > 0 else 0
                    )
                    against_percentage = (
                        (against_votes / total_votes * 100) if total_votes > 0 else 0
                    )
                    abstain_percentage = (
                        (abstain_votes / total_votes * 100) if total_votes > 0 else 0
                    )

                    # Convert timestamp to datetime
                    created_time = datetime.fromtimestamp(
                        int(proposal_data.get("createdTimestamp", 0))
                    )

                    proposal = {
                        "protocol": "uniswap",
                        "id": int(proposal_data.get("id", 0)),
                        "title": title,
                        "description": description,
                        "proposer": proposal_data.get("proposer", ""),
                        "status": status_map.get(status, status),
                        "start_block": int(proposal_data.get("startBlock", 0)),
                        "end_block": int(proposal_data.get("endBlock", 0)),
                        "for_votes": for_votes,
                        "against_votes": against_votes,
                        "abstain_votes": abstain_votes,
                        "for_percentage": for_percentage,
                        "against_percentage": against_percentage,
                        "abstain_percentage": abstain_percentage,
                        "total_votes": total_votes,
                        "created_at": created_time.isoformat(),
                    }

                    proposals.append(proposal)

            return proposals

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"Error fetching Uniswap governance proposals: {str(e)}")
            # Fallback to sample data if API call fails
            logger.warning(
                "Falling back to sample data for Uniswap governance proposals"
            )
            return self._generate_sample_proposal_data("uniswap", limit)

    def _fetch_aave_proposals(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch Aave governance proposals using GraphQL.

        Args:
            limit: Number of proposals to retrieve

        Returns:
            List of proposal dictionaries
        """
        logger.info("Fetching Aave governance proposals")
        proposals = []

        try:
            # Define the GraphQL query for Aave proposals
            query = (
                """
            query {
              proposals(first: %d, orderBy: startBlock, orderDirection: desc) {
                id
                creator
                executor
                title
                shortDescription
                description
                state
                ipfsHash
                startBlock
                endBlock
                executionTime
                forVotes
                againstVotes
                totalVotes
                executed
                canceled
                strategy
                totalPropositionSupply
              }
            }
            """
                % limit
            )

            # Call the GraphQL endpoint
            url = GRAPHQL_ENDPOINTS["aave"]
            response = self.session.post(url, json={"query": query})
            response.raise_for_status()
            data = response.json()

            if "data" in data and "proposals" in data["data"]:
                for proposal_data in data["data"]["proposals"]:
                    # Get proposal state in human-readable form
                    state = proposal_data.get("state", "UNKNOWN")
                    state_map = {
                        "PENDING": "Pending",
                        "ACTIVE": "Active",
                        "CANCELED": "Canceled",
                        "DEFEATED": "Defeated",
                        "SUCCEEDED": "Succeeded",
                        "QUEUED": "Queued",
                        "EXPIRED": "Expired",
                        "EXECUTED": "Executed",
                    }

                    # Use title or generate one from description
                    title = proposal_data.get("title", "")
                    if not title and proposal_data.get("shortDescription"):
                        title = proposal_data.get("shortDescription")
                    elif not title:
                        title = f"Proposal {proposal_data.get('id', 'Unknown')}"

                    # Parse votes
                    for_votes = float(proposal_data.get("forVotes", "0")) / (10**18)
                    against_votes = float(proposal_data.get("againstVotes", "0")) / (
                        10**18
                    )
                    total_votes = float(proposal_data.get("totalVotes", "0")) / (10**18)
                    abstain_votes = total_votes - for_votes - against_votes

                    # Calculate vote percentages
                    for_percentage = (
                        (for_votes / total_votes * 100) if total_votes > 0 else 0
                    )
                    against_percentage = (
                        (against_votes / total_votes * 100) if total_votes > 0 else 0
                    )
                    abstain_percentage = (
                        (abstain_votes / total_votes * 100) if total_votes > 0 else 0
                    )

                    # Convert execution time to datetime if available
                    created_at = datetime.now().isoformat()
                    if proposal_data.get("executionTime"):
                        try:
                            created_time = datetime.fromtimestamp(
                                int(proposal_data.get("executionTime", 0))
                            )
                            created_at = created_time.isoformat()
                        except (ValueError, TypeError):
                            pass

                    proposal = {
                        "protocol": "aave",
                        "id": int(proposal_data.get("id", 0)),
                        "title": title,
                        "description": proposal_data.get("description", ""),
                        "proposer": proposal_data.get("creator", ""),
                        "status": state_map.get(state, state),
                        "start_block": int(proposal_data.get("startBlock", 0)),
                        "end_block": int(proposal_data.get("endBlock", 0)),
                        "for_votes": for_votes,
                        "against_votes": against_votes,
                        "abstain_votes": abstain_votes,
                        "for_percentage": for_percentage,
                        "against_percentage": against_percentage,
                        "abstain_percentage": abstain_percentage,
                        "total_votes": total_votes,
                        "created_at": created_at,
                        "ipfs_hash": proposal_data.get("ipfsHash", ""),
                    }

                    proposals.append(proposal)

            return proposals

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"Error fetching Aave governance proposals: {str(e)}")
            # Fallback to sample data if API call fails
            logger.warning("Falling back to sample data for Aave governance proposals")
            return self._generate_sample_proposal_data("aave", limit)

    def _fetch_governance_votes(
        self, protocol: str, proposal_id: int
    ) -> List[Dict[str, Any]]:
        """Fetch governance votes for a specific proposal using real API data.

        Args:
            protocol: Protocol name
            proposal_id: ID of the proposal

        Returns:
            List of vote dictionaries
        """
        logger.info(f"Fetching votes for proposal {proposal_id} in {protocol}")

        # Route to protocol-specific fetch method
        if protocol == "compound":
            return self._fetch_compound_votes(proposal_id)
        elif protocol == "uniswap":
            return self._fetch_uniswap_votes(proposal_id)
        elif protocol == "aave":
            return self._fetch_aave_votes(proposal_id)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    def _fetch_compound_votes(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Fetch votes for a Compound governance proposal.

        Args:
            proposal_id: ID of the proposal

        Returns:
            List of vote dictionaries
        """
        logger.info(f"Fetching votes for Compound proposal {proposal_id}")
        votes = []

        try:
            # Define the GraphQL query for Compound votes
            query = (
                """
            query {
              votes(where: {proposal: "%s"}, first: 1000) {
                id
                voter {
                  id
                }
                support
                votes
                blockNumber
                blockTimestamp
              }
            }
            """
                % proposal_id
            )

            # Call the GraphQL endpoint
            url = GRAPHQL_ENDPOINTS["compound"]
            response = self.session.post(url, json={"query": query})
            response.raise_for_status()
            data = response.json()

            if "data" in data and "votes" in data["data"]:
                for vote_data in data["data"]["votes"]:
                    # Map support value to readable vote choice
                    support = int(vote_data.get("support", 0))
                    vote_choice_map = {0: "against", 1: "for", 2: "abstain"}
                    vote_choice = vote_choice_map.get(support, "unknown")

                    # Parse vote power
                    vote_power = float(vote_data.get("votes", "0")) / (10**18)

                    # Convert timestamp to datetime if available
                    voted_at = datetime.now().isoformat()
                    if vote_data.get("blockTimestamp"):
                        try:
                            voted_time = datetime.fromtimestamp(
                                int(vote_data.get("blockTimestamp", 0))
                            )
                            voted_at = voted_time.isoformat()
                        except (ValueError, TypeError):
                            pass

                    votes.append(
                        {
                            "protocol": "compound",
                            "proposal_id": proposal_id,
                            "voter": vote_data.get("voter", {}).get("id", ""),
                            "vote_choice": vote_choice,
                            "vote_power": vote_power,
                            "block_number": int(vote_data.get("blockNumber", 0)),
                            "voted_at": voted_at,
                        }
                    )

            return votes

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(
                f"Error fetching votes for Compound proposal {proposal_id}: {str(e)}"
            )
            # Fallback to sample data if API call fails
            logger.warning(
                f"Falling back to sample data for Compound proposal {proposal_id} votes"
            )
            return self._generate_sample_vote_data("compound", proposal_id)

    def _fetch_uniswap_votes(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Fetch votes for a Uniswap governance proposal.

        Args:
            proposal_id: ID of the proposal

        Returns:
            List of vote dictionaries
        """
        logger.info(f"Fetching votes for Uniswap proposal {proposal_id}")
        votes = []

        try:
            # Define the GraphQL query for Uniswap votes
            query = (
                """
            query {
              votes(where: {proposal: "%s"}, first: 1000) {
                id
                voter
                support
                votes
                blockNumber
                reason
                timestamp
              }
            }
            """
                % proposal_id
            )

            # Call the GraphQL endpoint
            url = GRAPHQL_ENDPOINTS["uniswap"]
            response = self.session.post(url, json={"query": query})
            response.raise_for_status()
            data = response.json()

            if "data" in data and "votes" in data["data"]:
                for vote_data in data["data"]["votes"]:
                    # Map support value to readable vote choice
                    support = int(vote_data.get("support", 0))
                    vote_choice_map = {0: "against", 1: "for", 2: "abstain"}
                    vote_choice = vote_choice_map.get(support, "unknown")

                    # Parse vote power
                    vote_power = float(vote_data.get("votes", "0")) / (10**18)

                    # Convert timestamp to datetime if available
                    voted_at = datetime.now().isoformat()
                    if vote_data.get("timestamp"):
                        try:
                            voted_time = datetime.fromtimestamp(
                                int(vote_data.get("timestamp", 0))
                            )
                            voted_at = voted_time.isoformat()
                        except (ValueError, TypeError):
                            pass

                    votes.append(
                        {
                            "protocol": "uniswap",
                            "proposal_id": proposal_id,
                            "voter": vote_data.get("voter", ""),
                            "vote_choice": vote_choice,
                            "vote_power": vote_power,
                            "reason": vote_data.get("reason", ""),
                            "block_number": int(vote_data.get("blockNumber", 0)),
                            "voted_at": voted_at,
                        }
                    )

            return votes

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(
                f"Error fetching votes for Uniswap proposal {proposal_id}: {str(e)}"
            )
            # Fallback to sample data if API call fails
            logger.warning(
                f"Falling back to sample data for Uniswap proposal {proposal_id} votes"
            )
            return self._generate_sample_vote_data("uniswap", proposal_id)

    def _fetch_aave_votes(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Fetch votes for an Aave governance proposal.

        Args:
            proposal_id: ID of the proposal

        Returns:
            List of vote dictionaries
        """
        logger.info(f"Fetching votes for Aave proposal {proposal_id}")
        votes = []

        try:
            # Define the GraphQL query for Aave votes
            query = (
                """
            query {
              votes(where: {proposal: "%s"}, first: 1000) {
                id
                voter
                support
                votingPower
                timestamp
                proposal {
                  id
                }
              }
            }
            """
                % proposal_id
            )

            # Call the GraphQL endpoint
            url = GRAPHQL_ENDPOINTS["aave"]
            response = self.session.post(url, json={"query": query})
            response.raise_for_status()
            data = response.json()

            if "data" in data and "votes" in data["data"]:
                for vote_data in data["data"]["votes"]:
                    # Map support value to readable vote choice
                    support = vote_data.get("support", False)
                    vote_choice = "for" if support else "against"

                    # Parse vote power
                    vote_power = float(vote_data.get("votingPower", "0")) / (10**18)

                    # Convert timestamp to datetime if available
                    voted_at = datetime.now().isoformat()
                    if vote_data.get("timestamp"):
                        try:
                            voted_time = datetime.fromtimestamp(
                                int(vote_data.get("timestamp", 0))
                            )
                            voted_at = voted_time.isoformat()
                        except (ValueError, TypeError):
                            pass

                    votes.append(
                        {
                            "protocol": "aave",
                            "proposal_id": proposal_id,
                            "voter": vote_data.get("voter", ""),
                            "vote_choice": vote_choice,
                            "vote_power": vote_power,
                            "voted_at": voted_at,
                        }
                    )

            return votes

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(
                f"Error fetching votes for Aave proposal {proposal_id}: {str(e)}"
            )
            # Fallback to sample data if API call fails
            logger.warning(
                f"Falling back to sample data for Aave proposal {proposal_id} votes"
            )
            return self._generate_sample_vote_data("aave", proposal_id)

    def _calculate_participation_rate(self, proposals: List[Dict[str, Any]]) -> float:
        """Calculate governance participation rate based on proposals.

        Args:
            proposals: List of proposal dictionaries

        Returns:
            Participation rate as a float between 0 and 1
        """
        if not proposals:
            return 0.0

        total_eligible_votes = 0
        total_votes_cast = 0

        for proposal in proposals:
            # Sum up votes for and against
            for_votes = proposal.get("for_votes", 0)
            against_votes = proposal.get("against_votes", 0)
            abstain_votes = proposal.get("abstain_votes", 0)

            votes_cast = for_votes + against_votes + abstain_votes
            eligible_votes = proposal.get("eligible_votes", 0)

            # If eligible_votes is not available, use the total supply as an approximation
            if eligible_votes == 0:
                protocol = proposal.get("protocol")
                if protocol in PROTOCOL_INFO:
                    eligible_votes = PROTOCOL_INFO[protocol]["total_supply"]

            total_eligible_votes += eligible_votes
            total_votes_cast += votes_cast

        # Calculate overall participation rate
        if total_eligible_votes > 0:
            return total_votes_cast / total_eligible_votes
        else:
            return 0.0

    def _generate_sample_holder_data(
        self, protocol: str, count: int
    ) -> List[Dict[str, Any]]:
        """Generate sample token holder data for a specific protocol.

        Args:
            protocol: Protocol name
            count: Number of holders to generate

        Returns:
            List of token holder dictionaries
        """
        if protocol not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Get protocol info for sample data generation
        info = PROTOCOL_INFO[protocol]

        # Reserve top holders for whales/known addresses
        whale_count = min(len(info["whale_addresses"]), count // 5)
        regular_count = count - whale_count

        # Generate power-law distribution for token balances
        total_supply = info["total_supply"]
        whale_supply = total_supply * 0.4  # 40% held by whales
        regular_supply = total_supply * 0.6  # 60% held by regular holders

        # Generate whale balances (somewhat evenly distributed among whales)
        whale_balances = []
        for i in range(whale_count):
            # Give each whale a somewhat random but significant balance
            whale_balances.append(whale_supply / whale_count * random.uniform(0.7, 1.3))

        # Generate regular holder balances with power-law distribution
        regular_balances = self._generate_power_law_distribution(
            regular_count, regular_supply, alpha=1.5
        )

        # Create holder data structures
        holders = []

        # Add whale addresses
        for i in range(whale_count):
            address = info["whale_addresses"][i % len(info["whale_addresses"])]
            balance = whale_balances[i]

            holder = {
                "address": address,
                "balance": balance,
                "balance_readable": f"{balance:,.2f} {info['token_symbol']}",
                "percentage": (balance / total_supply) * 100,
                "is_contract": random.random() < 0.6,  # 60% chance of being a contract
                "last_transaction": (
                    datetime.now() - timedelta(days=random.randint(1, 30))
                ).isoformat(),
                "voting_power": balance,
                "delegated_power": 0.0,
                "delegated_to": None,
                "protocol": protocol,
            }
            holders.append(holder)

        # Add regular addresses
        for i in range(regular_count):
            # Generate random-looking Ethereum address
            address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            balance = regular_balances[i]

            # Determine if this holder has delegated their voting power
            is_delegated = random.random() < 0.3  # 30% chance of delegation
            delegated_to = None
            delegated_power = 0.0
            voting_power = balance

            if is_delegated and holders:
                # Delegate to one of the existing holders, preferably a whale
                delegate_idx = random.randint(0, min(len(holders) - 1, 10))
                delegated_to = holders[delegate_idx]["address"]
                delegated_power = balance
                voting_power = 0.0

                # Update the delegate's voting power
                holders[delegate_idx]["voting_power"] += balance

            holder = {
                "address": address,
                "balance": balance,
                "balance_readable": f"{balance:,.2f} {info['token_symbol']}",
                "percentage": (balance / total_supply) * 100,
                "is_contract": random.random() < 0.1,  # 10% chance of being a contract
                "last_transaction": (
                    datetime.now() - timedelta(days=random.randint(1, 60))
                ).isoformat(),
                "voting_power": voting_power,
                "delegated_power": delegated_power,
                "delegated_to": delegated_to,
                "protocol": protocol,
            }
            holders.append(holder)

        # Sort holders by balance in descending order
        holders.sort(key=lambda x: x["balance"], reverse=True)

        return holders

    def _generate_power_law_distribution(
        self, count: int, total: float, alpha: float = 1.5
    ) -> List[float]:
        """Generate a power-law distribution of values.

        Args:
            count: Number of values to generate
            total: Sum of all values
            alpha: Power-law exponent (higher means more skewed distribution)

        Returns:
            List of values following a power-law distribution
        """
        # Generate raw power-law values
        raw_values = [1.0 / (i + 1) ** alpha for i in range(count)]

        # Normalize to the desired total
        sum_values = sum(raw_values)
        normalized_values = [v * (total / sum_values) for v in raw_values]

        return normalized_values

    def _generate_sample_proposal_data(
        self, protocol: str, count: int
    ) -> List[Dict[str, Any]]:
        """Generate sample governance proposal data for a specific protocol.

        Args:
            protocol: Protocol name
            count: Number of proposals to generate

        Returns:
            List of proposal dictionaries
        """
        if protocol not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Get protocol info for sample data generation
        info = PROTOCOL_INFO[protocol]

        # Generate proposal titles based on protocol
        proposal_titles = {
            "compound": [
                "Update Reserve Factor for cTokens",
                "Add WBTC as Collateral",
                "Adjust Liquidation Incentive",
                "Update Price Oracle",
                "Increase Borrow Cap for USDC",
                "Reduce Reserve Factor for DAI",
                "Pause Borrowing for USDT",
                "Update Interest Rate Model",
                "Add Support for New Market",
                "Governance Parameter Update",
            ],
            "uniswap": [
                "Deploy Uniswap on Optimism",
                "Fee Switch Activation",
                "Deploy Uniswap v3 on Arbitrum",
                "Governance Treasury Diversification",
                "Increase Protocol Fee",
                "Deploy on Polygon Network",
                "Reduce Fee Tier for Stablecoin Pairs",
                "Create Uniswap Foundation",
                "Deploy on BNB Chain",
                "Adjust Fee Tiers",
            ],
            "aave": [
                "Add LINK as Collateral",
                "Update Risk Parameters",
                "Activate Stablecoin Optimization Module",
                "Add Support for New Network",
                "Update Liquidation Threshold",
                "Adjust Reserve Factor",
                "Enable Borrowing for MATIC",
                "Update Interest Rate Strategy",
                "Deploy Aave v3 on Optimism",
                "Governance Process Improvement",
            ],
        }

        protocol_titles = proposal_titles.get(protocol, ["Governance Proposal"])

        # Generate proposal data
        proposals = []

        for i in range(count):
            # Generate random proposal details
            proposal_id = i + 1

            # Determine proposal status
            status_options = ["active", "passed", "executed", "failed", "canceled"]
            status_weights = [
                0.1,
                0.5,
                0.2,
                0.1,
                0.1,
            ]  # More passed proposals than failed
            proposal_status = random.choices(status_options, status_weights)[0]

            # Generate random vote counts
            total_supply = info["total_supply"]
            participation_rate = random.uniform(0.1, 0.4)  # 10-40% participation
            eligible_votes = total_supply

            total_votes = eligible_votes * participation_rate

            # Determine outcome based on status
            if proposal_status in ["passed", "executed"]:
                # Passed proposals have more for votes
                for_percentage = random.uniform(0.51, 0.95)
            elif proposal_status == "failed":
                # Failed proposals have more against votes
                for_percentage = random.uniform(0.05, 0.49)
            else:
                # Active or canceled proposals have varied distributions
                for_percentage = random.uniform(0.3, 0.7)

            against_percentage = 1.0 - for_percentage

            for_votes = total_votes * for_percentage
            against_votes = total_votes * against_percentage
            abstain_votes = total_votes * random.uniform(0, 0.1)  # 0-10% abstain

            # Generate random timestamps
            now = datetime.now()

            # Older proposals are more likely to be executed/passed/failed
            if proposal_id <= count // 3:
                # Older proposals (completed)
                created_at = now - timedelta(days=random.randint(60, 120))
                start_time = created_at + timedelta(days=2)
                end_time = start_time + timedelta(days=3)
            elif proposal_id <= 2 * count // 3:
                # Medium-age proposals
                created_at = now - timedelta(days=random.randint(14, 59))
                start_time = created_at + timedelta(days=2)
                end_time = start_time + timedelta(days=3)
            else:
                # Recent proposals (possibly active)
                created_at = now - timedelta(days=random.randint(1, 13))
                start_time = created_at + timedelta(days=1)
                end_time = start_time + timedelta(days=3)

                # If the end time is in the future, it's active
                if end_time > now and proposal_status != "canceled":
                    proposal_status = "active"

            # For executed proposals, add an execution time
            executed_at = None
            if proposal_status == "executed":
                executed_at = end_time + timedelta(days=random.randint(1, 5))

            # Get a title for the proposal
            title = protocol_titles[i % len(protocol_titles)]

            # Create the proposal object
            proposal = {
                "id": proposal_id,
                "title": title,
                "description": f"This is a sample proposal to {title.lower()} for the {info['token_name']} protocol.",
                "proposer": random.choice(info["whale_addresses"]),
                "status": proposal_status,
                "created_at": created_at.isoformat(),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "executed_at": executed_at.isoformat() if executed_at else None,
                "for_votes": for_votes,
                "against_votes": against_votes,
                "abstain_votes": abstain_votes,
                "for_votes_readable": f"{for_votes:,.2f} {info['token_symbol']}",
                "against_votes_readable": f"{against_votes:,.2f} {info['token_symbol']}",
                "abstain_votes_readable": f"{abstain_votes:,.2f} {info['token_symbol']}",
                "quorum_votes": info["total_supply"] * 0.04,  # 4% quorum
                "eligible_votes": eligible_votes,
                "participation_rate": participation_rate,
                "protocol": protocol,
            }

            proposals.append(proposal)

        return proposals

    def _generate_sample_vote_data(
        self, protocol: str, proposal_id: int
    ) -> List[Dict[str, Any]]:
        """Generate sample vote data for a specific proposal.

        Args:
            protocol: Protocol name
            proposal_id: ID of the proposal

        Returns:
            List of vote dictionaries
        """
        if protocol not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Get protocol info
        info = PROTOCOL_INFO[protocol]

        # Generate a sample of 20-50 votes
        num_votes = random.randint(20, 50)

        # Generate addresses based on Ethereum format
        voters = []
        for _ in range(num_votes):
            # Generate a random Ethereum address
            addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))
            voters.append(addr)

        # Ensure the whales are among the voters
        for i, whale in enumerate(info["whale_addresses"]):
            if i < len(voters):
                voters[i] = whale

        votes = []

        # Get total token supply for calculating voting power
        total_supply = info["total_supply"]

        # Power law distribution for voting power
        voting_powers = self._generate_power_law_distribution(
            num_votes, total_supply * 0.4, 1.5
        )

        for i, voter in enumerate(voters):
            # Determine vote type (for/against/abstain)
            vote_types = ["for", "against", "abstain"]
            vote_weights = [0.7, 0.25, 0.05]  # 70% for, 25% against, 5% abstain
            vote_choice = random.choices(vote_types, weights=vote_weights)[0]

            # Determine voting power
            vote_power = voting_powers[i]

            # Format readable voting power with token symbol
            vote_power_readable = f"{vote_power:,.2f} {info['token_symbol']}"

            # Generate random timestamps from the past 2 weeks
            timestamp = datetime.now() - timedelta(days=random.randint(1, 14))

            # Generate a random transaction hash (for illustrative purposes)
            tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))

            # Small chance of having a reason for the vote
            reason = None
            if random.random() < 0.2:
                reasons = [
                    "I support this proposal because it improves the protocol.",
                    "This aligns with the long-term vision of the DAO.",
                    "The changes proposed are necessary for growth.",
                    "I oppose this change due to security concerns.",
                    "This proposal lacks sufficient testing.",
                ]
                reason = random.choice(reasons)

            vote = {
                "voter": voter,
                "proposal_id": proposal_id,
                "vote_choice": vote_choice,
                "vote_power": vote_power,
                "vote_power_readable": vote_power_readable,
                "voted_at": timestamp.isoformat(),
                "transaction_hash": tx_hash,
                "reason": reason,
                "protocol": protocol,
            }
            votes.append(vote)

        return votes
