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

# Configuration constants
SUPPORTED_PROTOCOLS = list(PROTOCOLS.keys())
SUPPORTED_METRICS = [
    "gini_coefficient",
    "nakamoto_coefficient", 
    "shannon_entropy",
    "herfindahl_index",
    "participation_rate"
]
SUPPORTED_FORMATS = ["json", "csv", "html", "png"]

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
@click.option('--protocol', type=ProtocolChoice(), required=True,
              help='Protocol to analyze (compound, uniswap, aave)')
@click.option('--limit', type=int, default=1000,
              help='Maximum number of token holders to analyze (default: 1000)')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json',
              help='Output format (default: json)')
@click.option('--output-dir', type=str, default='outputs', callback=validate_output_dir,
              help='Directory to save output files (default: outputs)')
@click.option('--chart', is_flag=True, 
              help='Generate distribution charts')
@click.option('--live-data/--simulated-data', default=True,
              help='Use live blockchain data or simulated data (default: live)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output with detailed metrics')
def analyze(protocol, limit, format, output_dir, chart, live_data, verbose):
    """📈 Analyze token distribution for a specific protocol.
    
    Retrieves current token holder data and calculates concentration metrics
    including Gini coefficient, Nakamoto coefficient, and participation rates.
    
    Examples:
      gova analyze --protocol compound --limit 500 --chart
      gova analyze --protocol uniswap --format csv --verbose
      gova analyze --protocol aave --simulated-data --output-dir ./test
    """
    click.echo(f"📊 Analyzing {protocol.upper()} token distribution...")
    click.echo(f"🔍 Fetching data for {limit:,} holders...")

    try:
        api_client = APIClient()
        
        # Get token holder data
        if live_data:
            holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)
            if not holders_data:
                click.echo("⚠️  No live data available, using simulated data", err=True)
                simulator = TokenDistributionSimulator()
                balances = simulator.generate_power_law_distribution(limit)
                holders_data = [{"address": f"0x{i:040x}", "balance": balance} for i, balance in enumerate(balances)]
        else:
            simulator = TokenDistributionSimulator()
            balances = simulator.generate_power_law_distribution(limit)
            holders_data = [{"address": f"0x{i:040x}", "balance": balance} for i, balance in enumerate(balances)]

        # Extract balances
        balances = []
        for holder in holders_data:
            balance = (
                holder.get("balance", 0) or holder.get("TokenHolderQuantity", 0) or holder.get("voting_power", 0)
            )
            if balance and balance > 0:
                balances.append(float(balance))

        if not balances:
            click.echo("❌ No valid balance data found", err=True)
            sys.exit(1)

        # Calculate metrics
        metrics = calculate_all_concentration_metrics(balances)
        
        # Prepare results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"{protocol}_analysis_{timestamp}.{format}")

        results = {
            "protocol": protocol,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_holders": len(holders_data),
            "total_supply": sum(balances),
            "metrics": metrics,
            "summary": {
                "top_10_concentration": sum(sorted(balances, reverse=True)[:10]) / sum(balances) * 100 if balances and sum(balances) > 0 else 0,
                "top_50_concentration": sum(sorted(balances, reverse=True)[:50]) / sum(balances) * 100 if balances and sum(balances) > 0 else 0,
                "average_balance": sum(balances) / len(balances) if balances else 0,
            }
        }

        # Save results
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
        elif format == "csv":
            import csv
            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Address", "Balance", "Percentage"])
                total = sum(balances)
                for holder in holders_data[:limit]:
                    balance = float(holder.get("balance", 0) or 0)
                    percentage = (balance / total * 100) if total > 0 else 0
                    writer.writerow([holder.get("address", ""), balance, f"{percentage:.4f}%"])

        # Generate chart if requested
        if chart:
            try:
                from governance_token_analyzer.visualization.chart_generator import ChartGenerator
                chart_gen = ChartGenerator()
                plot_file = os.path.join(output_dir, f"{protocol}_distribution_{timestamp}.png")
                chart_gen.plot_distribution_analysis(balances, protocol, plot_file)
                click.echo(f"📊 Chart saved: {plot_file}")
            except ImportError:
                click.echo("⚠️  Chart generation not available (missing dependencies)", err=True)

        # Display results
        click.echo(f"\n✅ Analysis complete!")
        click.echo(f"📁 Results saved: {output_file}")
        
        if verbose:
            click.echo(f"\n📊 Key Metrics:")
            click.echo(f"  • Gini Coefficient: {metrics.get('gini_coefficient', 0):.4f}")
            click.echo(f"  • Nakamoto Coefficient: {metrics.get('nakamoto_coefficient', 0)}")
            click.echo(f"  • Top 10% Concentration: {results['summary']['top_10_concentration']:.2f}%")
            click.echo(f"  • Total Holders: {len(holders_data):,}")
            
        return output_file

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)
        sys.exit(1)

