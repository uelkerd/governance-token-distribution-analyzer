#!/usr/bin/env python3
"""
Analyze command implementation for the Governance Token Distribution Analyzer CLI.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional
import csv
from datetime import datetime

import click
import matplotlib.pyplot as plt
import pandas as pd

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
from governance_token_analyzer.core.metrics_collector import MetricsCollector


def execute_analyze_command(
    protocol: str,
    limit: int = 1000,
    output_format: str = "json",
    output_dir: str = "outputs",
    chart: bool = False,
    live_data: bool = True,
    verbose: bool = False,
) -> None:
    """
    Execute the analyze command to analyze token distribution for a specific protocol.

    Args:
        protocol: Protocol to analyze (compound, uniswap, aave)
        limit: Maximum number of token holders to analyze
        output_format: Output format (json, csv)
        output_dir: Directory to save output files
        chart: Whether to generate distribution charts
        live_data: Whether to use live blockchain data or simulated data
        verbose: Whether to display detailed metrics
    """
    # Handle long file paths gracefully
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        if "File name too long" in str(e):
            click.echo(f"❌ Error: Output path too long: {output_dir}")
            click.echo("Please specify a shorter output directory path")
            sys.exit(1)
        elif "Permission denied" in str(e):
            click.echo(f"❌ Error: Permission denied when creating directory: {output_dir}")
            sys.exit(1)
        else:
            click.echo(f"❌ Error creating output directory: {e}")
            sys.exit(1)

    # Initialize metrics collector
    metrics_collector = MetricsCollector(use_live_data=live_data)

    # Get token distribution data
    click.echo(f"📊 Analyzing {protocol.upper()} token distribution...")

    if live_data:
        click.echo("📡 Fetching live blockchain data...")
    else:
        click.echo("🎲 Generating simulated data...")

    # Collect protocol data
    data = metrics_collector.collect_protocol_data(protocol, limit=limit)

    # Calculate metrics
    if "token_holders" in data and "metrics" in data:
        balances = [
            float(holder.get("balance", 0)) for holder in data["token_holders"] if float(holder.get("balance", 0)) > 0
        ]
        metrics = data["metrics"]

        if balances:
            # Display metrics
            click.echo("\n📊 Token Distribution Analysis:")
            click.echo(f"  • Total holders analyzed: {len(balances)}")
            click.echo(f"  • Gini coefficient: {metrics.get('gini_coefficient', 'N/A')}")
            click.echo(f"  • Nakamoto coefficient: {metrics.get('nakamoto_coefficient', 'N/A')}")

            if verbose:
                click.echo(f"  • Shannon entropy: {metrics.get('shannon_entropy', 'N/A')}")
                click.echo(f"  • Herfindahl index: {metrics.get('herfindahl_index', 'N/A')}")
                click.echo(f"  • Theil index: {metrics.get('theil_index', 'N/A')}")
                click.echo(f"  • Palma ratio: {metrics.get('palma_ratio', 'N/A')}")

            # Save output file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"{protocol}_analysis_{timestamp}.{output_format}")

            if output_format == "json":
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
            elif output_format == "csv":
                df = pd.DataFrame(data["token_holders"])
                df.to_csv(output_file, index=False)

            click.echo(f"\n💾 Analysis saved to {output_file}")

            # Generate chart if requested
            if chart:
                click.echo("\n📈 Generating distribution chart...")
                chart_file = os.path.join(output_dir, f"{protocol}_distribution_{timestamp}.png")

                # Create visualization
                plt.figure(figsize=(10, 6))

                # Sort balances in descending order
                balances_sorted = sorted(balances, reverse=True)

                # Plot distribution
                plt.plot(range(1, len(balances_sorted) + 1), balances_sorted)
                plt.title(f"{protocol.upper()} Token Distribution")
                plt.xlabel("Holder Rank")
                plt.ylabel("Token Balance")
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # Add Lorenz curve on second axis
                ax2 = plt.twinx()
                total = sum(balances_sorted)
                lorenz = [sum(balances_sorted[: i + 1]) / total for i in range(len(balances_sorted))]
                ax2.plot(range(1, len(balances_sorted) + 1), lorenz, "r-", alpha=0.7)
                ax2.set_ylabel("Cumulative Share", color="r")

                # Save chart
                plt.savefig(chart_file)
                plt.close()

                click.echo(f"📊 Chart saved to {chart_file}")
        else:
            click.echo("❌ No positive balances found in the data")
    else:
        click.echo("❌ No token holders or metrics found in the data")
