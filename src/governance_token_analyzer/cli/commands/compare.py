#!/usr/bin/env python3
"""
Compare protocols command implementation for the Governance Token Distribution Analyzer CLI.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

import click
import matplotlib.pyplot as plt
from governance_token_analyzer.core.config import PROTOCOLS
from governance_token_analyzer.core.historical_data import HistoricalDataManager
from governance_token_analyzer.core.metrics_collector import MetricsCollector


def execute_compare_protocols_command(
    protocols_arg: str,
    metric: str = "gini_coefficient",
    output_format: str = "json",
    output_dir: str = "outputs",
    chart: bool = False,
    detailed: bool = False,
    historical: bool = False,
    data_dir: str = "data/historical",
) -> None:
    """
    Execute the compare-protocols command to compare metrics across multiple protocols.

    Args:
        protocols_arg: Comma-separated list of protocols to compare or "all"
        metric: Primary metric for comparison
        output_format: Output format (json, html, png)
        output_dir: Directory to save output files
        chart: Whether to generate comparison charts
        detailed: Whether to include detailed metrics for each protocol
        historical: Whether to include historical data analysis
        data_dir: Directory containing historical data
    """
    # Process protocol list
    if protocols_arg.lower() == "all":
        protocol_list = list(PROTOCOLS.keys())
    else:
        protocol_list = [p.strip().lower() for p in protocols_arg.split(",")]
        # Validate protocols
        for p in protocol_list:
            if p not in PROTOCOLS:
                raise click.BadParameter(f"Unsupported protocol: {p}")

    click.echo(f"🔍 Comparing {len(protocol_list)} protocols: {', '.join(protocol_list).upper()}")

    # Initialize metrics collector
    metrics_collector = MetricsCollector(use_live_data=True)

    # Compare protocols
    comparison_data = metrics_collector.compare_protocols(protocol_list, metric)

    # Display comparison
    click.echo("\n📊 Protocol Comparison:")
    for p, data in comparison_data.items():
        click.echo(f"  • {p.upper()}: {data.get(metric, 'N/A')}")

    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.{output_format}")

    if output_format == "json":
        with open(output_file, "w") as f:
            json.dump(comparison_data, f, indent=2)
        click.echo(f"\n💾 Comparison saved to {output_file}")
    elif output_format == "html":
        # Generate HTML report
        html_content = f"""
        <html>
        <head>
            <title>Protocol Comparison</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Protocol Comparison</h1>
            <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <table>
                <tr>
                    <th>Protocol</th>
                    <th>{metric.replace("_", " ").title()}</th>
                </tr>
        """

        for p, data in comparison_data.items():
            html_content += f"""
                <tr>
                    <td>{p.upper()}</td>
                    <td>{data.get(metric, "N/A")}</td>
                </tr>
            """

        html_content += """
            </table>
        </body>
        </html>
        """

        with open(output_file, "w") as f:
            f.write(html_content)
        click.echo(f"\n💾 HTML report saved to {output_file}")
    elif output_format == "png":
        # Generate chart
        plt.figure(figsize=(10, 6))

        # Extract values and protocols
        protocols = list(comparison_data.keys())
        values = [comparison_data[p].get(metric, 0) for p in protocols]

        # Create bar chart
        plt.bar(protocols, values)
        plt.title(f"Protocol Comparison: {metric.replace('_', ' ').title()}")
        plt.xlabel("Protocol")
        plt.ylabel(metric.replace("_", " ").title())
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save chart
        plt.savefig(output_file)
        plt.close()

        click.echo(f"\n📊 Chart saved to {output_file}")

    # Add historical analysis if requested
    if historical:
        click.echo("\n📈 Adding historical analysis...")

        # Initialize data manager
        data_manager = HistoricalDataManager(data_dir)

        # Get historical data for each protocol
        historical_data_dict = {}
        for p in protocol_list:
            try:
                time_series = data_manager.get_time_series_data(p, metric)
                if not time_series.empty:
                    historical_data_dict[p] = time_series
                    click.echo(f"  ✓ Found historical data for {p.upper()}")
                else:
                    click.echo(f"  ⚠️ No historical data found for {p}")
            except Exception as e:
                click.echo(f"  ⚠️ Error loading historical data for {p}: {e}")

        if historical_data_dict:
            # Generate historical comparison chart
            historical_chart_file = os.path.join(output_dir, f"historical_comparison_{timestamp}.png")

            plt.figure(figsize=(12, 6))

            for p, ts_data in historical_data_dict.items():
                plt.plot(ts_data.index, ts_data[metric], label=p.upper())

            plt.title(f"Historical Comparison: {metric.replace('_', ' ').title()}")
            plt.xlabel("Date")
            plt.ylabel(metric.replace("_", " ").title())
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save chart
            plt.savefig(historical_chart_file)
            plt.close()

            click.echo(f"📊 Historical comparison chart saved to {historical_chart_file}")
        else:
            click.echo("⚠️ No historical data available for comparison")
