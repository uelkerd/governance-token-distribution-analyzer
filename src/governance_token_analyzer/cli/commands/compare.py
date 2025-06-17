#!/usr/bin/env python3
"""
Compare protocols command implementation for the Governance Token Distribution Analyzer CLI.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional
import csv
from datetime import datetime

import click
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
from governance_token_analyzer.core.cross_protocol_comparison import compare_protocols as compare_protocols_core
from governance_token_analyzer.core.config import PROTOCOLS
from governance_token_analyzer.core.historical_data import HistoricalDataManager


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
    Execute the compare-protocols command to compare token distribution metrics across protocols.

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
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Parse protocols argument
    if protocols_arg.lower() == "all":
        protocols = list(PROTOCOLS.keys())
    else:
        protocols = [p.strip().lower() for p in protocols_arg.split(",")]
        # Validate protocols
        for protocol in protocols:
            if protocol not in PROTOCOLS:
                click.echo(click.style(f"❌ Invalid protocol: {protocol}", fg="red"))
                click.echo(f"Valid protocols: {', '.join(PROTOCOLS.keys())}")
                sys.exit(1)

    # Initialize API client
    api_client = APIClient()

    try:
        # Fetch data for each protocol
        click.echo(f"📡 Fetching data for {len(protocols)} protocols...")
        
        protocol_data = {}
        for protocol in protocols:
            click.echo(f"  • {protocol.upper()}")
            
            # Get token holders
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
            
            if not balances:
                click.echo(click.style(f"⚠️ Warning: No valid balance data found for {protocol}", fg="yellow"))
                continue
                
            # Calculate metrics
            metrics = calculate_all_concentration_metrics(balances)
            
            # Get governance data
            proposals = api_client.get_governance_proposals(protocol)
            
            # Calculate participation metrics
            participation_rate = 0.0
            if proposals and balances:
                total_votes = sum(proposal.get("votes_count", 0) for proposal in proposals)
                participation_rate = total_votes / (len(proposals) * len(balances)) if proposals else 0
            
            # Store protocol data
            protocol_data[protocol] = {
                "metrics": metrics,
                "governance": {
                    "proposals_count": len(proposals),
                    "participation_rate": participation_rate,
                },
                "total_holders": len(balances),
            }
        
        # Check if we have data for at least one protocol
        if not protocol_data:
            click.echo(click.style("❌ No valid data found for any protocol", fg="red"))
            sys.exit(1)
        
        # Perform comparison
        click.echo("🔍 Comparing protocols...")
        comparison_results = compare_protocols_core(protocol_data, primary_metric=metric)
        
        # Add historical data if requested
        historical_data = {}
        if historical:
            click.echo("📈 Analyzing historical trends...")
            
            # Initialize historical data manager
            data_manager = HistoricalDataManager(data_dir)
            
            for protocol in protocols:
                try:
                    # Get time series data for the specified metric
                    time_series_df = data_manager.get_time_series_data(protocol, metric)
                    
                    if not time_series_df.empty:
                        # Convert to list format for output
                        historical_data[protocol] = []
                        
                        for date, row in time_series_df.iterrows():
                            # Handle different date formats
                            if isinstance(date, pd.Timestamp):
                                date_str = date.strftime("%Y-%m-%d")
                            else:
                                # Try to parse the date if it's a string
                                try:
                                    date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
                                except (ValueError, TypeError):
                                    date_str = str(date)
                            
                            # Extract the metric value
                            if isinstance(row, pd.Series):
                                value = row.iloc[0]
                            else:
                                value = row
                                
                            historical_data[protocol].append({
                                "date": date_str,
                                "value": float(value)
                            })
                except Exception as e:
                    click.echo(click.style(f"⚠️ Warning: Error fetching historical data for {protocol}: {e}", fg="yellow"))
        
        # Prepare output data
        output_data = {
            "comparison_timestamp": datetime.now().isoformat(),
            "protocols_compared": protocols,
            "primary_metric": metric,
            "comparison_results": comparison_results,
        }
        
        # Add detailed metrics if requested
        if detailed:
            output_data["protocol_details"] = protocol_data
            
        # Add historical data if requested and available
        if historical and historical_data:
            output_data["historical_data"] = historical_data
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        protocols_slug = "_".join(protocols) if len(protocols) <= 3 else f"{len(protocols)}_protocols"
        output_filename = f"comparison_{protocols_slug}_{timestamp}.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save output in requested format
        if output_format == "json":
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
                
        elif output_format == "html":
            # Simple HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Protocol Comparison - {", ".join([p.upper() for p in protocols])}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .chart-container {{ margin: 30px 0; }}
                </style>
            </head>
            <body>
                <h1>Protocol Comparison Report</h1>
                <p><strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><strong>Protocols:</strong> {", ".join([p.upper() for p in protocols])}</p>
                <p><strong>Primary Metric:</strong> {metric}</p>
                
                <h2>Comparison Results</h2>
                <table>
                    <tr>
                        <th>Protocol</th>
                        <th>{metric.replace("_", " ").title()}</th>
                        <th>Rank</th>
                    </tr>
            """
            
            # Add rows for each protocol
            for result in comparison_results["rankings"]:
                protocol = result["protocol"]
                value = result["value"]
                rank = result["rank"]
                
                html_content += f"""
                    <tr>
                        <td>{protocol.upper()}</td>
                        <td>{value:.4f}</td>
                        <td>{rank}</td>
                    </tr>
                """
                
            html_content += """
                </table>
                
                <h2>Summary</h2>
                <p><strong>Most Concentrated:</strong> {}</p>
                <p><strong>Least Concentrated:</strong> {}</p>
                <p><strong>Average Concentration:</strong> {:.4f}</p>
            """.format(
                comparison_results["most_concentrated"].upper(),
                comparison_results["least_concentrated"].upper(),
                comparison_results["average"]
            )
            
            # Add detailed metrics if requested
            if detailed:
                html_content += """
                <h2>Detailed Metrics</h2>
                <table>
                    <tr>
                        <th>Protocol</th>
                        <th>Gini Coefficient</th>
                        <th>Nakamoto Coefficient</th>
                        <th>Top 10%</th>
                        <th>Proposals</th>
                        <th>Participation Rate</th>
                    </tr>
                """
                
                for protocol, data in protocol_data.items():
                    metrics = data["metrics"]
                    governance = data["governance"]
                    
                    html_content += f"""
                    <tr>
                        <td>{protocol.upper()}</td>
                        <td>{metrics.get("gini_coefficient", "N/A"):.4f}</td>
                        <td>{metrics.get("nakamoto_coefficient", "N/A")}</td>
                        <td>{metrics.get("top_10_percentage", "N/A"):.2f}%</td>
                        <td>{governance.get("proposals_count", "N/A")}</td>
                        <td>{governance.get("participation_rate", "N/A"):.4f}</td>
                    </tr>
                    """
                    
                html_content += """
                </table>
                """
            
            # Add historical data if requested and available
            if historical and historical_data:
                html_content += """
                <h2>Historical Trends</h2>
                <p>Historical data is available but chart generation requires JavaScript libraries.</p>
                """
            
            # Close HTML
            html_content += """
            </body>
            </html>
            """
            
            with open(output_path, "w") as f:
                f.write(html_content)
                
        elif output_format == "png":
            # Generate chart directly to PNG
            if chart:
                plt.figure(figsize=(12, 8))
                
                # Prepare data for plotting
                protocols_list = []
                values_list = []
                
                for result in comparison_results["rankings"]:
                    protocols_list.append(result["protocol"].upper())
                    values_list.append(result["value"])
                
                # Sort by value for better visualization
                sorted_indices = np.argsort(values_list)
                protocols_list = [protocols_list[i] for i in sorted_indices]
                values_list = [values_list[i] for i in sorted_indices]
                
                # Create bar chart
                plt.bar(protocols_list, values_list, color='skyblue')
                plt.xlabel('Protocol')
                plt.ylabel(metric.replace('_', ' ').title())
                plt.title(f'Protocol Comparison by {metric.replace("_", " ").title()}')
                plt.xticks(rotation=45)
                plt.grid(axis='y', alpha=0.3)
                
                # Add value labels on top of bars
                for i, v in enumerate(values_list):
                    plt.text(i, v + 0.01, f'{v:.4f}', ha='center')
                
                plt.tight_layout()
                plt.savefig(output_path)
                plt.close()
            else:
                # If chart is not requested but format is PNG, create a simple text chart
                plt.figure(figsize=(10, 6))
                plt.text(0.5, 0.5, f"Protocol Comparison\n\n{comparison_results['summary']}", 
                         ha='center', va='center', fontsize=12)
                plt.axis('off')
                plt.savefig(output_path)
                plt.close()
        
        click.echo(f"💾 Comparison saved to {output_path}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Error during comparison: {e}", fg="red"))
        import traceback
        click.echo(traceback.format_exc())
        sys.exit(1) 