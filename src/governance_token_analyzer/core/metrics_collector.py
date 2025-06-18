"""
Metrics collector for governance token analysis.

This module provides functionality to collect and aggregate metrics
across different protocols for comparison and analysis.
"""

from typing import Dict, List, Any, Optional
import logging

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.token_analysis import (
    calculate_gini_coefficient,
    calculate_nakamoto_coefficient,
    calculate_shannon_entropy,
    calculate_theil_index,
    calculate_palma_ratio,
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics across different protocols.

    This class provides a unified interface for collecting metrics
    from various protocols for comparison and analysis.
    """

    def __init__(self, use_live_data: bool = True):
        """
        Initialize the MetricsCollector.

        Args:
            use_live_data: Whether to use live data or simulated data
        """
        self.use_live_data = use_live_data
        self.api_client = APIClient()

    def collect_protocol_data(self, protocol: str, limit: int = 1000) -> Dict[str, Any]:
        """
        Collect comprehensive data for a specific protocol.

        Args:
            protocol: Name of the protocol to collect data for
            limit: Maximum number of token holders to collect

        Returns:
            Dictionary containing token holder data and metrics
        """
        # Get token holders data
        holders_data = self.api_client.get_token_holders(protocol, limit=limit, use_real_data=self.use_live_data)

        # Extract balances
        balances = []
        for holder in holders_data:
            if isinstance(holder, dict) and "balance" in holder:
                try:
                    balance = float(holder["balance"])
                    if balance > 0:
                        balances.append(balance)
                except (ValueError, TypeError):
                    continue

        # Calculate metrics
        metrics = {}
        if balances:
            metrics["gini_coefficient"] = calculate_gini_coefficient(balances)
            metrics["nakamoto_coefficient"] = calculate_nakamoto_coefficient(balances)
            metrics["shannon_entropy"] = calculate_shannon_entropy(balances)
            metrics["theil_index"] = calculate_theil_index(balances)
            metrics["palma_ratio"] = calculate_palma_ratio(balances)
            metrics["total_holders"] = len(balances)
            metrics["total_supply"] = sum(balances)

        return {"protocol": protocol, "token_holders": holders_data, "balances": balances, "metrics": metrics}

    def compare_protocols(
        self, protocol_list: List[str], primary_metric: str = "gini_coefficient"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare metrics across multiple protocols.

        Args:
            protocol_list: List of protocols to compare
            primary_metric: Primary metric for comparison

        Returns:
            Dictionary mapping protocols to their metrics
        """
        results = {}

        for protocol in protocol_list:
            try:
                protocol_data = self.collect_protocol_data(protocol)
                metrics = protocol_data.get("metrics", {})

                if metrics:
                    results[protocol] = metrics
                else:
                    results[protocol] = {"error": "No metrics available"}

            except Exception as e:
                logger.error(f"Error collecting data for {protocol}: {str(e)}")
                results[protocol] = {"error": str(e)}

        return results

    def get_governance_data(self, protocol: str) -> Dict[str, Any]:
        """
        Get governance-related data for a protocol.

        Args:
            protocol: Name of the protocol

        Returns:
            Dictionary containing governance data
        """
        try:
            proposals = self.api_client.get_governance_proposals(protocol, use_real_data=self.use_live_data)

            # Collect votes for each proposal
            all_votes = []
            for proposal in proposals:
                if proposal.get("id"):
                    proposal_id = int(proposal["id"])
                    proposal_votes = self.api_client.get_governance_votes(
                        protocol, proposal_id, use_real_data=self.use_live_data
                    )
                    all_votes.extend(proposal_votes)

            return {
                "protocol": protocol,
                "proposals": proposals,
                "votes": all_votes,
                "proposal_count": len(proposals),
                "vote_count": len(all_votes),
            }
        except Exception as e:
            logger.error(f"Error getting governance data for {protocol}: {str(e)}")
            return {"protocol": protocol, "error": str(e)}
