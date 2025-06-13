from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

from .logging_config import get_logger
from .metrics import calculate_participation_rate, calculate_vote_distribution
from .metrics_collector import measure_api_call

# Configure logger
logger = get_logger(__name__)


@measure_api_call(protocol="<protocol_name>", method="analyze_governance_participation")
def analyze_governance_participation(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown",
) -> Dict[str, Any]:
    """Analyze governance participation metrics for a protocol.

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
            "metrics": {},
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
                    "voter_metrics": {},
                },
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
                    "avg_voting_power": total_power / len(votes) if votes else 0,
                }

            # Compile proposal metrics
            proposal_metrics.append(
                {
                    "proposal_id": proposal_id,
                    "title": proposal.get("title", "Untitled"),
                    "votes_count": len(votes),
                    "participation_rate": participation,
                    "vote_distribution": vote_distribution,
                    **power_metrics,
                }
            )

        # Create DataFrame of all votes
        votes_df = pd.DataFrame(all_votes) if all_votes else pd.DataFrame()

        # Calculate voter metrics
        voter_metrics = {}
        if not votes_df.empty and "voter" in votes_df.columns:
            # Count unique voters
            unique_voters = votes_df["voter"].nunique()
            voter_metrics["unique_voter_count"] = unique_voters

            # Calculate repeat voter metrics
            voter_frequency = votes_df["voter"].value_counts()
            voter_metrics["single_vote_count"] = (voter_frequency == 1).sum()
            voter_metrics["multi_vote_count"] = (voter_frequency > 1).sum()
            voter_metrics["avg_votes_per_voter"] = votes_df["voter"].value_counts().mean()

            # Calculate voter participation rate
            total_holders = len(token_holders)
            voter_metrics["voter_participation_rate"] = (
                (unique_voters / total_holders * 100) if total_holders > 0 else 0
            )

        # Calculate overall participation metrics
        total_votes = len(all_votes)
        total_holders = len(token_holders)
        overall_participation = calculate_participation_rate(all_votes, total_holders)

        # Compile results
        results = {
            "protocol": protocol_name,
            "metrics": {
                "proposal_count": proposal_count,
                "time_metrics": time_metrics,
                "participation_metrics": {
                    "total_votes": total_votes,
                    "overall_participation_rate": overall_participation,
                    "avg_votes_per_proposal": total_votes / proposal_count if proposal_count > 0 else 0,
                },
                "voter_metrics": voter_metrics,
                "proposal_metrics": proposal_metrics,
            },
        }

        logger.info(f"Governance participation analysis completed for {protocol_name}")
        logger.debug(f"Overall participation rate: {overall_participation}%")

        return results

    except Exception as e:
        logger.error(f"Error analyzing governance participation for {protocol_name}: {str(e)}")
        return {
            "protocol": protocol_name,
            "error": f"Analysis error: {str(e)}",
            "metrics": {},
        }


@measure_api_call(protocol="<protocol_name>", method="analyze_participation_by_holder_size")
def analyze_participation_by_holder_size(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown",
) -> Dict[str, Any]:
    """Analyze governance participation broken down by holder size categories.

    Args:
        governance_data: Dictionary containing governance-related data
        token_holders: DataFrame containing token holder data
        protocol_name: Name of the protocol being analyzed

    Returns:
        Dictionary containing participation metrics by holder size

    """
    logger.info(f"Analyzing participation by holder size for {protocol_name}")

    if not governance_data or not isinstance(governance_data, dict) or token_holders.empty:
        logger.warning(f"Insufficient data for holder size analysis for {protocol_name}")
        return {
            "protocol": protocol_name,
            "error": "Insufficient data for analysis",
            "metrics": {},
        }

    try:
        # Extract proposals and votes
        proposals = governance_data.get("proposals", [])
        all_votes = []

        for proposal in proposals:
            votes = proposal.get("votes", [])
            all_votes.extend(votes)

        if not all_votes:
            logger.warning(f"No votes found for {protocol_name}")
            return {"protocol": protocol_name, "metrics": {}}

        # Create a dictionary of voter addresses for quick lookup
        voter_addresses = set()
        for vote in all_votes:
            voter = vote.get("voter") or vote.get("voter_address")
            if voter:
                voter_addresses.add(voter.lower())

        # Categorize token holders by size
        token_holders["address_lower"] = token_holders["address"].str.lower()
        token_holders["participated"] = token_holders["address_lower"].isin(voter_addresses)

        # Define holder categories
        large_holders = token_holders[token_holders["percentage"] >= 1.0]
        medium_holders = token_holders[(token_holders["percentage"] < 1.0) & (token_holders["percentage"] >= 0.1)]
        small_holders = token_holders[token_holders["percentage"] < 0.1]

        # Calculate participation rates by category
        large_participation = large_holders["participated"].mean() * 100
        medium_participation = medium_holders["participated"].mean() * 100
        small_participation = small_holders["participated"].mean() * 100

        # Compile results
        results = {
            "protocol": protocol_name,
            "metrics": {
                "participation_by_size": {
                    "large_holders": {
                        "count": len(large_holders),
                        "participation_rate": large_participation,
                    },
                    "medium_holders": {
                        "count": len(medium_holders),
                        "participation_rate": medium_participation,
                    },
                    "small_holders": {
                        "count": len(small_holders),
                        "participation_rate": small_participation,
                    },
                }
            },
        }

        logger.info(f"Participation by holder size analysis completed for {protocol_name}")
        return results

    except Exception as e:
        logger.error(f"Error analyzing participation by holder size for {protocol_name}: {str(e)}")
        return {
            "protocol": protocol_name,
            "error": f"Analysis error: {str(e)}",
            "metrics": {},
        }


@measure_api_call(protocol="<protocol_name>", method="compare_participation_metrics")
def compare_participation_metrics(
    protocol_results: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """Create a comparison table of participation metrics across protocols.

    Args:
        protocol_results: Dictionary mapping protocol names to their participation analysis results

    Returns:
        DataFrame with comparative metrics for each protocol

    """
    comparison_data = []

    for protocol, results in protocol_results.items():
        if "error" in results:
            continue

        metrics = results.get("metrics", {})
        participation_metrics = metrics.get("participation_metrics", {})
        voter_metrics = metrics.get("voter_metrics", {})

        row = {
            "protocol": protocol,
            "proposal_count": metrics.get("proposal_count", 0),
            "total_votes": participation_metrics.get("total_votes", 0),
            "participation_rate": participation_metrics.get("overall_participation_rate", 0),
            "unique_voter_count": voter_metrics.get("unique_voter_count", 0),
            "voter_participation_rate": voter_metrics.get("voter_participation_rate", 0),
        }
        comparison_data.append(row)

    return pd.DataFrame(comparison_data)
