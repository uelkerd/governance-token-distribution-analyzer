#!/usr/bin/env python3
"""
Governance Token Distribution Analyzer CLI

Command-line interface for analyzing token distribution patterns,
concentration metrics, and governance participation across protocols.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import click
import pandas as pd

# Add the src directory to Python path for imports
try:
    # Import core functionality
    from governance_token_analyzer.core.api_client import APIClient
    from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
    from governance_token_analyzer.core.config import PROTOCOLS
    from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
    from governance_token_analyzer.core import historical_data
    from governance_token_analyzer.visualization.report_generator import ReportGenerator

    # Import command implementations
    from governance_token_analyzer.cli.commands.analyze import execute_analyze_command
    from governance_token_analyzer.cli.commands.compare import execute_compare_protocols_command
    from governance_token_analyzer.cli.commands.export import execute_export_historical_data_command
    from governance_token_analyzer.cli.commands.historical import execute_historical_analysis_command
    from governance_token_analyzer.cli.commands.report import execute_generate_report_command

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
def analyze(protocol, limit, format, output_dir, chart, live_data, simulated_data, verbose):
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
        execute_analyze_command(
            protocol=protocol,
            limit=limit,
            format=format,
            output_dir=output_dir,
            chart=chart,
            live_data=live_data,
            verbose=verbose,
        )
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
def compare_protocols(protocols, metric, format, output_dir, chart, detailed, historical, data_dir):
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
        execute_compare_protocols_command(
            protocols=protocols,
            metric=metric,
            format=format,
            output_dir=output_dir,
            chart=chart,
            detailed=detailed,
            historical=historical,
            data_dir=data_dir,
        )
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
def export_historical_data(protocol, format, output_dir, limit, include_historical, metric, data_dir):
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
    try:
        execute_export_historical_data_command(
            protocol=protocol,
            format=format,
            output_dir=output_dir,
            limit=limit,
            include_historical=include_historical,
            metric=metric,
            data_dir=data_dir,
        )
    except click.Abort:
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
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
def historical_analysis(protocol, metric, data_dir, output_dir, format, plot):
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
        execute_historical_analysis_command(
            protocol=protocol,
            metric=metric,
            data_dir=data_dir,
            output_dir=output_dir,
            format=format,
            plot=plot,
        )
    except click.Abort:
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
def generate_report(protocol, format, output_dir, include_historical, data_dir):
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
        execute_generate_report_command(
            protocol=protocol,
            format=format,
            output_dir=output_dir,
            include_historical=include_historical,
            data_dir=data_dir,
        )
    except click.Abort:
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
        # Extract token holder data (handle both 'token_holders' and 'result' keys)
        token_holders = snapshot_data.get("token_holders")
        if token_holders is None:
            token_holders = snapshot_data.get("result")
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
        # Create protocol directory if it doesn't exist
        protocol_dir = os.path.join(data_dir, protocol)
        os.makedirs(protocol_dir, exist_ok=True)

        # Initialize simulator
        simulator = TokenDistributionSimulator()

        # Generate historical data with trends
        click.echo("📈 Generating historical snapshots with trends...")
        historical_snapshots_dict = simulator.generate_historical_distribution(
            distribution_type="power_law",  # Always use power_law for consistent results
            num_periods=snapshots,
            period_days=interval,
            num_holders=1000,
        )

        if not historical_snapshots_dict:
            click.echo("❌ Failed to generate historical snapshots")
            sys.exit(1)

        click.echo(f"✅ Generated {len(historical_snapshots_dict)} historical snapshots")

        # Process and save snapshots, getting dates and gini values for visualization
        dates, gini_values = process_and_save_historical_snapshots(
            historical_snapshots_dict, protocol, protocol_dir, output_dir
        )

        click.echo(f"💾 Saved {len(dates)} valid snapshots to {protocol_dir}")

        # Generate visualization of the trend
        if dates and gini_values and len(dates) == len(gini_values):
            click.echo("📊 Creating trend visualization...")
            report_gen = ReportGenerator(output_dir=output_dir)

            output_file = os.path.join(
                output_dir, f"{protocol}_historical_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )

            # Generate time series chart
            report_gen.generate_time_series_chart(dates, gini_values, protocol.upper(), "Gini Coefficient", output_file)

            click.echo(f"📊 Trend visualization saved to {output_file}")
        else:
            click.echo("⚠️ Not enough valid data points for trend visualization")

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
