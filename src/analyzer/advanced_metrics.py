"""Advanced Concentration Metrics for Token Distribution Analysis.

This module provides advanced metrics for analyzing token distribution concentration
beyond the basic Gini coefficient and Herfindahl index.
"""

import numpy as np
from typing import List, Dict, Any
import logging
import networkx as nx
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_palma_ratio(balances: List[float]) -> float:
    """Calculate the Palma ratio, which is the ratio of the share of total income held by the
    top 10% to that held by the bottom 40%.

    In the context of token distribution, this measures the ratio of tokens held by the top 10%
    of holders versus the bottom 40%.

    Args:
        balances: List of token balances sorted in descending order

    Returns:
        Palma ratio as a float

    """
    if not balances or sum(balances) == 0:
        return 0.0

    # Sort balances in descending order to ensure correct calculation
    sorted_balances = sorted(balances, reverse=True)

    total = sum(sorted_balances)

    # Calculate the number of holders representing the top 10% and bottom 40%
    n = len(sorted_balances)
    top_10_count = max(1, int(n * 0.1))
    bottom_40_count = max(1, int(n * 0.4))

    # Calculate share of top 10% and bottom 40%
    top_10_share = sum(sorted_balances[:top_10_count]) / total
    bottom_40_share = sum(sorted_balances[-bottom_40_count:]) / total

    # Avoid division by zero
    if bottom_40_share == 0:
        return float("inf")  # Infinite inequality

    return top_10_share / bottom_40_share


def calculate_hoover_index(balances: List[float]) -> float:
    """Calculate the Hoover index (also known as Robin Hood index), which represents
    the proportion of tokens that would need to be redistributed to achieve perfect equality.

    Args:
        balances: List of token balances

    Returns:
        Hoover index as a float between 0 and 1

    """
    if not balances or sum(balances) == 0:
        return 0.0

    total = sum(balances)
    n = len(balances)

    # Calculate the mean balance
    mean_balance = total / n

    # Calculate the sum of absolute deviations from the mean
    sum_deviations = sum(abs(balance - mean_balance) for balance in balances)

    # The Hoover index is half of the relative mean deviation
    return sum_deviations / (2 * total)


def calculate_theil_index(balances: List[float]) -> float:
    """Calculate the Theil index, which is a measure of economic inequality.
    The Theil index can be decomposed to show inequality within and between different subgroups.

    Args:
        balances: List of token balances

    Returns:
        Theil index as a float (0 = perfect equality, higher values = more inequality)

    """
    if not balances or sum(balances) == 0:
        return 0.0

    n = len(balances)
    total = sum(balances)
    mean = total / n

    # Calculate Theil index
    theil = 0
    for balance in balances:
        if balance <= 0:
            continue  # Skip zero or negative balances

        # Calculate individual contribution to Theil index
        x_i = balance / mean
        theil += (x_i * np.log(x_i)) / n

    return theil


def calculate_nakamoto_coefficient(balances: List[float], threshold: float = 51.0) -> int:
    """Calculate the Nakamoto coefficient, which is the minimum number of entities
    required to achieve a specified threshold of control (usually 51%).

    Args:
        balances: List of token balances in descending order
        threshold: Control threshold percentage (default: 51%)

    Returns:
        Nakamoto coefficient as an integer

    """
    if not balances or sum(balances) == 0:
        return 0

    # Sort balances in descending order to ensure correct calculation
    sorted_balances = sorted(balances, reverse=True)

    total = sum(sorted_balances)
    running_sum = 0

    for i, balance in enumerate(sorted_balances):
        running_sum += balance
        if (running_sum / total * 100) >= threshold:
            return i + 1

    # If the threshold cannot be reached (unlikely in practice)
    return len(sorted_balances)


