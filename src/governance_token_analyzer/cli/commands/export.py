"""
Export command implementation for CLI.

This module implements data export functionality,
allowing users to export token distribution and governance data.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional

import click
import pandas as pd

from governance_token_analyzer.core.historical_data import HistoricalDataManager
from governance_token_analyzer.core.api_client import APIClient
from .utils import (
    ensure_output_directory,
    handle_cli_error,
    CLIError,
    generate_timestamp
)


def _export_to_json(data: pd.DataFrame, output_file: str) -> None:
    """Export DataFrame to JSON file."""
    try:
        # Convert DataFrame to JSON
        if isinstance(data.index, pd.DatetimeIndex):
            # Reset index to make timestamps serializable
            json_data = data.reset_index().to_json(orient="records", date_format="iso")
        else:
            json_data = data.to_json(orient="records")
            
        # Write to file
        with open(output_file, "w") as f:
            f.write(json_data)
            
        click.echo(f"💾 Data exported to {output_file}")
    except Exception as e:
        raise CLIError(f"Error exporting data to JSON: {e}")


def _export_to_csv(data: pd.DataFrame, output_file: str) -> None:
    """Export DataFrame to CSV file."""
    try:
        # Reset index if it's a DatetimeIndex to include it as a column
        if isinstance(data.index, pd.DatetimeIndex):
            data = data.reset_index()
            
        # Write to CSV
        data.to_csv(output_file, index=False)
        click.echo(f"💾 Data exported to {output_file}")
    except Exception as e:
        raise CLIError(f"Error exporting data to CSV: {e}")


def execute_export_historical_data_command(
    protocol: str,
    format: str = "json",
    output_dir: str = "exports",
    limit: int = 1000,
    include_historical: bool = False,
    metric: str = "gini_coefficient",
    data_dir: str = "data/historical"
) -> None:
    """
    Execute the export-historical-data command.
    
    Args:
        protocol: Protocol to export data for
        format: Export format (json, csv)
        output_dir: Directory to save exported files
        limit: Maximum number of records to export
        include_historical: Whether to include historical data
        metric: Metric to focus on for historical export
        data_dir: Directory containing historical data
    """
    try:
        # Ensure output directory exists
        ensure_output_directory(output_dir)
        
        click.echo(f"📤 Exporting data for {protocol.upper()}...")
        
        if include_historical:
            click.echo("📈 Including historical data...")
            
            # Initialize historical data manager
            data_manager = HistoricalDataManager(data_dir)
            
            # Get time series data
            try:
                time_series = data_manager.get_time_series_data(protocol, metric)
            except Exception as e:
                raise CLIError(f"Error loading historical data: {e}")
            
            # Check if we have data
            if time_series.empty:
                click.echo(f"⚠️ No historical data found for {protocol}")
            else:
                click.echo(f"📊 Found {len(time_series)} historical data points")
                
                # Generate output filename
                output_file = os.path.join(output_dir, f"{protocol}_{metric}_historical.{format}")
                
                # Export data based on format
                if format == "json":
                    _export_to_json(time_series, output_file)
                elif format == "csv":
                    _export_to_csv(time_series, output_file)
                    
        else:
            # Export current data
            click.echo("📡 Fetching current data...")
            
            # Initialize API client
            api_client = APIClient()
            
            # Get token holders data
            try:
                holders_data = api_client.get_token_holders(protocol, limit=limit, use_real_data=True)
            except Exception as e:
                raise CLIError(f"Error fetching token holders data: {e}")
            
            if not holders_data:
                raise CLIError(f"No token holders data found for {protocol}")
                
            click.echo(f"📊 Found {len(holders_data)} token holders")
            
            # Convert to DataFrame
            df = pd.DataFrame(holders_data)
            
            # Generate output filename
            timestamp = generate_timestamp()
            output_file = os.path.join(output_dir, f"{protocol}_token_holders_{timestamp}.{format}")
            
            # Export data based on format
            if format == "json":
                _export_to_json(df, output_file)
            elif format == "csv":
                _export_to_csv(df, output_file)
                
    except CLIError:
        # CLIError is already handled by the utility function
        raise
    except Exception as e:
        handle_cli_error(e) 