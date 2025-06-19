#!/usr/bin/env python3
"""
Report generation command implementation for the Governance Token Distribution Analyzer CLI.

This module implements comprehensive report generation functionality,
allowing users to create detailed analysis reports with visualizations.
"""

import os
from typing import Dict, Any, List, Optional

import click

from governance_token_analyzer.core.metrics_collector import MetricsCollector
from governance_token_analyzer.core.historical_data import HistoricalDataManager
from governance_token_analyzer.visualization.report_generator import ReportGenerator
from .utils import ensure_output_directory, handle_cli_error, CLIError, generate_timestamp
from governance_token_analyzer.core.api_client import APIClient


def _fetch_governance_data_safely(api_client, protocol: str) -> List[Dict[str, Any]]:
    """Safely fetch governance data with error handling."""
    try:
        governance_data = api_client.get_governance_proposals(protocol)
        if governance_data:
            click.echo(f"📊 Found {len(governance_data)} governance proposals")
            return governance_data
        click.echo("⚠️ No governance proposals found")
        return []
    except Exception as e:
        click.secho(f"⚠️ Error fetching governance data: {e}", fg="yellow")
        return []


def _fetch_votes_data_safely(api_client, governance_data: List[Dict[str, Any]], protocol: str) -> List[Dict[str, Any]]:
    """Safely fetch votes data for all proposals."""
    all_votes = []

    for i, proposal in enumerate(governance_data, 1):
        proposal_id = proposal.get("id")
        if not proposal_id:
            click.secho(f"⚠️ Skipping proposal {i}: No proposal ID found", fg="yellow")
            continue

        click.echo(f"🗳️ Fetching votes for proposal {i} (ID: {proposal_id})")
        try:
            votes = api_client.get_governance_votes(protocol, proposal_id)
            if votes:
                all_votes.extend(votes)
                click.echo(f"  ✓ Found {len(votes)} votes")
            else:
                click.secho(f"  ⚠️ No votes found for proposal {i}", fg="yellow")
        except Exception as e:
            click.secho(f"  ⚠️ Error fetching votes for proposal {i}: {e}", fg="yellow")

    click.echo(f"✅ Fetched {len(all_votes)} total votes across all proposals")
    return all_votes


def _load_historical_data_safely(data_dir: str, protocol: str) -> Optional[Dict[str, Any]]:
    """Safely load historical data with error handling."""
    try:
        data_manager = HistoricalDataManager(data_dir)
        historical_data = {}

        metrics_to_load = ["gini_coefficient", "nakamoto_coefficient", "participation_rate"]

        for metric in metrics_to_load:
            try:
                time_series = data_manager.get_time_series_data(protocol, metric)
                if not time_series.empty:
                    historical_data[metric] = time_series
                    click.echo(f"  ✓ Loaded historical {metric} data")
                else:
                    click.echo(f"  ⚠️ No historical {metric} data found")
            except Exception as e:
                click.echo(f"  ⚠️ Error loading historical {metric} data: {e}")

        return historical_data if historical_data else None

    except Exception as e:
        click.echo(f"⚠️ Error loading historical data: {e}")
        return None


def execute_generate_report_command(
    protocol: str,
    output_format: str = "html",
    output_dir: str = "reports",
    include_historical: bool = False,
    data_dir: str = "data/historical",
) -> None:
    """
    Execute the generate-report command.
    Args:
        protocol: Protocol to generate report for
        output_format: Output format (html, json, pdf)
        output_dir: Directory to save report
        include_historical: Whether to include historical data
        data_dir: Directory containing historical data
    """
    try:
        # Ensure output directory exists
        ensure_output_directory(output_dir)

        click.echo(f"📊 Generating report for {protocol.upper()}...")

        # Initialize API client
        api_client = APIClient()

        # Get token holders data
        try:
            click.echo("📡 Fetching token holders data...")
            holders_data = api_client.get_token_holders(protocol, limit=1000, use_real_data=True)
        except Exception as e:
            raise CLIError(f"Error fetching token holders data: {e}")

        # Get governance data
        try:
            click.echo("📡 Fetching governance data...")
            governance_data = api_client.get_governance_proposals(protocol, use_real_data=True)
        except Exception as e:
            click.echo(f"⚠️ Error fetching governance data: {e}")
            governance_data = []

        # Get votes data
        try:
            click.echo("📡 Fetching votes data...")
            votes_data = []
            for proposal in governance_data:
                if "id" in proposal:
                    proposal_votes = api_client.get_governance_votes(
                        protocol, proposal_id=proposal["id"], use_real_data=True
                    )
                    votes_data.extend(proposal_votes)
        except Exception as e:
            click.echo(f"⚠️ Error fetching votes data: {e}")
            votes_data = []

        # Process token holders data
        current_data = {
            "token_holders": holders_data,
            "metrics": {},  # Will be calculated by the report generator
        }

        # Initialize report generator
        report_gen = ReportGenerator(output_dir=output_dir)

        # Get historical data if requested
        historical_data = None
        if include_historical:
            click.echo("📈 Including historical data...")

            # Initialize historical data manager
            data_manager = HistoricalDataManager(data_dir)

            try:
                # Get time series data for key metrics
                time_series = {}
                for metric in ["gini_coefficient", "nakamoto_coefficient"]:
                    try:
                        metric_data = data_manager.get_time_series_data(protocol, metric)
                        if not metric_data.empty:
                            time_series[metric] = metric_data
                    except Exception as e:
                        click.echo(f"⚠️ Could not load time series for {metric}: {e}")

                # Get snapshots
                snapshots = data_manager.get_snapshots(protocol)

                if snapshots or time_series:
                    historical_data = {"time_series": time_series, "snapshots": snapshots}
                    click.echo(
                        f"📊 Found historical data: {len(snapshots)} snapshots and {len(time_series)} time series"
                    )
                else:
                    click.echo("⚠️ No historical data found")
            except Exception as e:
                click.echo(f"⚠️ Error loading historical data: {e}")

        # Generate the report
        report_path = report_gen.generate_report(
            protocol=protocol,
            current_data=current_data,
            governance_data=governance_data,
            votes_data=votes_data,
            historical_data=historical_data,
            output_format=output_format,
            include_historical=True if historical_data else False,
        )

        click.echo(f"✅ Report generated: {report_path}")

    except CLIError:
        # CLIError is already handled by the utility function
        raise
    except Exception as e:
        handle_cli_error(e)
