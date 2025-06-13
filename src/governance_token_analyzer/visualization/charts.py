"""Charts Module for visualizing governance token data.
This module provides functions to create various visualizations
for token distribution and governance metrics.
"""

import logging
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from ..core.exceptions import VisualizationError

# Configure logging
logger = logging.getLogger(__name__)


def create_distribution_comparison(
    *dfs: pd.DataFrame, title: str = "Token Holder Distribution Comparison"
) -> plt.Figure:
    """Create a comparison chart of token holder distributions for multiple protocols.

    Args:
        *dfs: DataFrames containing token holder data for different protocols
        title: Chart title

    Returns:
        Matplotlib Figure object

    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot each protocol's distribution
    for i, df in enumerate(dfs):
        if "protocol" in df.columns:
            protocol_name = df["protocol"].iloc[0]
        else:
            protocol_name = f"Protocol {i + 1}"

        # Sort by balance and calculate cumulative percentage
        sorted_df = df.sort_values(by="balance", ascending=False).reset_index(drop=True)
        sorted_df["cumulative_percentage"] = sorted_df["percentage"].cumsum()

        # Plot the Lorenz curve
        x = np.linspace(0, 100, len(sorted_df))
        ax.plot(x, sorted_df["cumulative_percentage"], label=protocol_name)

    # Add perfect equality line
    ax.plot([0, 100], [0, 100], "k--", alpha=0.5, label="Perfect Equality")

    # Set labels and title
    ax.set_xlabel("Percentage of Token Holders")
    ax.set_ylabel("Cumulative Percentage of Tokens")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def create_metrics_comparison(
    metrics_dict: Dict[str, Dict[str, float]],
    title: str = "Governance Metrics Comparison",
) -> plt.Figure:
    """Create a bar chart comparing governance metrics across protocols.

    Args:
        metrics_dict: Dictionary mapping protocol names to their metrics
        title: Chart title

    Returns:
        Matplotlib Figure object

    """
    # Extract protocol names and metrics
    protocols = list(metrics_dict.keys())
    metrics = list(metrics_dict[protocols[0]].keys())

    # Create figure with subplots for each metric
    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 4 * len(metrics)))

    # If there's only one metric, axes will not be a list
    if len(metrics) == 1:
        axes = [axes]

    # Plot each metric
    for i, metric in enumerate(metrics):
        ax = axes[i]
        values = [metrics_dict[protocol].get(metric, 0) for protocol in protocols]

        # Create bar chart
        bars = ax.bar(protocols, values)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center",
                va="bottom",
            )

        # Set labels and title
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_title(f"{metric.replace('_', ' ').title()} by Protocol")
        ax.grid(True, alpha=0.3, axis="y")

    # Set overall title
    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    return fig


def create_participation_trend(
    participation_data: Dict[str, List[Dict[str, Any]]],
    title: str = "Governance Participation Trends",
) -> plt.Figure:
    """Create a line chart showing governance participation trends over time.

    Args:
        participation_data: Dictionary mapping protocol names to their participation data
        title: Chart title

    Returns:
        Matplotlib Figure object

    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot each protocol's participation trend
    for protocol, data in participation_data.items():
        # Extract dates and participation rates
        dates = [item.get("date") for item in data]
        rates = [item.get("participation_rate", 0) for item in data]

        # Plot the trend
        ax.plot(dates, rates, marker="o", label=protocol)

    # Set labels and title
    ax.set_xlabel("Date")
    ax.set_ylabel("Participation Rate (%)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    fig.tight_layout()

    return fig


def create_whale_influence_chart(
    whale_data: Dict[str, Dict[str, float]], title: str = "Whale Influence by Protocol"
) -> plt.Figure:
    """Create a chart showing whale influence metrics by protocol.

    Args:
        whale_data: Dictionary mapping protocol names to their whale metrics
        title: Chart title

    Returns:
        Matplotlib Figure object

    """
    # Extract protocol names
    protocols = list(whale_data.keys())

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # Plot whale percentage of holders
    whale_percentages = [
        whale_data[protocol].get("whale_percentage", 0) for protocol in protocols
    ]
    ax1.bar(protocols, whale_percentages)
    ax1.set_ylabel("Percentage of Holders (%)")
    ax1.set_title("Whales as Percentage of Total Holders")

    # Plot whale holdings percentage
    holdings_percentages = [
        whale_data[protocol].get("holdings_percentage", 0) for protocol in protocols
    ]
    ax2.bar(protocols, holdings_percentages)
    ax2.set_ylabel("Percentage of Total Supply (%)")
    ax2.set_title("Whale Holdings as Percentage of Total Supply")

    # Set overall title
    fig.suptitle(title, fontsize=16)

    # Add grid lines
    ax1.grid(True, alpha=0.3, axis="y")
    ax2.grid(True, alpha=0.3, axis="y")

    fig.tight_layout(rect=[0, 0, 1, 0.95])

    return fig


def save_chart(fig: plt.Figure, filename: str, dpi: int = 300) -> None:
    """Save a chart to a file.

    Args:
        fig: Matplotlib Figure object
        filename: Output filename
        dpi: Resolution in dots per inch

    Returns:
        None

    """
    fig.savefig(filename, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def create_delegation_network_visualization(
    delegation_graph: nx.DiGraph,
    key_delegatees: List[Dict[str, Any]] = None,
    title: str = "Delegation Network",
    figsize: Tuple[int, int] = (12, 10),
) -> plt.Figure:
    """Create a visualization of the delegation network.

    Args:
        delegation_graph: NetworkX DiGraph representing the delegation network
        key_delegatees: List of key delegatees to highlight
        title: Title for the visualization
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Extract key delegatee addresses if provided
        key_addresses = set()
        if key_delegatees:
            key_addresses = {d["address"] for d in key_delegatees}

        # Set node colors based on whether they're key delegatees
        node_colors = []
        for node in delegation_graph.nodes():
            if node in key_addresses:
                node_colors.append("tab:red")
            elif delegation_graph.in_degree(node) > 0:
                node_colors.append("tab:orange")
            elif delegation_graph.out_degree(node) > 0:
                node_colors.append("tab:blue")
            else:
                node_colors.append("tab:gray")

        # Set node sizes based on balance
        node_sizes = []
        for node in delegation_graph.nodes():
            balance = delegation_graph.nodes[node].get("balance", 0)
            node_sizes.append(100 + (balance / 1000))

        # Set edge widths based on amount
        edge_widths = []
        for _, _, data in delegation_graph.edges(data=True):
            amount = data.get("amount", 0)
            edge_widths.append(0.5 + (amount / 10000))

        # Create a spring layout
        pos = nx.spring_layout(delegation_graph, k=0.3, iterations=50)

        # Draw nodes
        nx.draw_networkx_nodes(
            delegation_graph,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.8,
        )

        # Draw edges
        nx.draw_networkx_edges(
            delegation_graph,
            pos,
            ax=ax,
            width=edge_widths,
            alpha=0.6,
            edge_color="tab:gray",
            arrowsize=15,
            connectionstyle="arc3,rad=0.1",
        )

        # Add labels to key delegatees
        labels = {}
        for node in delegation_graph.nodes():
            if node in key_addresses:
                # Shorten address for display
                short_addr = f"{node[:6]}...{node[-4:]}"
                labels[node] = short_addr

        nx.draw_networkx_labels(
            delegation_graph, pos, labels=labels, font_size=10, font_weight="bold"
        )

        # Add legend
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="tab:red",
                markersize=10,
                label="Key Delegatee",
            ),
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="tab:orange",
                markersize=10,
                label="Delegatee",
            ),
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="tab:blue",
                markersize=10,
                label="Delegator",
            ),
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="tab:gray",
                markersize=10,
                label="No Delegation",
            ),
        ]

        ax.legend(handles=legend_elements, loc="upper right")

        # Set title and remove axes
        ax.set_title(title, fontsize=16)
        ax.set_axis_off()

        return fig

    except Exception as e:
        logger.error(f"Failed to create delegation network visualization: {e}")
        raise VisualizationError(
            f"Failed to create delegation network visualization: {e}"
        )


def create_delegation_metrics_chart(
    metrics: Dict[str, float],
    title: str = "Delegation Metrics",
    figsize: Tuple[int, int] = (10, 6),
) -> plt.Figure:
    """Create a chart visualizing delegation metrics.

    Args:
        metrics: Dictionary of delegation metrics
        title: Chart title
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Extract metrics to display
        display_metrics = {
            "Delegation Rate (%)": metrics.get("delegation_rate", 0),
            "Delegator %": metrics.get("delegator_percentage", 0),
            "Delegation Concentration": metrics.get("delegation_concentration", 0)
            * 100,
        }

        # Create bar chart
        bars = ax.bar(
            display_metrics.keys(),
            display_metrics.values(),
            color=["tab:blue", "tab:orange", "tab:red"],
        )

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 1,
                f"{height:.1f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Set labels and title
        ax.set_ylabel("Percentage")
        ax.set_title(title, fontsize=14)
        ax.grid(axis="y", alpha=0.3)

        # Set y-axis limit
        ax.set_ylim(0, max(display_metrics.values()) * 1.2)

        # Add metrics counts as text
        delegator_count = metrics.get("delegator_count", 0)
        delegatee_count = metrics.get("delegatee_count", 0)
        avg_delegation = metrics.get("avg_delegation_amount", 0)

        metrics_text = (
            f"Delegators: {delegator_count}\n"
            f"Delegatees: {delegatee_count}\n"
            f"Avg. Delegation: {avg_delegation:.2f}"
        )

        # Add text box
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        ax.text(
            0.05,
            0.95,
            metrics_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=props,
        )

        return fig

    except Exception as e:
        logger.error(f"Failed to create delegation metrics chart: {e}")
        raise VisualizationError(f"Failed to create delegation metrics chart: {e}")
