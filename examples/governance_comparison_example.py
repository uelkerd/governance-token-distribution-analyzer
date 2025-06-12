#!/usr/bin/env python
"""
Governance Comparison Example

This script demonstrates how to use the governance token analyzer to compare
token distribution and governance participation across multiple protocols.

Usage:
    python examples/governance_comparison_example.py
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from governance_token_analyzer.core import (
    concentration_analysis,
    participation_analysis,
    cross_protocol_comparison,
)
from governance_token_analyzer.core.logging_config import setup_logging, get_logger
from governance_token_analyzer.core.metrics_collector import MetricsCollector

# Setup logging and metrics collection
setup_logging(log_level="INFO")
logger = get_logger(__name__)
metrics = MetricsCollector()


def main():
    """Main function to run the governance comparison example."""
    logger.info("Starting governance comparison example")

    # Protocols to analyze
    protocols = ["compound", "uniswap", "aave"]

    # Dictionary to store results for each protocol
    token_data = {}
    governance_data = {}
    concentration_results = {}
    participation_results = {}

    # Step 1: Load data for each protocol from sample JSON files
    for protocol in protocols:
        logger.info(f"Loading data for {protocol}")

        file_path = f"data/sample_data/{protocol}_sample_data.json"
        if not os.path.exists(file_path):
            logger.warning(f"Sample data file not found for {protocol} at {file_path}")
            continue

        with open(file_path, "r") as f:
            sample_data = json.load(f)

        # Prepare token holder DataFrame
        holders_list = sample_data.get("token_holders", [])
        if not holders_list:
            logger.warning(f"No token holder data in sample file for {protocol}")
            continue

        holders_df = pd.DataFrame(holders_list)
        holders_df.rename(
            columns={
                "TokenHolderAddress": "address",
                "TokenHolderQuantity": "balance",
                "TokenHolderPercentage": "percentage",
            },
            inplace=True,
        )

        holders_df["balance"] = pd.to_numeric(holders_df["balance"])
        holders_df["percentage"] = pd.to_numeric(holders_df["percentage"])

        # Store data
        token_data[protocol] = holders_df
        governance_data[protocol] = {
            "proposals": sample_data.get("proposals", []),
            "votes": sample_data.get("votes", []),
        }

    # Step 2: Analyze token concentration for each protocol
    for protocol, holders_df in token_data.items():
        logger.info(f"Analyzing token concentration for {protocol}")

        # Analyze concentration
        concentration_result = concentration_analysis.analyze_token_concentration(
            holders_df, protocol_name=protocol
        )

        # Store results
        concentration_results[protocol] = concentration_result

        # Print some key metrics
        metrics_data = concentration_result.get("metrics", {})
        concentration_metrics = metrics_data.get("concentration_metrics", {})

        if concentration_metrics:
            logger.info(
                f"{protocol.capitalize()} - Gini Coefficient: {concentration_metrics.get('gini_coefficient', 'N/A')}"
            )
            logger.info(
                f"{protocol.capitalize()} - Top 10 Concentration: {concentration_metrics.get('concentration_ratio_top10', 'N/A')}%"
            )

    # Step 3: Analyze governance participation for each protocol
    for protocol, holders_df in token_data.items():
        if protocol not in governance_data:
            continue

        logger.info(f"Analyzing governance participation for {protocol}")

        # Analyze participation
        participation_result = participation_analysis.analyze_governance_participation(
            governance_data[protocol], holders_df, protocol_name=protocol
        )

        # Additional analysis by holder size
        holder_size_result = (
            participation_analysis.analyze_participation_by_holder_size(
                governance_data[protocol], holders_df, protocol_name=protocol
            )
        )

        # Combine results
        if "metrics" in participation_result and "metrics" in holder_size_result:
            participation_result["metrics"].update(holder_size_result["metrics"])

        # Store results
        participation_results[protocol] = participation_result

        # Print some key metrics
        metrics_data = participation_result.get("metrics", {})
        participation_metrics = metrics_data.get("participation_metrics", {})

        if participation_metrics:
            logger.info(
                f"{protocol.capitalize()} - Participation Rate: {participation_metrics.get('overall_participation_rate', 'N/A')}%"
            )
            logger.info(
                f"{protocol.capitalize()} - Total Votes: {participation_metrics.get('total_votes', 'N/A')}"
            )

    # Step 4: Perform cross-protocol comparison
    logger.info("Performing cross-protocol comparison")

    # Create comprehensive comparison
    comparisons = cross_protocol_comparison.create_comprehensive_comparison(
        concentration_results, participation_results
    )

    # Identify governance patterns
    patterns = cross_protocol_comparison.identify_governance_patterns(comparisons)

    # Generate comparative rankings
    rankings = cross_protocol_comparison.generate_comparative_rankings(comparisons)

    # Step 5: Visualize results
    if "combined" in comparisons:
        logger.info("Visualizing comparison results")
        visualize_comparisons(comparisons)

    # Step 6: Print insights
    if "insights" in patterns:
        logger.info("Key insights from cross-protocol analysis:")
        for key, insight in patterns["insights"].items():
            logger.info(f"- {insight.get('interpretation', '')}")

    # Print performance metrics
    logger.info(f"API call metrics: {metrics.get_metrics()}")
    logger.info("Governance comparison example completed")


def visualize_comparisons(comparisons):
    """
    Create visualizations of the protocol comparisons.

    Args:
        comparisons: Dictionary containing comparison DataFrames
    """
    # Set up the visualization style
    sns.set(style="whitegrid")

    # Get the combined comparison DataFrame
    combined_df = comparisons.get("combined")

    if combined_df is None or combined_df.empty:
        logger.warning("No combined data available for visualization")
        return

    # Create a directory for plots if it doesn't exist
    os.makedirs("plots", exist_ok=True)

    # 1. Concentration metrics comparison
    concentration_cols = ["gini_coefficient", "concentration_ratio_top10"]
    if all(col in combined_df.columns for col in concentration_cols):
        plt.figure(figsize=(10, 6))

        # Bar chart of Gini coefficients
        ax = sns.barplot(x="protocol", y="gini_coefficient", data=combined_df)
        ax.set_title("Token Concentration (Gini Coefficient) by Protocol")
        ax.set_ylabel("Gini Coefficient (0-1)")
        ax.set_xlabel("Protocol")

        # Save plot
        plt.tight_layout()
        plt.savefig("plots/gini_coefficient_comparison.png")
        plt.close()

        # Bar chart of top 10 concentration
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x="protocol", y="concentration_ratio_top10", data=combined_df)
        ax.set_title("Top 10 Holder Concentration by Protocol")
        ax.set_ylabel("Percentage of Total Supply")
        ax.set_xlabel("Protocol")

        # Save plot
        plt.tight_layout()
        plt.savefig("plots/top10_concentration_comparison.png")
        plt.close()

    # 2. Participation metrics comparison
    participation_cols = ["participation_rate", "voter_participation_rate"]
    if all(col in combined_df.columns for col in participation_cols):
        plt.figure(figsize=(10, 6))

        # Bar chart of participation rates
        ax = sns.barplot(x="protocol", y="participation_rate", data=combined_df)
        ax.set_title("Governance Participation Rate by Protocol")
        ax.set_ylabel("Participation Rate (%)")
        ax.set_xlabel("Protocol")

        # Save plot
        plt.tight_layout()
        plt.savefig("plots/participation_rate_comparison.png")
        plt.close()

    # 3. Correlation matrix if available
    if "correlation_matrix" in comparisons:
        corr_matrix = comparisons["correlation_matrix"]

        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        ax = sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            linewidths=0.5,
        )
        ax.set_title("Correlation Matrix of Governance Metrics")

        # Save plot
        plt.tight_layout()
        plt.savefig("plots/correlation_matrix_comparison.png")
        plt.close()


if __name__ == "__main__":
    main()
