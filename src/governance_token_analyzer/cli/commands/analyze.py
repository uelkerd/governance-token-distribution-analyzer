"""Analyze command implementation for the governance token analyzer CLI."""

import os
import sys
import json
from datetime import datetime
from typing import Any

import click
import pandas as pd
import matplotlib.pyplot as plt

from governance_token_analyzer.core.metrics_collector import MetricsCollector


def execute_analyze_command(
    protocol: str,
    limit: int = 1000,
    format: str = "json",
    output_dir: str = "outputs",
    chart: bool = False,
    live_data: bool = True,
    verbose: bool = False,
) -> None:
    """
    Execute the analyze command to analyze token distribution for a specific protocol.

    Args:
        protocol: Protocol to analyze
        limit: Maximum number of token holders to analyze
        format: Output format (json, csv)
        output_dir: Directory to save output files
        chart: Whether to generate distribution charts
        live_data: Whether to use live blockchain data
        verbose: Whether to enable verbose output
    """
    # Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        click.secho(f"❌ Error creating output directory: {e}", fg="red")
        sys.exit(1)

    # Initialize metrics collector
    metrics_collector = MetricsCollector(use_live_data=live_data)

    if live_data:
        click.echo("📡 Fetching live blockchain data...")
    else:
        click.echo("🎲 Generating simulated data...")

    # Collect protocol data with error handling
    try:
        data = metrics_collector.collect_protocol_data(protocol, limit=limit)
        if not data:
            click.secho(f"❌ Failed to collect data for {protocol}", fg="red")
            sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Error collecting data for {protocol}: {e}", fg="red")
        sys.exit(1)

    # Calculate metrics
    if "token_holders" in data and "metrics" in data:
        balances = []
        for holder_data in data["token_holders"]:
            balance = float(holder_data.get("balance", 0))
            if balance > 0:
                balances.append(balance)
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
            output_file = os.path.join(output_dir, f"{protocol}_analysis_{timestamp}.{format}")

            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
            elif format == "csv":
                # Save token holders
                df = pd.DataFrame(data["token_holders"])
                df.to_csv(output_file, index=False)

                # Save metrics as a separate CSV file
                metrics_file = os.path.join(output_dir, f"{protocol}_metrics_{timestamp}.csv")
                metrics_df = pd.DataFrame([metrics])
                metrics_df.to_csv(metrics_file, index=False)

                click.echo(f"\n💾 Analysis saved to {output_file}")
                click.echo(f"💾 Metrics saved to {metrics_file}")

            # Generate chart if requested
            if chart:
                click.echo("\n📈 Generating distribution chart...")
                chart_file = os.path.join(output_dir, f"{protocol}_distribution_{timestamp}.png")

                # Create visualization
                plt.figure(figsize=(10, 6))

                # Sort balances in descending order
                balances_sorted = sorted(balances, reverse=True)

                if not balances_sorted:
                    click.secho("⚠️ No balances to plot", fg="yellow")
                    plt.close()
                    return

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
                if total > 0:  # Prevent division by zero
                    lorenz = [sum(balances_sorted[: i + 1]) / total for i in range(len(balances_sorted))]
                    ax2.plot(range(1, len(balances_sorted) + 1), lorenz, "r-", alpha=0.7)
                    ax2.set_ylabel("Cumulative Share", color="r")
                else:
                    click.secho("⚠️ Cannot create Lorenz curve: Total balance is zero", fg="yellow")

                # Save chart
                plt.savefig(chart_file)
                plt.close()

                click.echo(f"📊 Chart saved to {chart_file}")
        else:
            click.echo("❌ No positive balances found in the data")
    else:
        click.echo("❌ No token holders or metrics found in the data")
