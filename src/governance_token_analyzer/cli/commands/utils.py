"""
Shared utilities for CLI command implementations.

This module provides common functionality to reduce code duplication
and complexity across CLI commands.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

import click
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from governance_token_analyzer.core.metrics_collector import MetricsCollector
from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
from governance_token_analyzer.visualization.report_generator import ReportGenerator


class CLIError(Exception):
    """Custom exception for CLI command errors."""
    pass


def handle_cli_error(error: Exception) -> None:
    """
    Handle CLI errors with appropriate formatting and exit code.
    
    Args:
        error: The exception to handle
    """
    if isinstance(error, CLIError):
        click.echo(f"❌ Error: {str(error)}", err=True)
    else:
        click.echo(f"❌ Unexpected error: {str(error)}", err=True)
        
        # Show traceback in debug mode
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
            
    sys.exit(1)


def ensure_output_directory(directory: str) -> str:
    """
    Ensure the output directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        The path to the directory
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            click.echo(f"📁 Created output directory: {directory}")
        except Exception as e:
            raise CLIError(f"Failed to create output directory {directory}: {e}")
    
    return directory


def generate_timestamp() -> str:
    """
    Generate a timestamp string for file naming.
    
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def filter_numeric_values(protocols: List[str], data: Dict[str, Dict[str, Any]], metric: str) -> Tuple[List[str], List[float]]:
    """
    Filter protocols and values to include only numeric values for a specific metric.
    
    Args:
        protocols: List of protocol names
        data: Dictionary mapping protocols to metrics
        metric: The metric to filter
        
    Returns:
        Tuple of (valid_protocols, valid_values)
    """
    valid_protocols = []
    valid_values = []
    
    for protocol in protocols:
        if protocol in data and metric in data[protocol]:
            try:
                value = float(data[protocol][metric])
                valid_protocols.append(protocol)
                valid_values.append(value)
            except (ValueError, TypeError):
                click.secho(f"⚠️ Skipping non-numeric value for {protocol}: {data[protocol][metric]}", fg="yellow")
    
    return valid_protocols, valid_values


def create_bar_chart(protocols: List[str], values: List[float], metric: str, output_file: str) -> None:
    """
    Create a bar chart comparing protocols by a specific metric.
    
    Args:
        protocols: List of protocol names
        values: List of metric values
        metric: The metric being compared
        output_file: Path to save the chart
    """
    if not protocols or not values:
        raise CLIError("No valid data to create chart")
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    
    # Use uppercase protocol names for display
    display_names = [p.upper() for p in protocols]
    
    # Create bars with different colors
    bars = plt.bar(display_names, values, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'][:len(protocols)])
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.,
            height + 0.02,
            f'{height:.3f}',
            ha='center',
            va='bottom',
            fontsize=10
        )
    
    # Add chart details
    plt.title(f"Protocol Comparison: {metric.replace('_', ' ').title()}")
    plt.ylabel(metric.replace("_", " ").title())
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save chart
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    click.echo(f"📊 Comparison chart saved to {output_file}")


def display_protocol_comparison(comparison_data: Dict[str, Dict[str, Any]], metric: str) -> None:
    """
    Display protocol comparison results in the terminal.
    
    Args:
        comparison_data: Dictionary mapping protocols to metrics
        metric: The primary metric for comparison
    """
    click.echo("\n📊 Protocol Comparison Results:")
    click.echo("-" * 60)
    
    # Format header
    header = f"{'Protocol':<15} | {metric.replace('_', ' ').title():<20}"
    click.echo(header)
    click.echo("-" * 60)
    
    # Sort protocols by the primary metric
    sorted_protocols = []
    for protocol, metrics in comparison_data.items():
        if metric in metrics and isinstance(metrics[metric], (int, float)):
            sorted_protocols.append((protocol, metrics[metric]))
    
    # Sort by metric value (descending)
    sorted_protocols.sort(key=lambda x: x[1], reverse=True)
    
    # Display sorted results
    for protocol, value in sorted_protocols:
        click.echo(f"{protocol.upper():<15} | {value:<20.4f}")
    
    # Display protocols with errors or missing data
    for protocol, metrics in comparison_data.items():
        if metric not in metrics or not isinstance(metrics.get(metric), (int, float)):
            error_msg = metrics.get("error", "No data available")
            click.echo(f"{protocol.upper():<15} | ⚠️  {error_msg}")
    
    click.echo("-" * 60)


def display_metrics(metrics: Dict[str, Any], verbose: bool = False) -> None:
    """
    Display metrics in a formatted way.
    
    Args:
        metrics: Dictionary of metrics
        verbose: Whether to show detailed metrics
    """
    click.echo("\n📊 Token Distribution Analysis:")
    
    # Always show core metrics
    core_metrics = ["gini_coefficient", "nakamoto_coefficient"]
    for metric in core_metrics:
        value = metrics.get(metric, 'N/A')
        if isinstance(value, (int, float)):
            click.echo(f"  • {metric.replace('_', ' ').title()}: {value:.4f}")
        else:
            click.echo(f"  • {metric.replace('_', ' ').title()}: {value}")
    
    # Show additional metrics if verbose
    if verbose:
        verbose_metrics = ["shannon_entropy", "herfindahl_index", "theil_index", "palma_ratio"]
        for metric in verbose_metrics:
            value = metrics.get(metric, 'N/A')
            if isinstance(value, (int, float)):
                click.echo(f"  • {metric.replace('_', ' ').title()}: {value:.4f}")
            else:
                click.echo(f"  • {metric.replace('_', ' ').title()}: {value}")


def collect_protocol_data_safely(metrics_collector: MetricsCollector, protocol: str, limit: int = 1000) -> Dict[str, Any]:
    """
    Safely collect protocol data with proper error handling.
    
    Args:
        metrics_collector: MetricsCollector instance
        protocol: Protocol to collect data for
        limit: Maximum number of token holders
        
    Returns:
        Protocol data dictionary
        
    Raises:
        CLIError: If data collection fails
    """
    try:
        data = metrics_collector.collect_protocol_data(protocol, limit=limit)
        if not data:
            raise CLIError(f"Failed to collect data for {protocol}")
        return data
    except Exception as e:
        raise CLIError(f"Error collecting data for {protocol}: {e}")


def save_data_file(data: Any, output_file: str, format_type: str) -> None:
    """
    Save data to file in the specified format.
    
    Args:
        data: Data to save
        output_file: Output file path
        format_type: Format type ('json', 'csv', etc.)
        
    Raises:
        CLIError: If saving fails
    """
    try:
        if format_type == "json":
            import json
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
        elif format_type == "csv":
            if isinstance(data, dict) and "token_holders" in data:
                df = pd.DataFrame(data["token_holders"])
                df.to_csv(output_file, index=False)
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(output_file, index=False)
        else:
            raise CLIError(f"Unsupported format: {format_type}")
            
        click.echo(f"💾 Data saved to {output_file}")
    except Exception as e:
        raise CLIError(f"Error saving data to {output_file}: {e}")


def create_distribution_chart(balances: List[float], protocol: str, chart_file: str) -> None:
    """
    Create and save a token distribution chart.
    
    Args:
        balances: List of token balances
        protocol: Protocol name
        chart_file: Output file path
        
    Raises:
        CLIError: If chart creation fails
    """
    try:
        if not balances:
            click.secho("⚠️ No balances to plot", fg="yellow")
            return
        
        # Sort balances in descending order
        balances_sorted = sorted(balances, reverse=True)
        
        plt.figure(figsize=(10, 6))
        
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
        if total > 0:  # Prevent division by zero
            lorenz = [sum(balances_sorted[:i + 1]) / total for i in range(len(balances_sorted))]
            ax2.plot(range(1, len(balances_sorted) + 1), lorenz, "r-", alpha=0.7)
            ax2.set_ylabel("Cumulative Share", color="r")
        else:
            click.secho("⚠️ Cannot create Lorenz curve: Total balance is zero", fg="yellow")
        
        # Save chart
        plt.savefig(chart_file)
        plt.close()
        
        click.echo(f"📊 Chart saved to {chart_file}")
    except Exception as e:
        raise CLIError(f"Error creating distribution chart: {e}") 