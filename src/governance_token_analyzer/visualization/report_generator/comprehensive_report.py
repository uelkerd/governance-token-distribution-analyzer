#!/usr/bin/env python
"""Comprehensive Report Generator for Governance Token Distribution Analysis.

This module provides functions for generating comprehensive reports
for governance token distribution analysis.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


def generate_comprehensive_report(
    protocol: str,
    current_data: Dict[str, Any],
    governance_data: List[Dict[str, Any]],
    votes_data: List[Dict[str, Any]],
    historical_data: Optional[Dict[str, Any]] = None,
    output_dir: str = "reports",
    output_format: str = "html",
    output_path: Optional[str] = None,
) -> str:
    """Generate a comprehensive analysis report.

    This function creates a complete analysis including current data,
    governance proposals, voting data, and historical analysis if available.

    Args:
        protocol: Protocol name
        current_data: Current distribution data
        governance_data: Governance proposals data
        votes_data: Voting data
        historical_data: Historical data dictionary
        output_dir: Directory where reports will be saved
        output_format: Output format ('html', 'json', 'pdf')
        output_path: Path to save the report

    Returns:
        Path to the generated report
    """
    # Set up output directory and report path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = output_dir
    os.makedirs(report_dir, exist_ok=True)

    # Create visualization directory
    viz_dir = os.path.join(report_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)

    # Set the output path if not provided
    if output_path is None:
        output_path = os.path.join(report_dir, f"{protocol}_comprehensive_report_{timestamp}.{output_format.lower()}")

    # Generate report based on format
    if output_format == "html":
        return _generate_comprehensive_html_report(
            protocol=protocol,
            current_data=current_data,
            governance_data=governance_data,
            votes_data=votes_data,
            historical_data=historical_data,
            output_path=output_path,
            viz_dir=viz_dir,
            timestamp=timestamp,
        )
    elif output_format == "json":
        # JSON report generation
        # ... (implementation details)
        return "JSON report generation not implemented yet"
    elif output_format == "pdf":
        # PDF report generation
        # ... (implementation details)
        raise NotImplementedError("PDF report generation not implemented yet")
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def _generate_comprehensive_html_report(
    protocol: str,
    current_data: Dict[str, Any],
    governance_data: List[Dict[str, Any]],
    votes_data: List[Dict[str, Any]],
    historical_data: Optional[Dict[str, Any]],
    output_path: str,
    viz_dir: str,
    timestamp: str,
) -> str:
    """Generate a comprehensive HTML report.

    Args:
        protocol: Protocol name
        current_data: Current distribution data
        governance_data: Governance proposals data
        votes_data: Voting data
        historical_data: Historical data dictionary
        output_path: Path to save the report
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Path to the generated report
    """
    # Create HTML content
    html_content = create_comprehensive_report_header(protocol)

    # Extract metrics
    metrics_data = _extract_metrics(current_data) if current_data else []
    html_content += _create_metrics_section(metrics_data)

    # Create visualizations
    visualizations_html, visualizations = create_visualizations_section(
        protocol, current_data, governance_data, votes_data, viz_dir, timestamp
    )
    html_content += visualizations_html

    # Add historical section if available
    if historical_data:
        from .historical_report_generator import create_time_series_section, create_snapshots_section

        if "time_series" in historical_data:
            html_content += create_time_series_section(protocol, historical_data["time_series"], viz_dir, timestamp)

        if "snapshots" in historical_data:
            html_content += create_snapshots_section(protocol, historical_data["snapshots"])

    # Add governance section
    html_content += _create_governance_section(governance_data, votes_data)

    # Add conclusion
    html_content += """
    <div class="section">
        <h2>Conclusion</h2>
        <p>This comprehensive analysis provides insights into the governance token distribution and participation metrics.
        The data shows patterns in token holder distribution and governance participation that can inform decision-making.</p>
    </div>

    <div class="footer">
        <p>Generated using Governance Token Distribution Analyzer</p>
    </div>
    </body>
    </html>
    """

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_content)

    return output_path


def create_comprehensive_report_header(protocol: str) -> str:
    """Create the header section of the comprehensive report.

    Args:
        protocol: Protocol name

    Returns:
        HTML string for the header section
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{protocol.upper()} Comprehensive Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            img {{ max-width: 100%; height: auto; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>{protocol.upper()} Comprehensive Analysis Report</h1>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="section">
            <h2>Overview</h2>
            <p>This report provides a comprehensive analysis of governance token distribution metrics for {protocol.upper()}.
            It includes current metrics, visualizations, governance data, and historical analysis.</p>
        </div>
    """


def _extract_metrics(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract key metrics from protocol data.

    Args:
        data: Protocol data

    Returns:
        List of metrics
    """
    metrics = []

    # Extract metrics if available
    if "metrics" in data:
        for key, value in data["metrics"].items():
            metric = {
                "name": key.replace("_", " ").title(),
                "value": value,
                "description": _get_metric_description(key),
            }
            metrics.append(metric)

    # Add token holder count
    if "token_holders" in data:
        metrics.append(
            {
                "name": "Token Holder Count",
                "value": len(data["token_holders"]),
                "description": "Total number of token holders",
            }
        )

    # Add governance participation if available
    if "governance_data" in data and "participation_rate" in data["governance_data"]:
        metrics.append(
            {
                "name": "Governance Participation Rate",
                "value": f"{data['governance_data']['participation_rate']:.2f}%",
                "description": "Percentage of token supply that participates in governance",
            }
        )

    return metrics


def _get_metric_description(metric_name: str) -> str:
    """Get description for a specific metric.

    Args:
        metric_name: Name of the metric

    Returns:
        Description of the metric
    """
    descriptions = {
        "gini_coefficient": "Measure of inequality in token distribution (0=equal, 1=unequal)",
        "top_10_concentration": "Percentage of tokens held by top 10 holders",
        "participation_rate": "Percentage of token supply that participates in governance",
        "proposal_count": "Number of governance proposals",
    }

    return descriptions.get(metric_name, "No description available")


def _create_metrics_section(metrics: List[Dict[str, Any]]) -> str:
    """Create the metrics section of the report.

    Args:
        metrics: List of metrics

    Returns:
        HTML string for the metrics section
    """
    if not metrics:
        return ""

    html_content = """
    <div class="section">
        <h2>Key Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Description</th>
            </tr>
    """

    for metric in metrics:
        html_content += f"""
        <tr>
            <td>{metric["name"]}</td>
            <td>{metric["value"]}</td>
            <td>{metric["description"]}</td>
        </tr>
        """

    html_content += """
        </table>
    </div>
    """

    return html_content


def create_visualizations_section(
    protocol: str,
    current_data: Dict[str, Any],
    governance_data: List[Dict[str, Any]],
    votes_data: List[Dict[str, Any]],
    viz_dir: str,
    timestamp: str,
) -> Tuple[str, List[Dict[str, str]]]:
    """Create the visualizations section of the report.

    Args:
        protocol: Protocol name
        current_data: Current distribution data
        governance_data: Governance proposals data
        votes_data: Voting data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Tuple of (HTML string for the visualizations section, List of visualizations)
    """
    visualizations = []
    html_content = """
    <div class="section">
        <h2>Visualizations</h2>
    """

    # Create token distribution visualization
    if current_data and "token_holders" in current_data:
        distribution_viz = _create_token_distribution_visualization(protocol, current_data, viz_dir, timestamp)
        if distribution_viz:
            visualizations.append(distribution_viz)

    # Create governance visualization
    if governance_data:
        governance_viz = _create_governance_visualization(protocol, governance_data, viz_dir, timestamp)
        if governance_viz:
            visualizations.append(governance_viz)

    # Create votes visualization
    if votes_data:
        votes_viz = _create_votes_visualization(protocol, votes_data, viz_dir, timestamp)
        if votes_viz:
            visualizations.append(votes_viz)

    # Add visualizations to HTML content
    for viz in visualizations:
        viz_path = os.path.basename(viz["path"])
        html_content += f"""
        <div class="visualization">
            <h3>{viz["title"]}</h3>
            <img src="{viz_path}" alt="{viz["title"]}">
            <p>{viz["description"]}</p>
        </div>
        """

    html_content += "</div>\n"
    return html_content, visualizations


def _create_token_distribution_visualization(
    protocol: str, data: Dict[str, Any], viz_dir: str, timestamp: str
) -> Optional[Dict[str, str]]:
    """Create visualization for token distribution.

    Args:
        protocol: Protocol name
        data: Protocol data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Visualization metadata or None if failed
    """
    try:
        if "token_holders" not in data or not data["token_holders"]:
            return None

        # Prepare data for visualization
        token_holders = data["token_holders"]
        holders_data = []
        for holder in token_holders[:20]:  # Top 20 holders
            if "TokenHolderAddress" in holder and "TokenHolderQuantity" in holder:
                holders_data.append(
                    {
                        "address": holder["TokenHolderAddress"],
                        "balance": float(holder["TokenHolderQuantity"]),
                    }
                )

        # Create distribution chart if we have data
        if holders_data:
            chart_file = os.path.join(viz_dir, f"{protocol}_distribution_{timestamp}.png")

            # Extract data for plotting
            addresses = [h["address"] for h in holders_data]
            balances = [h["balance"] for h in holders_data]

            # Create the chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(range(len(addresses)), balances)
            ax.set_title(f"{protocol.upper()} Token Distribution")
            ax.set_xlabel("Holder Rank")
            ax.set_ylabel("Token Balance")
            ax.set_xticks([])  # Hide x-axis labels as they would be too crowded

            # Save the chart
            plt.tight_layout()
            plt.savefig(chart_file)
            plt.close(fig)

            # Return visualization metadata
            return {
                "title": "Token Distribution",
                "path": chart_file,
                "description": "Distribution of tokens among top token holders.",
            }
    except Exception as e:
        logger.error(f"Error generating token distribution visualization: {e}")

    return None


def _create_governance_visualization(
    protocol: str, governance_data: List[Dict[str, Any]], viz_dir: str, timestamp: str
) -> Optional[Dict[str, str]]:
    """Create visualization for governance data.

    Args:
        protocol: Protocol name
        governance_data: Governance data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Visualization metadata or None if failed
    """
    try:
        if not governance_data:
            return None

        # Create governance participation chart
        chart_file = os.path.join(viz_dir, f"{protocol}_governance_{timestamp}.png")

        # Extract participation data
        proposals_data = []
        for proposal in governance_data:
            if "id" in proposal and "for_votes" in proposal and "against_votes" in proposal:
                proposals_data.append(
                    {
                        "id": proposal["id"],
                        "for": float(proposal.get("for_votes", 0)),
                        "against": float(proposal.get("against_votes", 0)),
                    }
                )

        if proposals_data:
            fig, ax = plt.subplots(figsize=(10, 6))

            proposal_ids = [p["id"] for p in proposals_data]
            for_votes = [p["for"] for p in proposals_data]
            against_votes = [p["against"] for p in proposals_data]

            # Width of the bars
            width = 0.3

            # Position of bars on x-axis
            ind = np.arange(len(proposal_ids))

            # Creating bars
            ax.bar(ind - width / 2, for_votes, width, label="For")
            ax.bar(ind + width / 2, against_votes, width, label="Against")

            # Labels and title
            ax.set_xlabel("Proposal ID")
            ax.set_ylabel("Votes")
            ax.set_title(f"{protocol.upper()} Governance Participation")
            ax.set_xticks(ind)
            ax.set_xticklabels(proposal_ids)
            ax.legend()

            # Save figure
            plt.tight_layout()
            plt.savefig(chart_file)
            plt.close(fig)

            # Return visualization metadata
            return {
                "title": "Governance Participation",
                "path": chart_file,
                "description": "Voting participation across governance proposals.",
            }
    except Exception as e:
        logger.error(f"Error generating governance visualization: {e}")

    return None


def _create_votes_visualization(
    protocol: str, votes_data: List[Dict[str, Any]], viz_dir: str, timestamp: str
) -> Optional[Dict[str, str]]:
    """Create visualization for votes data.

    Args:
        protocol: Protocol name
        votes_data: Votes data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Visualization metadata or None if failed
    """
    try:
        if not votes_data:
            return None

        # Create votes distribution chart
        chart_file = os.path.join(viz_dir, f"{protocol}_votes_{timestamp}.png")

        # Group votes by proposal
        proposals = {}
        for vote in votes_data:
            if "proposal_id" in vote and "voter" in vote and "support" in vote:
                proposal_id = vote["proposal_id"]
                if proposal_id not in proposals:
                    proposals[proposal_id] = {"for": 0, "against": 0}

                if vote["support"]:
                    proposals[proposal_id]["for"] += 1
                else:
                    proposals[proposal_id]["against"] += 1

        if proposals:
            fig, ax = plt.subplots(figsize=(10, 6))

            proposal_ids = list(proposals.keys())
            for_votes = [proposals[p]["for"] for p in proposal_ids]
            against_votes = [proposals[p]["against"] for p in proposal_ids]

            # Width of the bars
            width = 0.3

            # Position of bars on x-axis
            ind = np.arange(len(proposal_ids))

            # Creating bars
            ax.bar(ind - width / 2, for_votes, width, label="For")
            ax.bar(ind + width / 2, against_votes, width, label="Against")

            # Labels and title
            ax.set_xlabel("Proposal ID")
            ax.set_ylabel("Vote Count")
            ax.set_title(f"{protocol.upper()} Vote Distribution")
            ax.set_xticks(ind)
            ax.set_xticklabels(proposal_ids)
            ax.legend()

            # Save figure
            plt.tight_layout()
            plt.savefig(chart_file)
            plt.close(fig)

            # Return visualization metadata
            return {
                "title": "Vote Distribution",
                "path": chart_file,
                "description": "Distribution of votes across governance proposals.",
            }
    except Exception as e:
        logger.error(f"Error generating votes visualization: {e}")

    return None


def _create_governance_section(governance_data: List[Dict[str, Any]], votes_data: List[Dict[str, Any]]) -> str:
    """Create the governance section of the report.

    Args:
        governance_data: Governance data
        votes_data: Votes data

    Returns:
        HTML string for the governance section
    """
    if not governance_data:
        return ""

    html_content = """
    <div class="section">
        <h2>Governance Analysis</h2>
    """

    # Add governance proposals table
    html_content += """
        <h3>Recent Governance Proposals</h3>
        <div style="max-height: 400px; overflow-y: auto;">
            <table>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>For Votes</th>
                    <th>Against Votes</th>
                    <th>Start Date</th>
                    <th>End Date</th>
                </tr>
    """

    # Add governance proposals
    for proposal in governance_data[:20]:  # Limit to 20 most recent proposals
        html_content += f"""
        <tr>
            <td>{proposal.get("id", "N/A")}</td>
            <td>{proposal.get("title", "N/A")}</td>
            <td>{proposal.get("status", "N/A")}</td>
            <td>{proposal.get("for_votes", "N/A")}</td>
            <td>{proposal.get("against_votes", "N/A")}</td>
            <td>{proposal.get("start_date", "N/A")}</td>
            <td>{proposal.get("end_date", "N/A")}</td>
        </tr>
        """

    html_content += """
            </table>
        </div>
    """

    # Add governance participation metrics
    if governance_data:
        total_proposals = len(governance_data)
        passed_proposals = sum(1 for p in governance_data if p.get("status", "").lower() == "passed")
        rejected_proposals = sum(1 for p in governance_data if p.get("status", "").lower() == "rejected")

        html_content += f"""
        <h3>Governance Participation Metrics</h3>
        <ul>
            <li><strong>Total Proposals:</strong> {total_proposals}</li>
            <li><strong>Passed Proposals:</strong> {passed_proposals} ({passed_proposals / total_proposals * 100:.1f}% of total)</li>
            <li><strong>Rejected Proposals:</strong> {rejected_proposals} ({rejected_proposals / total_proposals * 100:.1f}% of total)</li>
        </ul>
        """

    html_content += "</div>\n"
    return html_content
