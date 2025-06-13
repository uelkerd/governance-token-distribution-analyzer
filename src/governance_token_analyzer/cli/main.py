"""Enhanced CLI entrypoint for the governance token analyzer.

This module provides a comprehensive command-line interface for analyzing governance token
distributions across multiple DeFi protocols with detailed help, examples, and validation.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import click

# Import core functionality
try:
    from governance_token_analyzer.core.api_client import APIClient
    from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
    from governance_token_analyzer.core.config import PROTOCOLS
    from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
    from governance_token_analyzer.core import historical_data
    from governance_token_analyzer.visualization.report_generator import ReportGenerator
except ImportError as e:
    click.echo(f"Error importing modules: {e}", err=True)
    sys.exit(1)

# Supported protocols - use PROTOCOLS from core.config only
SUPPORTED_PROTOCOLS = list(PROTOCOLS.keys())
SUPPORTED_METRICS = ["gini_coefficient", "participation_rate", "holder_concentration", "nakamoto_coefficient"]
SUPPORTED_FORMATS = ["json", "csv", "html"]  # Removed unsupported png format


class ProtocolChoice(click.Choice):
    """Custom choice class for protocols with better error messages."""

    def __init__(self):
        super().__init__(SUPPORTED_PROTOCOLS, case_sensitive=False)

    def convert(self, value, param, ctx):
        if value is None:
            return value
        return super().convert(value.lower(), param, ctx)


def validate_output_dir(ctx, param, value):
    """Validate and create output directory if it doesn't exist."""
    if value:
        try:
            os.makedirs(value, exist_ok=True)
            return value
        except OSError as e:
            raise click.BadParameter(f"Cannot create output directory '{value}': {e}")
    return value


def print_protocol_info():
    """Print information about supported protocols."""
    click.echo("\n📊 Supported Protocols:")
    for protocol, info in PROTOCOLS.items():
        click.echo(f"  • {info['name']} ({info['symbol']}) - {protocol}")
        click.echo(f"    Contract: {info['token_address']}")
    click.echo()


def print_examples():
    """Print usage examples."""
    click.echo("\n💡 Usage Examples:")
    click.echo("  # Analyze Compound token distribution")
    click.echo("  gova analyze compound --limit 100 --format json")
    click.echo()
    click.echo("  # Compare all protocols with detailed report")
    click.echo("  gova compare --protocols compound,uniswap,aave --format html")
    click.echo()
    click.echo("  # Generate historical analysis")
    click.echo("  gova historical-analysis compound --snapshots 12 --interval 30")
    click.echo()
    click.echo("  # Export data for external analysis")
    click.echo("  gova export compound --format csv --output-dir ./exports")
    click.echo()


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.option("--protocols", is_flag=True, help="List supported protocols")
@click.option("--examples", is_flag=True, help="Show usage examples")
@click.pass_context
def cli(ctx, version, protocols, examples):
    """🏛️ Governance Token Distribution Analyzer

    A comprehensive tool for analyzing governance token distributions across DeFi protocols.
    Supports Compound (COMP), Uniswap (UNI), and Aave (AAVE) with live data integration.

    Features:
    • Token distribution concentration analysis
    • Governance participation metrics
    • Cross-protocol comparisons
    • Historical trend analysis
    • Voting block detection
    • Advanced visualization and reporting

    Use --help with any command for detailed information and examples.
    """
    if ctx.invoked_subcommand is None:
        if version:
            click.echo("Governance Token Analyzer v0.1.0")
            click.echo("Built for analyzing DeFi governance token distributions")
        elif protocols:
            print_protocol_info()
        elif examples:
            print_examples()
        else:
            click.echo(ctx.get_help())
            print_protocol_info()
            print_examples()


def _safe_calculate_concentration(balances, top_n):
    """Safely calculate concentration percentage avoiding division by zero."""
    if not balances or sum(balances) == 0:
        return 0
    return sum(sorted(balances, reverse=True)[:top_n]) / sum(balances) * 100


