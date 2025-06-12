"""
Uniswap Protocol Module for analyzing UNI token distribution.
This module handles fetching and processing data for the Uniswap protocol.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from ..core.api_client import APIClient

# Initialize API client
api_client = APIClient()


def get_token_holders(
    limit: int = 100, use_real_data: bool = False
) -> List[Dict[str, Any]]:
    """
    Get list of top UNI token holders.

    Args:
        limit: Number of holders to retrieve
        use_real_data: Whether to use real data from APIs (vs. sample data)

    Returns:
        List of token holder dictionaries
    """
    return api_client.get_token_holders("uniswap", limit, use_real_data)


def get_governance_proposals(
    limit: int = 10, use_real_data: bool = False
) -> List[Dict[str, Any]]:
    """
    Get list of Uniswap governance proposals.

    Args:
        limit: Number of proposals to retrieve
        use_real_data: Whether to use real data from APIs (vs. sample data)

    Returns:
        List of proposal dictionaries
    """
    return api_client.get_governance_proposals("uniswap", limit, use_real_data)


def get_governance_votes(
    proposal_id: int, use_real_data: bool = False
) -> List[Dict[str, Any]]:
    """
    Get list of votes for a specific proposal.

    Args:
        proposal_id: ID of the proposal
        use_real_data: Whether to use real data from APIs (vs. sample data)

    Returns:
        List of vote dictionaries
    """
    return api_client.get_governance_votes("uniswap", proposal_id, use_real_data)


def get_sample_data() -> Dict[str, Any]:
    """
    Get sample data for testing.

    Returns:
        Dictionary containing sample data for token holders and governance
    """
    return api_client.get_protocol_data("uniswap")

    # Generate votes for each proposal
    votes = []
    for proposal in proposals:
        proposal_votes = _generate_sample_vote_data(proposal["id"])
        votes.extend(proposal_votes)


def get_protocol_info() -> Dict[str, Any]:
    """
    Get basic information about the Uniswap protocol.

    Returns:
        Dictionary containing basic protocol information
    """
    data = get_sample_data()
    return {
        "protocol": "uniswap",
        "token_symbol": data["token_symbol"],
        "token_name": data["token_name"],
        "total_supply": data["total_supply"],
        "participation_rate": data["participation_rate"],
    }


def calculate_voting_power_distribution() -> Dict[str, float]:
    """
    Calculate the distribution of voting power across holders.

    Returns:
        Dictionary containing voting power distribution metrics
    """
    holders = get_token_holders()

    # Calculate voting power distribution
    total_supply = sum(holder["balance"] for holder in holders)

    # Calculate percentage held by top holders
    top_10_percentage = (
        sum(holder["balance"] for holder in holders[:10]) / total_supply * 100
    )
    top_20_percentage = (
        sum(holder["balance"] for holder in holders[:20]) / total_supply * 100
    )
    top_50_percentage = (
        sum(holder["balance"] for holder in holders[:50]) / total_supply * 100
    )

    # Calculate delegated voting power
    total_delegated = sum(holder.get("delegated_power", 0) for holder in holders)
    delegation_percentage = (total_delegated / total_supply) * 100

    return {
        "top_10_percentage": top_10_percentage,
        "top_20_percentage": top_20_percentage,
        "top_50_percentage": top_50_percentage,
        "delegation_percentage": delegation_percentage,
    }

    # Create a list of decreasing balances (Pareto-like distribution but more distributed than Compound)
    balances = []
    remaining_supply = total_supply

    # Uniswap has a more dispersed distribution due to the airdrop
    for i in range(count):
        # Generate a balance based on a power-law distribution
        # Whales have smaller percentage than in Compound
        share = random.uniform(0.02, 0.1) if i < 10 else random.uniform(0.0001, 0.02)
        balance = min(remaining_supply * share, remaining_supply)
        balances.append(balance)
        remaining_supply -= balance

    # Add any remaining supply to the last holder
    if remaining_supply > 0 and balances:
        balances[-1] += remaining_supply

    # Convert to percentage and create holder dictionaries
    for i in range(count):
        address = (
            f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}"
        )
        balance = balances[i]
        percentage = (balance / total_supply) * 100

        holders.append(
            {
                "address": address,
                "balance": balance,
                "percentage": percentage,
                "txn_count": random.randint(1, 100),
                "last_txn_date": (
                    datetime.now() - timedelta(days=random.randint(1, 365))
                ).isoformat(),
            }
        )

    # Sort by balance in descending order
    holders.sort(key=lambda x: x["balance"], reverse=True)

    return holders


# Deprecated functions - for backward compatibility only
import warnings
import random
from datetime import datetime, timedelta


def _generate_sample_holder_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample token holder data for testing."""
    warnings.warn(
        "_generate_sample_holder_data is deprecated, use api_client.get_token_holders instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return api_client._generate_sample_holder_data("uniswap", count)


def _generate_sample_proposal_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample governance proposal data for testing."""
    warnings.warn(
        "_generate_sample_proposal_data is deprecated, use api_client.get_governance_proposals instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return api_client._generate_sample_proposal_data("uniswap", count)

    for i in range(count):
        proposal_id = i + 1
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(3, 7))

        # Random proposal state
        states = ["active", "passed", "executed", "defeated", "expired"]
        state = random.choice(states)

        # Random vote counts - Uniswap has larger vote counts due to more tokens
        for_votes = random.randint(10000000, 50000000)
        against_votes = random.randint(1000000, 20000000)
        total_votes = for_votes + against_votes

        proposals.append(
            {
                "id": proposal_id,
                "title": f"Proposal {proposal_id}: {random.choice(['Fee Change', 'Treasury Allocation', 'Protocol Upgrade', 'Governance Change'])}",
                "description": f"This proposal aims to {random.choice(['change fees', 'allocate treasury funds', 'upgrade the protocol', 'change governance parameters'])}",
                "proposer": f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "state": state,
                "for_votes": for_votes,
                "against_votes": against_votes,
                "total_votes": total_votes,
                "participation_rate": random.uniform(
                    5, 30
                ),  # percentage - lower than Compound due to more dispersed tokens
            }
        )

    return proposals


def _generate_sample_vote_data(proposal_id: int) -> List[Dict[str, Any]]:
    """Generate sample vote data for a specific proposal."""
    warnings.warn(
        "_generate_sample_vote_data is deprecated, use api_client.get_governance_votes instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return api_client._generate_sample_vote_data("uniswap", proposal_id)
