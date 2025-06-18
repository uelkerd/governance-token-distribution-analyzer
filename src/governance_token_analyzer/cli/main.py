#!/usr/bin/env python3
"""
Governance Token Distribution Analyzer CLI

Command-line interface for analyzing token distribution patterns,
concentration metrics, and governance participation across protocols.
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

import click
import pandas as pd
import matplotlib.pyplot as plt

# Add the src directory to Python path for imports
try:
    # Import core functionality
    from governance_token_analyzer.core.api_client import APIClient
    from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
    from governance_token_analyzer.core.config import PROTOCOLS
    from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
    from governance_token_analyzer.core import historical_data
    from governance_token_analyzer.visualization.report_generator import ReportGenerator

    # Import from core.voting_block_analysis instead of non-existent analysis module
    from governance_token_analyzer.core.voting_block_analysis import VotingBlockAnalyzer
except ImportError as e:
    click.echo(f"Error importing modules: {e}", err=True)
    # Don't exit here to allow tests to import the module without running commands
    if __name__ == "__main__":
        sys.exit(1)

# Configuration constants
SUPPORTED_PROTOCOLS = list(PROTOCOLS.keys())
SUPPORTED_METRICS = [
    "gini_coefficient",
    "nakamoto_coefficient",
    "shannon_entropy",
    "herfindahl_index",
    "participation_rate",
]
SUPPORTED_FORMATS = ["json", "csv", "html", "png"]


# CLI Group Configuration
@click.group(context_settings={"max_content_width": 120})
@click.version_option(version="1.0.0", prog_name="gova")
@click.pass_context
def cli(ctx):
    """🏛️ Governance Token Distribution Analyzer

    A comprehensive tool for analyzing token concentration,
    governance participation, and voting power distribution
    across DeFi protocols.

    Examples:

    [1] gova analyze -p compound -f json

    [2] gova compare-protocols -p compound,uniswap -m gini_coefficient

    [3] gova generate-report -p compound -f html

    [4] gova status -a -t

    Common Arguments:

    [A] -p, --protocol       Protocol to analyze (compound, uniswap, aave)

    [B] -f, --format         Output format (json, csv, html, png)

    [C] -o, --output-dir     Directory to save output files

    [D] -v, --verbose        Enable verbose output

    [E] -c, --chart          Generate charts/visualizations

    [F] -h, --help           Show command help
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


class ProtocolChoice(click.Choice):
    """Custom choice class for protocol selection."""

    def __init__(self):
        super().__init__(SUPPORTED_PROTOCOLS, case_sensitive=False)


def validate_output_dir(ctx, param, value):
    """Validate and create output directory if it doesn't exist."""
    if value:
        try:
            os.makedirs(value, exist_ok=True)
            return value
        except OSError as e:
            raise click.BadParameter(f"Cannot create output directory '{value}': {e}")
    return value


def validate_positive_int(ctx, param, value):
    """Validate that the value is a positive integer."""
    if value is not None and value <= 0:
        raise click.BadParameter(f"Value must be a positive integer, got: {value}")
    return value


