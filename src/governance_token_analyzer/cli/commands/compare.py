"""
Compare command implementation for CLI.

This module implements the protocol comparison functionality,
allowing users to compare metrics across multiple DeFi protocols.
"""

import os
from typing import List

import click
import matplotlib.pyplot as plt

from governance_token_analyzer.core.metrics_collector import MetricsCollector
from governance_token_analyzer.core.historical_data import HistoricalDataManager
from .utils import (
    ensure_output_directory,
    handle_cli_error,
    CLIError,
    display_protocol_comparison,
    filter_numeric_values,
    create_bar_chart,
    generate_timestamp,
)


def _generate_html_report(comparison_data: dict, metric: str) -> str:
    """Generate HTML content for comparison report."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protocol Comparison Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
            .protocol {{ margin: 10px 0; padding: 10px; background: #f8f9fa; }}
            .metric {{ font-weight: bold; color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1 class="header">Protocol Comparison: {metric.replace("_", " ").title()}</h1>
        <div class="protocols">
    """

    for protocol, data in comparison_data.items():
        value = data.get(metric, "N/A")
        html_content += f"""
            <div class="protocol">
                <h3>{protocol.upper()}</h3>
                <p><span class="metric">{metric.replace("_", " ").title()}:</span> {value}</p>
            </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content


def _save_html_report(html_content: str, output_file: str) -> None:
    """Save HTML report to file."""
    with open(output_file, "w") as f:
        f.write(html_content)
    click.echo(f"\n💾 HTML report saved to {output_file}")


def _create_historical_comparison_chart(
    protocol_list: List[str], metric: str, data_manager: HistoricalDataManager, output_dir: str, timestamp: str
) -> None:
    """Create historical comparison chart for protocols."""
    click.echo("\n📈 Adding historical analysis...")

    # Get historical data for each protocol
    historical_data_dict = {}
    for protocol in protocol_list:
        try:
            time_series = data_manager.get_time_series_data(protocol, metric)
            if not time_series.empty and metric in time_series.columns:
                historical_data_dict[protocol] = time_series
                click.echo(f"  ✓ Found historical data for {protocol.upper()}")
            else:
                if time_series.empty:
                    click.echo(f"  ⚠️ No historical data found for {protocol}")
                else:
                    click.secho(f"  ⚠️ Metric '{metric}' not found in historical data for {protocol}", fg="yellow")
        except Exception as e:
            click.echo(f"  ⚠️ Error loading historical data for {protocol}: {e}")

    if historical_data_dict:
        # Generate historical comparison chart
        historical_chart_file = os.path.join(output_dir, f"historical_comparison_{timestamp}.png")

        plt.figure(figsize=(12, 6))

        for protocol, ts_data in historical_data_dict.items():
            try:
                plt.plot(ts_data.index, ts_data[metric], label=protocol.upper())
            except Exception as e:
                click.secho(f"  ⚠️ Error plotting {protocol.upper()}: {e}", fg="yellow")

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


def execute_compare_protocols_command(
    protocols: str,
    metric: str = "gini_coefficient",
    format: str = "json",
    output_dir: str = "outputs",
    chart: bool = False,
    detailed: bool = False,
    historical: bool = False,
    data_dir: str = "data/historical",
) -> None:
    """
    Execute the compare-protocols command.

    Args:
        protocols: Comma-separated list of protocols to compare
        metric: Primary metric for comparison
        format: Output format (json, html, png)
        output_dir: Directory to save output files
        chart: Whether to generate comparison charts
        detailed: Whether to include detailed metrics
        historical: Whether to include historical analysis
        data_dir: Directory containing historical data
    """
    try:
        # Ensure output directory exists
        ensure_output_directory(output_dir)

        # Parse protocol list
        if protocols.lower() == "all":
            protocol_list = ["compound", "uniswap", "aave"]
        else:
            protocol_list = [p.strip() for p in protocols.split(",")]

        click.echo(f"🔍 Comparing {len(protocol_list)} protocols: {', '.join(protocol_list)}")

        # Initialize metrics collector
        metrics_collector = MetricsCollector(use_live_data=True)

        # Compare protocols
        comparison_data = metrics_collector.compare_protocols(protocol_list, metric)

        # Display comparison results
        display_protocol_comparison(comparison_data, metric)

        # Generate output file
        timestamp = generate_timestamp()

        if format == "json":
            import json

            output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.json")
            with open(output_file, "w") as f:
                json.dump(comparison_data, f, indent=2)
            click.echo(f"\n💾 Comparison data saved to {output_file}")

        elif format == "html":
            output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.html")
            html_content = _generate_html_report(comparison_data, metric)
            _save_html_report(html_content, output_file)

        elif format == "png" or chart:
            output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.png")
            protocols_list = list(comparison_data.keys())
            valid_protocols, valid_values = filter_numeric_values(protocols_list, comparison_data, metric)
            create_bar_chart(valid_protocols, valid_values, metric, output_file)

        # Add historical analysis if requested
        if historical:
            try:
                data_manager = HistoricalDataManager(data_dir)
                _create_historical_comparison_chart(protocol_list, metric, data_manager, output_dir, timestamp)
            except Exception as e:
                click.secho(f"⚠️ Error in historical analysis: {e}", fg="yellow")

    except CLIError:
        # CLIError is already handled by the utility function
        raise
    except Exception as e:
        handle_cli_error(e)
