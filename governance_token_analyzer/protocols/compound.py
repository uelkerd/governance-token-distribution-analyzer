"""
Compound Protocol Module for analyzing COMP token distribution.
This module handles fetching and processing data for the Compound protocol.
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def get_token_holders(limit: int = 100, use_real_data: bool = False) -> List[Dict[str, Any]]:
    """
    Get list of top COMP token holders.
    
    Args:
        limit: Number of holders to retrieve
        use_real_data: Whether to use real data from APIs (vs. sample data)
        
    Returns:
        List of token holder dictionaries
    """
    if use_real_data:
        # Code to fetch real data from Etherscan or The Graph
        # This would be implemented later
        raise NotImplementedError("Real data fetching not implemented yet")
    else:
        return _generate_sample_holder_data(limit)


def get_governance_proposals(limit: int = 10, use_real_data: bool = False) -> List[Dict[str, Any]]:
    """
    Get list of Compound governance proposals.
    
    Args:
        limit: Number of proposals to retrieve
        use_real_data: Whether to use real data from APIs (vs. sample data)
        
    Returns:
        List of proposal dictionaries
    """
    if use_real_data:
        # Code to fetch real data from Compound API
        raise NotImplementedError("Real data fetching not implemented yet")
    else:
        return _generate_sample_proposal_data(limit)


def get_governance_votes(proposal_id: int, use_real_data: bool = False) -> List[Dict[str, Any]]:
    """
    Get list of votes for a specific proposal.
    
    Args:
        proposal_id: ID of the proposal
        use_real_data: Whether to use real data from APIs (vs. sample data)
        
    Returns:
        List of vote dictionaries
    """
    if use_real_data:
        # Code to fetch real data from Compound API
        raise NotImplementedError("Real data fetching not implemented yet")
    else:
        return _generate_sample_vote_data(proposal_id)


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
        proposal_votes = _generate_sample_vote_data(proposal['id'])
        votes.extend(proposal_votes)
    
    return {
        'token_holders': token_holders,
        'proposals': proposals,
        'votes': votes,
        'governance_data': {
            'votes': votes,
            'total_holders': 1000
        }
    }


def _generate_sample_holder_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample token holder data for testing."""
    holders = []
    total_supply = 10000000  # 10M COMP tokens
    
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
        address = f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}"
        balance = balances[i]
        percentage = (balance / total_supply) * 100
        
        holders.append({
            'address': address,
            'balance': balance,
            'percentage': percentage,
            'txn_count': random.randint(1, 100),
            'last_txn_date': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        })
    
    # Sort by balance in descending order
    holders.sort(key=lambda x: x['balance'], reverse=True)
    
    return holders


def _generate_sample_proposal_data(count: int) -> List[Dict[str, Any]]:
    """Generate sample governance proposal data for testing."""
    proposals = []
    
    for i in range(count):
        proposal_id = i + 1
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(3, 7))
        
        # Random proposal state
        states = ['active', 'passed', 'executed', 'defeated', 'expired']
        state = random.choice(states)
        
        # Random vote counts
        for_votes = random.randint(1000000, 5000000)
        against_votes = random.randint(100000, 2000000)
        total_votes = for_votes + against_votes
        
        proposals.append({
            'id': proposal_id,
            'title': f"Proposal {proposal_id}: {'Increase' if random.random() > 0.5 else 'Decrease'} Interest Rate",
            'description': f"This proposal aims to {'increase' if random.random() > 0.5 else 'decrease'} the interest rate for {random.choice(['USDC', 'ETH', 'DAI', 'WBTC'])}",
            'proposer': f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}",
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'state': state,
            'for_votes': for_votes,
            'against_votes': against_votes,
            'total_votes': total_votes,
            'participation_rate': random.uniform(10, 50)  # percentage
        })
    
    return proposals


def _generate_sample_vote_data(proposal_id: int) -> List[Dict[str, Any]]:
    """Generate sample vote data for a specific proposal."""
    votes = []
    vote_count = random.randint(50, 200)
    
    for i in range(vote_count):
        # Generate a random vote weight
        weight = random.uniform(100, 100000)
        
        # Generate vote type with bias towards 'for' votes
        vote_type = random.choices(['for', 'against', 'abstain'], weights=[0.7, 0.25, 0.05])[0]
        
        votes.append({
            'proposal_id': proposal_id,
            'voter_address': f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):040x}",
            'vote': vote_type,
            'weight': weight,
            'timestamp': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        })
    
    return votes 