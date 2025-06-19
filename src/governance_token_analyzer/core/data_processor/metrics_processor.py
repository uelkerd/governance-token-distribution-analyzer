"""Metrics Processor for Governance Token Distribution Analyzer.

This module provides functionality for calculating various metrics related to
governance token distribution and governance participation.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class MetricsProcessor:
    """Processor for calculating governance token metrics."""

    def calculate_distribution_metrics(self, token_holders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics related to token distribution.

        Args:
            token_holders: List of token holder dictionaries

        Returns:
            Dictionary of distribution metrics
        """
        logger.info(f"Calculating distribution metrics for {len(token_holders)} holders")

        if not token_holders:
            logger.warning("No token holders provided")
            return {}

        # Extract balances
        balances = [float(holder.get("balance", 0)) for holder in token_holders]

        # Calculate basic statistics
        total_tokens = sum(balances)
        holder_count = len(balances)

        # Avoid division by zero
        if total_tokens == 0 or holder_count == 0:
            logger.warning("No tokens or holders found")
            return {
                "holder_count": 0,
                "total_tokens": 0,
                "mean_balance": 0,
                "median_balance": 0,
                "gini_coefficient": 0,
                "top10_concentration": 0,
                "whale_dominance": 0,
            }

        # Sort balances in descending order
        sorted_balances = sorted(balances, reverse=True)

        # Calculate basic statistics
        mean_balance = total_tokens / holder_count
        median_balance = (
            sorted_balances[holder_count // 2]
            if holder_count % 2 == 1
            else (sorted_balances[holder_count // 2 - 1] + sorted_balances[holder_count // 2]) / 2
        )

        # Calculate Gini coefficient
        gini = self._calculate_gini_coefficient(balances)

        # Calculate top holder concentrations
        top10_sum = sum(sorted_balances[:10]) if len(sorted_balances) >= 10 else sum(sorted_balances)
        top10_concentration = (top10_sum / total_tokens) * 100 if total_tokens > 0 else 0

        # Calculate whale dominance (holders with >1% of supply)
        whale_threshold = total_tokens * 0.01
        whale_count = sum(1 for balance in balances if balance > whale_threshold)
        whale_total = sum(balance for balance in balances if balance > whale_threshold)
        whale_dominance = (whale_total / total_tokens) * 100 if total_tokens > 0 else 0

        return {
            "holder_count": holder_count,
            "total_tokens": total_tokens,
            "mean_balance": mean_balance,
            "median_balance": median_balance,
            "gini_coefficient": gini,
            "top10_concentration": top10_concentration,
            "whale_dominance": whale_dominance,
            "whale_count": whale_count,
        }

    @staticmethod
    def calculate_governance_metrics(proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics related to governance participation.

        Args:
            proposals: List of governance proposal dictionaries

        Returns:
            Dictionary of governance metrics
        """
        logger.info(f"Calculating governance metrics for {len(proposals)} proposals")

        if not proposals:
            logger.warning("No proposals provided")
            return {}

        # Calculate proposal counts
        proposal_count = len(proposals)

        # Calculate vote counts
        total_votes = sum(
            int(proposal.get("forVotes", 0))
            + int(proposal.get("againstVotes", 0))
            + int(proposal.get("abstainVotes", 0))
            for proposal in proposals
        )

        # Calculate average votes per proposal
        avg_votes_per_proposal = total_votes / proposal_count if proposal_count > 0 else 0

        # Calculate success rate
        executed_count = sum(1 for p in proposals if p.get("executed", False))
        success_rate = (executed_count / proposal_count) * 100 if proposal_count > 0 else 0

        # Calculate average participation rate
        participation_rates = []
        for proposal in proposals:
            for_votes = int(proposal.get("forVotes", 0))
            against_votes = int(proposal.get("againstVotes", 0))
            abstain_votes = int(proposal.get("abstainVotes", 0))
            total_proposal_votes = for_votes + against_votes + abstain_votes

            # Assuming total_supply is available in the proposal or a constant
            # Here we use a placeholder value
            total_supply = 1000000  # This should be replaced with actual total supply

            participation_rate = (total_proposal_votes / total_supply) * 100
            participation_rates.append(participation_rate)

        avg_participation_rate = sum(participation_rates) / len(participation_rates) if participation_rates else 0

        return {
            "proposal_count": proposal_count,
            "total_votes": total_votes,
            "avg_votes_per_proposal": avg_votes_per_proposal,
            "success_rate": success_rate,
            "avg_participation_rate": avg_participation_rate,
        }

    @staticmethod
    def calculate_comparison_metrics(protocol_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comparison metrics across multiple protocols.

        Args:
            protocol_metrics: Dictionary mapping protocol names to metric dictionaries

        Returns:
            Dictionary of comparison metrics
        """
        logger.info(f"Calculating comparison metrics for {len(protocol_metrics)} protocols")

        if not protocol_metrics:
            logger.warning("No protocol metrics provided")
            return {}

        # Extract key metrics for comparison
        comparison = {}

        # Distribution metrics comparison
        distribution_metrics = ["gini_coefficient", "top10_concentration", "whale_dominance"]
        for metric in distribution_metrics:
            comparison[metric] = {protocol: metrics.get(metric, 0) for protocol, metrics in protocol_metrics.items()}

        # Governance metrics comparison
        governance_metrics = ["proposal_count", "avg_participation_rate", "success_rate"]
        for metric in governance_metrics:
            comparison[metric] = {protocol: metrics.get(metric, 0) for protocol, metrics in protocol_metrics.items()}

        # Calculate overall decentralization score
        decentralization_scores = {}
        for protocol, metrics in protocol_metrics.items():
            # Lower Gini coefficient is better (more equal distribution)
            gini_score = 100 - (metrics.get("gini_coefficient", 0) * 100)

            # Lower top10 concentration is better
            concentration_score = 100 - metrics.get("top10_concentration", 0)

            # Higher participation is better
            participation_score = metrics.get("avg_participation_rate", 0)

            # Calculate weighted average (customize weights as needed)
            decentralization_score = gini_score * 0.4 + concentration_score * 0.4 + participation_score * 0.2

            decentralization_scores[protocol] = decentralization_score

        comparison["decentralization_score"] = decentralization_scores

        return comparison

    @staticmethod
    def _calculate_gini_coefficient(balances: List[float]) -> float:
        """Calculate the Gini coefficient for token distribution.

        Args:
            balances: List of token balances

        Returns:
            Gini coefficient (0-1, where 0 is perfect equality and 1 is perfect inequality)
        """
        # Handle edge cases
        if not balances or sum(balances) == 0:
            return 0

        # Sort balances in ascending order
        sorted_balances = sorted(balances)
        n = len(sorted_balances)

        # Calculate cumulative sum
        cumsum = np.cumsum(sorted_balances)

        # Calculate Gini coefficient using the formula:
        # G = 1 - (2/n) * sum_{i=1}^{n} ((n+1-i)/n) * (x_i/sum(x))
        # where x_i are the sorted balances
        total = sum(sorted_balances)
        gini = 1 - 2 * sum((n + 1 - i) * balance for i, balance in enumerate(sorted_balances, 1)) / (n * total)

        return gini
