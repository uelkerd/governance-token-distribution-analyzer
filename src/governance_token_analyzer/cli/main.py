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
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import click

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import core functionality
try:
    from governance_token_analyzer.core.api_client import APIClient
    from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
    from governance_token_analyzer.core.config import PROTOCOLS
    from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
    from governance_token_analyzer.core import historical_data
    from governance_token_analyzer.visualization.report_generator import ReportGenerator
    from governance_token_analyzer.visualization.chart_generator import ChartGenerator
    from governance_token_analyzer.analysis.voting_block import VotingBlockAnalyzer
except ImportError as e:
    click.echo(f"Error importing modules: {e}", err=True)
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


def extract_balances_from_holders(holders_data: List[Dict[str, Any]], click_obj: Any) -> List[float]:
    """
    Helper function to extract token balances from holder data.
    Works with both live API data and simulated data.
    
    Args:
        holders_data: List of holder dictionaries
        click_obj: Click context for error logging
        
    Returns:
        List of float balances
    """
    balances = []
    for holder in holders_data:
        try:
            # Make sure we're dealing with a dictionary
            if not isinstance(holder, dict):
                continue
                
            # Try multiple possible balance field names and formats
            balance_value = (
                holder.get("balance") or 
                holder.get("TokenHolderQuantity") or 
                holder.get("voting_power") or 
                holder.get("value") or 
                0
            )
            
            if balance_value is not None and balance_value != "":
                # Convert to float, handling various string formats
                if isinstance(balance_value, str):
                    # Remove common formatting characters
                    clean_value = balance_value.replace(",", "").replace("$", "").strip()
                    balance_float = float(clean_value)
                else:
                    balance_float = float(balance_value)

                if balance_float > 0:
                    balances.append(balance_float)
        except (ValueError, TypeError, AttributeError) as e:
            click_obj.echo(f"⚠️ Error processing balance: {e}", err=True)
            continue
    
    return balances


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


