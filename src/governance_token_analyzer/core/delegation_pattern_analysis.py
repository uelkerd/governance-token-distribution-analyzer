"""Module for analyzing delegation patterns in governance protocols.

This module provides functionality to detect, analyze, and visualize
delegation patterns within governance token holders.
"""

import logging
from typing import Any, Dict, List

import networkx as nx
import numpy as np

from .exceptions import AnalysisError, DataFormatError

# Configure logging
logger = logging.getLogger(__name__)


class DelegationPatternAnalyzer:
    """Analyzes delegation patterns in governance protocols.

    This class provides methods to identify delegation patterns, analyze
    delegation concentration, and detect changes in delegation behavior
    over time.
    """

    def __init__(self, min_delegation_threshold: float = 0.01):
        """Initialize the DelegationPatternAnalyzer.

        Args:
            min_delegation_threshold: Minimum percentage of total supply for a
                delegation to be considered significant

        """
        self.min_delegation_threshold = min_delegation_threshold
        logger.info(
            f"Initialized DelegationPatternAnalyzer with min_delegation_threshold={min_delegation_threshold}"
        )

    def analyze_delegation_network(
        self, governance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the delegation network from governance data.

        Args:
            governance_data: Dictionary containing governance data with delegations
                             Expected keys: 'delegations', 'token_holders'

        Returns:
            Dictionary with delegation network analysis results

        Raises:
            DataFormatError: If the input data doesn't have the expected format
            AnalysisError: If there's an error during analysis

        """
        try:
            if "delegations" not in governance_data:
                logger.error("No delegation data found in governance_data")
                raise DataFormatError(
                    "No delegation data found. Expected 'delegations' key"
                )

            if "token_holders" not in governance_data:
                logger.error("No token holder data found in governance_data")
                raise DataFormatError(
                    "No token holder data found. Expected 'token_holders' key"
                )

            delegations = governance_data["delegations"]
            token_holders = governance_data["token_holders"]

            # Create a delegation graph
            delegation_graph = self._create_delegation_graph(delegations, token_holders)

            # Calculate delegation metrics
            delegation_metrics = self._calculate_delegation_metrics(
                delegation_graph, token_holders
            )

            # Identify key delegatees
            key_delegatees = self._identify_key_delegatees(
                delegation_graph, token_holders
            )

            # Analyze delegation patterns
            delegation_patterns = self._analyze_delegation_patterns(
                delegation_graph, token_holders
            )

            return {
                "metrics": delegation_metrics,
                "key_delegatees": key_delegatees,
                "patterns": delegation_patterns,
                "graph": delegation_graph,
            }

        except Exception as e:
            if isinstance(e, (DataFormatError, AnalysisError)):
                raise
            logger.error(f"Error analyzing delegation network: {e}")
            raise AnalysisError(f"Error analyzing delegation network: {e}")

    def compare_delegation_patterns(
        self, historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare delegation patterns across multiple historical snapshots.

        Args:
            historical_data: List of historical governance data snapshots

        Returns:
            Dictionary with delegation pattern comparison results

        Raises:
            DataFormatError: If the input data doesn't have the expected format
            AnalysisError: If there's an error during analysis

        """
        try:
            if not historical_data or not isinstance(historical_data, list):
                logger.error("Invalid historical data provided")
                raise DataFormatError("Historical data must be a non-empty list")

            # Extract timestamps and analyze each snapshot
            snapshots_analysis = []
            timestamps = []

            for snapshot in historical_data:
                if "timestamp" not in snapshot or "data" not in snapshot:
                    logger.error("Invalid snapshot format in historical data")
                    raise DataFormatError(
                        "Each snapshot must have 'timestamp' and 'data' keys"
                    )

                timestamps.append(snapshot["timestamp"])

                # Only analyze if delegation data exists
                if (
                    "delegations" in snapshot["data"]
                    and "token_holders" in snapshot["data"]
                ):
                    analysis = self.analyze_delegation_network(snapshot["data"])
                    snapshots_analysis.append(
                        {"timestamp": snapshot["timestamp"], "analysis": analysis}
                    )

            # Compare patterns across time
            comparison_results = self._compare_delegation_across_time(
                snapshots_analysis
            )

            return {"snapshots": snapshots_analysis, "comparison": comparison_results}

        except Exception as e:
            if isinstance(e, (DataFormatError, AnalysisError)):
                raise
            logger.error(f"Error comparing delegation patterns: {e}")
            raise AnalysisError(f"Error comparing delegation patterns: {e}")

    def detect_delegation_shifts(
        self, historical_data: List[Dict[str, Any]], shift_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """Detect significant shifts in delegation patterns.

        Args:
            historical_data: List of historical governance data snapshots
            shift_threshold: Threshold for considering a change significant

        Returns:
            Dictionary with detected delegation shifts

        Raises:
            DataFormatError: If the input data doesn't have the expected format
            AnalysisError: If there's an error during analysis

        """
        try:
            comparison_data = self.compare_delegation_patterns(historical_data)

            # If we don't have enough snapshots with delegation data, return empty results
            if len(comparison_data["snapshots"]) < 2:
                logger.warning(
                    "Not enough snapshots with delegation data to detect shifts"
                )
                return {"significant_shifts": [], "shift_metrics": {}}

            # Analyze the changes between consecutive snapshots
            shifts = []

            for i in range(1, len(comparison_data["snapshots"])):
                current = comparison_data["snapshots"][i]
                previous = comparison_data["snapshots"][i - 1]

                # Calculate metrics change
                metrics_change = self._calculate_metrics_change(
                    previous["analysis"]["metrics"], current["analysis"]["metrics"]
                )

                # Detect key delegatee changes
                delegatee_changes = self._detect_key_delegatee_changes(
                    previous["analysis"]["key_delegatees"],
                    current["analysis"]["key_delegatees"],
                )

                # Check if changes exceed threshold
                significant_changes = {
                    key: value
                    for key, value in metrics_change.items()
                    if abs(value) >= shift_threshold
                }

                if significant_changes or delegatee_changes["significant"]:
                    shifts.append(
                        {
                            "from_timestamp": previous["timestamp"],
                            "to_timestamp": current["timestamp"],
                            "metrics_change": metrics_change,
                            "significant_metrics": significant_changes,
                            "delegatee_changes": delegatee_changes,
                        }
                    )

            # Calculate overall shift metrics
            shift_metrics = self._calculate_shift_metrics(shifts)

            return {"significant_shifts": shifts, "shift_metrics": shift_metrics}

        except Exception as e:
            if isinstance(e, (DataFormatError, AnalysisError)):
                raise
            logger.error(f"Error detecting delegation shifts: {e}")
            raise AnalysisError(f"Error detecting delegation shifts: {e}")

    def find_influential_delegators(
        self, governance_data: Dict[str, Any], influence_threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Find the most influential delegators in the network.

        Args:
            governance_data: Dictionary containing governance data
            influence_threshold: Minimum influence threshold

        Returns:
            List of influential delegators with their metrics

        Raises:
            DataFormatError: If the input data doesn't have the expected format
            AnalysisError: If there's an error during analysis

        """
        try:
            if "delegations" not in governance_data:
                logger.error("No delegation data found in governance_data")
                raise DataFormatError(
                    "No delegation data found. Expected 'delegations' key"
                )

            if "token_holders" not in governance_data:
                logger.error("No token holder data found in governance_data")
                raise DataFormatError(
                    "No token holder data found. Expected 'token_holders' key"
                )

            delegations = governance_data["delegations"]
            token_holders = governance_data["token_holders"]

            # Create a delegation graph
            delegation_graph = self._create_delegation_graph(delegations, token_holders)

            # Calculate total token supply
            total_supply = sum(holder["balance"] for holder in token_holders)

            # Calculate influence for each delegator
            influential_delegators = []

            for holder in token_holders:
                address = holder["address"]

                # Skip if not a delegator
                if address not in delegation_graph or not delegation_graph.out_edges(
                    address
                ):
                    continue

                # Calculate delegated influence
                delegated_tokens = 0
                delegates = []

                for _, delegate in delegation_graph.out_edges(address):
                    edge_data = delegation_graph.get_edge_data(address, delegate)
                    delegated_tokens += edge_data.get("amount", 0)
                    delegates.append(
                        {"address": delegate, "amount": edge_data.get("amount", 0)}
                    )

                influence_ratio = delegated_tokens / total_supply

                if influence_ratio >= influence_threshold:
                    influential_delegators.append(
                        {
                            "address": address,
                            "balance": holder["balance"],
                            "delegated_tokens": delegated_tokens,
                            "influence_ratio": influence_ratio,
                            "delegates": delegates,
                        }
                    )

            # Sort by influence ratio
            influential_delegators.sort(
                key=lambda x: x["influence_ratio"], reverse=True
            )

            return influential_delegators

        except Exception as e:
            if isinstance(e, (DataFormatError, AnalysisError)):
                raise
            logger.error(f"Error finding influential delegators: {e}")
            raise AnalysisError(f"Error finding influential delegators: {e}")

    def _create_delegation_graph(
        self, delegations: List[Dict[str, Any]], token_holders: List[Dict[str, Any]]
    ) -> nx.DiGraph:
        """Create a directed graph representing the delegation network.

        Args:
            delegations: List of delegation records
            token_holders: List of token holder records

        Returns:
            NetworkX DiGraph representing the delegation network

        """
        # Create a directed graph
        graph = nx.DiGraph()

        # Create a mapping of addresses to balances for quick lookup
        address_to_balance = {
            holder["address"]: holder["balance"] for holder in token_holders
        }

        # Add all token holders as nodes
        for holder in token_holders:
            graph.add_node(holder["address"], balance=holder["balance"])

        # Add delegation edges
        for delegation in delegations:
            delegator = delegation["delegator"]
            delegatee = delegation["delegatee"]
            amount = delegation.get("amount", address_to_balance.get(delegator, 0))

            # Only add edge if both nodes exist
            if delegator in graph and delegatee in graph:
                graph.add_edge(delegator, delegatee, amount=amount)

        return graph

    def _calculate_delegation_metrics(
        self, graph: nx.DiGraph, token_holders: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate key metrics for the delegation network.

        Args:
            graph: NetworkX DiGraph representing the delegation network
            token_holders: List of token holder records

        Returns:
            Dictionary of calculated metrics

        """
        # Calculate total tokens
        total_tokens = sum(holder["balance"] for holder in token_holders)

        # Calculate delegation metrics
        metrics = {}

        # Percentage of tokens delegated
        delegated_tokens = sum(data["amount"] for _, _, data in graph.edges(data=True))
        metrics["delegation_rate"] = (
            (delegated_tokens / total_tokens) * 100 if total_tokens > 0 else 0
        )

        # Number of delegators (nodes with outgoing edges)
        delegators = [node for node in graph.nodes() if graph.out_degree(node) > 0]
        metrics["delegator_count"] = len(delegators)

        # Number of delegatees (nodes with incoming edges)
        delegatees = [node for node in graph.nodes() if graph.in_degree(node) > 0]
        metrics["delegatee_count"] = len(delegatees)

        # Percentage of holders that delegate
        metrics["delegator_percentage"] = (
            (len(delegators) / len(token_holders)) * 100 if token_holders else 0
        )

        # Average delegated amount per delegator
        metrics["avg_delegation_amount"] = (
            delegated_tokens / len(delegators) if delegators else 0
        )

        # Delegation concentration (Gini-like measure for delegatees)
        if delegatees:
            delegated_amounts = [
                sum(data["amount"] for _, _, data in graph.in_edges(node, data=True))
                for node in delegatees
            ]

            # Sort delegated amounts
            delegated_amounts.sort()

            # Calculate Gini coefficient for delegation
            n = len(delegated_amounts)
            indices = np.arange(1, n + 1)
            metrics["delegation_concentration"] = (
                2 * np.sum(indices * delegated_amounts)
            ) / (n * np.sum(delegated_amounts)) - (n + 1) / n
        else:
            metrics["delegation_concentration"] = 0

        return metrics

    def _identify_key_delegatees(
        self, graph: nx.DiGraph, token_holders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify key delegatees in the network.

        Args:
            graph: NetworkX DiGraph representing the delegation network
            token_holders: List of token holder records

        Returns:
            List of key delegatees with their metrics

        """
        # Calculate total tokens
        total_tokens = sum(holder["balance"] for holder in token_holders)

        # Create a mapping of addresses to balances for quick lookup
        address_to_balance = {
            holder["address"]: holder["balance"] for holder in token_holders
        }

        # Get all delegatees (nodes with incoming edges)
        delegatees = [node for node in graph.nodes() if graph.in_degree(node) > 0]

        key_delegatees = []

        for delegatee in delegatees:
            # Calculate total delegated to this delegatee
            delegated_to_node = sum(
                data["amount"] for _, _, data in graph.in_edges(delegatee, data=True)
            )

            # Calculate percentage of total supply
            percentage_of_supply = (
                (delegated_to_node / total_tokens) * 100 if total_tokens > 0 else 0
            )

            # Only include if above threshold
            if percentage_of_supply >= self.min_delegation_threshold * 100:
                # Get number of delegators
                delegator_count = graph.in_degree(delegatee)

                # Own balance
                own_balance = address_to_balance.get(delegatee, 0)

                # Total voting power (own + delegated)
                total_voting_power = own_balance + delegated_to_node

                key_delegatees.append(
                    {
                        "address": delegatee,
                        "own_balance": own_balance,
                        "delegated_amount": delegated_to_node,
                        "total_voting_power": total_voting_power,
                        "percentage_of_supply": percentage_of_supply,
                        "delegator_count": delegator_count,
                        "voting_power_multiplier": total_voting_power / own_balance
                        if own_balance > 0
                        else float("inf"),
                    }
                )

        # Sort by total voting power
        key_delegatees.sort(key=lambda x: x["total_voting_power"], reverse=True)

        return key_delegatees

    def _analyze_delegation_patterns(
        self, graph: nx.DiGraph, token_holders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze delegation patterns in the network.

        Args:
            graph: NetworkX DiGraph representing the delegation network
            token_holders: List of token holder records

        Returns:
            Dictionary with delegation pattern analysis

        """
        # Create holder categories by balance
        balance_categories = self._categorize_holders_by_balance(token_holders)

        # Analyze delegation patterns by category
        category_patterns = {}

        for category, holders in balance_categories.items():
            addresses = [holder["address"] for holder in holders]

            # Calculate category metrics
            delegators_in_category = [
                addr for addr in addresses if graph.out_degree(addr) > 0
            ]
            delegatees_in_category = [
                addr for addr in addresses if graph.in_degree(addr) > 0
            ]

            # Delegation rate for this category
            total_balance = sum(holder["balance"] for holder in holders)
            delegated_amount = sum(
                data["amount"]
                for u, v, data in graph.edges(data=True)
                if u in addresses
            )

            delegation_rate = (
                (delegated_amount / total_balance) * 100 if total_balance > 0 else 0
            )

            category_patterns[category] = {
                "holder_count": len(holders),
                "delegator_count": len(delegators_in_category),
                "delegatee_count": len(delegatees_in_category),
                "delegation_rate": delegation_rate,
                "avg_balance": total_balance / len(holders) if holders else 0,
                "total_balance": total_balance,
            }

        # Detect circular delegations
        circular_delegations = self._detect_circular_delegations(graph)

        # Identify whale delegations (large holders delegating to each other)
        whale_delegations = self._identify_whale_delegations(graph, token_holders)

        return {
            "category_patterns": category_patterns,
            "circular_delegations": circular_delegations,
            "whale_delegations": whale_delegations,
        }

    def _categorize_holders_by_balance(
        self, token_holders: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize token holders by their balance.

        Args:
            token_holders: List of token holder records

        Returns:
            Dictionary mapping categories to lists of holders

        """
        # Calculate total supply
        total_supply = sum(holder["balance"] for holder in token_holders)

        # Define categories
        categories = {
            "whale": {"min_pct": 0.01, "holders": []},
            "large": {"min_pct": 0.001, "holders": []},
            "medium": {"min_pct": 0.0001, "holders": []},
            "small": {"min_pct": 0, "holders": []},
        }

        # Categorize holders
        for holder in token_holders:
            percentage = holder["balance"] / total_supply if total_supply > 0 else 0

            if percentage >= categories["whale"]["min_pct"]:
                categories["whale"]["holders"].append(holder)
            elif percentage >= categories["large"]["min_pct"]:
                categories["large"]["holders"].append(holder)
            elif percentage >= categories["medium"]["min_pct"]:
                categories["medium"]["holders"].append(holder)
            else:
                categories["small"]["holders"].append(holder)

        # Return just the holders for each category
        return {
            "whale": categories["whale"]["holders"],
            "large": categories["large"]["holders"],
            "medium": categories["medium"]["holders"],
            "small": categories["small"]["holders"],
        }

    def _detect_circular_delegations(self, graph: nx.DiGraph) -> List[List[str]]:
        """Detect circular delegation patterns in the network.

        Args:
            graph: NetworkX DiGraph representing the delegation network

        Returns:
            List of circular delegation chains

        """
        # Find all simple cycles in the graph
        try:
            cycles = list(nx.simple_cycles(graph))

            # Filter out cycles with length < 2
            cycles = [cycle for cycle in cycles if len(cycle) >= 2]

            return cycles
        except nx.NetworkXNoCycle:
            return []

    def _identify_whale_delegations(
        self, graph: nx.DiGraph, token_holders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify delegations between whale addresses.

        Args:
            graph: NetworkX DiGraph representing the delegation network
            token_holders: List of token holder records

        Returns:
            List of whale-to-whale delegations

        """
        # Calculate total supply
        total_supply = sum(holder["balance"] for holder in token_holders)

        # Identify whale addresses (>1% of supply)
        whale_threshold = 0.01 * total_supply
        whale_addresses = {
            holder["address"]
            for holder in token_holders
            if holder["balance"] >= whale_threshold
        }

        # Find whale-to-whale delegations
        whale_delegations = []

        for u, v, data in graph.edges(data=True):
            if u in whale_addresses and v in whale_addresses:
                whale_delegations.append(
                    {
                        "delegator": u,
                        "delegatee": v,
                        "amount": data["amount"],
                        "percentage": (data["amount"] / total_supply) * 100
                        if total_supply > 0
                        else 0,
                    }
                )

        # Sort by amount
        whale_delegations.sort(key=lambda x: x["amount"], reverse=True)

        return whale_delegations

    def _compare_delegation_across_time(
        self, snapshots_analysis: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare delegation patterns across time.

        Args:
            snapshots_analysis: List of snapshot analyses

        Returns:
            Dictionary with comparison results

        """
        if len(snapshots_analysis) < 2:
            return {"metrics_trends": {}, "delegatee_changes": []}

        # Extract timestamps and metrics
        metrics_by_timestamp = {
            snapshot["timestamp"]: snapshot["analysis"]["metrics"]
            for snapshot in snapshots_analysis
        }

        # Create metrics trends
        metrics_trends = {}

        # Get all unique metric keys
        all_metrics = set()
        for metrics in metrics_by_timestamp.values():
            all_metrics.update(metrics.keys())

        # Create time series for each metric
        for metric in all_metrics:
            metrics_trends[metric] = {
                timestamp: metrics.get(metric, None)
                for timestamp, metrics in metrics_by_timestamp.items()
            }

        # Track changes in key delegatees
        delegatee_changes = []

        for i in range(1, len(snapshots_analysis)):
            current = snapshots_analysis[i]
            previous = snapshots_analysis[i - 1]

            changes = self._detect_key_delegatee_changes(
                previous["analysis"]["key_delegatees"],
                current["analysis"]["key_delegatees"],
            )

            if changes["added"] or changes["removed"] or changes["changed"]:
                delegatee_changes.append(
                    {
                        "from_timestamp": previous["timestamp"],
                        "to_timestamp": current["timestamp"],
                        "changes": changes,
                    }
                )

        return {
            "metrics_trends": metrics_trends,
            "delegatee_changes": delegatee_changes,
        }

    def _calculate_metrics_change(
        self, previous_metrics: Dict[str, float], current_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate change in metrics between two snapshots.

        Args:
            previous_metrics: Metrics from previous snapshot
            current_metrics: Metrics from current snapshot

        Returns:
            Dictionary with metric changes

        """
        changes = {}

        # Find all unique metric keys
        all_metrics = set(previous_metrics.keys()) | set(current_metrics.keys())

        for metric in all_metrics:
            prev_value = previous_metrics.get(metric, 0)
            curr_value = current_metrics.get(metric, 0)

            # Calculate absolute change
            abs_change = curr_value - prev_value

            # Calculate percentage change
            if prev_value != 0:
                pct_change = abs_change / prev_value
            else:
                pct_change = float("inf") if abs_change > 0 else 0

            changes[metric] = pct_change

        return changes

    def _detect_key_delegatee_changes(
        self,
        previous_delegatees: List[Dict[str, Any]],
        current_delegatees: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Detect changes in key delegatees between snapshots.

        Args:
            previous_delegatees: Key delegatees from previous snapshot
            current_delegatees: Key delegatees from current snapshot

        Returns:
            Dictionary with delegatee changes

        """
        # Extract addresses
        prev_addresses = {d["address"] for d in previous_delegatees}
        curr_addresses = {d["address"] for d in current_delegatees}

        # Find added and removed delegatees
        added = curr_addresses - prev_addresses
        removed = prev_addresses - curr_addresses

        # Find changed delegatees (significant change in voting power)
        changed = []

        for prev in previous_delegatees:
            for curr in current_delegatees:
                if prev["address"] == curr["address"]:
                    # Calculate percentage change in voting power
                    prev_power = prev["total_voting_power"]
                    curr_power = curr["total_voting_power"]

                    if prev_power > 0:
                        change_pct = (curr_power - prev_power) / prev_power

                        # If change is significant (>10%), add to changed list
                        if abs(change_pct) >= 0.1:
                            changed.append(
                                {
                                    "address": prev["address"],
                                    "previous_power": prev_power,
                                    "current_power": curr_power,
                                    "change_percentage": change_pct,
                                }
                            )

        # Determine if changes are significant
        significant = len(added) > 0 or len(removed) > 0 or len(changed) > 0

        return {
            "added": [{"address": addr} for addr in added],
            "removed": [{"address": addr} for addr in removed],
            "changed": changed,
            "significant": significant,
        }

    def _calculate_shift_metrics(self, shifts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics about delegation shifts.

        Args:
            shifts: List of detected shifts

        Returns:
            Dictionary with shift metrics

        """
        if not shifts:
            return {
                "total_shifts": 0,
                "avg_metrics_change": {},
                "max_metrics_change": {},
            }

        # Count total shifts
        total_shifts = len(shifts)

        # Collect all metric changes
        all_metrics = set()
        for shift in shifts:
            all_metrics.update(shift["metrics_change"].keys())

        # Calculate average and max change for each metric
        avg_changes = {}
        max_changes = {}

        for metric in all_metrics:
            changes = [
                abs(shift["metrics_change"].get(metric, 0))
                for shift in shifts
                if metric in shift["metrics_change"]
            ]

            if changes:
                avg_changes[metric] = sum(changes) / len(changes)
                max_changes[metric] = max(changes)
            else:
                avg_changes[metric] = 0
                max_changes[metric] = 0

        return {
            "total_shifts": total_shifts,
            "avg_metrics_change": avg_changes,
            "max_metrics_change": max_changes,
        }


def analyze_delegation_patterns(
    protocol_data: Dict[str, Any], min_threshold: float = 0.01
) -> Dict[str, Any]:
    """Analyze delegation patterns in a protocol.

    Args:
        protocol_data: Protocol data including governance data and delegations
        min_threshold: Minimum threshold for significant delegations

    Returns:
        Analysis results

    Raises:
        DataFormatError: If protocol data is missing required fields
        AnalysisError: If there's an error during analysis

    """
    try:
        analyzer = DelegationPatternAnalyzer(min_delegation_threshold=min_threshold)

        # Check if the required data is present
        if "governance_data" not in protocol_data:
            logger.error("Missing governance_data in protocol_data")
            raise DataFormatError("Protocol data missing 'governance_data' field")

        governance_data = protocol_data["governance_data"]

        # Analyze delegation network
        results = analyzer.analyze_delegation_network(governance_data)

        # Find influential delegators
        influential_delegators = analyzer.find_influential_delegators(governance_data)

        return {
            "delegation_network": results,
            "influential_delegators": influential_delegators,
        }

    except Exception as e:
        if isinstance(e, (DataFormatError, AnalysisError)):
            raise
        logger.error(f"Error analyzing delegation patterns: {e}")
        raise AnalysisError(f"Error analyzing delegation patterns: {e}")


def analyze_historical_delegation_patterns(
    historical_data: List[Dict[str, Any]],
    min_threshold: float = 0.01,
    shift_threshold: float = 0.1,
) -> Dict[str, Any]:
    """Analyze historical delegation patterns.

    Args:
        historical_data: List of historical snapshots
        min_threshold: Minimum threshold for significant delegations
        shift_threshold: Threshold for considering a change significant

    Returns:
        Historical analysis results

    Raises:
        DataFormatError: If historical data is missing required fields
        AnalysisError: If there's an error during analysis

    """
    try:
        analyzer = DelegationPatternAnalyzer(min_delegation_threshold=min_threshold)

        # Validate historical data
        if not historical_data or not isinstance(historical_data, list):
            logger.error("Invalid historical data provided")
            raise DataFormatError("Historical data must be a non-empty list")

        # Prepare historical governance data
        historical_governance_data = []

        for snapshot in historical_data:
            if "timestamp" not in snapshot or "data" not in snapshot:
                logger.error("Invalid snapshot format in historical data")
                raise DataFormatError(
                    "Each snapshot must have 'timestamp' and 'data' keys"
                )

            # Only include snapshots with governance data
            if "governance_data" in snapshot["data"]:
                # Create a new snapshot with governance data at the top level
                historical_governance_data.append(
                    {
                        "timestamp": snapshot["timestamp"],
                        "data": snapshot["data"]["governance_data"],
                    }
                )

        # Compare delegation patterns
        comparison_results = analyzer.compare_delegation_patterns(
            historical_governance_data
        )

        # Detect delegation shifts
        shift_results = analyzer.detect_delegation_shifts(
            historical_governance_data, shift_threshold=shift_threshold
        )

        return {"comparison": comparison_results, "shifts": shift_results}

    except Exception as e:
        if isinstance(e, (DataFormatError, AnalysisError)):
            raise
        logger.error(f"Error analyzing historical delegation patterns: {e}")
        raise AnalysisError(f"Error analyzing historical delegation patterns: {e}")
