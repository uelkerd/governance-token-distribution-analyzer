#!/usr/bin/env python3
"""
Historical analysis command implementation for the Governance Token Distribution Analyzer CLI.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

import click
import matplotlib.pyplot as plt
import numpy as np

from governance_token_analyzer.core.historical_data import HistoricalDataManager


def execute_historical_analysis_command(
    protocol: str,
    metric: str = "gini_coefficient",
    data_dir: str = "data/historical",
    output_dir: str = "outputs",
    output_format: str = "png",
    plot: bool = True,
) -> None:
    """
    Execute the historical-analysis command to analyze historical trends in token distribution metrics.

    Args:
        protocol: Protocol to analyze historical data for
        metric: Metric to analyze over time
        data_dir: Directory containing historical data
        output_dir: Directory to save analysis results
        output_format: Output format (json, png)
        plot: Whether to generate time series plots
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    click.echo(f"📈 Analyzing historical {metric} data for {protocol.upper()}...")

    # Initialize historical data manager
    data_manager = HistoricalDataManager(data_dir)

    # Get time series data for the protocol and metric
    try:
        time_series = data_manager.get_time_series_data(protocol, metric)

        if time_series.empty:
            click.echo(f"❌ No historical data found for {protocol.upper()}")
            sys.exit(1)

        click.echo(f"✅ Found {len(time_series)} historical data points")

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format == "json":
            # Convert time series to JSON format
            json_data = {
                "protocol": protocol,
                "metric": metric,
                "timestamps": time_series.index.strftime("%Y-%m-%d").tolist(),
                "values": time_series[metric].tolist(),
                "analysis_timestamp": datetime.now().isoformat(),
            }

            # Save JSON output
            output_file = os.path.join(output_dir, f"{protocol}_historical_{metric}_{timestamp}.json")
            with open(output_file, "w") as f:
                json.dump(json_data, f, indent=2)

            click.echo(f"💾 Historical data saved to {output_file}")

        if plot or output_format == "png":
            # Generate time series plot
            plt.figure(figsize=(12, 6))

            # Plot time series
            plt.plot(time_series.index, time_series[metric])

            # Add trend line
            if len(time_series) > 1:
                z = np.polyfit(range(len(time_series)), time_series[metric], 1)
                p = np.poly1d(z)
                plt.plot(time_series.index, p(range(len(time_series))), "r--", alpha=0.7)

            plt.title(f"{protocol.upper()} Historical {metric.replace('_', ' ').title()}")
            plt.xlabel("Date")
            plt.ylabel(metric.replace("_", " ").title())
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save plot
            if output_format == "png":
                output_file = os.path.join(output_dir, f"{protocol}_historical_{metric}_{timestamp}.png")
                plt.savefig(output_file)
                plt.close()
                click.echo(f"📊 Historical chart saved to {output_file}")
            else:
                plt.show()
                plt.close()

    except FileNotFoundError:
        click.echo(f"❌ No historical data directory found at {data_dir}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error analyzing historical data: {e}")
        sys.exit(1)
