"""
Aave Protocol Module for analyzing AAVE token distribution.
This module handles fetching and processing data for the Aave protocol.
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
    Get list of top AAVE token holders.

    Args:
        limit: Number of holders to retrieve
        use_real_data: Whether to use real data from APIs (vs. sample data)

    Returns:
        List of token holder dictionaries
    """
    return api_client.get_token_holders('aave', limit, use_real_data)


def get_governance_proposals(
    limit: int = 10, use_real_data: bool = False
) -> List[Dict[str, Any]]:
    """
    Get list of Aave governance proposals.

    Args:
        limit: Number of proposals to retrieve
        use_real_data: Whether to use real data from APIs (vs. sample data)

    Returns:
        List of proposal dictionaries
    """
    return api_client.get_governance_proposals('aave', limit, use_real_data)


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
    return api_client.get_governance_votes('aave', proposal_id, use_real_data)


def get_sample_data() -> Dict[str, Any]:
    """
    Get sample data for testing.

    Returns:
        Dictionary containing sample data for token holders and governance
    """
    token_holders = _generate_sample_holder_data(100)
    proposals = _generate_sample_proposal_data(5)

    # Generate votes for each proposal
    votes = []
    for proposal in proposals:
        proposal_votes = _generate_sample_vote_data(proposal["id"])
        votes.extend(proposal_votes)

    return {
        "token_holders": token_holders,
        "proposals": proposals,
        "votes": votes,
        "governance_data": {
            "votes": votes,
            "total_holders": 15000,  # Aave has fewer holders than Uniswap but more than Compound
        },
    }


def _generate_sample_holder_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample token holder data for testing."""
    holders = []
    total_supply = 16000000  # 16M AAVE tokens

    # Create a list of decreasing balances (Pareto-like distribution)
    balances = []
    remaining_supply = total_supply

    # Aave distribution is between Compound (more concentrated) and Uniswap (more dispersed)
    for i in range(count):
        # Generate a balance based on a power-law distribution
        share = random.uniform(0.03, 0.15) if i < 10 else random.uniform(0.0005, 0.03)
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

        # Aave has a staking mechanism, so include staking information
        staked_percentage = random.uniform(0, 100)
        staked_balance = balance * (staked_percentage / 100)

        holders.append(
            {
                "address": address,
                "balance": balance,
                "percentage": percentage,
                "staked_balance": staked_balance,
                "staked_percentage": staked_percentage,
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
        stacklevel=2
    )
    return api_client._generate_sample_holder_data('aave', count)


def _generate_sample_proposal_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample governance proposal data for testing."""
    proposals = []

    for i in range(count):
        proposal_id = i + 1
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(3, 7))

        # Random proposal state
        states = ["active", "passed", "executed", "defeated", "expired"]
        state = random.choice(states)

        # Random vote counts
        for_votes = random.randint(2000000, 8000000)
        against_votes = random.randint(500000, 3000000)
        total_votes = for_votes + against_votes

        proposals.append(
            {
                "id": proposal_id,
                "title": f"Proposal {proposal_id}: {random.choice(['Risk Parameter Update', 'New Asset Listing', 'Protocol Upgrade', 'Safety Module Change'])}",
                "description": f"This proposal aims to {random.choice(['update risk parameters', 'list a new asset', 'upgrade the protocol', 'modify the safety module'])}",
                "proposer": f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "state": state,
                "for_votes": for_votes,
                "against_votes": against_votes,
                "total_votes": total_votes,
                "participation_rate": random.uniform(
                    20, 60
                ),  # percentage - higher than others due to staking incentives
            }
        )

    return proposals


def _generate_sample_vote_data(proposal_id: int) -> List[Dict[str, Any]]:
    """Generate sample vote data for a specific proposal."""
    votes = []
    vote_count = random.randint(70, 250)

    for i in range(vote_count):
        # Generate a random vote weight
        weight = random.uniform(500, 200000)

        # Generate vote type with bias towards 'for' votes
        vote_type = random.choices(
            ["for", "against", "abstain"], weights=[0.75, 0.2, 0.05]
        )[0]

        # Aave has delegation and staking, so include that information
        delegated = random.choice([True, False])
        staked = random.choice([True, False])

        votes.append(
            {
                "proposal_id": proposal_id,
                "voter_address": f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}",
                "vote": vote_type,
                "weight": weight,
                "delegated": delegated,
                "staked": staked,
                "timestamp": (
                    datetime.now() - timedelta(days=random.randint(1, 30))
                ).isoformat(),
            }
        )

    return votes
