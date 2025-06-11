"""
Voting Block Analysis Module for identifying coordinated governance participation.

This module provides functionality to detect and analyze voting blocks, which are groups
of addresses that consistently vote together on governance proposals. This can help identify
coordination, voting power concentration, and potential governance attacks.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
from datetime import datetime
import networkx as nx
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from collections import defaultdict

from governance_token_analyzer.core.exceptions import (
    DataFormatError,
    HistoricalDataError,
)

# Configure logging
logger = logging.getLogger(__name__)


class VotingBlockAnalyzer:
    """
    Analyzes voting patterns to identify coordinated voting blocks in governance.
    """

    def __init__(self):
        """Initialize the voting block analyzer."""
        self.voting_history = {}
        self.address_similarity = None
        self.voting_blocks = []

    def load_voting_data(self, proposals: List[Dict[str, Any]]) -> None:
        """
        Load voting data from a list of governance proposals.

        Args:
            proposals: List of proposal objects containing voting information

        Raises:
            DataFormatError: If the proposal data doesn't have the expected format
        """
        try:
            voting_data = {}

            for proposal in proposals:
                if "id" not in proposal or "votes" not in proposal:
                    logger.warning(f"Skipping proposal: missing required fields")
                    continue

                proposal_id = proposal["id"]
                votes = proposal.get("votes", [])

                if not votes:
                    logger.warning(f"Proposal {proposal_id}: No votes found")
                    continue

                for vote in votes:
                    if "voter" not in vote or "support" not in vote:
                        logger.warning(
                            f"Skipping vote in proposal {proposal_id}: missing required fields"
                        )
                        continue

                    voter = vote["voter"]
                    support = vote["support"]

                    if voter not in voting_data:
                        voting_data[voter] = {}

                    voting_data[voter][proposal_id] = support

            self.voting_history = voting_data
            logger.info(
                f"Loaded voting data for {len(voting_data)} addresses across {len(proposals)} proposals"
            )

        except Exception as e:
            logger.error(f"Failed to load voting data: {e}")
            raise DataFormatError(f"Failed to load voting data: {e}") from e

    def calculate_voting_similarity(self, min_overlap: int = 3) -> pd.DataFrame:
        """
        Calculate similarity in voting patterns between addresses.

        Args:
            min_overlap: Minimum number of proposals that two addresses must have both voted on

        Returns:
            DataFrame with similarity scores between address pairs

        Raises:
            HistoricalDataError: If there's an issue calculating voting similarity
        """
        try:
            if not self.voting_history:
                logger.warning("No voting history data available")
                return pd.DataFrame()

            addresses = list(self.voting_history.keys())
            n_addresses = len(addresses)

            # Initialize similarity matrix
            similarity = np.zeros((n_addresses, n_addresses))

            # Calculate similarity between each pair of addresses
            for i in range(n_addresses):
                addr1 = addresses[i]
                votes1 = self.voting_history[addr1]

                for j in range(i + 1, n_addresses):
                    addr2 = addresses[j]
                    votes2 = self.voting_history[addr2]

                    # Find proposals both addresses voted on
                    common_proposals = set(votes1.keys()) & set(votes2.keys())

                    if len(common_proposals) < min_overlap:
                        continue

                    # Calculate agreement ratio
                    agreements = sum(
                        1 for p in common_proposals if votes1[p] == votes2[p]
                    )
                    agreement_ratio = agreements / len(common_proposals)

                    # Update similarity matrix (symmetric)
                    similarity[i, j] = agreement_ratio
                    similarity[j, i] = agreement_ratio

            # Create DataFrame for easier analysis
            sim_df = pd.DataFrame(similarity, index=addresses, columns=addresses)
            self.address_similarity = sim_df

            logger.info(
                f"Calculated voting similarity for {n_addresses} addresses with minimum overlap of {min_overlap} proposals"
            )
            return sim_df

        except Exception as e:
            logger.error(f"Failed to calculate voting similarity: {e}")
            raise HistoricalDataError(
                f"Failed to calculate voting similarity: {e}"
            ) from e

    def identify_voting_blocks(
        self, similarity_threshold: float = 0.8
    ) -> List[List[str]]:
        """
        Identify voting blocks based on voting pattern similarity.

        Args:
            similarity_threshold: Minimum similarity score to consider addresses as part of the same block

        Returns:
            List of voting blocks, where each block is a list of addresses

        Raises:
            HistoricalDataError: If there's an issue identifying voting blocks
        """
        try:
            if self.address_similarity is None:
                logger.warning("No similarity data available. Calculating now...")
                self.calculate_voting_similarity()

            if self.address_similarity.empty:
                logger.warning("No address similarity data available")
                return []

            # Create a graph where nodes are addresses
            G = nx.Graph()

            # Add nodes
            addresses = list(self.address_similarity.index)
            G.add_nodes_from(addresses)

            # Add edges between addresses with high similarity
            for i, addr1 in enumerate(addresses):
                for j, addr2 in enumerate(addresses):
                    if (
                        i < j
                        and self.address_similarity.loc[addr1, addr2]
                        >= similarity_threshold
                    ):
                        G.add_edge(
                            addr1,
                            addr2,
                            weight=self.address_similarity.loc[addr1, addr2],
                        )

            # Find connected components (voting blocks)
            voting_blocks = [
                list(component)
                for component in nx.connected_components(G)
                if len(component) > 1
            ]
            self.voting_blocks = voting_blocks

            logger.info(
                f"Identified {len(voting_blocks)} voting blocks with similarity threshold of {similarity_threshold}"
            )
            return voting_blocks

        except Exception as e:
            logger.error(f"Failed to identify voting blocks: {e}")
            raise HistoricalDataError(f"Failed to identify voting blocks: {e}") from e

    def calculate_voting_power(
        self, voting_blocks: List[List[str]], token_balances: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate the total voting power of each identified voting block.

        Args:
            voting_blocks: List of voting blocks (each a list of addresses)
            token_balances: Dictionary mapping addresses to their token balances

        Returns:
            Dictionary mapping block IDs to their total voting power

        Raises:
            DataFormatError: If the token balances data doesn't have the expected format
        """
        try:
            if not voting_blocks:
                logger.warning("No voting blocks provided")
                return {}

            if not token_balances:
                logger.warning("No token balance data provided")
                return {}

            block_power = {}
            total_tokens = sum(token_balances.values())

            for i, block in enumerate(voting_blocks):
                block_id = f"Block_{i + 1}"
                block_tokens = sum(token_balances.get(addr, 0) for addr in block)
                block_percentage = (
                    (block_tokens / total_tokens * 100) if total_tokens > 0 else 0
                )

                block_power[block_id] = {
                    "addresses": block,
                    "address_count": len(block),
                    "total_tokens": block_tokens,
                    "percentage": block_percentage,
                }

            logger.info(f"Calculated voting power for {len(voting_blocks)} blocks")
            return block_power

        except Exception as e:
            if isinstance(e, KeyError):
                logger.error(f"Error accessing token balance data: {e}")
                raise DataFormatError(f"Error accessing token balance data: {e}") from e
            logger.error(f"Failed to calculate voting block power: {e}")
            raise HistoricalDataError(
                f"Failed to calculate voting block power: {e}"
            ) from e

    def get_block_voting_patterns(self, block: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze voting patterns for a specific block.

        Args:
            block: List of addresses in the voting block

        Returns:
            Dictionary with voting pattern statistics for the block

        Raises:
            HistoricalDataError: If there's an issue analyzing voting patterns
        """
        try:
            if not block:
                logger.warning("Empty block provided")
                return {}

            # Get all proposals voted on by any member of the block
            all_proposals = set()
            for addr in block:
                if addr in self.voting_history:
                    all_proposals.update(self.voting_history[addr].keys())

            if not all_proposals:
                logger.warning("No voting history found for addresses in this block")
                return {}

            proposal_stats = {}

            for proposal_id in all_proposals:
                # Count votes for this proposal
                votes = {"for": 0, "against": 0, "abstain": 0, "no_vote": 0}

                for addr in block:
                    if (
                        addr in self.voting_history
                        and proposal_id in self.voting_history[addr]
                    ):
                        vote = self.voting_history[addr][proposal_id]
                        if vote == 1:
                            votes["for"] += 1
                        elif vote == 0:
                            votes["against"] += 1
                        else:
                            votes["abstain"] += 1
                    else:
                        votes["no_vote"] += 1

                # Calculate consensus percentage
                voted = votes["for"] + votes["against"] + votes["abstain"]
                consensus_pct = 0

                if voted > 0:
                    max_vote = max(votes["for"], votes["against"], votes["abstain"])
                    consensus_pct = (max_vote / voted) * 100

                proposal_stats[proposal_id] = {
                    "votes": votes,
                    "block_size": len(block),
                    "participation_pct": (voted / len(block)) * 100,
                    "consensus_pct": consensus_pct,
                }

            # Calculate average statistics
            avg_participation = sum(
                p["participation_pct"] for p in proposal_stats.values()
            ) / len(proposal_stats)
            avg_consensus = sum(
                p["consensus_pct"] for p in proposal_stats.values()
            ) / len(proposal_stats)

            result = {
                "proposals": proposal_stats,
                "avg_participation": avg_participation,
                "avg_consensus": avg_consensus,
                "block_size": len(block),
            }

            logger.info(
                f"Analyzed voting patterns for block with {len(block)} addresses across {len(all_proposals)} proposals"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to analyze block voting patterns: {e}")
            raise HistoricalDataError(
                f"Failed to analyze block voting patterns: {e}"
            ) from e

    def visualize_voting_blocks(
        self, token_balances: Optional[Dict[str, float]] = None
    ) -> plt.Figure:
        """
        Create a network visualization of voting blocks.

        Args:
            token_balances: Optional dictionary mapping addresses to token balances

        Returns:
            Matplotlib Figure object

        Raises:
            HistoricalDataError: If there's an issue creating the visualization
        """
        try:
            if self.address_similarity is None or self.address_similarity.empty:
                logger.warning("No similarity data available for visualization")
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.text(
                    0.5,
                    0.5,
                    "No voting block data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                return fig

            if not self.voting_blocks:
                logger.warning("No voting blocks identified for visualization")
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.text(
                    0.5,
                    0.5,
                    "No voting blocks identified",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                return fig

            # Create graph
            G = nx.Graph()

            # Define color map for different blocks
            colors = plt.cm.tab10(np.linspace(0, 1, len(self.voting_blocks)))
            color_map = {}

            # Add nodes and assign colors by block
            for i, block in enumerate(self.voting_blocks):
                for addr in block:
                    G.add_node(addr, block=i)
                    color_map[addr] = colors[i]

            # Add edges between addresses in the same block
            for i, addr1 in enumerate(self.address_similarity.index):
                for j, addr2 in enumerate(self.address_similarity.index):
                    if i < j and addr1 in color_map and addr2 in color_map:
                        similarity = self.address_similarity.loc[addr1, addr2]
                        if similarity > 0.6:  # Add edge if similarity is significant
                            G.add_edge(addr1, addr2, weight=similarity)

            # Size nodes by token balance if available
            node_sizes = []
            if token_balances:
                max_balance = max(token_balances.values()) if token_balances else 1
                for node in G.nodes():
                    balance = token_balances.get(node, 0)
                    # Normalize size between 50 and 500
                    size = 50 + (balance / max_balance) * 450
                    node_sizes.append(size)
            else:
                node_sizes = [100] * len(G.nodes())

            # Create figure
            fig, ax = plt.subplots(figsize=(12, 10))

            # Use spring layout for network visualization
            pos = nx.spring_layout(G, seed=42)

            # Draw nodes
            for node, (x, y) in pos.items():
                ax.scatter(
                    x,
                    y,
                    s=node_sizes[list(G.nodes()).index(node)],
                    color=color_map[node],
                    alpha=0.7,
                )

            # Draw edges
            for u, v, data in G.edges(data=True):
                ax.plot(
                    [pos[u][0], pos[v][0]],
                    [pos[u][1], pos[v][1]],
                    "k-",
                    alpha=0.2 + data["weight"] * 0.6,
                )

            # Add block labels
            block_centers = {}
            for i, block in enumerate(self.voting_blocks):
                xs = [pos[addr][0] for addr in block if addr in pos]
                ys = [pos[addr][1] for addr in block if addr in pos]
                if xs and ys:
                    block_centers[i] = (np.mean(xs), np.mean(ys))
                    ax.text(
                        block_centers[i][0],
                        block_centers[i][1],
                        f"Block {i + 1}",
                        fontsize=12,
                        fontweight="bold",
                        ha="center",
                        va="center",
                        bbox=dict(facecolor="white", alpha=0.7, boxstyle="round"),
                    )

            ax.set_title("Governance Voting Blocks")
            ax.axis("off")

            logger.info(
                f"Created visualization for {len(self.voting_blocks)} voting blocks with {len(G.nodes())} addresses"
            )
            return fig

        except Exception as e:
            logger.error(f"Failed to visualize voting blocks: {e}")
            raise HistoricalDataError(f"Failed to visualize voting blocks: {e}") from e


def analyze_proposal_influence(
    proposals: List[Dict[str, Any]], token_balances: Dict[str, float]
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze the influence of large token holders on proposal outcomes.

    Args:
        proposals: List of proposals with voting data
        token_balances: Dictionary mapping addresses to token balances

    Returns:
        Dictionary with influence analysis by proposal

    Raises:
        DataFormatError: If the input data doesn't have the expected format
        HistoricalDataError: If there's an issue with the analysis
    """
    try:
        if not proposals:
            logger.warning("No proposals provided for influence analysis")
            return {}

        if not token_balances:
            logger.warning("No token balance data provided for influence analysis")
            return {}

        # Sort addresses by token balance (descending)
        sorted_holders = sorted(
            token_balances.items(), key=lambda x: x[1], reverse=True
        )
        total_tokens = sum(token_balances.values())

        # Analyze each proposal
        results = {}

        for proposal in proposals:
            if (
                "id" not in proposal
                or "votes" not in proposal
                or "outcome" not in proposal
            ):
                logger.warning(f"Skipping proposal: missing required fields")
                continue

            proposal_id = proposal["id"]
            votes = proposal.get("votes", [])
            outcome = proposal["outcome"]  # 'passed' or 'rejected'

            # Map votes by address
            vote_map = {}
            for vote in votes:
                if "voter" not in vote or "support" not in vote:
                    continue
                vote_map[vote["voter"]] = vote["support"]

            # Calculate cumulative influence
            cumulative_influence = []
            cumulative_tokens = 0
            votes_for = 0
            votes_against = 0

            for holder, balance in sorted_holders:
                vote = vote_map.get(holder)
                if vote is not None:
                    cumulative_tokens += balance

                    if vote == 1:  # For
                        votes_for += balance
                    elif vote == 0:  # Against
                        votes_against += balance

                    # Calculate current vote percentage
                    if votes_for + votes_against > 0:
                        for_percentage = (votes_for / (votes_for + votes_against)) * 100
                    else:
                        for_percentage = 0

                    # Determine if outcome would be different without this vote
                    current_outcome = "passed" if for_percentage > 50 else "rejected"

                    cumulative_influence.append(
                        {
                            "address": holder,
                            "balance": balance,
                            "vote": "for" if vote == 1 else "against",
                            "cumulative_tokens": cumulative_tokens,
                            "cumulative_percentage": (cumulative_tokens / total_tokens)
                            * 100,
                            "for_percentage": for_percentage,
                            "current_outcome": current_outcome,
                        }
                    )

            # Find threshold where outcome changes
            threshold_found = False
            threshold_data = None

            for i, data in enumerate(cumulative_influence):
                if i > 0:
                    prev = cumulative_influence[i - 1]
                    if prev["current_outcome"] != data["current_outcome"]:
                        threshold_found = True
                        threshold_data = {
                            "addresses_needed": i + 1,
                            "tokens_needed": data["cumulative_tokens"],
                            "percentage_needed": data["cumulative_percentage"],
                        }
                        break

            # Determine whale influence
            top_10_balance = sum(balance for _, balance in sorted_holders[:10])
            top_10_percentage = (top_10_balance / total_tokens) * 100

            top_10_votes = {
                "for": sum(
                    balance
                    for addr, balance in sorted_holders[:10]
                    if vote_map.get(addr) == 1
                ),
                "against": sum(
                    balance
                    for addr, balance in sorted_holders[:10]
                    if vote_map.get(addr) == 0
                ),
            }

            top_10_votes_percentage = 0
            if votes_for + votes_against > 0:
                if outcome == "passed":
                    top_10_votes_percentage = (
                        top_10_votes["for"] / (votes_for + votes_against)
                    ) * 100
                else:
                    top_10_votes_percentage = (
                        top_10_votes["against"] / (votes_for + votes_against)
                    ) * 100

            results[proposal_id] = {
                "outcome": outcome,
                "threshold": threshold_data,
                "threshold_found": threshold_found,
                "top_10_influence": {
                    "total_balance": top_10_balance,
                    "percentage_of_supply": top_10_percentage,
                    "votes": top_10_votes,
                    "aligned_vote_percentage": top_10_votes_percentage,
                },
                "votes_for": votes_for,
                "votes_against": votes_against,
                "participation_percentage": ((votes_for + votes_against) / total_tokens)
                * 100,
            }

        logger.info(f"Analyzed influence patterns for {len(results)} proposals")
        return results

    except Exception as e:
        if isinstance(e, KeyError):
            logger.error(f"Error accessing data fields: {e}")
            raise DataFormatError(f"Error accessing data fields: {e}") from e
        logger.error(f"Failed to analyze proposal influence: {e}")
        raise HistoricalDataError(f"Failed to analyze proposal influence: {e}") from e


def detect_voting_anomalies(
    proposals: List[Dict[str, Any]], token_holders: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect anomalies in voting patterns that might indicate coordination or manipulation.

    Args:
        proposals: List of proposals with voting data
        token_holders: List of token holder data

    Returns:
        Dictionary of detected anomalies by category

    Raises:
        DataFormatError: If the input data doesn't have the expected format
        HistoricalDataError: If there's an issue with the analysis
    """
    try:
        if not proposals:
            logger.warning("No proposals provided for anomaly detection")
            return {}

        if not token_holders:
            logger.warning("No token holder data provided for anomaly detection")
            return {}

        # Map addresses to token balances
        balance_map = {
            h["address"]: h["balance"]
            for h in token_holders
            if "address" in h and "balance" in h
        }

        # Prepare voting data
        voting_data = defaultdict(dict)
        proposal_participation = {}

        for proposal in proposals:
            if "id" not in proposal or "votes" not in proposal:
                continue

            proposal_id = proposal["id"]
            votes = proposal.get("votes", [])

            # Track participation for this proposal
            participation_count = len(votes)
            total_holders = len(token_holders)
            participation_rate = (
                (participation_count / total_holders) if total_holders > 0 else 0
            )
            proposal_participation[proposal_id] = participation_rate

            # Map votes by address
            for vote in votes:
                if "voter" not in vote or "support" not in vote:
                    continue

                voter = vote["voter"]
                support = vote["support"]

                voting_data[voter][proposal_id] = support

        # Find anomalies
        anomalies = {
            "sudden_participation": [],
            "coordinated_voting": [],
            "vote_against_size": [],
            "whale_against_community": [],
        }

        # 1. Detect sudden participation increases
        avg_participation = (
            sum(proposal_participation.values()) / len(proposal_participation)
            if proposal_participation
            else 0
        )

        for proposal_id, rate in proposal_participation.items():
            if rate > avg_participation * 1.5:  # 50% higher than average
                anomalies["sudden_participation"].append(
                    {
                        "proposal_id": proposal_id,
                        "participation_rate": rate,
                        "average_rate": avg_participation,
                        "increase_percentage": (
                            (rate - avg_participation) / avg_participation
                        )
                        * 100,
                    }
                )

        # 2. Detect coordinated voting (addresses that always vote together)
        if (
            len(proposals) >= 3
        ):  # Need at least 3 proposals for meaningful pattern detection
            # Find address pairs that voted on at least 3 common proposals
            for addr1, votes1 in voting_data.items():
                for addr2, votes2 in voting_data.items():
                    if addr1 >= addr2:  # Avoid duplicates and self-comparison
                        continue

                    # Find common proposals
                    common_props = set(votes1.keys()) & set(votes2.keys())

                    if len(common_props) >= 3:
                        # Check if they always voted the same
                        always_same = all(votes1[p] == votes2[p] for p in common_props)

                        if always_same:
                            anomalies["coordinated_voting"].append(
                                {
                                    "addresses": [addr1, addr2],
                                    "common_proposals": len(common_props),
                                    "balances": [
                                        balance_map.get(addr1, 0),
                                        balance_map.get(addr2, 0),
                                    ],
                                }
                            )

        # 3. Detect votes that go against token holding size
        for proposal in proposals:
            if (
                "id" not in proposal
                or "votes" not in proposal
                or "outcome" not in proposal
            ):
                continue

            proposal_id = proposal["id"]
            votes = proposal.get("votes", [])
            outcome = proposal["outcome"]

            # Calculate total voting power by outcome
            power_for = 0
            power_against = 0

            for vote in votes:
                if "voter" not in vote or "support" not in vote:
                    continue

                voter = vote["voter"]
                support = vote["support"]
                balance = balance_map.get(voter, 0)

                if support == 1:  # For
                    power_for += balance
                elif support == 0:  # Against
                    power_against += balance

            total_power = power_for + power_against

            # Check if outcome goes against token power distribution
            if total_power > 0:
                power_for_pct = (power_for / total_power) * 100
                power_against_pct = (power_against / total_power) * 100

                if (outcome == "passed" and power_against_pct > power_for_pct) or (
                    outcome == "rejected" and power_for_pct > power_against_pct
                ):
                    anomalies["vote_against_size"].append(
                        {
                            "proposal_id": proposal_id,
                            "outcome": outcome,
                            "power_for_percentage": power_for_pct,
                            "power_against_percentage": power_against_pct,
                        }
                    )

        # 4. Detect whales voting against community
        for proposal in proposals:
            if "id" not in proposal or "votes" not in proposal:
                continue

            proposal_id = proposal["id"]
            votes = proposal.get("votes", [])

            # Sort holders by balance
            sorted_voters = []
            for vote in votes:
                if "voter" not in vote or "support" not in vote:
                    continue

                voter = vote["voter"]
                support = vote["support"]
                balance = balance_map.get(voter, 0)

                sorted_voters.append(
                    {"address": voter, "support": support, "balance": balance}
                )

            sorted_voters.sort(key=lambda x: x["balance"], reverse=True)

            # Check if top 10% vote differently than bottom 90%
            if len(sorted_voters) >= 10:
                top_count = max(1, len(sorted_voters) // 10)

                top_votes = [v["support"] for v in sorted_voters[:top_count]]
                bottom_votes = [v["support"] for v in sorted_voters[top_count:]]

                top_for = sum(1 for v in top_votes if v == 1)
                top_against = sum(1 for v in top_votes if v == 0)

                bottom_for = sum(1 for v in bottom_votes if v == 1)
                bottom_against = sum(1 for v in bottom_votes if v == 0)

                top_sentiment = "for" if top_for > top_against else "against"
                bottom_sentiment = "for" if bottom_for > bottom_against else "against"

                if top_sentiment != bottom_sentiment:
                    anomalies["whale_against_community"].append(
                        {
                            "proposal_id": proposal_id,
                            "top_sentiment": top_sentiment,
                            "bottom_sentiment": bottom_sentiment,
                            "top_for_percentage": (top_for / top_count) * 100
                            if top_count > 0
                            else 0,
                            "top_against_percentage": (top_against / top_count) * 100
                            if top_count > 0
                            else 0,
                            "bottom_for_percentage": (bottom_for / len(bottom_votes))
                            * 100
                            if bottom_votes
                            else 0,
                            "bottom_against_percentage": (
                                bottom_against / len(bottom_votes)
                            )
                            * 100
                            if bottom_votes
                            else 0,
                        }
                    )

        logger.info(
            f"Detected {sum(len(v) for v in anomalies.values())} anomalies across {len(proposals)} proposals"
        )
        return anomalies

    except Exception as e:
        if isinstance(e, KeyError):
            logger.error(f"Error accessing data fields: {e}")
            raise DataFormatError(f"Error accessing data fields: {e}") from e
        logger.error(f"Failed to detect voting anomalies: {e}")
        raise HistoricalDataError(f"Failed to detect voting anomalies: {e}") from e