def calculate_lorenz_curve(balances: List[float]) -> Dict[str, List[float]]:
    """Calculate the Lorenz curve coordinates for token distribution.

    The Lorenz curve plots the cumulative share of tokens (y-axis) against
    the cumulative share of holders (x-axis).

    Args:
        balances: List of token balances

    Returns:
        Dictionary with 'x' and 'y' coordinates for the Lorenz curve

    """
    if not balances or sum(balances) == 0:
        return {"x": [0, 1], "y": [0, 1]}

    # Sort balances in ascending order for Lorenz curve calculation
    sorted_balances = sorted(balances)

    n = len(sorted_balances)
    total = sum(sorted_balances)

    # Initialize with origin point
    x_values = [0]
    y_values = [0]

    # Calculate cumulative percentages
    cum_balance = 0
    for i, balance in enumerate(sorted_balances):
        cum_balance += balance
        x_values.append((i + 1) / n)
        y_values.append(cum_balance / total)

    return {"x": x_values, "y": y_values}


def calculate_top_percentiles(balances: List[float], percentiles: List[int] = None) -> Dict[str, float]:
    """Calculate the percentage of tokens held by the top X% of holders for specified percentiles.

    Args:
        balances: List of token balances
        percentiles: List of percentiles to calculate

    Returns:
        Dictionary mapping percentiles to concentration percentages

    """
    if percentiles is None:
        percentiles = [1, 5, 10, 20, 50]

    if not balances or sum(balances) == 0:
        return {str(p): 0.0 for p in percentiles}

    # Sort balances in descending order
    sorted_balances = sorted(balances, reverse=True)

    total = sum(sorted_balances)
    n = len(sorted_balances)

    result = {}
    for p in percentiles:
        # Calculate the number of holders in the top p%
        holder_count = max(1, int(n * p / 100))

        # Calculate the percentage of tokens held by these holders
        top_p_balance = sum(sorted_balances[:holder_count])
        result[str(p)] = (top_p_balance / total) * 100

    return result


def calculate_all_concentration_metrics(balances: List[float]) -> Dict[str, Any]:
    """Calculate all concentration metrics for a set of token balances.

    Args:
        balances: List of token balances

    Returns:
        Dictionary of concentration metrics

    """
    # Convert to float and ensure positive balances for calculations
    try:
        numeric_balances = []
        for b in balances:
            try:
                # Handle various string formats
                if isinstance(b, str):
                    # Remove common formatting characters
                    clean_balance = b.replace(',', '').replace('$', '').replace(' ', '')
                    if clean_balance:
                        numeric_balances.append(float(clean_balance))
                elif isinstance(b, (int, float)):
                    numeric_balances.append(float(b))
            except (ValueError, TypeError):
                # Skip invalid values
                continue
        
        positive_balances = [b for b in numeric_balances if b > 0]
    except Exception as e:
        logger.error(f"Error processing balances: {str(e)}")
        positive_balances = []

    if not positive_balances:
        logger.warning("No positive balances provided for concentration metrics calculation")
        return {
            "gini_coefficient": 0,
            "herfindahl_index": 0,
            "palma_ratio": 0,
            "hoover_index": 0,
            "theil_index": 0,
            "nakamoto_coefficient": 0,
            "top_percentile_concentration": {},
            "lorenz_curve": {"x": [0, 1], "y": [0, 1]},
        }

    # Sort balances in descending order for consistent calculations
    sorted_balances = sorted(positive_balances, reverse=True)

    try:
        # Calculate all metrics
        return {
            "palma_ratio": calculate_palma_ratio(sorted_balances),
            "hoover_index": calculate_hoover_index(sorted_balances),
            "theil_index": calculate_theil_index(sorted_balances),
            "nakamoto_coefficient": calculate_nakamoto_coefficient(sorted_balances),
            "top_percentile_concentration": calculate_top_percentiles(sorted_balances),
            "lorenz_curve": calculate_lorenz_curve(sorted_balances),
        }
    except Exception as e:
        logger.error(f"Error calculating concentration metrics: {str(e)}")
        # Return empty metrics in case of calculation error
        return {
            "palma_ratio": None,
            "hoover_index": None,
            "theil_index": None,
            "nakamoto_coefficient": None,
            "top_percentile_concentration": {},
            "lorenz_curve": {"x": [0, 1], "y": [0, 1]},
        }