# COMPARE PROTOCOLS COMMAND (renamed from compare)
@cli.command('compare-protocols')
@click.option('--protocols', type=str, required=True,
              help='Comma-separated list of protocols to compare (e.g., compound,uniswap,aave) or "all"')
@click.option('--metric', type=click.Choice(SUPPORTED_METRICS), default='gini_coefficient',
              help='Primary metric for comparison (default: gini_coefficient)')
@click.option('--format', type=click.Choice(['json', 'html']), default='json',
              help='Output format (default: json)')
@click.option('--output-dir', type=str, default='outputs', callback=validate_output_dir,
              help='Directory to save output files (default: outputs)')
@click.option('--chart', is_flag=True, 
              help='Generate comparison charts')
@click.option('--detailed', is_flag=True,
              help='Include detailed metrics for each protocol')
@click.option('--historical', is_flag=True,
              help='Include historical data analysis')
@click.option('--data-dir', type=str, default='data/historical',
              help='Directory containing historical data (default: data/historical)')
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
                    "top_10_concentration": sum(sorted(balances, reverse=True)[:10]) / sum(balances) * 100 if sum(balances) > 0 else 0,
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
            for i, protocol in enumerate(final_results["ranking"]):
                value = comparison_results[protocol]["summary"]["primary_metric_value"]
                html_content += f"<li>{protocol.upper()}: {value:.4f}</li>"
            html_content += "</ol></body></html>"

            with open(output_file, "w") as f:
                f.write(html_content)

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

# EXPORT COMMAND (renamed to export-historical-data for tests)
@cli.command('export-historical-data')
@click.option('--protocol', type=ProtocolChoice(), required=True,
              help='Protocol to export data for')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json',
              help='Export format (default: json)')
@click.option('--output-dir', type=str, default='exports', callback=validate_output_dir,
              help='Directory to save exported files (default: exports)')
@click.option('--limit', type=int, default=1000,
              help='Maximum number of records to export (default: 1000)')
@click.option('--include-historical', is_flag=True,
              help='Include historical snapshots in export')
@click.option('--metric', type=click.Choice(SUPPORTED_METRICS), default='gini_coefficient',
              help='Metric to focus on for historical export')
@click.option('--data-dir', type=str, default='data/historical',
              help='Directory containing historical data')
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if include_historical and os.path.exists(data_dir):
            # Export historical data
            output_file = os.path.join(output_dir, f"{protocol}_{metric}_historical.{format}")
            
            data_manager = historical_data.HistoricalDataManager(data_dir=data_dir)
            snapshots = data_manager.get_snapshots(protocol)
            
            historical_data_export = {
                "protocol": protocol,
                "metric": metric,
                "export_timestamp": datetime.now().isoformat(),
                "data_points": []
            }
            
            for snapshot in snapshots:
                snapshot_data = data_manager.load_snapshot(protocol, snapshot["timestamp"])
                if snapshot_data:
                    historical_data_export["data_points"].append({
                        "timestamp": snapshot["timestamp"],
                        "metrics": snapshot_data.get("metrics", {}),
                        "summary": snapshot_data.get("summary", {})
                    })
            
            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(historical_data_export, f, indent=2)
            
        else:
            # Export current data
            output_file = os.path.join(output_dir, f"{protocol}_export_{timestamp}.{format}")
            
            # Get current data
            holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)
            
            if format == "json":
                export_data = {
                    "protocol": protocol,
                    "export_timestamp": datetime.now().isoformat(),
                    "total_records": len(holders_data),
                    "holders": holders_data[:limit]
                }
                with open(output_file, "w") as f:
                    json.dump(export_data, f, indent=2)
                    
            elif format == "csv":
                import csv
                with open(output_file, "w", newline="") as f:
                    if holders_data:
                        fieldnames = holders_data[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(holders_data[:limit])

        click.echo("✅ Export complete!")
        click.echo(f"📁 File saved: {output_file}")
        return output_file

    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)

