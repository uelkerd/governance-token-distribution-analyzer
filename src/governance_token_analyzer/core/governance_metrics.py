"""Governance Effectiveness Metrics

This module provides tools to analyze the effectiveness of DAO governance
and correlate token distribution patterns with governance outcomes.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GovernanceEffectivenessAnalyzer:
    """Analyzes governance effectiveness metrics and correlates them with
    token distribution patterns.
    """

    def __init__(self):
        """Initialize the governance effectiveness analyzer."""
        pass

    def calculate_voter_participation(self,
                                    proposal_votes: List[Dict[str, Any]],
                                    total_eligible_votes: float) -> Dict[str, float]:
        """Calculate voter participation metrics.

        Args:
            proposal_votes: List of dictionaries containing proposal voting data
            total_eligible_votes: Total number of tokens eligible to vote

        Returns:
            Dictionary with participation metrics
        """
        if not proposal_votes:
            return {
                "participation_rate": 0.0,
                "average_votes_cast": 0.0,
                "unique_voters_percentage": 0.0,
            }

        # Calculate total votes cast across all proposals
        total_votes_cast = sum(proposal.get("votes_cast", 0) for proposal in proposal_votes)

        # Calculate average votes cast per proposal
        average_votes_cast = total_votes_cast / len(proposal_votes)

        # Calculate overall participation rate
        participation_rate = (average_votes_cast / total_eligible_votes) * 100 if total_eligible_votes > 0 else 0.0

        # Count unique voters
        unique_voters = set()
        for proposal in proposal_votes:
            if "voter_addresses" in proposal:
                unique_voters.update(proposal["voter_addresses"])

        # Calculate unique voter percentage
        unique_voters_percentage = (len(unique_voters) / total_eligible_votes) * 100 if total_eligible_votes > 0 else 0.0

        return {
            "participation_rate": participation_rate,
            "average_votes_cast": average_votes_cast,
            "unique_voters_percentage": unique_voters_percentage,
        }

    def calculate_proposal_success_rate(self, proposals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate metrics related to proposal success rates.

        Args:
            proposals: List of dictionaries containing proposal data

        Returns:
            Dictionary with proposal success metrics
        """
        if not proposals:
            return {
                "proposal_success_rate": 0.0,
                "proposal_implementation_rate": 0.0
            }

        # Count total proposals and successful ones
        total_proposals = len(proposals)
        successful_proposals = sum(1 for p in proposals if p.get("status") == "passed")

        # Calculate success rate
        success_rate = (successful_proposals / total_proposals) * 100 if total_proposals > 0 else 0.0

        # Count implemented proposals
        implemented_proposals = sum(1 for p in proposals
                                   if p.get("status") == "passed" and p.get("implemented", False))

        # Calculate implementation rate (% of passed proposals that were implemented)
        implementation_rate = (implemented_proposals / successful_proposals) * 100 if successful_proposals > 0 else 0.0

        return {
            "proposal_success_rate": success_rate,
            "proposal_implementation_rate": implementation_rate,
        }

    def analyze_governance_effectiveness(self,
                                       proposals: List[Dict[str, Any]],
                                       token_distribution: List[Dict[str, Any]],
                                       total_eligible_votes: float) -> Dict[str, Any]:
        """Calculate comprehensive governance effectiveness metrics.

        Args:
            proposals: List of dictionaries containing proposal data
            token_distribution: List of dictionaries containing token holder data
            total_eligible_votes: Total number of tokens eligible to vote

        Returns:
            Dictionary with all governance effectiveness metrics
        """
        if not proposals:
            return {
                "participation": {},
                "success": {},
                "timestamp": datetime.now().timestamp(),
                "protocol": "unknown",
            }

        # Extract proposal votes for participation analysis
        proposal_votes = [
            {
                "proposal_id": p.get("id"),
                "votes_cast": p.get("votes_cast", 0),
                "voter_addresses": p.get("voter_addresses", []),
                "status": p.get("status"),
            }
            for p in proposals
        ]

        # Calculate metrics
        participation_metrics = self.calculate_voter_participation(
            proposal_votes, total_eligible_votes
        )
        success_metrics = self.calculate_proposal_success_rate(proposals)

        # Combine all metrics
        all_metrics = {
            "participation": participation_metrics,
            "success": success_metrics,
            "timestamp": datetime.now().timestamp(),
            "protocol": proposals[0].get("protocol", "unknown")
            if proposals
            else "unknown",
        }

        return all_metrics