# ANALYZE COMMAND
@cli.command(
    help="📊 Analyze token distribution for a specific protocol (-p) with concentration metrics and distribution charts."
)
@click.option(
    "--protocol", "-p", type=ProtocolChoice(), required=True, help="Protocol to analyze (compound, uniswap, aave)"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=1000,
    callback=validate_positive_int,
    help="Maximum number of token holders to analyze (default: 1000)",
)
@click.option(
    "--format", "-f", type=click.Choice(["json", "csv"]), default="json", help="Output format (default: json)"
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save output files (default: outputs)",
)
@click.option("--chart", "-c", is_flag=True, help="Generate distribution charts")
@click.option(
    "--live-data",
    "-L",
    is_flag=True,
    default=True,
    help="Use live blockchain data (default)",
)
@click.option(
    "--simulated-data",
    "-S",
    is_flag=True,
    help="Use simulated data instead of live data",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output with detailed metrics")
def analyze(protocol, limit, output_format, output_dir, chart, live_data, simulated_data, verbose):
    """📊 Analyze token distribution for a specific protocol.

    Calculates concentration metrics and generates detailed analysis reports.

    Options:
      -p, --protocol             Protocol to analyze (compound, uniswap, aave)
      -l, --limit                Maximum number of token holders to analyze (default: 1000)
      -f, --format               Output format (default: json)
      -o, --output-dir           Directory to save output files (default: outputs)
      -c, --chart                Generate distribution charts
      -L, --live-data            Use live blockchain data (default)
      -S, --simulated-data       Use simulated data instead of live data
      -v, --verbose              Enable verbose output with detailed metrics

    Examples:
      gova analyze -p compound -f json
      gova analyze -p uniswap -c -v
      gova analyze -p aave -S
    """
    # Handle mutually exclusive options
    if live_data and simulated_data:
        raise click.UsageError(
            "Options --live-data and --simulated-data are mutually exclusive. Please specify only one."
        )

    # Set live_data based on simulated_data flag
    if simulated_data:
        live_data = False

    try:
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
                
        # Initialize components
        api_client = APIClient()
        
        # Get token distribution data
        click.echo(f"📊 Analyzing {protocol.upper()} token distribution...")
        
        if live_data:
            click.echo("📡 Fetching live blockchain data...")
            data = api_client.get_protocol_data(protocol, limit=limit)
        else:
            click.echo("🎲 Generating simulated data...")
            simulator = TokenDistributionSimulator()
            data = simulator.generate_protocol_data(protocol, num_holders=limit)
        
        # Calculate metrics
        if "token_holders" in data:
            balances = [float(holder.get("balance", 0)) for holder in data["token_holders"] if float(holder.get("balance", 0)) > 0]
            
            if balances:
                metrics = calculate_all_concentration_metrics(balances)
                data["metrics"] = metrics
                
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
                    lorenz = [sum(balances_sorted[:i+1])/total for i in range(len(balances_sorted))]
                    ax2.plot(range(1, len(balances_sorted) + 1), lorenz, 'r-', alpha=0.7)
                    ax2.set_ylabel("Cumulative Share", color='r')
                    
                    # Save chart
                    plt.savefig(chart_file)
                    plt.close()
                    
                    click.echo(f"📊 Chart saved to {chart_file}")
            else:
                click.echo("❌ No positive balances found in the data")
        else:
            click.echo("❌ No token holders found in the data")
    except click.Abort:
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# COMPARE PROTOCOLS COMMAND
@cli.command(
    "compare-protocols",
    help="🔍 Compare token distribution metrics (-m) across multiple protocols (-p) with visualization options.",
)
@click.option(
    "--protocols",
    "-p",
    type=str,
    required=True,
    help='Comma-separated list of protocols to compare (e.g., compound,uniswap,aave) or "all"',
)
@click.option(
    "--metric",
    "-m",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Primary metric for comparison (default: gini_coefficient)",
)
@click.option(
    "--format", "-f", type=click.Choice(["json", "html", "png"]), default="json", help="Output format (default: json)"
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save output files (default: outputs)",
)
@click.option("--chart", "-c", is_flag=True, help="Generate comparison charts")
@click.option("--detailed", "-d", is_flag=True, help="Include detailed metrics for each protocol")
@click.option("--historical", "-H", is_flag=True, help="Include historical data analysis")
@click.option(
    "--data-dir",
    "-D",
    type=str,
    default="data/historical",
    help="Directory containing historical data (default: data/historical)",
)
def compare_protocols(protocols, metric, output_format, output_dir, chart, detailed, historical, data_dir):
    """🔍 Compare token distribution metrics across multiple protocols.

    Analyzes and visualizes differences in concentration and governance metrics.

    Options:
      -p, --protocols            Comma-separated list of protocols to compare or "all"
      -m, --metric               Primary metric for comparison (default: gini_coefficient)
      -f, --format               Output format (default: json)
      -o, --output-dir           Directory to save output files (default: outputs)
      -c, --chart                Generate comparison charts
      -d, --detailed             Include detailed metrics for each protocol
      -H, --historical           Include historical data analysis
      -D, --data-dir             Directory containing historical data (default: data/historical)

    Examples:
      gova compare-protocols -p compound,uniswap -m gini_coefficient
      gova compare-protocols -p all -c -d
      gova compare-protocols -p compound,aave -H
    """
    try:
        # Process protocol list
        if protocols.lower() == "all":
            protocol_list = SUPPORTED_PROTOCOLS
        else:
            protocol_list = [p.strip().lower() for p in protocols.split(",")]
            # Validate protocols
            for p in protocol_list:
                if p not in SUPPORTED_PROTOCOLS:
                    raise click.BadParameter(f"Unsupported protocol: {p}")
        
        click.echo(f"🔍 Comparing {len(protocol_list)} protocols: {', '.join(protocol_list).upper()}")
        
        # Initialize API client
        api_client = APIClient()
        
        # Collect data for each protocol
        protocol_data = {}
        for p in protocol_list:
            click.echo(f"📊 Analyzing {p.upper()}...")
            try:
                data = api_client.get_protocol_data(p)
                protocol_data[p] = data
            except Exception as e:
                click.echo(f"⚠️ Error getting data for {p}: {e}")
                protocol_data[p] = {"error": str(e)}
        
        # Compare metrics across protocols
        comparison_data = {}
        for p, data in protocol_data.items():
            if "metrics" in data:
                comparison_data[p] = {
                    "protocol": p,
                    metric: data["metrics"].get(metric, "N/A")
                }
                
                if detailed:
                    comparison_data[p].update(data["metrics"])
            else:
                comparison_data[p] = {"protocol": p, metric: "N/A", "error": data.get("error", "Unknown error")}
        
        # Display comparison
        click.echo("\n📊 Protocol Comparison:")
        for p, data in comparison_data.items():
            click.echo(f"  • {p.upper()}: {data.get(metric, 'N/A')}")
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.{format}")
        
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(comparison_data, f, indent=2)
            click.echo(f"\n💾 Comparison saved to {output_file}")
        elif format == "html":
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
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <table>
                    <tr>
                        <th>Protocol</th>
                        <th>{metric.replace('_', ' ').title()}</th>
                    </tr>
            """
            
            for p, data in comparison_data.items():
                html_content += f"""
                    <tr>
                        <td>{p.upper()}</td>
                        <td>{data.get(metric, 'N/A')}</td>
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
        elif format == "png":
            # Generate chart
            plt.figure(figsize=(10, 6))
            
            # Extract values and protocols
            protocols = list(comparison_data.keys())
            values = [comparison_data[p].get(metric, 0) for p in protocols]
            
            # Create bar chart
            plt.bar(protocols, values)
            plt.title(f"Protocol Comparison: {metric.replace('_', ' ').title()}")
            plt.xlabel("Protocol")
            plt.ylabel(metric.replace('_', ' ').title())
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
            data_manager = historical_data.HistoricalDataManager(data_dir)
            
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
                plt.ylabel(metric.replace('_', ' ').title())
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save chart
                plt.savefig(historical_chart_file)
                plt.close()
                
                click.echo(f"📊 Historical comparison chart saved to {historical_chart_file}")
            else:
                click.echo("⚠️ No historical data available for comparison")
    except click.Abort:
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# EXPORT HISTORICAL DATA COMMAND
@cli.command(
    "export-historical-data",
    help="📤 Export token distribution data (-p) in various formats (-f) for further analysis.",
)
@click.option("--protocol", "-p", type=ProtocolChoice(), required=True, help="Protocol to export data for")
@click.option(
    "--format", "-f", type=click.Choice(["json", "csv"]), default="json", help="Export format (default: json)"
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="exports",
    callback=validate_output_dir,
    help="Directory to save exported files (default: exports)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=1000,
    callback=validate_positive_int,
    help="Maximum number of records to export (default: 1000)",
)
@click.option("--include-historical", "-H", is_flag=True, help="Include historical snapshots in export")
@click.option(
    "--metric",
    "-m",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Metric to focus on for historical export",
)
@click.option("--data-dir", "-D", type=str, default="data/historical", help="Directory containing historical data")
def export_historical_data(protocol, output_format, output_dir, limit, include_historical, metric, data_dir):
    """📤 Export token distribution data for further analysis.

    Exports raw data in various formats for use in external tools.

    Options:
      -p, --protocol             Protocol to export data for
      -f, --format               Export format (default: json)
      -o, --output-dir           Directory to save exported files (default: exports)
      -l, --limit                Maximum number of records to export (default: 1000)
      -H, --include-historical   Include historical snapshots in export
      -m, --metric               Metric to focus on for historical export
      -D, --data-dir             Directory containing historical data

    Examples:
      gova export-historical-data -p compound -f json
      gova export-historical-data -p uniswap -h
      gova export-historical-data -p aave -f csv -l 5000
    """
    click.echo(f"📤 Exporting {protocol.upper()} token distribution data...")

    try:
        # Initialize components
        api_client = APIClient()

        # Get current data
        click.echo("📡 Fetching current data...")
        holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)

        # Prepare export data
        export_data = {
            "protocol": protocol,
            "protocol_info": PROTOCOLS.get(protocol, {}),
            "export_timestamp": datetime.now().isoformat(),
            "current_data": holders_data,
        }

        # Add historical data if requested
        if include_historical:
            click.echo("📜 Loading historical snapshots...")
            try:
                if snapshots := historical_data.load_historical_snapshots(protocol, data_dir):
                    click.echo(f"✅ Loaded {len(snapshots)} historical snapshots")
                    export_data["historical_snapshots"] = snapshots
                else:
                    click.echo("⚠️  No historical snapshots found")
            except Exception as e:
                click.echo(f"⚠️  Error loading historical data: {e}")

        # Generate output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{protocol}_{metric}_historical.{format}")
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(export_data, f, indent=2)
            elif format == "csv":
                # Convert to DataFrame for CSV export
                df = pd.DataFrame({
                    "protocol": protocol,
                    "timestamp": datetime.now().isoformat(),
                    "holders_count": len(export_data.get("current_data", [])),
                }, index=[0])
                
                if "historical_snapshots" in export_data:
                    # Add historical data columns
                    for i, snapshot in enumerate(export_data["historical_snapshots"]):
                        date = snapshot.get("date", f"snapshot_{i}")
                        value = snapshot.get(metric, 0)
                        df[f"snapshot_{i}_date"] = date
                        df[f"snapshot_{i}_value"] = value
                
                df.to_csv(output_file, index=False)
            
            click.echo(f"✅ Data exported to {output_file}")
        except Exception as e:
            click.echo(f"❌ Error saving export file: {e}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error exporting data: {e}", err=True)
        sys.exit(1)


