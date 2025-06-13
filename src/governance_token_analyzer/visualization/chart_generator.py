"""Chart Generator Module for creating visualizations.

This module provides chart generation functionality for governance token analysis,
including distribution charts, historical trends, and protocol comparisons.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import os


class ChartGenerator:
    """Generates various charts and visualizations for governance token analysis."""

    def __init__(self):
        """Initialize the chart generator with default settings."""
        # Set up matplotlib style
        plt.style.use("default")
        sns.set_palette("husl")

        # Configure default figure settings
        self.default_figsize = (12, 8)
        self.default_dpi = 300

    def plot_distribution_analysis(self, balances: List[float], protocol: str, output_path: str) -> str:
        """Plot token distribution analysis charts.

        Args:
            balances: List of token balances
            protocol: Protocol name
            output_path: Path to save the chart

        Returns:
            Path to the saved chart
        """
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f"{protocol.upper()} Token Distribution Analysis", fontsize=16, fontweight="bold")

        # Sort balances for analysis
        sorted_balances = sorted(balances, reverse=True)

        # 1. Distribution histogram
        ax1.hist(balances, bins=50, alpha=0.7, color="skyblue", edgecolor="black")
        ax1.set_title("Token Balance Distribution")
        ax1.set_xlabel("Token Balance")
        ax1.set_ylabel("Number of Holders")
        ax1.set_yscale("log")

        # 2. Top holders concentration
        top_percentages = [1, 5, 10, 25, 50]
        concentrations = []
        total_supply = sum(balances)

        for pct in top_percentages:
            n_holders = max(1, int(len(balances) * pct / 100))
            concentration = sum(sorted_balances[:n_holders]) / total_supply * 100
            concentrations.append(concentration)

        ax2.bar(top_percentages, concentrations, color="lightcoral", alpha=0.7)
        ax2.set_title("Concentration by Top Holders")
        ax2.set_xlabel("Top % of Holders")
        ax2.set_ylabel("% of Total Supply")

        # 3. Cumulative distribution
        cumulative_pct = np.cumsum(sorted_balances) / total_supply * 100
        holder_pct = np.arange(1, len(balances) + 1) / len(balances) * 100

        ax3.plot(holder_pct, cumulative_pct, color="green", linewidth=2)
        ax3.set_title("Cumulative Token Distribution")
        ax3.set_xlabel("% of Holders")
        ax3.set_ylabel("% of Total Supply")
        ax3.grid(True, alpha=0.3)

        # 4. Lorenz curve for Gini coefficient visualization
        # Calculate Lorenz curve points
        sorted_balances_norm = np.array(sorted_balances) / sum(sorted_balances)
        cumulative_wealth = np.cumsum(sorted_balances_norm)
        cumulative_population = np.linspace(0, 1, len(balances))

        ax4.plot(
            [0] + list(cumulative_population),
            [0] + list(cumulative_wealth),
            color="blue",
            linewidth=2,
            label="Lorenz Curve",
        )
        ax4.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect Equality")
        ax4.set_title("Lorenz Curve (Inequality Visualization)")
        ax4.set_xlabel("Cumulative % of Holders")
        ax4.set_ylabel("Cumulative % of Tokens")
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.default_dpi, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_historical_trends(
        self, dates: List[str], values: List[float], metric: str, protocol: str, output_path: str
    ) -> str:
        """Plot historical trends for a metric.

        Args:
            dates: List of date strings
            values: List of metric values
            metric: Metric name
            protocol: Protocol name
            output_path: Path to save the chart

        Returns:
            Path to the saved chart
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        # Convert dates to datetime if they're strings
        if dates and isinstance(dates[0], str):
            try:
                dates = [datetime.fromisoformat(d.replace("Z", "+00:00")) for d in dates]
            except ValueError:
                # Fallback to simple indexing if date parsing fails
                dates = list(range(len(values)))

        ax.plot(dates, values, marker="o", linewidth=2, markersize=6, color="blue")
        ax.set_title(
            f"{protocol.upper()} - {metric.replace('_', ' ').title()} Over Time", fontsize=14, fontweight="bold"
        )
        ax.set_xlabel("Date")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.grid(True, alpha=0.3)

        # Format x-axis if dates are datetime objects
        if dates and hasattr(dates[0], "strftime"):
            plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.default_dpi, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_protocol_comparison(self, protocols: List[str], values: List[float], metric: str, output_path: str) -> str:
        """Plot protocol comparison chart.

        Args:
            protocols: List of protocol names
            values: List of metric values for each protocol
            metric: Metric name
            output_path: Path to save the chart

        Returns:
            Path to the saved chart
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        # Create bar chart
        bars = ax.bar(
            protocols, values, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"][: len(protocols)]
        )

        ax.set_title(f"Protocol Comparison - {metric.replace('_', ' ').title()}", fontsize=14, fontweight="bold")
        ax.set_xlabel("Protocol")
        ax.set_ylabel(metric.replace("_", " ").title())

        # Add value labels on top of bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2.0, height, f"{value:.4f}", ha="center", va="bottom")

        # Rotate x-axis labels if needed
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.default_dpi, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_concentration_metrics(self, metrics: Dict[str, float], protocol: str, output_path: str) -> str:
        """Plot concentration metrics in a dashboard format.

        Args:
            metrics: Dictionary of metric names and values
            protocol: Protocol name
            output_path: Path to save the chart

        Returns:
            Path to the saved chart
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f"{protocol.upper()} Concentration Metrics Dashboard", fontsize=16, fontweight="bold")

        # 1. Gini Coefficient gauge
        gini = metrics.get("gini_coefficient", 0)
        self._plot_gauge(ax1, gini, "Gini Coefficient", 0, 1)

        # 2. Nakamoto Coefficient
        nakamoto = metrics.get("nakamoto_coefficient", 0)
        ax2.bar(["Nakamoto Coefficient"], [nakamoto], color="lightgreen", alpha=0.7)
        ax2.set_title("Nakamoto Coefficient")
        ax2.set_ylabel("Number of Entities")

        # 3. HHI Index
        hhi = metrics.get("hhi_index", 0)
        ax3.bar(["HHI Index"], [hhi], color="orange", alpha=0.7)
        ax3.set_title("Herfindahl-Hirschman Index")
        ax3.set_ylabel("HHI Value")

        # 4. Concentration ratios
        concentration_metrics = {
            k: v for k, v in metrics.items() if "concentration" in k and k != "concentration_ratio"
        }
        if concentration_metrics:
            names = [k.replace("_", " ").title() for k in concentration_metrics.keys()]
            values = list(concentration_metrics.values())
            ax4.bar(names, values, color="lightcoral", alpha=0.7)
            ax4.set_title("Concentration Ratios")
            ax4.set_ylabel("Concentration (%)")
            plt.setp(ax4.get_xticklabels(), rotation=45, ha="right")

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.default_dpi, bbox_inches="tight")
        plt.close()

        return output_path

    def _plot_gauge(self, ax, value: float, title: str, min_val: float = 0, max_val: float = 1):
        """Plot a gauge chart for a single metric.

        Args:
            ax: Matplotlib axis
            value: Current value
            title: Chart title
            min_val: Minimum value for gauge
            max_val: Maximum value for gauge
        """
        # Create gauge visualization
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)

        # Plot the gauge background
        ax.plot(theta, r, "k-", linewidth=8, alpha=0.3)

        # Plot the value indicator
        value_theta = np.pi * (value - min_val) / (max_val - min_val)
        ax.plot([value_theta, value_theta], [0, 1], "r-", linewidth=6)

        # Add value text
        ax.text(np.pi / 2, 0.5, f"{value:.3f}", ha="center", va="center", fontsize=20, fontweight="bold")

        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlim(0, np.pi)
        ax.set_ylim(0, 1.2)
        ax.set_aspect("equal")
        ax.axis("off")
