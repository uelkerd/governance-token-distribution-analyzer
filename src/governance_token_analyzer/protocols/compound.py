"""Compound Protocol Module for analyzing COMP token distribution.
This module handles fetching and processing data for the Compound protocol.
"""

from typing import Any, Dict, List

from ..core.api_client import APIClient
from ..core.config import Config

# Initialize API client and config
config = Config()
api_client = APIClient()

# Determine if we should use real data by default based on API key availability
DEFAULT_USE_REAL_DATA = bool(config.etherscan_api_key)


def get_token_holders(limit: int = 100, use_real_data: bool = None) -> List[Dict[str, Any]]:
    """Get list of top COMP token holders.

    Args:
        limit: Number of holders to retrieve
        use_real_data: Whether to use real data from APIs. If None, automatically 
                      determined based on API key availability.

    Returns:
        List of token holder dictionaries
    """
    if use_real_data is None:
        use_real_data = DEFAULT_USE_REAL_DATA
    
    return api_client.get_token_holders('compound', limit, use_real_data)


def get_governance_proposals(limit: int = 10, use_real_data: bool = None) -> List[Dict[str, Any]]:
    """Get list of Compound governance proposals.

    Args:
        limit: Number of proposals to retrieve
        use_real_data: Whether to use real data from APIs. If None, automatically 
                      determined based on API key availability.

    Returns:
        List of proposal dictionaries
    """
    if use_real_data is None:
        use_real_data = DEFAULT_USE_REAL_DATA
    
    return api_client.get_governance_proposals('compound', limit, use_real_data)


def get_governance_votes(proposal_id: int, use_real_data: bool = None) -> List[Dict[str, Any]]:
    """Get list of votes for a specific proposal.

    Args:
        proposal_id: ID of the proposal
        use_real_data: Whether to use real data from APIs. If None, automatically 
                      determined based on API key availability.

    Returns:
        List of vote dictionaries
    """
    if use_real_data is None:
        use_real_data = DEFAULT_USE_REAL_DATA
    
    return api_client.get_governance_votes('compound', proposal_id, use_real_data)


def get_sample_data() -> Dict[str, Any]:
    """Get sample data for testing.

    Returns:
        Dictionary containing sample data for token holders and governance
    """
    return api_client.get_protocol_data("compound")

    # Generate votes for each proposal
    votes = []
    for proposal in proposals:
        proposal_votes = _generate_sample_vote_data(proposal["id"])
        votes.extend(proposal_votes)


def get_protocol_info() -> Dict[str, Any]:
    """Get basic information about the Compound protocol.

    Returns:
        Dictionary containing basic protocol information
    """
    data = get_sample_data()
    return {
        "protocol": "compound",
        "token_symbol": data["token_symbol"],
        "token_name": data["token_name"],
        "total_supply": data["total_supply"],
        "participation_rate": data["participation_rate"],
    }


def calculate_voting_power_distribution() -> Dict[str, float]:
    """Calculate the distribution of voting power across holders.

    Returns:
        Dictionary containing voting power distribution metrics
    """
    holders = get_token_holders()

    # Calculate voting power distribution
    total_supply = sum(holder['balance'] for holder in holders)

    # Calculate percentage held by top holders
    top_10_percentage = sum(holder['balance'] for holder in holders[:10]) / total_supply * 100
    top_20_percentage = sum(holder['balance'] for holder in holders[:20]) / total_supply * 100
    top_50_percentage = sum(holder['balance'] for holder in holders[:50]) / total_supply * 100

    # Calculate delegated voting power
    total_delegated = sum(holder.get("delegated_power", 0) for holder in holders)
    delegation_percentage = (total_delegated / total_supply) * 100

    return {
        "top_10_percentage": top_10_percentage,
        "top_20_percentage": top_20_percentage,
        "top_50_percentage": top_50_percentage,
        "delegation_percentage": delegation_percentage,
    }

    # Create a list of decreasing balances (Pareto-like distribution)
    balances = []
    remaining_supply = total_supply
    for i in range(count):
        # Generate a balance based on a power-law distribution
        share = random.uniform(0.05, 0.3) if i < 10 else random.uniform(0.001, 0.05)
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


def _generate_sample_holder_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample token holder data for testing."""
    warnings.warn(
        "_generate_sample_holder_data is deprecated, use api_client.get_token_holders instead",
        DeprecationWarning,
        stacklevel=2
    )
    return api_client._generate_sample_holder_data("compound", count)


def _generate_sample_proposal_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample governance proposal data for testing."""
    warnings.warn(
        "_generate_sample_proposal_data is deprecated, use api_client.get_governance_proposals instead",
        DeprecationWarning,
        stacklevel=2
    )
    return api_client._generate_sample_proposal_data("compound", count)

    for i in range(count):
        proposal_id = i + 1
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(3, 7))

        # Random proposal state
        states = ["active", "passed", "executed", "defeated", "expired"]
        state = random.choice(states)

        # Random vote counts
        for_votes = random.randint(1000000, 5000000)
        against_votes = random.randint(100000, 2000000)
        total_votes = for_votes + against_votes

        proposals.append(
            {
                "id": proposal_id,
                "title": f"Proposal {proposal_id}: {'Increase' if random.random() > 0.5 else 'Decrease'} Interest Rate",
                "description": f"This proposal aims to {'increase' if random.random() > 0.5 else 'decrease'} the interest rate for {random.choice(['USDC', 'ETH', 'DAI', 'WBTC'])}",
                "proposer": f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "state": state,
                "for_votes": for_votes,
                "against_votes": against_votes,
                "total_votes": total_votes,
                "participation_rate": random.uniform(10, 50),  # percentage
            }
        )

    return proposals


def _generate_sample_vote_data(proposal_id: int) -> List[Dict[str, Any]]:
    """Generate sample vote data for a specific proposal."""
    warnings.warn(
        "_generate_sample_vote_data is deprecated, use api_client.get_governance_votes instead",
        DeprecationWarning,
        stacklevel=2
    )
    return api_client._generate_sample_vote_data('compound', proposal_id)