class VotingBlockAnalyzer:
    """Analyzes voting patterns to identify voting blocks or coalitions in governance.

    This class provides methods for analyzing voting patterns across proposals,
    identifying groups of token holders that tend to vote similarly, and
    visualizing these voting blocks.
    """

    def __init__(self):
        """Initialize the voting block analyzer."""
        self.logger = logging.getLogger(__name__)

    def identify_voting_blocks(
        self, proposals: List[Dict[str, Any]], similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Identify voting blocks based on voting patterns.

        Args:
            proposals: List of governance proposals with voting data
            similarity_threshold: Threshold for considering voters as part of the same block
                                 (0.0 to 1.0, higher means more similar voting patterns required)

        Returns:
            Dictionary containing voting block analysis results

        """
        try:
            # Extract voting data
            voter_votes = defaultdict(dict)  # voter_address -> {proposal_id: vote}

            for proposal in proposals:
                proposal_id = proposal.get("id", "unknown")

                # Extract votes for this proposal
                for vote_data in proposal.get("votes", []):
                    voter = vote_data.get("voter_address")
                    vote = vote_data.get("vote")  # Assuming 'for', 'against', or 'abstain'

                    if voter and vote:
                        voter_votes[voter][proposal_id] = vote

            # Only consider voters who voted on at least 2 proposals
            active_voters = {voter: votes for voter, votes in voter_votes.items() if len(votes) >= 2}

            if len(active_voters) < 2:
                return {"blocks": [], "block_stats": {}, "voter_block_mapping": {}}

            # Calculate voting similarity between all pairs of voters
            similarity_matrix = {}
            voters = list(active_voters.keys())

            for i, voter1 in enumerate(voters):
                for voter2 in voters[i + 1 :]:
                    # Find proposals both voters voted on
                    common_proposals = set(active_voters[voter1].keys()) & set(active_voters[voter2].keys())

                    if not common_proposals:
                        continue

                    # Count how many times they voted the same way
                    same_votes = sum(
                        1 for p in common_proposals if active_voters[voter1][p] == active_voters[voter2][p]
                    )
                    similarity = same_votes / len(common_proposals)

                    if similarity >= similarity_threshold:
                        pair_key = (voter1, voter2)
                        similarity_matrix[pair_key] = similarity

            # Build a graph of voter relationships
            G = nx.Graph()

            # Add all active voters as nodes
            for voter in active_voters:
                G.add_node(voter)

            # Add edges between similar voters
            for (voter1, voter2), similarity in similarity_matrix.items():
                G.add_edge(voter1, voter2, weight=similarity)

            # Identify communities (voting blocks)
            communities = list(nx.community.greedy_modularity_communities(G))

            # Format the results
            blocks = []
            voter_block_mapping = {}

            for i, community in enumerate(communities):
                block_id = f"block_{i + 1}"
                block_voters = list(community)
                blocks.append({"id": block_id, "size": len(block_voters), "voters": block_voters})

                # Map each voter to their block
                for voter in block_voters:
                    voter_block_mapping[voter] = block_id

            # Calculate statistics for each block
            block_stats = {}
            for block in blocks:
                block_id = block["id"]
                block_voters = block["voters"]

                # Calculate voting cohesion (how often members vote the same way)
                cohesion = 0.0
                pair_count = 0

                for i, voter1 in enumerate(block_voters):
                    for voter2 in block_voters[i + 1 :]:
                        pair_key = (voter1, voter2) if voter1 < voter2 else (voter2, voter1)
                        if pair_key in similarity_matrix:
                            cohesion += similarity_matrix[pair_key]
                            pair_count += 1

                avg_cohesion = cohesion / pair_count if pair_count > 0 else 0.0

                block_stats[block_id] = {
                    "size": block["size"],
                    "cohesion": avg_cohesion,
                    "influence_score": block["size"] * avg_cohesion,  # Simple influence metric
                }

            return {
                "blocks": blocks,
                "block_stats": block_stats,
                "voter_block_mapping": voter_block_mapping,
                "total_blocks": len(blocks),
                "largest_block_size": max([b["size"] for b in blocks]) if blocks else 0,
            }

        except Exception as e:
            self.logger.error(f"Error identifying voting blocks: {str(e)}")
            return {"error": str(e)}

    def analyze_block_voting_patterns(self, proposals: List[Dict[str, Any]], blocks: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how different voting blocks vote on proposals.

        Args:
            proposals: List of governance proposals with voting data
            blocks: Voting blocks data from identify_voting_blocks

        Returns:
            Dictionary containing block voting pattern analysis

        """
        try:
            # Extract the voter to block mapping
            voter_block_mapping = blocks.get("voter_block_mapping", {})
            block_stats = blocks.get("block_stats", {})

            if not voter_block_mapping or not block_stats:
                return {"error": "Invalid block data provided"}

            # Analyze voting patterns for each block on each proposal
            block_voting_patterns = {}

            for proposal in proposals:
                proposal_id = proposal.get("id", "unknown")

                # Count votes by block
                block_votes = defaultdict(lambda: {"for": 0, "against": 0, "abstain": 0})

                for vote_data in proposal.get("votes", []):
                    voter = vote_data.get("voter_address")
                    vote = vote_data.get("vote")  # Assuming 'for', 'against', or 'abstain'

                    if voter in voter_block_mapping and vote:
                        block_id = voter_block_mapping[voter]
                        block_votes[block_id][vote] += 1

                # Calculate dominant vote for each block
                proposal_blocks = {}
                for block_id, votes in block_votes.items():
                    total_votes = sum(votes.values())
                    dominant_vote = max(votes.items(), key=lambda x: x[1])[0]
                    dominant_percentage = (votes[dominant_vote] / total_votes) * 100 if total_votes > 0 else 0

                    proposal_blocks[block_id] = {
                        "votes": votes,
                        "dominant_vote": dominant_vote,
                        "dominant_percentage": dominant_percentage,
                        "total_votes": total_votes,
                    }

                block_voting_patterns[proposal_id] = proposal_blocks

            # Calculate block agreement/disagreement
            block_relationships = {}
            block_ids = list(block_stats.keys())

            for i, block1 in enumerate(block_ids):
                for block2 in block_ids[i + 1 :]:
                    # Count how often they agree/disagree
                    agreements = 0
                    total_common_proposals = 0

                    for proposal_id, blocks_data in block_voting_patterns.items():
                        if block1 in blocks_data and block2 in blocks_data:
                            total_common_proposals += 1
                            if blocks_data[block1]["dominant_vote"] == blocks_data[block2]["dominant_vote"]:
                                agreements += 1

                    if total_common_proposals > 0:
                        agreement_rate = (agreements / total_common_proposals) * 100
                        block_relationships[f"{block1}_{block2}"] = {
                            "agreement_rate": agreement_rate,
                            "common_proposals": total_common_proposals,
                        }

            return {
                "block_voting_patterns": block_voting_patterns,
                "block_relationships": block_relationships,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing block voting patterns: {str(e)}")
            return {"error": str(e)}

    def calculate_block_influence(
        self,
        proposals: List[Dict[str, Any]],
        blocks: Dict[str, Any],
        token_holders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate the influence of each voting block based on token holdings and voting patterns.

        Args:
            proposals: List of governance proposals with voting data
            blocks: Voting block data from identify_voting_blocks
            token_holders: List of token holders with their balances

        Returns:
            Dictionary containing block influence analysis

        """
        try:
            # Extract the voter to block mapping
            voter_block_mapping = blocks.get("voter_block_mapping", {})
            block_stats = blocks.get("block_stats", {})

            if not voter_block_mapping or not block_stats:
                return {"error": "Invalid block data provided"}

            # Create a mapping from addresses to token balances
            address_to_balance = {}
            for holder in token_holders:
                address = holder.get("TokenHolderAddress")
                balance = float(holder.get("TokenHolderQuantity", 0))
                if address:
                    address_to_balance[address] = balance

            # Calculate token holdings for each block
            block_holdings = defaultdict(float)
            for voter, block_id in voter_block_mapping.items():
                balance = address_to_balance.get(voter, 0)
                block_holdings[block_id] += balance

            # Calculate total tokens across all blocks
            total_block_tokens = sum(block_holdings.values())

            # Calculate influence metrics for each block
            block_influence = {}
            for block_id, stats in block_stats.items():
                token_share = (block_holdings[block_id] / total_block_tokens) * 100 if total_block_tokens > 0 else 0
                cohesion = stats.get("cohesion", 0)

                # Calculate influence as a combination of token share and cohesion
                influence = token_share * cohesion

                block_influence[block_id] = {
                    "token_holdings": block_holdings[block_id],
                    "token_share": token_share,
                    "cohesion": cohesion,
                    "influence_score": influence,
                }

            # Rank blocks by influence
            ranked_blocks = sorted(
                block_influence.items(),
                key=lambda x: x[1]["influence_score"],
                reverse=True,
            )

            return {
                "block_influence": block_influence,
                "ranked_blocks": [{"id": block_id, **influence} for block_id, influence in ranked_blocks],
                "most_influential_block": ranked_blocks[0][0] if ranked_blocks else None,
            }

        except Exception as e:
            self.logger.error(f"Error calculating block influence: {str(e)}")
            return {"error": str(e)}


class DelegationAnalyzer:
    """Analyzes delegation patterns in governance token systems.

    This class provides methods for analyzing how token holders delegate their
    voting power, identifying key delegates, and visualizing delegation networks.
    """

    def __init__(self):
        """Initialize the delegation analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze_delegation_network(
        self, delegations: List[Dict[str, Any]], token_holders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the delegation network structure.

        Args:
            delegations: List of delegation records (delegator -> delegate)
            token_holders: List of token holders with their balances

        Returns:
            Dictionary containing delegation network analysis

        """
        try:
            # Create a network graph of delegations
            G = nx.DiGraph()

            # Create a mapping from addresses to token balances
            address_to_balance = {}
            for holder in token_holders:
                address = holder.get("TokenHolderAddress")
                balance = float(holder.get("TokenHolderQuantity", 0))
                if address:
                    address_to_balance[address] = balance
                    G.add_node(address, balance=balance)

            # Add delegation edges
            for delegation in delegations:
                delegator = delegation.get("delegator")
                delegate = delegation.get("delegate")
                amount = delegation.get("amount", address_to_balance.get(delegator, 0))

                if delegator and delegate:
                    G.add_edge(delegator, delegate, amount=amount)

            # Identify key delegates (nodes with high in-degree)
            in_degrees = dict(G.in_degree())
            key_delegates = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)

            # Calculate delegated voting power for each delegate
            delegated_power = {}
            for node in G.nodes():
                # Sum of tokens delegated to this node
                incoming = sum(G.edges[edge]["amount"] for edge in G.in_edges(node))
                delegated_power[node] = incoming

            # Rank delegates by delegated power
            ranked_delegates = sorted(delegated_power.items(), key=lambda x: x[1], reverse=True)

            # Calculate network centralization metrics
            try:
                # Degree centrality
                in_degree_centrality = nx.in_degree_centrality(G)
                # PageRank
                pagerank = nx.pagerank(G, weight="amount")
                # Authority scores (HITS algorithm)
                hits = nx.hits(G, max_iter=100)
                authority_scores = hits[1]  # authority scores
            except:
                in_degree_centrality = {}
                pagerank = {}
                authority_scores = {}

            # Identify delegation chains
            delegation_chains = []
            for node in G.nodes():
                if G.in_degree(node) == 0 and G.out_degree(node) > 0:  # Start of a chain
                    chain = self._trace_delegation_chain(G, node)
                    delegation_chains.append(chain)

            return {
                "key_delegates": [{"address": addr, "delegators": count} for addr, count in key_delegates[:10]],
                "ranked_delegates": [
                    {"address": addr, "delegated_power": power} for addr, power in ranked_delegates[:10]
                ],
                "top_delegate": ranked_delegates[0][0] if ranked_delegates else None,
                "top_delegate_power": ranked_delegates[0][1] if ranked_delegates else 0,
                "total_delegations": sum(in_degrees.values()),
                "delegation_chains": delegation_chains,
                "centrality_metrics": {
                    "top_centrality": max(in_degree_centrality.items(), key=lambda x: x[1])
                    if in_degree_centrality
                    else None,
                    "top_pagerank": max(pagerank.items(), key=lambda x: x[1]) if pagerank else None,
                    "top_authority": max(authority_scores.items(), key=lambda x: x[1]) if authority_scores else None,
                },
            }

        except Exception as e:
            self.logger.error(f"Error analyzing delegation network: {str(e)}")
            return {"error": str(e)}

    def _trace_delegation_chain(self, G, start_node, max_depth=10):
        """Trace a delegation chain starting from a specific node.

        Args:
            G: NetworkX graph of delegations
            start_node: Starting node for the chain
            max_depth: Maximum depth to trace (to avoid infinite loops)

        Returns:
            List representing the delegation chain

        """
        chain = [start_node]
        current = start_node
        depth = 0

        while depth < max_depth and G.out_degree(current) > 0:
            # Get the next node in the chain (the delegate)
            successors = list(G.successors(current))
            if not successors:
                break

            # Take the first delegate
            next_node = successors[0]
            chain.append(next_node)
            current = next_node
            depth += 1

            # Detect cycles
            if next_node in chain[:-1]:
                chain.append("(cycle detected)")
                break

        return chain

    def analyze_delegation_effectiveness(
        self, delegations: List[Dict[str, Any]], proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze how effective delegation is in terms of governance participation.

        Args:
            delegations: List of delegation records
            proposals: List of governance proposals with voting data

        Returns:
            Dictionary containing delegation effectiveness metrics

        """
        try:
            # Create a mapping from delegators to delegates
            delegator_to_delegate = {}
            for delegation in delegations:
                delegator = delegation.get("delegator")
                delegate = delegation.get("delegate")
                if delegator and delegate:
                    delegator_to_delegate[delegator] = delegate

            # Analyze delegate voting behavior
            delegate_votes = defaultdict(list)
            delegate_voting_rate = defaultdict(lambda: {"proposals": 0, "votes": 0})

            for proposal in proposals:
                proposal_id = proposal.get("id", "unknown")

                # Track which delegates voted on this proposal
                voting_delegates = set()
                for vote_data in proposal.get("votes", []):
                    voter = vote_data.get("voter_address")
                    vote = vote_data.get("vote")

                    if voter in delegator_to_delegate.values():
                        delegate_votes[voter].append({"proposal_id": proposal_id, "vote": vote})
                        voting_delegates.add(voter)

                # Update voting rates
                for delegate in delegator_to_delegate.values():
                    delegate_voting_rate[delegate]["proposals"] += 1
                    if delegate in voting_delegates:
                        delegate_voting_rate[delegate]["votes"] += 1

            # Calculate delegate participation rates
            delegate_participation = {}
            for delegate, stats in delegate_voting_rate.items():
                rate = (stats["votes"] / stats["proposals"]) * 100 if stats["proposals"] > 0 else 0
                delegate_participation[delegate] = rate

            # Calculate overall delegation effectiveness
            active_delegates = sum(1 for rate in delegate_participation.values() if rate > 0)
            inactive_delegates = sum(1 for rate in delegate_participation.values() if rate == 0)
            avg_participation = (
                sum(delegate_participation.values()) / len(delegate_participation) if delegate_participation else 0
            )

            # Categorize delegates by activity level
            delegate_categories = {
                "highly_active": sum(1 for rate in delegate_participation.values() if rate >= 75),
                "active": sum(1 for rate in delegate_participation.values() if 50 <= rate < 75),
                "occasional": sum(1 for rate in delegate_participation.values() if 25 <= rate < 50),
                "inactive": sum(1 for rate in delegate_participation.values() if rate < 25),
            }

            return {
                "delegate_participation": delegate_participation,
                "average_delegate_participation": avg_participation,
                "active_delegates": active_delegates,
                "inactive_delegates": inactive_delegates,
                "delegate_categories": delegate_categories,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing delegation effectiveness: {str(e)}")
            return {"error": str(e)}

    def calculate_delegation_metrics(
        self, delegations: List[Dict[str, Any]], token_holders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate various metrics about the delegation patterns.

        Args:
            delegations: List of delegation records
            token_holders: List of token holders with their balances

        Returns:
            Dictionary containing delegation metrics

        """
        try:
            # Count unique delegators and delegates
            delegators = set()
            delegates = set()

            for delegation in delegations:
                delegator = delegation.get("delegator")
                delegate = delegation.get("delegate")

                if delegator:
                    delegators.add(delegator)
                if delegate:
                    delegates.add(delegate)

            # Create a mapping from addresses to token balances
            address_to_balance = {}
            for holder in token_holders:
                address = holder.get("TokenHolderAddress")
                balance = float(holder.get("TokenHolderQuantity", 0))
                if address:
                    address_to_balance[address] = balance

            # Calculate total tokens delegated
            total_delegated = 0
            for delegator in delegators:
                balance = address_to_balance.get(delegator, 0)
                total_delegated += balance

            # Calculate total supply from token holders
            total_supply = sum(address_to_balance.values())

            # Calculate delegation concentration metrics
            delegated_to_top_5 = 0
            delegated_to_top_10 = 0

            # Count delegations per delegate
            delegate_counts = defaultdict(int)
            delegate_tokens = defaultdict(float)

            for delegation in delegations:
                delegator = delegation.get("delegator")
                delegate = delegation.get("delegate")

                if delegator and delegate:
                    delegate_counts[delegate] += 1
                    delegate_tokens[delegate] += address_to_balance.get(delegator, 0)

            # Sort delegates by delegated tokens
            sorted_delegates = sorted(delegate_tokens.items(), key=lambda x: x[1], reverse=True)

            # Calculate delegation to top delegates
            if sorted_delegates:
                delegated_to_top_5 = sum(tokens for _, tokens in sorted_delegates[:5])
                delegated_to_top_10 = sum(tokens for _, tokens in sorted_delegates[:10])

            return {
                "unique_delegators": len(delegators),
                "unique_delegates": len(delegates),
                "total_delegated_tokens": total_delegated,
                "delegation_percentage": (total_delegated / total_supply) * 100 if total_supply > 0 else 0,
                "delegated_to_top_5": delegated_to_top_5,
                "delegated_to_top_5_percentage": (delegated_to_top_5 / total_delegated) * 100
                if total_delegated > 0
                else 0,
                "delegated_to_top_10": delegated_to_top_10,
                "delegated_to_top_10_percentage": (delegated_to_top_10 / total_delegated) * 100
                if total_delegated > 0
                else 0,
                "top_delegates": sorted_delegates[:10],
            }

        except Exception as e:
            self.logger.error(f"Error calculating delegation metrics: {str(e)}")
            return {"error": str(e)}