# HISTORICAL ANALYSIS COMMAND  
@cli.command('historical-analysis')
@click.option('--protocol', type=ProtocolChoice(), required=True,
              help='Protocol to analyze historical data for')
@click.option('--metric', type=click.Choice(SUPPORTED_METRICS), default='gini_coefficient',
              help='Metric to analyze over time (default: gini_coefficient)')
@click.option('--data-dir', type=str, default='data/historical',
              help='Directory containing historical data (default: data/historical)')
@click.option('--output-dir', type=str, default='outputs', callback=validate_output_dir,
              help='Directory to save analysis results (default: outputs)')
@click.option('--format', type=click.Choice(['json', 'png']), default='png',
              help='Output format (default: png)')
@click.option('--plot', is_flag=True, default=True,
              help='Generate time series plots')
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "png" or plot:
            # Generate plot
            try:
                from governance_token_analyzer.visualization.chart_generator import ChartGenerator
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
                "historical_data": []
            }
            
            for snapshot in snapshots:
                snapshot_data = data_manager.load_snapshot(protocol, snapshot["timestamp"])
                if snapshot_data:
                    analysis_results["historical_data"].append({
                        "timestamp": snapshot["timestamp"],
                        "metric_value": snapshot_data.get("metrics", {}).get(metric, 0),
                        "summary": snapshot_data.get("summary", {})
                    })
            
            with open(output_file, "w") as f:
                json.dump(analysis_results, f, indent=2)
                
            click.echo(f"📁 Analysis saved: {output_file}")

        click.echo("✅ Historical analysis complete!")

    except Exception as e:
        click.echo(f"❌ Historical analysis failed: {e}", err=True)
        sys.exit(1)

# GENERATE REPORT COMMAND (renamed from report)
@cli.command('generate-report')
@click.option('--protocol', type=ProtocolChoice(), required=True,
              help='Protocol to generate report for')
@click.option('--format', type=click.Choice(['html']), default='html',
              help='Report format (default: html)')
@click.option('--output-dir', type=str, default='reports', callback=validate_output_dir,
              help='Directory to save report files (default: reports)')
@click.option('--include-historical', is_flag=True,
              help='Include historical analysis in report')
@click.option('--data-dir', type=str, default='data/historical',
              help='Directory containing historical data')
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
        
        # Get current data
        holders_data = api_client.get_token_holders(protocol, limit=1000, use_real_data=True)
        balances = [float(h.get("balance", 0)) for h in holders_data if h.get("balance")]
        
        if not balances:
            click.echo("⚠️  No live data available, using simulated data", err=True)
            simulator = TokenDistributionSimulator()
            balances = simulator.generate_power_law_distribution(1000)

        # Calculate current metrics
        current_metrics = calculate_all_concentration_metrics(balances)
        
        # Prepare report data
        report_data = {
            "protocol": protocol,
            "protocol_info": PROTOCOLS.get(protocol, {}),
            "timestamp": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "holders_count": len(balances),
            "total_supply": sum(balances)
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
@cli.command('simulate-historical')
@click.option('--protocol', type=ProtocolChoice(), required=True,
              help='Protocol to simulate historical data for')
@click.option('--snapshots', type=int, default=10,
              help='Number of historical snapshots to generate (default: 10)')
@click.option('--interval', type=int, default=7,
              help='Interval between snapshots in days (default: 7)')
@click.option('--data-dir', type=str, default='data/historical', callback=validate_output_dir,
              help='Directory to store historical data (default: data/historical)')
@click.option('--output-dir', type=str, default='outputs', callback=validate_output_dir,
              help='Directory for output files (default: outputs)')
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
            protocol=protocol,
            num_snapshots=snapshots,
            interval_days=interval,
            data_manager=data_manager
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
@click.option('--check-apis', is_flag=True,
              help='Check API key configuration and connectivity')
@click.option('--test-protocols', is_flag=True, 
              help='Test data retrieval for all supported protocols')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed status information')
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
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', type=str, default='validation', callback=validate_output_dir,
              help='Directory to save validation results (default: validation)')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed validation results')
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
