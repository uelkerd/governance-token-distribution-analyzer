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

    def calculate_voter_participation(
        self, proposal_votes: List[Dict[str, Any]], total_eligible_votes: float
    ) -> Dict[str, float]:
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
        total_votes_cast = sum(
            proposal.get("votes_cast", 0) for proposal in proposal_votes
        )

        # Calculate average votes cast per proposal
        average_votes_cast = total_votes_cast / len(proposal_votes)

        # Calculate overall participation rate
        participation_rate = (
            (average_votes_cast / total_eligible_votes) * 100
            if total_eligible_votes > 0
            else 0.0
        )

        # Count unique voters
        unique_voters = set()
        for proposal in proposal_votes:
            if "voter_addresses" in proposal:
                unique_voters.update(proposal["voter_addresses"])

        # Calculate unique voter percentage
        unique_voters_percentage = (
            (len(unique_voters) / total_eligible_votes) * 100
            if total_eligible_votes > 0
            else 0.0
        )

        return {
            "participation_rate": participation_rate,
            "average_votes_cast": average_votes_cast,
            "unique_voters_percentage": unique_voters_percentage,
        }

    def calculate_proposal_success_rate(
        self, proposals: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate metrics related to proposal success rates.

        Args:
            proposals: List of dictionaries containing proposal data

        Returns:
            Dictionary with proposal success metrics
        """
        if not proposals:
            return {"proposal_success_rate": 0.0, "proposal_implementation_rate": 0.0}

        # Count total proposals and successful ones
        total_proposals = len(proposals)
        successful_proposals = sum(1 for p in proposals if p.get("status") == "passed")

        # Calculate success rate
        success_rate = (
            (successful_proposals / total_proposals) * 100
            if total_proposals > 0
            else 0.0
        )

        # Count implemented proposals
        implemented_proposals = sum(
            1
            for p in proposals
            if p.get("status") == "passed" and p.get("implemented", False)
        )

        # Calculate implementation rate (% of passed proposals that were implemented)
        implementation_rate = (
            (implemented_proposals / successful_proposals) * 100
            if successful_proposals > 0
            else 0.0
        )

        return {
            "proposal_success_rate": success_rate,
            "proposal_implementation_rate": implementation_rate,
        }

    def analyze_governance_effectiveness(
        self,
        proposals: List[Dict[str, Any]],
        token_distribution: List[Dict[str, Any]],
        total_eligible_votes: float,
    ) -> Dict[str, Any]:
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


class ParticipationAnalyzer:
    """Analyzes governance participation metrics for token holders.

    This class provides methods for analyzing participation in governance processes,
    including voting patterns, voter segmentation, and proposal participation rates.
    """

    def __init__(self):
        """Initialize the participation analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze_protocol_participation(
        self,
        protocol_key: str,
        proposals: List[Dict[str, Any]],
        token_holders: List[Dict[str, Any]],
        total_supply: float,
    ) -> Dict[str, Any]:
        """Analyze the participation metrics for a specific protocol.

        Args:
            protocol_key: Key of the protocol being analyzed
            proposals: List of governance proposals with voting data
            token_holders: List of token holders with their balances
            total_supply: Total token supply as a float

        Returns:
            Dictionary containing the participation analysis results
        """
        try:
            # Calculate basic participation metrics
            total_proposals = len(proposals)
            if total_proposals == 0:
                self.logger.warning(f"No proposals found for {protocol_key}")
                return {
                    "participation_rate": 0.0,
                    "total_proposals": 0,
                    "active_voters": 0,
                    "voter_segments": {
                        "highly_active": 0,
                        "active": 0,
                        "occasional": 0,
                        "inactive": 0,
                    },
                    "proposal_participation": [],
                }

            # Collect voting data
            all_voters = set()
            proposal_participation = []
            voter_participation_count = {}  # Track how many proposals each voter participated in

            for proposal in proposals:
                proposal_id = proposal.get("id", "unknown")
                votes_cast = proposal.get("votes_cast", 0)
                voter_addresses = proposal.get("voter_addresses", [])

                # Track voters
                all_voters.update(voter_addresses)

                # Track participation count for each voter
                for voter in voter_addresses:
                    voter_participation_count[voter] = (
                        voter_participation_count.get(voter, 0) + 1
                    )

                # Calculate participation rate for this proposal
                participation_rate = (
                    (votes_cast / total_supply) * 100 if total_supply > 0 else 0.0
                )

                proposal_participation.append(
                    {
                        "proposal_id": proposal_id,
                        "votes_cast": votes_cast,
                        "participation_rate": participation_rate,
                        "unique_voters": len(voter_addresses),
                    }
                )

            # Calculate overall participation rate
            total_votes_cast = sum(p.get("votes_cast", 0) for p in proposals)
            avg_votes_per_proposal = (
                total_votes_cast / total_proposals if total_proposals > 0 else 0
            )
            overall_participation_rate = (
                (avg_votes_per_proposal / total_supply) * 100
                if total_supply > 0
                else 0.0
            )

            # Segment voters based on participation frequency
            highly_active = 0  # Voted in >75% of proposals
            active = 0  # Voted in 50-75% of proposals
            occasional = 0  # Voted in 25-50% of proposals
            inactive = 0  # Voted in <25% of proposals

            for voter, participation_count in voter_participation_count.items():
                participation_percentage = (participation_count / total_proposals) * 100

                if participation_percentage > 75:
                    highly_active += 1
                elif participation_percentage > 50:
                    active += 1
                elif participation_percentage > 25:
                    occasional += 1
                else:
                    inactive += 1

            # Calculate number of potential voters not participating
            total_holders = len(token_holders)
            never_voted = total_holders - len(all_voters)
            inactive += never_voted

            return {
                "participation_rate": overall_participation_rate,
                "total_proposals": total_proposals,
                "active_voters": len(all_voters),
                "voter_segments": {
                    "highly_active": highly_active,
                    "active": active,
                    "occasional": occasional,
                    "inactive": inactive,
                },
                "proposal_participation": proposal_participation,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing protocol participation: {str(e)}")
            return {"error": str(e)}

    def calculate_voter_engagement_trends(
        self, proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate trends in voter engagement over time.

        Args:
            proposals: List of governance proposals with voting data, ordered by time

        Returns:
            Dictionary containing voter engagement trend metrics
        """
        if not proposals:
            return {"trend": "stable", "trend_data": [], "change_percentage": 0.0}

        try:
            # Sort proposals by timestamp if available
            sorted_proposals = sorted(
                [p for p in proposals if "timestamp" in p], key=lambda x: x["timestamp"]
            )

            if len(sorted_proposals) < 2:
                return {
                    "trend": "insufficient_data",
                    "trend_data": [],
                    "change_percentage": 0.0,
                }

            # Calculate participation rates over time
            trend_data = []
            for proposal in sorted_proposals:
                votes_cast = proposal.get("votes_cast", 0)
                total_supply = proposal.get("total_eligible_votes", 0)
                participation_rate = (
                    (votes_cast / total_supply) * 100 if total_supply > 0 else 0.0
                )

                trend_data.append(
                    {
                        "proposal_id": proposal.get("id", "unknown"),
                        "timestamp": proposal.get("timestamp"),
                        "participation_rate": participation_rate,
                    }
                )

            # Calculate trend direction
            early_participation = sum(
                item["participation_rate"]
                for item in trend_data[: len(trend_data) // 3]
            ) / (len(trend_data) // 3)
            recent_participation = sum(
                item["participation_rate"]
                for item in trend_data[-len(trend_data) // 3 :]
            ) / (len(trend_data) // 3)

            change_percentage = (
                ((recent_participation - early_participation) / early_participation)
                * 100
                if early_participation > 0
                else 0.0
            )

            if change_percentage > 10:
                trend = "increasing"
            elif change_percentage < -10:
                trend = "decreasing"
            else:
                trend = "stable"

            return {
                "trend": trend,
                "trend_data": trend_data,
                "change_percentage": change_percentage,
            }

        except Exception as e:
            self.logger.error(f"Error calculating voter engagement trends: {str(e)}")
            return {
                "trend": "error",
                "trend_data": [],
                "change_percentage": 0.0,
                "error": str(e),
            }

    def analyze_voter_overlap(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the overlap of voters between different proposals.

        Args:
            proposals: List of governance proposals with voting data

        Returns:
            Dictionary containing voter overlap metrics
        """
        if not proposals or len(proposals) < 2:
            return {"average_overlap": 0.0, "max_overlap": 0.0, "min_overlap": 0.0}

        try:
            # Extract voter sets for each proposal
            proposal_voters = []
            for proposal in proposals:
                voters = set(proposal.get("voter_addresses", []))
                if voters:  # Only include proposals with voter data
                    proposal_voters.append(voters)

            if len(proposal_voters) < 2:
                return {"average_overlap": 0.0, "max_overlap": 0.0, "min_overlap": 0.0}

            # Calculate overlap between all pairs of proposals
            overlaps = []
            for i in range(len(proposal_voters)):
                for j in range(i + 1, len(proposal_voters)):
                    set_i = proposal_voters[i]
                    set_j = proposal_voters[j]

                    # Calculate Jaccard similarity (intersection over union)
                    intersection = len(set_i.intersection(set_j))
                    union = len(set_i.union(set_j))

                    if union > 0:
                        overlap = intersection / union
                        overlaps.append(overlap)

            # Calculate overlap statistics
            if overlaps:
                average_overlap = sum(overlaps) / len(overlaps)
                max_overlap = max(overlaps)
                min_overlap = min(overlaps)
            else:
                average_overlap = max_overlap = min_overlap = 0.0

            return {
                "average_overlap": average_overlap * 100,  # Convert to percentage
                "max_overlap": max_overlap * 100,
                "min_overlap": min_overlap * 100,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing voter overlap: {str(e)}")
            return {
                "average_overlap": 0.0,
                "max_overlap": 0.0,
                "min_overlap": 0.0,
                "error": str(e),
            }