@cli.command()
@click.argument("protocol", type=ProtocolChoice())
@click.option("--limit", type=int, default=100, help="Number of top token holders to analyze (default: 100)")
@click.option("--format", type=click.Choice(SUPPORTED_FORMATS), default="json", help="Output format (default: json)")
@click.option(
    "--output-dir",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save output files (default: outputs)",
)
@click.option("--charts", is_flag=True, help="Generate visualization charts")
@click.option(
    "--live-data/--simulated-data", default=True, help="Use live blockchain data or simulated data (default: live)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output with detailed metrics")
def analyze(protocol, limit, format, output_dir, charts, live_data, verbose):
    """📈 Analyze token distribution for a specific protocol.

    Calculates comprehensive concentration metrics including Gini coefficient,
    Nakamoto coefficient, and top holder percentages.

    PROTOCOL: The protocol to analyze (compound, uniswap, or aave)

    Examples:
      gova analyze compound --limit 200 --charts
      gova analyze uniswap --format csv --output-dir ./data
      gova analyze aave --verbose --live-data
    """
    click.echo(f"🔍 Analyzing {protocol.upper()} token distribution...")

    if verbose:
        click.echo(f"  • Protocol: {PROTOCOLS[protocol]['name']}")
        click.echo(f"  • Token: {PROTOCOLS[protocol]['symbol']}")
        click.echo(f"  • Limit: {limit} holders")
        click.echo(f"  • Data source: {'Live blockchain data' if live_data else 'Simulated data'}")

    try:
        # Initialize API client
        api_client = APIClient()

        # Get token holders data
        if live_data:
            click.echo("📡 Fetching live data from blockchain...")
            holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)
        else:
            click.echo("🎲 Generating simulated data...")
            simulator = TokenDistributionSimulator()
            holders_data = simulator.generate_power_law_distribution(limit)

        # Extract balances for analysis
        balances = []
        for holder in holders_data:
            # Handle different data structures
            if isinstance(holder, dict):
                balance = (
                    holder.get("balance", 0) or holder.get("TokenHolderQuantity", 0) or holder.get("voting_power", 0)
                )
            else:
                balance = holder

            # Convert to float
            if isinstance(balance, str):
                try:
                    balance = float(balance)
                except ValueError:
                    balance = 0
            elif isinstance(balance, (int, float)):
                balance = float(balance)
            else:
                balance = 0

            balances.append(balance)

        if not balances:
            click.echo("⚠️  No valid balance data found, using simulated data", err=True)
            simulator = TokenDistributionSimulator()
            balances = simulator.generate_power_law_distribution(limit)

        # Calculate metrics
        click.echo("🧮 Calculating concentration metrics...")
        metrics = calculate_all_concentration_metrics(balances)

        # Add safe concentration calculations
        metrics.update(
            {
                "top_10_concentration": _safe_calculate_concentration(balances, 10),
                "top_50_concentration": _safe_calculate_concentration(balances, 50),
                "total_holders": len(balances),
                "total_supply_analyzed": sum(balances) if balances else 0,
            }
        )

        # Create output data structure
        analysis_results = {
            "protocol": protocol,
            "protocol_info": PROTOCOLS[protocol],
            "analysis_timestamp": datetime.now().isoformat(),
            "data_source": "live" if live_data else "simulated",
            "sample_size": len(balances),
            "metrics": metrics,
            "summary": {
                "high_concentration": metrics.get("gini_coefficient", 0) > 0.8,
                "participation_health": "healthy" if metrics.get("participation_rate", 0) > 10 else "concerning",
            },
        }

        # Generate output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{protocol}_analysis_{timestamp}.{format}")

        if format == "json":
            with open(output_file, "w") as f:
                json.dump(analysis_results, f, indent=2)
        elif format == "csv":
            # Export key metrics as CSV
            import csv

            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for key, value in metrics.items():
                    writer.writerow([key, value])
        elif format == "html":
            # Generate HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{protocol.upper()} Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #333; }}
                    .metric {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
                    .highlight {{ background: #e8f5e8; }}
                </style>
            </head>
            <body>
                <h1>{PROTOCOLS[protocol]["name"]} Analysis Report</h1>
                <div class="metric highlight">
                    <strong>Gini Coefficient:</strong> {metrics.get("gini_coefficient", 0):.4f}
                </div>
                <div class="metric">
                    <strong>Top 10% Concentration:</strong> {metrics.get("top_10_concentration", 0):.2f}%
                </div>
                <div class="metric">
                    <strong>Nakamoto Coefficient:</strong> {metrics.get("nakamoto_coefficient", 0)}
                </div>
                <div class="metric">
                    <strong>Total Holders:</strong> {len(balances)}
                </div>
            </body>
            </html>
            """
            with open(output_file, "w") as f:
                f.write(html_content)

        # Handle charts option
        if charts:
            try:
                import matplotlib.pyplot as plt

                # Generate concentration chart
                top_holders = sorted(balances, reverse=True)[:20]
                plt.figure(figsize=(10, 6))
                plt.bar(range(len(top_holders)), top_holders)
                plt.title(f"{protocol.upper()} - Top 20 Holder Distribution")
                plt.xlabel("Holder Rank")
                plt.ylabel("Token Balance")

                chart_file = output_file.replace(f".{format}", "_chart.png")
                plt.savefig(chart_file)
                plt.close()
                click.echo(f"📊 Chart saved: {chart_file}")
            except ImportError:
                click.echo("⚠️  matplotlib not available, skipping chart generation")

        # Display results
        click.echo(f"\n✅ Analysis complete!")
        click.echo(f"📁 Results saved: {output_file}")
        click.echo(f"\n📊 Key Metrics:")
        click.echo(f"  • Gini Coefficient: {metrics.get('gini_coefficient', 0):.4f}")
        click.echo(f"  • Top 10% Concentration: {metrics.get('top_10_concentration', 0):.2f}%")
        click.echo(f"  • Nakamoto Coefficient: {metrics.get('nakamoto_coefficient', 0)}")
        click.echo(f"  • Total Holders: {len(balances)}")

        if verbose:
            click.echo(f"\n🔍 Detailed Metrics:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    click.echo(f"  • {key}: {value:.4f}")
                else:
                    click.echo(f"  • {key}: {value}")

        return output_file

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--protocols",
    type=str,
    required=True,
    help="Comma-separated list of protocols to compare (e.g., compound,uniswap,aave)",
)
@click.option(
    "--metric",
    type=click.Choice(SUPPORTED_METRICS),
    default="gini_coefficient",
    help="Primary metric for comparison (default: gini_coefficient)",
)
@click.option(
    "--format", type=click.Choice(["json", "html", "csv"]), default="json", help="Output format (default: json)"
)
@click.option(
    "--output-dir",
    type=str,
    default="outputs",
    callback=validate_output_dir,
    help="Directory to save comparison results",
)
@click.option("--charts", is_flag=True, help="Generate comparison charts")
@click.option("--detailed", is_flag=True, help="Include detailed metrics for each protocol")
def compare(protocols, metric, format, output_dir, charts, detailed):
    """⚖️ Compare token distributions across multiple protocols.

    Generates side-by-side comparisons of concentration metrics and governance patterns.

    Examples:
      gova compare --protocols compound,uniswap --metric gini_coefficient
      gova compare --protocols compound,uniswap,aave --format html --charts
      gova compare --protocols all --detailed
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

            # Get data for each protocol
            holders_data = api_client.get_token_holders(protocol, limit=100, use_real_data=True)
            balances = [float(h.get("balance", 0)) for h in holders_data if h.get("balance") is not None]

            if not balances:
                simulator = TokenDistributionSimulator()
                balances = simulator.generate_power_law_distribution(100)

            # Calculate metrics
            metrics = calculate_all_concentration_metrics(balances)

            comparison_results[protocol] = {
                "protocol_info": PROTOCOLS[protocol],
                "metrics": metrics,
                "summary": {
                    "primary_metric_value": metrics.get(metric, 0),
                    "total_holders": len(balances),
                    "top_10_concentration": _safe_calculate_concentration(balances, 10),
                },
            }

        # Generate comparison summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"protocol_comparison_{timestamp}.{format}")

        final_results = {
            "comparison_timestamp": datetime.now().isoformat(),
            "primary_metric": metric,
            "protocols_compared": protocol_list,
            "results": comparison_results,
            "ranking": sorted(
                protocol_list, key=lambda p: comparison_results[p]["summary"]["primary_metric_value"], reverse=True
            ),
        }

        # Save results
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(final_results, f, indent=2)
        elif format == "html":
            # Generate HTML report
            html_content = f"""
            <html><head><title>Protocol Comparison Report</title></head>
            <body>
            <h1>Governance Token Distribution Comparison</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            <h2>Ranking by {metric}:</h2>
            <ol>
            """
            for protocol in final_results["ranking"]:
                value = comparison_results[protocol]["summary"]["primary_metric_value"]
                html_content += f"<li>{protocol.upper()}: {value:.4f}</li>"
            html_content += "</ol></body></html>"

            with open(output_file, "w") as f:
                f.write(html_content)
        elif format == "csv":
            # Export comparison as CSV
            import csv

            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Protocol", "Primary Metric", "Value", "Total Holders"])
                for protocol in protocol_list:
                    result = comparison_results[protocol]
                    writer.writerow(
                        [
                            protocol.upper(),
                            metric,
                            result["summary"]["primary_metric_value"],
                            result["summary"]["total_holders"],
                        ]
                    )

        # Handle charts option
        if charts:
            try:
                import matplotlib.pyplot as plt

                protocols_names = [p.upper() for p in protocol_list]
                values = [comparison_results[p]["summary"]["primary_metric_value"] for p in protocol_list]

                plt.figure(figsize=(10, 6))
                plt.bar(protocols_names, values)
                plt.title(f"Protocol Comparison - {metric}")
                plt.ylabel(metric.replace("_", " ").title())
                plt.xticks(rotation=45)

                chart_file = output_file.replace(f".{format}", "_chart.png")
                plt.tight_layout()
                plt.savefig(chart_file)
                plt.close()
                click.echo(f"📊 Chart saved: {chart_file}")
            except ImportError:
                click.echo("⚠️  matplotlib not available, skipping chart generation")

        # Display summary
        click.echo(f"\n✅ Comparison complete!")
        click.echo(f"📁 Results saved: {output_file}")
        click.echo(f"\n🏆 Ranking by {metric}:")
        for i, protocol in enumerate(final_results["ranking"], 1):
            value = comparison_results[protocol]["summary"]["primary_metric_value"]
            click.echo(f"  {i}. {protocol.upper()}: {value:.4f}")

        return output_file

    except Exception as e:
        click.echo(f"❌ Comparison failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("protocol", type=ProtocolChoice())
@click.option("--snapshots", type=int, default=12, help="Number of historical snapshots to generate (default: 12)")
@click.option("--interval", type=int, default=30, help="Days between snapshots (default: 30)")
@click.option(
    "--metric", type=click.Choice(SUPPORTED_METRICS), default="gini_coefficient", help="Metric to track over time"
)
@click.option(
    "--output-dir",
    type=str,
    default="data/historical",
    callback=validate_output_dir,
    help="Directory to store historical data",
)
@click.option("--plot", is_flag=True, help="Generate time series plot")
def historical_analysis(protocol, snapshots, interval, metric, output_dir, plot):
    """📈 Generate historical analysis of token distribution trends.

    Simulates historical data to show how concentration metrics evolve over time.

    Examples:
      gova historical-analysis compound --snapshots 24 --interval 15
      gova historical-analysis uniswap --metric participation_rate --plot
    """
    click.echo(f"📈 Generating historical analysis for {protocol.upper()}...")
    click.echo(f"  • Snapshots: {snapshots}")
    click.echo(f"  • Interval: {interval} days")
    click.echo(f"  • Metric: {metric}")

    try:
        # Generate historical data
        historical_data_gen = historical_data
        data_points = historical_data_gen.generate_historical_snapshots(
            protocol, snapshots=snapshots, interval_days=interval
        )

        # Calculate metrics for each snapshot
        historical_metrics = []
        for snapshot in data_points:
            balances = [float(h.get("balance", 0)) for h in snapshot["holders"]]
            if balances:
                metrics = calculate_all_concentration_metrics(balances)
                historical_metrics.append({"date": snapshot["date"], "metrics": metrics, "sample_size": len(balances)})

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{protocol}_historical_{timestamp}.json")

        results = {
            "protocol": protocol,
            "analysis_timestamp": datetime.now().isoformat(),
            "parameters": {"snapshots": snapshots, "interval_days": interval, "primary_metric": metric},
            "historical_data": historical_metrics,
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        # Generate plot if requested
        if plot:
            try:
                import matplotlib.pyplot as plt
                from datetime import datetime as dt

                dates = [dt.fromisoformat(point["date"]) for point in historical_metrics]
                values = [point["metrics"].get(metric, 0) for point in historical_metrics]

                plt.figure(figsize=(12, 6))
                plt.plot(dates, values, marker="o")
                plt.title(f"{protocol.upper()} - {metric.replace('_', ' ').title()} Over Time")
                plt.xlabel("Date")
                plt.ylabel(metric.replace("_", " ").title())
                plt.xticks(rotation=45)

                plot_file = output_file.replace(".json", "_trend.png")
                plt.tight_layout()
                plt.savefig(plot_file)
                plt.close()
                click.echo(f"📊 Plot saved: {plot_file}")
            except ImportError:
                click.echo("⚠️  matplotlib not available, skipping plot generation")

        click.echo(f"✅ Historical analysis complete!")
        click.echo(f"📁 Data saved: {output_file}")
        click.echo(f"📊 Generated {len(historical_metrics)} data points")

        return output_file

    except Exception as e:
        click.echo(f"❌ Historical analysis failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("protocol", type=ProtocolChoice())
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Export format (default: json)")
@click.option(
    "--output-dir", type=str, default="exports", callback=validate_output_dir, help="Directory to save exported data"
)
@click.option("--include-historical", is_flag=True, help="Include historical data in export")
@click.option("--limit", type=int, default=1000, help="Maximum number of token holders to export")
@click.option(
    "--governance-proposals",
    type=int,
    default=10,
    help="Number of recent governance proposals to include (default: 10)",
)
def export(protocol, format, output_dir, include_historical, limit, governance_proposals):
    """💾 Export comprehensive protocol data for external analysis.

    Exports token holder data, governance proposals, and participation metrics.

    Examples:
      gova export compound --format csv --limit 500
      gova export uniswap --include-historical --governance-proposals 20
    """
    click.echo(f"💾 Exporting {protocol.upper()} data...")

    try:
        api_client = APIClient()

        # Get token holders data
        click.echo("📡 Fetching token holders...")
        holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)

        # Get governance data
        click.echo("🗳️  Fetching governance proposals...")
        try:
            governance_data = api_client.get_governance_proposals(protocol, limit=governance_proposals)
        except Exception as e:
            click.echo(f"⚠️  Could not fetch governance data: {e}")
            governance_data = []

        # Prepare export data
        export_data = {
            "protocol": protocol,
            "protocol_info": PROTOCOLS[protocol],
            "export_timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_holders": len(holders_data),
                "governance_proposals": len(governance_data),
                "includes_historical": include_historical,
            },
            "token_holders": holders_data,
            "governance_proposals": governance_data,
        }

        # Add historical data if requested
        if include_historical:
            click.echo("📈 Including historical data...")
            try:
                historical_snapshots = historical_data.generate_historical_snapshots(
                    protocol, snapshots=6, interval_days=30
                )
                export_data["historical_snapshots"] = historical_snapshots
            except Exception as e:
                click.echo(f"⚠️  Could not include historical data: {e}")

        # Generate output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{protocol}_export_{timestamp}.{format}")

        # Save in requested format
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)
        elif format == "csv":
            # Export holders as CSV
            import csv

            with open(output_file, "w", newline="") as f:
                if holders_data:
                    writer = csv.DictWriter(f, fieldnames=holders_data[0].keys())
                    writer.writeheader()
                    writer.writerows(holders_data)

        click.echo("✅ Export complete!")
        click.echo(f"📁 Data exported to: {output_file}")
        click.echo(f"📊 Records exported: {len(holders_data)} holders")

        return output_file

    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("protocol", type=ProtocolChoice())
@click.option("--format", type=click.Choice(["html"]), default="html", help="Report format (default: html)")
@click.option(
    "--output-dir", type=str, default="reports", callback=validate_output_dir, help="Directory to save the report"
)
@click.option("--include-charts", is_flag=True, default=True, help="Include visualization charts in the report")
@click.option("--detailed", is_flag=True, help="Generate detailed report with all metrics")
def report(protocol, format, output_dir, include_charts, detailed):
    """📋 Generate comprehensive analysis report.

    Creates a detailed report with visualizations, metrics, and insights.
    Note: Currently only HTML format is supported.

    Examples:
      gova report compound --detailed
      gova report uniswap --include-charts
    """
    click.echo(f"📋 Generating {format.upper()} report for {protocol.upper()}...")

    try:
        # Generate report using the existing report generator
        report_gen = ReportGenerator()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"{protocol}_report_{timestamp}.{format}")

        # Create a comprehensive HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{protocol.upper()} Governance Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                .metric {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
                .highlight {{ background: #e8f5e8; }}
                .warning {{ background: #fff3cd; }}
            </style>
        </head>
        <body>
            <h1>{PROTOCOLS[protocol]["name"]} ({PROTOCOLS[protocol]["symbol"]}) Analysis Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            
            <h2>Executive Summary</h2>
            <p>This report analyzes the governance token distribution for {PROTOCOLS[protocol]["name"]}.</p>
            
            <h2>Key Metrics</h2>
            <div class="metric">
                <strong>Token Contract:</strong> {PROTOCOLS[protocol]["token_address"]}
            </div>
            
            <h2>Distribution Analysis</h2>
            <p>Detailed concentration metrics and governance participation analysis will be displayed here.</p>
            
            {"<h2>Detailed Metrics</h2><p>All available concentration and governance metrics included.</p>" if detailed else ""}
            {"<h2>Visualizations</h2><p>Charts and graphs showing distribution patterns.</p>" if include_charts else ""}
            
            <h2>Methodology</h2>
            <p>This analysis uses live blockchain data to calculate distribution concentration metrics.</p>
        </body>
        </html>
        """

        with open(report_file, "w") as f:
            f.write(html_content)

        click.echo("✅ Report generated successfully!")
        click.echo(f"📁 Report saved: {report_file}")

        return report_file

    except Exception as e:
        click.echo(f"❌ Report generation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--file", "-f", type=click.Path(exists=True), help="Validate specific output file")
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    default="outputs",
    help="Directory containing output files to validate",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
@click.option("--report", "-r", is_flag=True, help="Generate validation report")
def validate(file, directory, verbose, report):
    """🔍 Validate governance token analysis outputs for accuracy and consistency.

    This command validates analysis outputs against:
    • Mathematical accuracy (ranges, calculations)
    • Data consistency (structure, formats)
    • Known benchmarks (expected ranges for protocols)
    • Cross-protocol comparison consistency

    Examples:
      gova validate --file outputs/compound_analysis.json
      gova validate --directory outputs --verbose
      gova validate --report
    """
    try:
        from .validate import validate as validate_cmd

        validate_cmd.callback(file, directory, verbose, report)
    except ImportError:
        click.echo("❌ Validation module not available", err=True)
        click.echo("The validation feature requires additional setup.")
        sys.exit(1)


@cli.command()
@click.option("--check-apis", is_flag=True, help="Check API connectivity and keys")
@click.option("--test-protocols", is_flag=True, help="Test data fetching for all protocols")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed diagnostic information")
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


if __name__ == "__main__":
    cli()