# HISTORICAL ANALYSIS COMMAND
@cli.command(
    "historical-analysis",
    help="📈 Analyze historical trends (-p) in token distribution metrics (-m) with time series visualization.",
)
@click.option("--protocol", "-p", type=ProtocolChoice(), required=True, help="Protocol to analyze historical data for")
@click.option(
    "--metric",
    "-m",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Metric to analyze over time (default: gini_coefficient)",
)
@click.option(
    "--data-dir",
    "-D",
    type=str,
    default="data/historical",
    help="Directory containing historical data (default: data/historical)",
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save analysis results (default: outputs)",
)
@click.option("--format", "-f", type=click.Choice(["json", "png"]), default="png", help="Output format (default: png)")
@click.option("--plot", "-c", is_flag=True, default=True, help="Generate time series plots")
def historical_analysis(protocol, metric, data_dir, output_dir, output_format, plot):
    """📈 Analyze historical trends in token distribution metrics.

    Tracks changes in concentration and governance metrics over time.

    Options:
      -p, --protocol             Protocol to analyze historical data for
      -m, --metric               Metric to analyze over time (default: gini_coefficient)
      -D, --data-dir             Directory containing historical data (default: data/historical)
      -o, --output-dir           Directory to save analysis results (default: outputs)
      -f, --format               Output format (default: png)
      -c, --plot                 Generate time series plots (default: True)

    Examples:
      gova historical-analysis -p compound
      gova historical-analysis -p uniswap -m shannon_entropy
      gova historical-analysis -p aave -f json
    """
    try:
        # Initialize data manager
        from governance_token_analyzer.core.historical_data import HistoricalDataManager

        data_manager = HistoricalDataManager(data_dir)

        # Get time series data
        click.echo(f"📊 Loading historical data for {protocol.upper()}...")

        try:
            time_series_df = data_manager.get_time_series_data(protocol, metric)

            if time_series_df.empty:
                click.echo(f"❌ No historical data found for {protocol} and metric {metric}")
                sys.exit(1)

            # Get the number of snapshots
            num_snapshots = len(time_series_df)
            click.echo(f"✅ Found {num_snapshots} historical snapshots")

            # Calculate trend analysis
            click.echo("🧮 Calculating distribution trends...")
            from governance_token_analyzer.core.historical_data import calculate_distribution_change

            # Convert DataFrame to the format expected by calculate_distribution_change
            # The function expects a list of dictionaries with 'date' and 'value' keys
            trend_data = []

            for date, row in time_series_df.iterrows():
                # Handle different date formats
                if isinstance(date, pd.Timestamp):
                    date_str = date.strftime("%Y-%m-%d")
                else:
                    # Try to parse the date if it's a string
                    try:
                        date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
                    except (ValueError, TypeError) as e:
                        click.echo(f"⚠️ Warning: Failed to parse date '{date}' due to error: {e}")
                        date_str = str(date)

                # Extract the metric value
                if isinstance(row, pd.Series):
                    value = row.iloc[0]
                else:
                    value = row

                trend_data.append({"date": date_str, "value": float(value)})

            # Sort by date to ensure chronological order
            trend_data.sort(key=lambda x: x["date"])

            # Calculate trend metrics
            if len(trend_data) >= 2:
                # Extract first and last data points for old and new distribution
                old_data = pd.DataFrame([trend_data[0]])
                new_data = pd.DataFrame([trend_data[-1]])
                
                # Add required columns for calculate_distribution_change
                old_data['address'] = old_data['date']  # Use date as address for compatibility
                new_data['address'] = new_data['date']  # Use date as address for compatibility
                old_data['balance'] = old_data['value']  # Use value as balance for compatibility
                new_data['balance'] = new_data['value']  # Use value as balance for compatibility
                
                try:
                    changes_df = calculate_distribution_change(old_data, new_data)
                    
                    # Create a simple trend metrics dictionary
                    trend_metrics = {
                        "overall_change": float(new_data['value'].iloc[0] - old_data['value'].iloc[0]),
                        "avg_change_per_period": float((new_data['value'].iloc[0] - old_data['value'].iloc[0]) / (len(trend_data) - 1)),
                        "volatility": 0.0,  # Calculate actual volatility if needed
                        "trend_direction": "increasing" if new_data['value'].iloc[0] > old_data['value'].iloc[0] else "decreasing"
                    }
                    
                    # Display trend metrics
                    click.echo("\n📊 Trend Analysis Results:")
                    click.echo(f"  • Overall change: {trend_metrics['overall_change']:.4f}")
                    click.echo(f"  • Average change per period: {trend_metrics['avg_change_per_period']:.4f}")
                    click.echo(f"  • Volatility: {trend_metrics['volatility']:.4f}")
                    click.echo(f"  • Trend direction: {trend_metrics['trend_direction']}")
                except Exception as e:
                    click.echo(f"❌ Error processing historical data: {e}")
                    sys.exit(1)

                # Save trend metrics
                if output_format == "json" and trend_metrics:
                    output_file = os.path.join(output_dir, f"{protocol}_{metric}_trends.json")
                    with open(output_file, "w") as f:
                        json.dump(
                            {
                                "protocol": protocol,
                                "metric": metric,
                                "time_series": trend_data,
                                "trend_metrics": trend_metrics,
                            },
                            f,
                            indent=2,
                        )
                    click.echo(f"\n💾 Results saved to {output_file}")

                # Generate visualization
                if plot:
                    click.echo("\n📈 Generating time series visualization...")

                    # Extract dates and values for plotting
                    dates = [entry["date"] for entry in trend_data]
                    values = [entry["value"] for entry in trend_data]

                    # Create the plot
                    plt.figure(figsize=(12, 6))
                    plt.plot(dates, values, marker="o", linestyle="-", color="#1f77b4")
                    plt.title(f"{protocol.upper()} - {metric.replace('_', ' ').title()} Over Time")
                    plt.xlabel("Date")
                    plt.ylabel(metric.replace("_", " ").title())
                    plt.grid(True, linestyle="--", alpha=0.7)
                    plt.xticks(rotation=45)
                    plt.tight_layout()

                    # Save the plot
                    output_file = os.path.join(output_dir, f"{protocol}_{metric}.png")
                    plt.savefig(output_file, dpi=300, bbox_inches="tight")
                    plt.close()

                    click.echo(f"📊 Visualization saved to {output_file}")
            else:
                click.echo("❌ Not enough data points for trend analysis (minimum 2 required)")
        except Exception as e:
            click.echo(f"❌ Error processing historical data: {e}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# GENERATE REPORT COMMAND
@cli.command(
    "generate-report", help="📑 Generate a comprehensive analysis report (-p) with visualizations and detailed metrics."
)
@click.option("--protocol", "-p", type=ProtocolChoice(), required=True, help="Protocol to generate report for")
@click.option("--format", "-f", type=click.Choice(["html"]), default="html", help="Report format (default: html)")
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="reports",
    callback=validate_output_dir,
    help="Directory to save report files (default: reports)",
)
@click.option("--include-historical", "-H", is_flag=True, help="Include historical analysis in report")
@click.option("--data-dir", "-D", type=str, default="data/historical", help="Directory containing historical data")
def generate_report(protocol, output_format, output_dir, include_historical, data_dir):
    """📑 Generate a comprehensive analysis report for a protocol.

    Creates a detailed report with visualizations and insights.

    Options:
      -p, --protocol             Protocol to generate report for
      -f, --format               Report format (default: html)
      -o, --output-dir           Directory to save report files (default: reports)
      -H, --include-historical   Include historical analysis in report
      -D, --data-dir             Directory containing historical data

    Examples:
      gova generate-report -p compound
      gova generate-report -p uniswap -h
      gova generate-report -p aave -o custom_reports
    """
    try:
        # Initialize components
        api_client = APIClient()
        report_gen = ReportGenerator(output_dir=output_dir)

        # Get current data
        click.echo("📡 Fetching current data...")
        holders_data = api_client.get_token_holders(protocol, limit=1000, use_real_data=True)

        # Extract balances
        balances = []
        for holder in holders_data:
            if isinstance(holder, dict) and "balance" in holder:
                try:
                    balance = float(holder["balance"])
                    if balance > 0:
                        balances.append(balance)
                except (ValueError, TypeError):
                    continue

        # Get governance data
        click.echo("🏛️ Fetching governance data...")
        proposals = api_client.get_governance_proposals(protocol)
        click.echo(f"📊 Found {len(proposals)} governance proposals")

        # Get votes for each proposal
        PROPOSAL_VOTE_FETCH_LIMIT = 10  # Limit number of proposals to fetch votes for performance
        all_votes = []
        for proposal in proposals[:PROPOSAL_VOTE_FETCH_LIMIT]:
            proposal_id = proposal.get("id")
            if proposal_id:
                click.echo(f"🗳️ Fetching votes for proposal {proposal_id}")
                votes = api_client.get_governance_votes(protocol, proposal_id)
                all_votes.extend(votes)

        click.echo(f"✅ Fetched {len(all_votes)} total votes across all proposals")

        # Get historical data if requested
        historical_data_records = None
        if include_historical:
            click.echo("📜 Loading historical data...")
            try:
                # Load historical snapshots
                from governance_token_analyzer.core.historical_data import HistoricalDataManager

                data_manager = HistoricalDataManager(data_dir)
                snapshots = data_manager.get_snapshots(protocol)

                if snapshots:
                    click.echo(f"✅ Loaded {len(snapshots)} historical snapshots")

                    # Get time series data for Gini coefficient
                    time_series_df = data_manager.get_time_series_data(protocol, "gini_coefficient")

                    # Convert to list of dictionaries with date and value
                    historical_data_records = []
                    for date, value in time_series_df.iterrows():
                        historical_data_records.append(
                            {"date": date.strftime("%Y-%m-%d"), "value": float(value.iloc[0])}
                        )
                else:
                    click.echo("⚠️ No historical data found")
            except Exception as e:
                click.echo(f"⚠️ Error loading historical data: {e}")

        # Prepare data for report
        data = {
            "protocol": protocol,
            "balances": balances,
            "proposals": proposals,
            "votes": all_votes,
            "historical_data": historical_data_records,
            "timestamp": datetime.now().isoformat(),
        }

        # Generate the report
        click.echo("🔧 Generating report...")
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Get current date for the report filename
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"{protocol}_report.{format}")
            
            # Generate the report using snapshot_report method
            report_gen.generate_snapshot_report(
                protocol_data=data,
                protocol_name=protocol,
                output_format=format,
                output_file=output_file,
                include_visualizations=True
            )
            
            click.echo(f"✅ Report generated and saved to {output_file}")
        except Exception as e:
            click.echo(f"❌ Error generating report: {e}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def _ensure_directories(dirs):
    """Ensure directories exist."""
    try:
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        return True
    except OSError as e:
        click.echo(f"❌ Error creating directories: {e}", err=True)
        return False


def _process_snapshot(index, date_str, snapshot_data, protocol, protocol_dir):
    """
    Process a single historical snapshot and save to disk.

    Args:
        index: Snapshot index
        date_str: Date string for the snapshot
        snapshot_data: The snapshot data to process
        protocol: Protocol name
        protocol_dir: Directory to save the snapshot

    Returns:
        tuple: Date string and gini coefficient value, or (None, None) if processing fails
    """
    try:
        # Extract token holder data
        token_holders = snapshot_data.get("token_holders", [])
        if not token_holders:
            click.echo(f"⚠️ Warning: No token holders in snapshot {date_str}")
            return None, None

        # Process token holders data
        df, gini = _extract_metrics_from_holders(token_holders, date_str)
        if df is None:
            return None, None

        # Save processed snapshot
        _save_snapshot_to_file(date_str, token_holders, gini, df, protocol, protocol_dir)

        # Return values for visualization
        return date_str, gini

    except Exception as e:
        click.echo(f"⚠️ Warning: Failed to process snapshot {date_str}: {e}")
        return None, None


def _extract_metrics_from_holders(token_holders, date_str):
    """
    Extract metrics from token holder data.

    Args:
        token_holders: List of token holders with their balances
        date_str: Date string for logging purposes

    Returns:
        tuple: DataFrame of processed data and gini coefficient value, or (None, None) if processing fails
    """
    # Convert to DataFrame for consistency
    df = pd.DataFrame(token_holders)

    # Calculate metrics
    gini = None
    if "balance" in df.columns and len(df) > 0:
        try:
            # Convert balance column to numeric, handling errors gracefully
            df["balance"] = pd.to_numeric(df["balance"], errors="coerce")
            df = df.dropna(subset=["balance"])

            # Calculate Gini coefficient if we have valid balances
            if not df.empty and df["balance"].sum() > 0:
                from governance_token_analyzer.core.advanced_metrics import calculate_gini_coefficient

                gini = calculate_gini_coefficient(df["balance"].values)
        except Exception as e:
            click.echo(f"⚠️ Warning: Error calculating metrics for {date_str}: {e}")

    return df, gini


def _save_snapshot_to_file(date_str, token_holders, gini, df, protocol, protocol_dir):
    """
    Save processed snapshot to file.

    Args:
        date_str: Date string for the snapshot
        token_holders: List of token holders with their balances
        gini: Calculated gini coefficient
        df: DataFrame of processed data
        protocol: Protocol name
        protocol_dir: Directory to save the snapshot
    """
    # Create filename and path
    filename = f"{protocol}_snapshot_{date_str.replace('-', '')}.json"
    filepath = os.path.join(protocol_dir, filename)

    # Add metadata to snapshot
    enhanced_data = {
        "timestamp": date_str,
        "data": {
            "token_holders": token_holders,
            "metrics": {
                "gini_coefficient": gini,
                "total_tokens": df["balance"].sum() if "balance" in df.columns else 0,
                "num_holders": len(df),
            },
        },
    }

    # Save to file
    with open(filepath, "w") as f:
        json.dump(enhanced_data, f, indent=2)


def process_and_save_historical_snapshots(historical_snapshots_dict, protocol, protocol_dir, output_dir):
    """
    Process and save historical snapshots to disk.

    Args:
        historical_snapshots_dict: Dictionary of historical snapshots
        protocol: Protocol name
        protocol_dir: Directory to save snapshot files
        output_dir: Directory to save visualization outputs

    Returns:
        tuple: Lists of dates and gini values for visualization
    """
    # Ensure required directories exist
    if not _ensure_directories([protocol_dir, output_dir]):
        return [], []

    # Process all snapshots and collect visualization data
    visualization_data = [
        _process_snapshot(i, date_str, snapshot_data, protocol, protocol_dir)
        for i, (date_str, snapshot_data) in enumerate(historical_snapshots_dict.items())
    ]

    # Filter out None values and unzip the valid data points
    valid_data = [(d, g) for d, g in visualization_data if d is not None and g is not None]
    dates, gini_values = zip(*valid_data) if valid_data else ([], [])

    return list(dates), list(gini_values)


@cli.command(
    "simulate-historical",
    help="🎲 Generate simulated historical data (-p) with configurable snapshots (-s) and intervals (-i).",
)
@click.option("--protocol", "-p", type=ProtocolChoice(), required=True, help="Protocol to simulate historical data for")
@click.option(
    "--snapshots", "-s", type=int, default=10, help="Number of historical snapshots to generate (default: 10)"
)
@click.option("--interval", "-i", type=int, default=7, help="Interval between snapshots in days (default: 7)")
@click.option(
    "--data-dir",
    "-D",
    type=str,
    default="data/historical",
    help="Directory containing historical data (default: data/historical)",
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save simulated data (default: outputs)",
)
def simulate_historical(protocol, snapshots, interval, data_dir, output_dir):
    """🎲 Generate simulated historical data.

    Creates synthetic historical snapshots for testing and development.

    Options:
      -p, --protocol             Protocol to simulate historical data for
      -s, --snapshots            Number of historical snapshots to generate (default: 10)
      -i, --interval             Interval between snapshots in days (default: 7)
      -D, --data-dir             Directory containing historical data (default: data/historical)
      -o, --output-dir           Directory to save simulated data (default: outputs)

    Examples:
      gova simulate-historical -p compound
      gova simulate-historical -p uniswap -s 20 -i 14
      gova simulate-historical -p aave -D custom_data
    """
    click.echo(f"🎲 Simulating historical data for {protocol.upper()}...")
    click.echo(f"📊 Generating {snapshots} snapshots at {interval}-day intervals")

    try:
        # Create output directories
        protocol_dir = os.path.join(data_dir, protocol)
        os.makedirs(protocol_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        click.echo(f"🎲 Generating {snapshots} historical snapshots for {protocol.upper()}...")
        
        try:
            # Initialize simulator
            simulator = TokenDistributionSimulator()
            
            # Generate snapshots
            for i in range(snapshots):
                # Calculate date for this snapshot
                days_ago = (snapshots - i - 1) * interval
                snapshot_date = datetime.now() - timedelta(days=days_ago)
                date_str = snapshot_date.strftime("%Y-%m-%d")
                
                click.echo(f"  📊 Generating snapshot for {date_str}...")
                
                # Generate data for this snapshot
                snapshot_data = simulator.generate_protocol_data(
                    protocol, 
                    num_holders=1000, 
                    date=date_str,
                    variance_factor=0.1 * i  # Increase variance over time
                )
                
                # Calculate metrics
                if "token_holders" in snapshot_data:
                    balances = [float(holder.get("balance", 0)) for holder in snapshot_data["token_holders"] if float(holder.get("balance", 0)) > 0]
                    
                    if balances:
                        metrics = calculate_all_concentration_metrics(balances)
                        snapshot_data["metrics"] = metrics
                
                # Save snapshot
                snapshot_file = os.path.join(protocol_dir, f"{protocol}_snapshot_{date_str}.json")
                
                with open(snapshot_file, "w") as f:
                    json.dump(snapshot_data, f, indent=2)
            
            click.echo(f"✅ Generated {snapshots} historical snapshots for {protocol.upper()}")
            click.echo(f"💾 Snapshots saved to {protocol_dir}")
        except Exception as e:
            click.echo(f"❌ Error generating historical data: {e}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error simulating historical data: {str(e)}", err=True)
        if os.environ.get("DEBUG"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


# STATUS COMMAND
@cli.command(help="ℹ️ Check system status, API connectivity (-a), and protocol data availability (-t).")
@click.option("--check-apis", "-a", is_flag=True, help="Check API key configuration and connectivity")
@click.option("--test-protocols", "-t", is_flag=True, help="Test data retrieval for all supported protocols")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed status information")
def status(check_apis, test_protocols, verbose):
    """ℹ️ Check system status and configuration.

    Verifies API connectivity, environment setup, and data availability.

    Options:
      -a, --check-apis           Check API key configuration and connectivity
      -t, --test-protocols       Test data retrieval for all supported protocols
      -v, --verbose              Show detailed status information

    Examples:
      gova status
      gova status -a -v
      gova status -t
    """
    click.echo("ℹ️ Governance Token Distribution Analyzer - Status Check")
    click.echo("=" * 60)

    # Check environment
    click.echo("🔧 Environment:")
    click.echo(f"  Python version: {sys.version.split()[0]}")
    click.echo(f"  Operating system: {os.name.upper()}")

    # Check API keys
    if check_apis or not test_protocols:
        click.echo("\n🔑 API Keys:")
        api_keys = {
            "ETHERSCAN_API_KEY": os.environ.get("ETHERSCAN_API_KEY", ""),
            "ALCHEMY_API_KEY": os.environ.get("ALCHEMY_API_KEY", ""),
            "GRAPH_API_KEY": os.environ.get("GRAPH_API_KEY", ""),
            "INFURA_API_KEY": os.environ.get("INFURA_API_KEY", ""),
        }

        for key_name, key_value in api_keys.items():
            status_icon = "✅" if key_value else "❌"
            status_text = "Configured" if key_value else "Not configured"

            # Mask API key for security
            masked_key = "••••••" + key_value[-4:] if key_value and len(key_value) > 4 else ""
            key_display = f" ({masked_key})" if masked_key else ""

            click.echo(f"  {status_icon} {key_name}: {status_text}{key_display}")

    # Test protocol data retrieval
    if test_protocols:
        click.echo("\n📡 Protocol Data Retrieval:")
        api_client = APIClient()

        for protocol in SUPPORTED_PROTOCOLS:
            click.echo(f"  Testing {protocol.upper()}...")

            try:
                # Test token holders retrieval
                holders = api_client.get_token_holders(protocol, limit=5, use_real_data=True)
                holders_status = f"✅ ({len(holders)} holders)" if holders else "❌ (No data)"
                click.echo(f"    Token holders: {holders_status}")

                # Test governance proposals retrieval
                proposals = api_client.get_governance_proposals(protocol, use_real_data=True)
                proposals_status = f"✅ ({len(proposals)} proposals)" if proposals else "❌ (No data)"
                click.echo(f"    Governance proposals: {proposals_status}")

                # Test governance votes retrieval
                votes = api_client.get_governance_votes(protocol, use_real_data=True)
                votes_status = f"✅ ({len(votes)} votes)" if votes else "❌ (No data)"
                click.echo(f"    Governance votes: {votes_status}")

                if verbose:
                    # Show sample data
                    if holders:
                        click.echo(f"    Sample holder: {holders[0]}")
                    if proposals:
                        click.echo(f"    Sample proposal: {proposals[0]}")

            except Exception as e:
                click.echo(f"    ❌ Error: {e}")

    click.echo("\n✅ Status check complete")


# VALIDATE COMMAND
@cli.command(help="🔍 Validate analysis results against benchmarks with detailed validation reporting (-v).")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="validation",
    callback=validate_output_dir,
    help="Directory to save validation results (default: validation)",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
def validate(input_file, output_dir, verbose):
    """🔍 Validate analysis results against benchmarks.

    Checks if analysis outputs are within expected ranges and formats.

    Options:
      input_file                 Path to the file to validate
      -o, --output-dir           Directory to save validation results (default: validation)
      -v, --verbose              Show detailed validation results

    Examples:
      gova validate outputs/compound_analysis_20230401_120000.json
      gova validate outputs/comparison_20230401_120000.json -v
    """
    click.echo(f"🔍 Validating analysis results from {input_file}...")

    try:
        # Import validation module
        from governance_token_analyzer.cli.validate import OutputValidator

        # Load input file
        with open(input_file, "r") as f:
            data = json.load(f)

        # Validate data
        validator = OutputValidator()
        result = validator.validate_analysis_output(data)

        # Display results
        validation_status = "✅ PASSED" if result["validation_passed"] else "❌ FAILED"
        click.echo(f"\n📄 Validation result: {validation_status}")

        if verbose:
            if result.get("checks"):
                click.echo("\n✓ Checks passed:")
                for check in result["checks"]:
                    click.echo(f"  {check}")

            if result.get("warnings"):
                click.echo("\n⚠️  Warnings:")
                for warning in result["warnings"]:
                    click.echo(f"  {warning}")

            if result.get("errors"):
                click.echo("\n❌ Errors:")
                for error in result["errors"]:
                    click.echo(f"  {error}")

        # Save validation results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"validation_result_{timestamp}.json")

        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        click.echo(f"\n💾 Validation results saved to {output_file}")

        # Exit with appropriate code
        if not result["validation_passed"]:
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error validating file: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
