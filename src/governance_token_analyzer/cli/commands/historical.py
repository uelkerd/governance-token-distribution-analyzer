#!/usr/bin/env python3
"""
Historical analysis command implementation for CLI.

This module implements historical trend analysis functionality,
allowing users to analyze time series data for governance metrics.
"""

import os
from typing import Dict, Any, List, Optional

import click
import pandas as pd

from governance_token_analyzer.core.historical_data import HistoricalDataManager
from governance_token_analyzer.visualization.historical_charts import create_time_series_chart
from .utils import ensure_output_directory, handle_cli_error, CLIError, generate_timestamp


def _create_time_series_plot(time_series: pd.DataFrame, protocol: str, metric: str, output_file: str) -> None:
    """Create and save a time series plot with trend line."""
    if time_series.empty:
        raise CLIError(f"No historical data available for {protocol} {metric}")

    if metric not in time_series.columns:
        raise CLIError(f"Metric '{metric}' not found in historical data for {protocol}")

    # Create the plot
    create_time_series_chart(
        time_series=time_series,
        output_path=output_file,
        title=f"{protocol.upper()} Historical {metric.replace('_', ' ').title()}",
    )

    click.echo(f"📊 Time series plot saved to {output_file}")


def _export_time_series_data(time_series: pd.DataFrame, protocol: str, metric: str, output_file: str) -> None:
    """Export time series data to JSON file."""
    if time_series.empty:
        raise CLIError(f"No historical data available for {protocol} {metric}")

    if metric not in time_series.columns:
        raise CLIError(f"Metric '{metric}' not found in historical data for {protocol}")

    # Convert to JSON
    try:
        # Convert index to string format for JSON serialization
        time_series_json = time_series.reset_index().to_json(orient="records", date_format="iso")

        # Write to file
        with open(output_file, "w") as f:
            f.write(time_series_json)

        click.echo(f"💾 Time series data saved to {output_file}")
    except Exception as e:
        raise CLIError(f"Error exporting time series data: {e}")


def execute_historical_analysis_command(
    protocol: str,
    metric: str = "gini_coefficient",
    data_dir: str = "data/historical",
    output_dir: str = "outputs",
    output_format: str = "png",
    plot: bool = True,
) -> None:
    """
    Execute the historical-analysis command.

    Args:
        protocol: Protocol to analyze historical data for
        metric: Metric to analyze over time
        data_dir: Directory containing historical data
        output_dir: Directory to save analysis results
        output_format: Output format (json, png)
        plot: Whether to generate time series plots
    """
    try:
        # Ensure output directory exists
        ensure_output_directory(output_dir)

        click.echo(f"📈 Analyzing historical {metric} data for {protocol.upper()}...")

        # Initialize historical data manager
        data_manager = HistoricalDataManager(data_dir)

        # Get time series data
        try:
            time_series = data_manager.get_time_series_data(protocol, metric)
        except Exception as e:
            raise CLIError(f"Error loading historical data: {e}")

        # Check if we have data
        if time_series.empty:
            raise CLIError(f"No historical data found for {protocol}")

        # Display summary statistics
        click.echo(f"📊 Found {len(time_series)} historical data points")

        if metric in time_series.columns:
            latest = time_series[metric].iloc[-1] if not time_series.empty else "N/A"
            earliest = time_series[metric].iloc[0] if not time_series.empty else "N/A"

            click.echo(f"  ✓ Latest {metric}: {latest}")
            click.echo(f"  ✓ Earliest {metric}: {earliest}")

            # Calculate change
            if isinstance(latest, (int, float)) and isinstance(earliest, (int, float)):
                change = latest - earliest
                change_pct = (change / earliest) * 100 if earliest != 0 else float("inf")

                if change > 0:
                    click.echo(f"  ↗️ Increase: {change:.4f} ({change_pct:.2f}%)")
                elif change < 0:
                    click.echo(f"  ↘️ Decrease: {change:.4f} ({change_pct:.2f}%)")
                else:
                    click.echo("  ↔️ No change")
        else:
            click.echo(f"⚠️ Metric '{metric}' not found in historical data")

        # Generate output based on format
        timestamp = generate_timestamp()  # Use the utility function for timestamp
        if output_format == "png" and plot:
            output_file = os.path.join(output_dir, f"{protocol}_{metric}_{timestamp}.png")  # Add timestamp
            _create_time_series_plot(time_series, protocol, metric, output_file)
        elif output_format == "json":
            output_file = os.path.join(output_dir, f"{protocol}_{metric}_historical_{timestamp}.json")  # Add timestamp
            _export_time_series_data(time_series, protocol, metric, output_file)

    except CLIError:
        # CLIError is already handled by the utility function
        raise
    except Exception as e:
        handle_cli_error(e)
