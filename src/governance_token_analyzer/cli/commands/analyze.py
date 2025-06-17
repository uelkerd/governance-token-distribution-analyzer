#!/usr/bin/env python3
"""
Analyze command implementation for the Governance Token Distribution Analyzer CLI.
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

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics


def execute_analyze_command(
    protocol: str,
    limit: int = 1000,
    output_format: str = "json",
    output_dir: str = "outputs",
    chart: bool = False,
    live_data: bool = True,
    verbose: bool = False,
) -> None:
    """
    Execute the analyze command to analyze token distribution for a specific protocol.

    Args:
        protocol: Protocol to analyze (compound, uniswap, aave)
        limit: Maximum number of token holders to analyze
        output_format: Output format (json, csv)
        output_dir: Directory to save output files
        chart: Whether to generate distribution charts
        live_data: Whether to use live blockchain data
        verbose: Whether to enable verbose output with detailed metrics
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Initialize API client
    api_client = APIClient()

    try:
        # Fetch token holders data
        click.echo(f"📡 Fetching token holder data for {protocol.upper()}...")
        holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=live_data)
        
        if not holders_data:
            click.echo(click.style("❌ No token holder data found", fg="red"))
            sys.exit(1)
            
        click.echo(f"✅ Found {len(holders_data)} token holders")

        # Extract balances for analysis
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
            click.echo(click.style("❌ No valid balance data found", fg="red"))
            sys.exit(1)

        # Calculate concentration metrics
        click.echo("🧮 Calculating concentration metrics...")
        metrics = calculate_all_concentration_metrics(balances)
        
        # Prepare output data
        output_data = {
            "protocol": protocol,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_holders_analyzed": len(balances),
            "metrics": metrics,
        }
        
        # Add verbose metrics if requested
        if verbose:
            # Get governance data
            click.echo("🏛️ Fetching governance data...")
            proposals = api_client.get_governance_proposals(protocol)
            
            # Calculate participation metrics
            participation_rate = 0.0
            if proposals:
                total_votes = sum(proposal.get("votes_count", 0) for proposal in proposals)
                participation_rate = total_votes / (len(proposals) * len(balances)) if proposals and balances else 0
                
            output_data["governance"] = {
                "proposals_count": len(proposals),
                "participation_rate": participation_rate,
                "proposals": proposals[:5] if verbose else []  # Include top 5 proposals in verbose mode
            }

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{protocol}_analysis_{timestamp}.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save output in requested format
        if output_format == "json":
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
                
        elif output_format == "csv":
            # For CSV, we need to flatten the nested structure
            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                
                # Write header
                header = ["protocol", "timestamp", "total_holders"]
                for metric_name in metrics.keys():
                    header.append(metric_name)
                    
                writer.writerow(header)
                
                # Write data row
                row = [
                    protocol,
                    output_data["analysis_timestamp"],
                    output_data["total_holders_analyzed"]
                ]
                
                for metric_value in metrics.values():
                    row.append(metric_value)
                    
                writer.writerow(row)
                
                # If verbose, write governance data
                if verbose and "governance" in output_data:
                    writer.writerow([])  # Empty row as separator
                    writer.writerow(["Governance Data"])
                    writer.writerow(["proposals_count", "participation_rate"])
                    writer.writerow([
                        output_data["governance"]["proposals_count"],
                        output_data["governance"]["participation_rate"]
                    ])
        
        click.echo(f"💾 Analysis saved to {output_path}")
        
        # Generate chart if requested
        if chart:
            chart_filename = f"{protocol}_distribution_{timestamp}.png"
            chart_path = os.path.join(output_dir, chart_filename)
            
            click.echo("📊 Generating distribution chart...")
            
            plt.figure(figsize=(10, 6))
            
            # Convert to pandas Series for easier plotting
            balances_series = pd.Series(balances).sort_values(ascending=False)
            
            # Plot top 100 holders (or all if less than 100)
            top_n = min(100, len(balances_series))
            plt.bar(range(top_n), balances_series.head(top_n))
            
            plt.title(f"{protocol.upper()} Token Distribution - Top {top_n} Holders")
            plt.xlabel("Holder Rank")
            plt.ylabel("Token Balance")
            plt.grid(axis="y", alpha=0.3)
            
            # Add key metrics as text annotation
            plt.figtext(
                0.02, 0.02,
                f"Gini Coefficient: {metrics.get('gini_coefficient', 'N/A'):.4f}\n"
                f"Nakamoto Coefficient: {metrics.get('nakamoto_coefficient', 'N/A')}\n"
                f"Top 10 Holders: {metrics.get('top_10_percentage', 'N/A'):.2f}%",
                fontsize=9,
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5}
            )
            
            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
            
            click.echo(f"📈 Chart saved to {chart_path}")
            
    except Exception as e:
        click.echo(click.style(f"❌ Error during analysis: {e}", fg="red"))
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1) 