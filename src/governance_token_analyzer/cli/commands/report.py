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
    format: str = "html",
    output_dir: str = "reports",
    include_historical: bool = False,
    data_dir: str = "data/historical",
) -> None:
    """
    Execute the generate-report command to create a comprehensive analysis report.

    Args:
        protocol: Protocol to generate report for
        format: Report format (html)
        output_dir: Directory to save report files
        include_historical: Whether to include historical analysis in report
        data_dir: Directory containing historical data
    """
    try:
        # Ensure output directory exists
        ensure_output_directory(output_dir)

        click.echo(f"📑 Generating report for {protocol.upper()}...")

        # Initialize components
        metrics_collector = MetricsCollector(use_live_data=True)
        report_generator = ReportGenerator()

        # Get current data
        click.echo("📡 Fetching current data...")
        try:
            current_data = metrics_collector.collect_protocol_data(protocol)
        except Exception as e:
            raise CLIError(f"Failed to fetch current data for {protocol}: {e}")

        # Get governance data
        click.echo("🏛️ Fetching governance data...")
        api_client = metrics_collector.api_client
        governance_data = _fetch_governance_data_safely(api_client, protocol)

        # Fetch votes data if we have governance proposals
        all_votes = []
        if governance_data:
            all_votes = _fetch_votes_data_safely(api_client, governance_data, protocol)

        # Get historical data if requested
        historical_data = None
        if include_historical:
            click.echo("📈 Including historical analysis...")
            historical_data = _load_historical_data_safely(data_dir, protocol)

        # Generate timestamp for output file
        timestamp = generate_timestamp()
        output_file = os.path.join(output_dir, f"{protocol}_report_{timestamp}.{format}")

        # Generate report
        click.echo("🔧 Generating report...")

        try:
            report_generator.generate_report(
                protocol=protocol,
                current_data=current_data,
                governance_data=governance_data,
                votes_data=all_votes,
                historical_data=historical_data,
                output_path=output_file,
                include_historical=include_historical,
            )

            click.echo(f"✅ Report saved to {output_file}")

        except Exception as e:
            raise CLIError(f"Error generating report: {e}")

    except CLIError:
        # CLIError is already handled by the utility function
        raise
    except Exception as e:
        handle_cli_error(e)
