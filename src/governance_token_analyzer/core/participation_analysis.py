import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from .metrics import calculate_participation_rate, calculate_vote_distribution
from .metrics_collector import measure_api_call
from .logging_config import get_logger

# Configure logger
logger = get_logger(__name__)


@measure_api_call(protocol="<protocol_name>", method="analyze_governance_participation")
def analyze_governance_participation(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Analyze governance participation metrics for a protocol.
    
    Args:
        governance_data: Dictionary containing governance-related data
        token_holders: DataFrame containing token holder data
        protocol_name: Name of the protocol being analyzed
        
    Returns:
        Dictionary containing participation metrics
    """
    logger.info(f"Analyzing governance participation for {protocol_name} protocol")
    
    if not governance_data or not isinstance(governance_data, dict):
        logger.warning(f"No governance data available for {protocol_name}")
        return {
            "protocol": protocol_name,
            "error": "No governance data available",
            "metrics": {}
        }
    
    try:
        # Extract proposals and votes
        proposals = governance_data.get("proposals", [])
        
        if not proposals:
            logger.warning(f"No proposals found for {protocol_name}")
            return {
                "protocol": protocol_name,
                "metrics": {
                    "proposal_count": 0,
                    "participation_metrics": {},
                    "voter_metrics": {}
                }
            }
        
        # Calculate basic proposal metrics
        proposal_count = len(proposals)
        proposal_df = pd.DataFrame(proposals)
        
        # Calculate time-based metrics if timestamps are available
        time_metrics = {}
        if "timestamp" in proposal_df.columns:
            proposal_df["timestamp"] = pd.to_datetime(proposal_df["timestamp"])
            current_time = datetime.now()
            
            # Last 30 days activity
            last_30_days = current_time - timedelta(days=30)
            recent_proposals = proposal_df[proposal_df["timestamp"] >= last_30_days]
            time_metrics["recent_proposal_count"] = len(recent_proposals)
            
            # Proposals per month
            if not proposal_df.empty:
                earliest_date = proposal_df["timestamp"].min()
                months_active = max(1, (current_time - earliest_date).days / 30)
                time_metrics["proposals_per_month"] = proposal_count / months_active
        
        # Analyze voting patterns
        all_votes = []
        proposal_metrics = []
        
        for proposal in proposals:
            proposal_id = proposal.get("id", "unknown")
            votes = proposal.get("votes", [])
            
            # Skip proposals with no votes
            if not votes:
                continue
                
            # Add proposal ID to each vote
            for vote in votes:
                vote["proposal_id"] = proposal_id
                all_votes.append(vote)
            
            # Calculate participation for this proposal
            total_holders = len(token_holders)
            participation = calculate_participation_rate(votes, total_holders)
            vote_distribution = calculate_vote_distribution(votes)
            
            # Calculate voting power metrics if available
            power_metrics = {}
            if all(vote.get("voting_power") is not None for vote in votes):
                voting_powers = [float(vote.get("voting_power", 0)) for vote in votes]
                total_power = sum(voting_powers)
                power_metrics = {
                    "total_voting_power": total_power,
                    "avg_voting_power": total_power / len(votes) if votes else 0
                }
            
            # Compile proposal metrics
            proposal_metrics.append({
                "proposal_id": proposal_id,
                "title": proposal.get("title", "Untitled"),
                "votes_count": len(votes),
                "participation_rate": participation,
                "vote_distribution": vote_distribution,
                **power_metrics
            })
        
        # Create DataFrame of all votes
        votes_df = pd.DataFrame(all_votes) if all_votes else pd.DataFrame()
        
        # Calculate voter metrics
        voter_metrics = {}
        if not votes_df.empty and "voter" in votes_df.columns:
            # Count unique voters
            unique_voters = votes_df["voter"].nunique()
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from .metrics import calculate_participation_rate, calculate_vote_distribution
from .metrics_collector import measure_api_call
from .logging_config import get_logger

# Configure logger
logger = get_logger(__name__)


@measure_api_call(protocol="<protocol_name>", method="analyze_governance_participation")
def analyze_governance_participation(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown"
) -> Dict[str, Any]:
    pass


@measure_api_call(protocol="<protocol_name>", method="analyze_participation_by_holder_size")
def analyze_participation_by_holder_size(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown"
) -> Dict[str, Any]:
    pass


@measure_api_call(protocol="<protocol_name>", method="compare_participation_metrics")
def compare_participation_metrics(
    protocol_results: Dict[str, Dict[str, Any]]
) -> pd.DataFrame:
    pass