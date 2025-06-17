#!/usr/bin/env python3
"""
Report generation command implementation for the Governance Token Distribution Analyzer CLI.
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

import click

from governance_token_analyzer.core.metrics_collector import MetricsCollector
from governance_token_analyzer.core.historical_data import HistoricalDataManager
from governance_token_analyzer.visualization.report_generator import ReportGenerator


def execute_generate_report_command(
    protocol: str,
    output_format: str = "html",
    output_dir: str = "reports",
    include_historical: bool = False,
    data_dir: str = "data/historical",
) -> None:
    """
    Execute the generate-report command to create a comprehensive analysis report.

    Args:
        protocol: Protocol to generate report for
        output_format: Report format (html)
        output_dir: Directory to save report files
        include_historical: Whether to include historical analysis in report
        data_dir: Directory containing historical data
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    click.echo(f"📑 Generating report for {protocol.upper()}...")

    try:
        # Initialize components
        metrics_collector = MetricsCollector(use_live_data=True)
        report_generator = ReportGenerator()

        # Get current data
        click.echo("📡 Fetching current data...")
        current_data = metrics_collector.collect_protocol_data(protocol)

        # Get governance data
        click.echo("🏛️ Fetching governance data...")
        api_client = metrics_collector.api_client
        governance_data = api_client.get_governance_proposals(protocol)

        if governance_data:
            click.echo(f"📊 Found {len(governance_data)} governance proposals")

            # Fetch votes for each proposal
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
        else:
            click.echo("⚠️ No governance proposals found")
            all_votes = []

        # Generate timestamp for output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{protocol}_report_{timestamp}.{output_format}")

        # Generate report
        click.echo("🔧 Generating report...")

        # Get historical data if requested
        historical_data = None
        if include_historical:
            click.echo("📈 Including historical analysis...")
            try:
                data_manager = HistoricalDataManager(data_dir)
                historical_data = {}

                for metric in ["gini_coefficient", "nakamoto_coefficient", "participation_rate"]:
                    try:
                        time_series = data_manager.get_time_series_data(protocol, metric)
                        if not time_series.empty:
                            historical_data[metric] = time_series
                    except Exception as e:
                        click.echo(f"⚠️ Error loading historical {metric} data: {e}")
            except Exception as e:
                click.echo(f"⚠️ Error loading historical data: {e}")
                historical_data = None

        # Generate the report
        report_generator.generate_report(
            protocol=protocol,
            current_data=current_data,
            governance_data=governance_data,
            votes_data=all_votes,
            historical_data=historical_data,
            output_path=output_file,
        )

        click.echo(f"✅ Report saved to {output_file}")

    except Exception as e:
        click.echo(f"❌ Error generating report: {e}")
        sys.exit(1)