# CLI Group Configuration
@click.group()
@click.version_option(version="1.0.0", prog_name="gova")
@click.pass_context
def cli(ctx):
    """🏛️ Governance Token Distribution Analyzer

    A comprehensive tool for analyzing token concentration,
    governance participation, and voting power distribution
    across DeFi protocols.

    Examples:
      gova analyze --protocol compound --format json
      gova compare-protocols --protocols compound,uniswap --metric gini_coefficient
      gova generate-report --protocol compound --format html
      gova status --check-apis --test-protocols
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


# ANALYZE COMMAND
@cli.command()
@click.option("--protocol", type=ProtocolChoice(), required=True, help="Protocol to analyze (compound, uniswap, aave)")
@click.option(
    "--limit",
    type=int,
    default=1000,
    callback=validate_positive_int,
    help="Maximum number of token holders to analyze (default: 1000)",
)
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Output format (default: json)")
@click.option(
    "--output-dir",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save output files (default: outputs)",
)
@click.option("--chart", is_flag=True, help="Generate distribution charts")
@click.option(
    "--live-data/--simulated-data", default=True, help="Use live blockchain data or simulated data (default: live)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output with detailed metrics")
def analyze(protocol, limit, format, output_dir, chart, live_data, verbose):
    """📊 Analyze token distribution for a specific protocol.

    Calculates concentration metrics and generates detailed analysis reports.

    Examples:
      gova analyze --protocol compound --format json
      gova analyze --protocol uniswap --chart --verbose
      gova analyze --protocol aave --simulated-data
    """
    click.echo(f"📊 Analyzing {protocol.upper()} token distribution...")
    click.echo(f"🎯 Target limit: {limit:,} holders")
    click.echo(f"📡 Data source: {'Live blockchain data' if live_data else 'Simulated data'}")

    try:
        # Initialize components
        api_client = APIClient()

        # Get data based on user preference
        if live_data:
            click.echo("📡 Fetching live data...")
            holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)

            # Extract and convert balances with robust error handling
            balances = extract_balances_from_holders(holders_data, click)

            if not balances:
                click.echo("⚠️  No valid live data found, falling back to simulated data", err=True)
                live_data = False

        if not live_data or not balances:
            click.echo("🎲 Generating simulated data...")
            simulator = TokenDistributionSimulator()
            # Use the user-specified limit parameter
            simulated_holders = simulator.generate_power_law_distribution(limit)
            # Extract just the balances from the simulated data
            balances = extract_balances_from_holders(simulated_holders, click)

        click.echo(f"✅ Processed {len(balances):,} token holders")

        # Calculate metrics
        click.echo("🧮 Calculating concentration metrics...")
        metrics = calculate_all_concentration_metrics(balances)

        # Prepare output data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "protocol": protocol,
            "protocol_info": PROTOCOLS.get(protocol, {}),
            "analysis_timestamp": datetime.now().isoformat(),
            "data_source": "live" if live_data and balances else "simulated",
            "total_holders": len(balances),
            "total_supply": sum(balances),
            "metrics": metrics,
            "top_holders": {
                "top_10_percentage": sum(sorted(balances, reverse=True)[:10]) / sum(balances) * 100
                if sum(balances) > 0
                else 0,
                "top_100_percentage": sum(sorted(balances, reverse=True)[:100]) / sum(balances) * 100
                if sum(balances) > 0
                else 0,
            },
        }

        # Generate output
        output_file = os.path.join(output_dir, f"{protocol}_analysis_{timestamp}.{format}")

        if format == "json":
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
        elif format == "csv":
            # Convert to CSV format
            csv_data = []
            for key, value in metrics.items():
                csv_data.append({"metric": key, "value": value})

            with open(output_file, "w", newline="") as f:
                if csv_data:
                    fieldnames = ["metric", "value"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

        # Generate charts if requested
        if chart:
            try:
                chart_gen = ChartGenerator()
                chart_file = os.path.join(output_dir, f"{protocol}_distribution_analysis.png")
                chart_gen.plot_distribution_analysis(balances, protocol, chart_file)
                click.echo(f"📊 Distribution chart saved: {chart_file}")
            except ImportError:
                click.echo("⚠️  Chart generation not available (missing dependencies)", err=True)

        # Display summary
        click.echo(f"\n✅ Analysis complete!")
        click.echo(f"📁 Results saved: {output_file}")

        if verbose:
            click.echo(f"\n📈 Key Metrics for {protocol.upper()}:")
            click.echo(f"  • Gini Coefficient: {metrics.get('gini_coefficient', 0):.4f}")
            click.echo(f"  • Concentration Ratio (Top 10): {results['top_holders']['top_10_percentage']:.2f}%")
            click.echo(f"  • Herfindahl Index: {metrics.get('herfindahl_index', 0):.4f}")
            click.echo(f"  • Total Holders: {len(balances):,}")
            click.echo(f"  • Total Supply: {sum(balances):,.2f}")

        return output_file

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)
        sys.exit(1)


# COMPARE PROTOCOLS COMMAND (renamed from compare)
@cli.command("compare-protocols")
@click.option(
    "--protocols",
    type=str,
    required=True,
    help='Comma-separated list of protocols to compare (e.g., compound,uniswap,aave) or "all"',
)
@click.option(
    "--metric",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Primary metric for comparison (default: gini_coefficient)",
)
@click.option(
    "--format", type=click.Choice(["json", "html", "png"]), default="json", help="Output format (default: json)"
)
@click.option(
    "--output-dir",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save output files (default: outputs)",
)
@click.option("--chart", is_flag=True, help="Generate comparison charts")
@click.option("--detailed", is_flag=True, help="Include detailed metrics for each protocol")
@click.option("--historical", is_flag=True, help="Include historical data analysis")
@click.option(
    "--data-dir",
    type=str,
    default="data/historical",
    help="Directory containing historical data (default: data/historical)",
)
def compare_protocols(protocols, metric, format, output_dir, chart, detailed, historical, data_dir):
    """⚖️ Compare token distributions across multiple protocols.

    Generates side-by-side comparisons of concentration metrics and governance patterns.

    Examples:
      gova compare-protocols --protocols compound,uniswap --metric gini_coefficient
      gova compare-protocols --protocols compound,uniswap,aave --format html --chart
      gova compare-protocols --protocols all --detailed
    """
    # Parse protocols
    if protocols.lower() == "all":
        protocol_list = SUPPORTED_PROTOCOLS
    else:
        protocol_list = [p.strip().lower() for p in protocols.split(",")]

    # Validate protocols
    invalid_protocols = [p for p in protocol_list if p not in SUPPORTED_PROTOCOLS]
    if invalid_protocols:
        click.echo(f"❌ Invalid protocols: {', '.join(invalid_protocols)}", err=True)
        click.echo(f"Supported protocols: {', '.join(SUPPORTED_PROTOCOLS)}")
        sys.exit(1)

    click.echo(f"⚖️ Comparing protocols: {', '.join(p.upper() for p in protocol_list)}")
    click.echo(f"📊 Primary metric: {metric}")

    try:
        api_client = APIClient()
        comparison_results = {}

        for protocol in protocol_list:
            click.echo(f"📡 Analyzing {protocol.upper()}...")

            # Get data for each protocol with robust type conversion
            holders_data = api_client.get_token_holders(protocol, limit=100, use_real_data=True)
            balances = extract_balances_from_holders(holders_data, click)

            if not balances:
                # Fallback to simulated data if no valid balances found
                click.echo(f"⚠️  No valid balance data for {protocol}, using simulated data", err=True)
                simulator = TokenDistributionSimulator()
                # Use an appropriate limit (100 is typical for comparative analysis)
                # Could enhance in future to accept a limit parameter for simulation
                simulated_holders = simulator.generate_power_law_distribution(100)
                # Extract just the balances from the simulated data
                balances = extract_balances_from_holders(simulated_holders, click)

            # Calculate metrics
            metrics = calculate_all_concentration_metrics(balances)

            comparison_results[protocol] = {
                "protocol_info": PROTOCOLS[protocol],
                "metrics": metrics,
                "summary": {
                    "primary_metric_value": metrics.get(metric, 0),
                    "total_holders": len(balances),
                    "top_10_concentration": sum(sorted(balances, reverse=True)[:10]) / sum(balances) * 100
                    if sum(balances) > 0
                    else 0,
                },
            }

        # Generate comparison summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        final_results = {
            "comparison_timestamp": datetime.now().isoformat(),
            "primary_metric": metric,
            "protocols_compared": protocol_list,
            "results": comparison_results,
            "ranking": sorted(
                protocol_list, key=lambda p: comparison_results[p]["summary"]["primary_metric_value"], reverse=True
            ),
        }

        # Handle different output formats
        if format == "json":
            output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.json")
            with open(output_file, "w") as f:
                json.dump(final_results, f, indent=2)
        elif format == "html":
            # Generate HTML comparison report
            report_gen = ReportGenerator()
            output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.html")
            html_content = report_gen.generate_comparison_report(comparison_results, output_format="html")
            with open(output_file, "w") as f:
                f.write(html_content)
        elif format == "png":
            # Generate PNG chart
            try:
                chart_gen = ChartGenerator()
                output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.png")

                # Extract protocols and values from comparison_results
                protocol_names = list(comparison_results.keys())
                metric_values = [result["summary"]["primary_metric_value"] for result in comparison_results.values()]

                chart_gen.plot_protocol_comparison(protocol_names, metric_values, metric, output_file)
            except ImportError:
                click.echo("⚠️  Chart generation not available (missing dependencies)", err=True)
                # Fallback to JSON if PNG generation fails
                output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.json")
                with open(output_file, "w") as f:
                    json.dump(final_results, f, indent=2)

        # Display summary
        click.echo(f"\n✅ Comparison complete!")
        click.echo(f"📁 Results saved: {output_file}")

        if detailed:
            click.echo(f"\n📊 Protocol Rankings by {metric}:")
            for i, protocol in enumerate(final_results["ranking"], 1):
                value = comparison_results[protocol]["summary"]["primary_metric_value"]
                click.echo(f"  {i}. {protocol.upper()}: {value:.4f}")

        return output_file

    except Exception as e:
        click.echo(f"❌ Comparison failed: {e}", err=True)
        sys.exit(1)


# EXPORT COMMAND (renamed to export-historical-data for tests)
@cli.command("export-historical-data")
@click.option("--protocol", type=ProtocolChoice(), required=True, help="Protocol to export data for")
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Export format (default: json)")
@click.option(
    "--output-dir",
    type=str,
    default="exports",
    callback=validate_output_dir,
    help="Directory to save exported files (default: exports)",
)
@click.option(
    "--limit",
    type=int,
    default=1000,
    callback=validate_positive_int,
    help="Maximum number of records to export (default: 1000)",
)
@click.option("--include-historical", is_flag=True, help="Include historical snapshots in export")
@click.option(
    "--metric",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Metric to focus on for historical export",
)
@click.option("--data-dir", type=str, default="data/historical", help="Directory containing historical data")
def export_historical_data(protocol, format, output_dir, limit, include_historical, metric, data_dir):
    """💾 Export token holder and governance data.

    Exports current and historical data in various formats for external analysis.

    Examples:
      gova export-historical-data --protocol compound --format csv --limit 500
      gova export-historical-data --protocol uniswap --include-historical --format json
    """
    click.echo(f"💾 Exporting {protocol.upper()} data...")

    try:
        api_client = APIClient()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Check if historical data exists first
        has_historical_data = False
        if os.path.exists(data_dir):
            data_manager = historical_data.HistoricalDataManager(data_dir=data_dir)
            snapshots = data_manager.get_snapshots(protocol)
            has_historical_data = len(snapshots) > 0

        # Export historical data if available (default behavior for this command)
        if has_historical_data:
            output_file = os.path.join(output_dir, f"{protocol}_{metric}_historical.{format}")

            historical_data_export = {
                "protocol": protocol,
                "metric": metric,
                "export_timestamp": datetime.now().isoformat(),
                "data_points": [],
            }

            for snapshot in snapshots:
                snapshot_data = data_manager.load_snapshot(protocol, snapshot["timestamp"])
                if snapshot_data:
                    historical_data_export["data_points"].append(
                        {
                            "timestamp": snapshot["timestamp"],
                            "metrics": snapshot_data.get("metrics", {}),
                            "summary": snapshot_data.get("summary", {}),
                        }
                    )

            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(historical_data_export, f, indent=2)
            elif format == "csv":
                # Convert historical data to CSV format
                csv_data = []
                for data_point in historical_data_export["data_points"]:
                    row = {
                        "timestamp": data_point["timestamp"],
                        "metric": metric,
                        "value": data_point["metrics"].get(metric, 0),
                    }
                    # Add other metrics as columns
                    for key, value in data_point["metrics"].items():
                        row[f"metric_{key}"] = value
                    csv_data.append(row)

                with open(output_file, "w", newline="") as f:
                    if csv_data:
                        fieldnames = csv_data[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(csv_data)

            click.echo("✅ Export complete!")
            click.echo(f"📁 Historical data exported: {output_file}")
            return output_file

        # Fall back to current data if no historical data available
        else:
            click.echo(f"⚠️  No historical data found for {protocol}, exporting current data instead", err=True)
            output_file = os.path.join(output_dir, f"{protocol}_export_{timestamp}.{format}")

            # Get current data
            holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)

            if not holders_data:
                click.echo("⚠️  No data available for export", err=True)
                # Create empty file to satisfy tests
                if format == "json":
                    with open(output_file, "w") as f:
                        json.dump({"protocol": protocol, "data": [], "message": "No data available"}, f, indent=2)
                elif format == "csv":
                    with open(output_file, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["protocol", "message"])
                        writer.writerow([protocol, "No data available"])
            else:
                if format == "json":
                    export_data = {
                        "protocol": protocol,
                        "export_timestamp": datetime.now().isoformat(),
                        "total_records": len(holders_data),
                        "holders": holders_data[:limit],
                    }
                    with open(output_file, "w") as f:
                        json.dump(export_data, f, indent=2)

                elif format == "csv":
                    with open(output_file, "w", newline="") as f:
                        if holders_data:
                            fieldnames = holders_data[0].keys()
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(holders_data[:limit])

            click.echo("✅ Export complete!")
            click.echo(f"📁 Current data exported: {output_file}")
            return output_file

    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


# HISTORICAL ANALYSIS COMMAND
@cli.command("historical-analysis")
@click.option("--protocol", type=ProtocolChoice(), required=True, help="Protocol to analyze historical data for")
@click.option(
    "--metric",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Metric to analyze over time (default: gini_coefficient)",
)
@click.option(
    "--data-dir",
    type=str,
    default="data/historical",
    help="Directory containing historical data (default: data/historical)",
)
@click.option(
    "--output-dir",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save analysis results (default: outputs)",
)
@click.option("--format", type=click.Choice(["json", "png"]), default="png", help="Output format (default: png)")
@click.option("--plot", is_flag=True, default=True, help="Generate time series plots")
def historical_analysis(protocol, metric, data_dir, output_dir, format, plot):
    """📈 Analyze historical trends in token distribution.

    Examines how concentration metrics have evolved over time for a protocol.

    Examples:
      gova historical-analysis --protocol compound --metric gini_coefficient
      gova historical-analysis --protocol uniswap --format json --data-dir ./data
    """
    click.echo(f"📈 Analyzing historical {metric} trends for {protocol.upper()}...")

    try:
        # Check if historical data exists
        if not os.path.exists(data_dir):
            click.echo(f"❌ Historical data directory not found: {data_dir}", err=True)
            click.echo("💡 Generate historical data first using: gova simulate-historical", err=True)
            sys.exit(1)

        data_manager = historical_data.HistoricalDataManager(data_dir=data_dir)
        snapshots = data_manager.get_snapshots(protocol)

        if not snapshots:
            click.echo(f"❌ No historical data found for {protocol}", err=True)
            sys.exit(1)

        click.echo(f"📊 Found {len(snapshots)} historical snapshots")

        # Analyze trends
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "png" or plot:
            # Generate plot
            try:
                chart_gen = ChartGenerator()
                plot_file = os.path.join(output_dir, f"{protocol}_{metric}.png")

                # Extract metric values over time
                dates = []
                values = []
                for snapshot in snapshots:
                    snapshot_data = data_manager.load_snapshot(protocol, snapshot["timestamp"])
                    if snapshot_data and "metrics" in snapshot_data:
                        dates.append(snapshot["timestamp"])
                        values.append(snapshot_data["metrics"].get(metric, 0))

                chart_gen.plot_historical_trends(dates, values, metric, protocol, plot_file)
                click.echo(f"📊 Historical plot saved: {plot_file}")

            except ImportError:
                click.echo("⚠️  Chart generation not available (missing dependencies)", err=True)

        if format == "json":
            # Save analysis results
            output_file = os.path.join(output_dir, f"{protocol}_{metric}_historical_{timestamp}.json")

            analysis_results = {
                "protocol": protocol,
                "metric": metric,
                "analysis_timestamp": datetime.now().isoformat(),
                "snapshots_analyzed": len(snapshots),
                "historical_data": [],
            }

            for snapshot in snapshots:
                snapshot_data = data_manager.load_snapshot(protocol, snapshot["timestamp"])
                if snapshot_data:
                    analysis_results["historical_data"].append(
                        {
                            "timestamp": snapshot["timestamp"],
                            "metric_value": snapshot_data.get("metrics", {}).get(metric, 0),
                            "summary": snapshot_data.get("summary", {}),
                        }
                    )

            with open(output_file, "w") as f:
                json.dump(analysis_results, f, indent=2)

            click.echo(f"📁 Analysis saved: {output_file}")

        click.echo("✅ Historical analysis complete!")

    except Exception as e:
        click.echo(f"❌ Historical analysis failed: {e}", err=True)
        sys.exit(1)


# GENERATE REPORT COMMAND (renamed from report)
@cli.command("generate-report")
@click.option("--protocol", type=ProtocolChoice(), required=True, help="Protocol to generate report for")
@click.option("--format", type=click.Choice(["html"]), default="html", help="Report format (default: html)")
@click.option(
    "--output-dir",
    type=str,
    default="reports",
    callback=validate_output_dir,
    help="Directory to save report files (default: reports)",
)
@click.option("--include-historical", is_flag=True, help="Include historical analysis in report")
@click.option("--data-dir", type=str, default="data/historical", help="Directory containing historical data")
def generate_report(protocol, format, output_dir, include_historical, data_dir):
    """📋 Generate comprehensive analysis reports.

    Creates detailed reports with visualizations, metrics, and insights.

    Examples:
      gova generate-report --protocol compound --format html
      gova generate-report --protocol uniswap --include-historical
    """
    click.echo(f"📋 Generating {format.upper()} report for {protocol.upper()}...")

    try:
        api_client = APIClient()
        report_gen = ReportGenerator()

        # Get current data with improved error handling
        holders_data = api_client.get_token_holders(protocol, limit=1000, use_real_data=True)
        balances = extract_balances_from_holders(holders_data, click)

        if not balances:
            click.echo("⚠️  No live data available, using simulated data", err=True)
            simulator = TokenDistributionSimulator()
            # Use a sensible default for reports (1000 data points)
            # Could enhance in future to accept a limit parameter for simulation
            simulated_holders = simulator.generate_power_law_distribution(1000)
            # Extract just the balances from the simulated data
            balances = extract_balances_from_holders(simulated_holders, click)

        # Calculate current metrics
        current_metrics = calculate_all_concentration_metrics(balances)

        # Prepare report data
        report_data = {
            "protocol": protocol,
            "protocol_info": PROTOCOLS.get(protocol, {}),
            "timestamp": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "holders_count": len(balances),
            "total_supply": sum(balances),
        }

        # Add historical data if requested
        if include_historical and os.path.exists(data_dir):
            data_manager = historical_data.HistoricalDataManager(data_dir=data_dir)
            snapshots = data_manager.get_snapshots(protocol)
            report_data["historical_snapshots"] = len(snapshots)
            report_data["include_historical"] = True
        else:
            report_data["include_historical"] = False

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"{protocol}_report.{format}")

        if format == "html":
            html_content = report_gen.generate_html_report(report_data)
            with open(report_file, "w") as f:
                f.write(html_content)

        click.echo("✅ Report generated successfully!")
        click.echo(f"📁 Report saved: {report_file}")
        return report_file

    except Exception as e:
        click.echo(f"❌ Report generation failed: {e}", err=True)
        sys.exit(1)


# SIMULATE HISTORICAL COMMAND
@cli.command("simulate-historical")
@click.option("--protocol", type=ProtocolChoice(), required=True, help="Protocol to simulate historical data for")
@click.option("--snapshots", type=int, default=10, help="Number of historical snapshots to generate (default: 10)")
@click.option("--interval", type=int, default=7, help="Interval between snapshots in days (default: 7)")
@click.option(
    "--data-dir",
    type=str,
    default="data/historical",
    callback=validate_output_dir,
    help="Directory to store historical data (default: data/historical)",
)
@click.option(
    "--output-dir",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory for output files (default: outputs)",
)
def simulate_historical(protocol, snapshots, interval, data_dir, output_dir):
    """🕒 Generate simulated historical data for testing.

    Creates synthetic historical snapshots for protocol analysis and testing.

    Examples:
      gova simulate-historical --protocol compound --snapshots 20 --interval 7
      gova simulate-historical --protocol uniswap --snapshots 50 --data-dir ./test_data
    """
    click.echo(f"🕒 Generating {snapshots} historical snapshots for {protocol.upper()}...")
    click.echo(f"📅 Interval: {interval} days")

    try:
        data_manager = historical_data.HistoricalDataManager(data_dir=data_dir)

        # Generate historical data
        historical_data.simulate_historical_data(
            protocol=protocol, num_snapshots=snapshots, interval_days=interval, data_manager=data_manager
        )

        click.echo("✅ Historical data simulation complete!")
        click.echo(f"📁 Data stored in: {data_dir}")
        click.echo(f"📊 Generated {snapshots} snapshots with {interval}-day intervals")

        # Verify the data was created
        generated_snapshots = data_manager.get_snapshots(protocol)
        click.echo(f"✅ Verified {len(generated_snapshots)} snapshots created")

    except Exception as e:
        click.echo(f"❌ Historical simulation failed: {e}", err=True)
        sys.exit(1)


# STATUS COMMAND
@cli.command()
@click.option("--check-apis", is_flag=True, help="Check API key configuration and connectivity")
@click.option("--test-protocols", is_flag=True, help="Test data retrieval for all supported protocols")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed status information")
def status(check_apis, test_protocols, verbose):
    """🔍 Check system status and configuration.

    Validates API keys, connectivity, and system health.

    Examples:
      gova status --check-apis
      gova status --test-protocols --verbose
    """
    click.echo("🔍 Governance Token Analyzer Status Check")
    click.echo("=" * 50)

    try:
        # Check basic configuration
        click.echo("📋 Configuration:")
        click.echo(f"  • Supported protocols: {len(SUPPORTED_PROTOCOLS)}")
        click.echo(f"  • Available metrics: {len(SUPPORTED_METRICS)}")
        click.echo(f"  • Output formats: {len(SUPPORTED_FORMATS)}")

        if check_apis:
            click.echo("\n🔑 API Status:")
            api_client = APIClient()

            # Check each API key
            if hasattr(api_client, "etherscan_api_key") and api_client.etherscan_api_key:
                click.echo("  ✅ Etherscan API key configured")
            else:
                click.echo("  ❌ Etherscan API key missing")

            if hasattr(api_client, "alchemy_api_key") and api_client.alchemy_api_key:
                click.echo("  ✅ Alchemy API key configured")
            else:
                click.echo("  ⚠️  Alchemy API key missing")

            if hasattr(api_client, "graph_api_key") and api_client.graph_api_key:
                click.echo("  ✅ The Graph API key configured")
            else:
                click.echo("  ⚠️  The Graph API key missing")

        if test_protocols:
            click.echo("\n🧪 Protocol Testing:")
            api_client = APIClient()

            for protocol in SUPPORTED_PROTOCOLS:
                try:
                    click.echo(f"  Testing {protocol.upper()}...", nl=False)
                    holders = api_client.get_token_holders(protocol, limit=5, use_real_data=True)
                    if holders:
                        click.echo(" ✅")
                        if verbose:
                            click.echo(f"    Retrieved {len(holders)} holders")
                    else:
                        click.echo(" ⚠️  (using fallback data)")
                except Exception as e:
                    click.echo(f" ❌ ({str(e)[:50]}...)")

        click.echo("\n✅ Status check complete!")

    except Exception as e:
        click.echo(f"❌ Status check failed: {e}", err=True)
        sys.exit(1)


# VALIDATE COMMAND
@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    type=str,
    default="validation",
    callback=validate_output_dir,
    help="Directory to save validation results (default: validation)",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
def validate(input_file, output_dir, verbose):
    """🔍 Validate analysis output accuracy and consistency.

    Performs comprehensive validation of analysis results including
    mathematical accuracy, data consistency, and cross-validation.

    Examples:
      gova validate outputs/compound_analysis_20231201_120000.json
      gova validate reports/protocol_comparison.json --verbose
    """
    click.echo(f"🔍 Validating analysis output: {input_file}")

    try:
        from governance_token_analyzer.cli.validate import validate_analysis_output

        # Run validation
        result = validate_analysis_output(input_file, output_dir, verbose)

        if result["overall_valid"]:
            click.echo("✅ Validation passed!")
        else:
            click.echo("❌ Validation issues found")

        click.echo(f"📊 Validation score: {result['validation_score']:.1f}%")

        if verbose:
            click.echo(f"📁 Detailed report: {result['report_file']}")

    except ImportError:
        click.echo("❌ Validation module not available", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
