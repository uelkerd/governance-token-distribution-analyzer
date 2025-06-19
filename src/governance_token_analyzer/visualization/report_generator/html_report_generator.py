#!/usr/bin/env python
"""HTML Report Generator for Governance Token Distribution Analysis.

This module provides functions for generating HTML reports with visualizations
for governance token distribution analysis.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


def generate_comprehensive_html_report(
    report_generator,
    protocol: str,
    current_data: Dict[str, Any],
    governance_data: List[Dict[str, Any]],
    votes_data: List[Dict[str, Any]],
    historical_data: Optional[Dict[str, Any]] = None,
    output_path: str = None,
    report_dir: str = None,
    viz_dir: str = None,
    timestamp: str = None,
) -> str:
    """Generate a comprehensive HTML report with all data components.

    Args:
        report_generator: The ReportGenerator instance
        protocol: Protocol name
        current_data: Current distribution data
        governance_data: Governance proposals data
        votes_data: Voting data
        historical_data: Historical data dictionary
        output_path: Path to save the report
        report_dir: Directory for the report
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Path to the generated report
    """
    # Initialize parameters with default values if not provided
    timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = report_dir or report_generator.output_dir
    viz_dir = viz_dir or os.path.join(report_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    output_path = output_path or os.path.join(report_dir, f"{protocol}_report_{timestamp}.html")

    # Extract metrics and create visualizations
    metrics_data = report_generator._extract_metrics(current_data) if current_data and "metrics" in current_data else []

    # Generate visualizations
    distribution_visualizations = create_token_distribution_visualization(protocol, current_data, viz_dir, timestamp)

    governance_visualizations = create_governance_visualization(protocol, governance_data, viz_dir, timestamp)

    # Process historical data if available
    historical_section = process_historical_data(protocol, historical_data, viz_dir, timestamp)

    # Combine all visualizations
    all_visualizations = distribution_visualizations + governance_visualizations
    if historical_section and "visualizations" in historical_section:
        all_visualizations.extend(historical_section["visualizations"])

    # Generate the HTML report using template
    try:
        return render_html_template(
            report_generator,
            protocol=protocol,
            metrics_data=metrics_data,
            all_visualizations=all_visualizations,
            governance_data=governance_data[:10],  # Limit to top 10 proposals
            historical_section=historical_section,
            output_path=output_path,
        )
    except Exception as e:
        logger.error(f"Error rendering HTML: {e}")

        # Fallback to basic HTML if template rendering fails
        return generate_basic_html_report(
            protocol=protocol,
            metrics=metrics_data,
            visualizations=all_visualizations,
            output_path=output_path,
            historical_section=historical_section,
        )


def render_html_template(
    report_generator,
    protocol: str,
    metrics_data: List[Dict[str, Any]],
    all_visualizations: List[Dict[str, str]],
    governance_data: List[Dict[str, Any]],
    historical_section: Dict[str, Any],
    output_path: str,
) -> str:
    """Render HTML template with the provided data.

    Args:
        report_generator: The ReportGenerator instance
        protocol: Protocol name
        metrics_data: Metrics data
        all_visualizations: All visualizations
        governance_data: Governance data
        historical_section: Historical section data
        output_path: Path to save the report

    Returns:
        Path to the generated report
    """
    # Set up Jinja environment
    env = report_generator.jinja_env

    # Load template
    template = env.get_template("report_template.html")

    # Render template
    html_content = template.render(
        protocol=protocol.upper(),
        title=f"{protocol.upper()} Governance Analysis Report",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=metrics_data,
        visualizations=all_visualizations,
        governance_data=governance_data,
        historical_analysis=historical_section,
        overview=f"Analysis of governance token distribution for {protocol.upper()}",
        conclusion="This report provides insights into the token distribution and governance of the protocol.",
    )

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_content)

    return output_path


def create_token_distribution_visualization(
    protocol: str, current_data: Dict[str, Any], viz_dir: str, timestamp: str
) -> List[Dict[str, str]]:
    """Create visualizations for token distribution.

    Args:
        protocol: Protocol name
        current_data: Current distribution data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        List of visualization metadata
    """
    visualizations = []

    if not current_data or "token_holders" not in current_data or not current_data["token_holders"]:
        return visualizations

    try:
        # Prepare data for visualization
        token_holders = current_data["token_holders"]
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

            # Add to visualizations list
            visualizations.append(
                {
                    "title": "Token Distribution",
                    "path": chart_file,
                    "description": "Distribution of tokens among top token holders.",
                }
            )
    except Exception as e:
        logger.error(f"Error generating token distribution visualizations: {e}")

    return visualizations


def create_governance_visualization(
    protocol: str, governance_data: List[Dict[str, Any]], viz_dir: str, timestamp: str
) -> List[Dict[str, str]]:
    """Create visualizations for governance data.

    Args:
        protocol: Protocol name
        governance_data: Governance data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        List of visualization metadata
    """
    visualizations = []

    if not governance_data:
        return visualizations

    try:
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
            plt.savefig(chart_file, dpi=300)
            plt.close(fig)

            # Add to visualizations
            visualizations.append(
                {
                    "title": "Governance Participation",
                    "path": chart_file,
                    "description": "Voting participation across governance proposals.",
                }
            )
    except Exception as e:
        logger.error(f"Error generating governance visualizations: {e}")

    return visualizations


def process_historical_data(
    protocol: str, historical_data: Optional[Dict[str, Any]], viz_dir: str, timestamp: str
) -> Optional[Dict[str, Any]]:
    """Process historical data and create visualizations.

    Args:
        protocol: Protocol name
        historical_data: Historical data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Historical section data
    """
    if not historical_data:
        return None

    historical_visualizations = []
    historical_metrics = {}

    try:
        # Process time series data
        if "time_series" in historical_data:
            process_time_series(
                protocol=protocol,
                time_series=historical_data["time_series"],
                viz_dir=viz_dir,
                timestamp=timestamp,
                historical_visualizations=historical_visualizations,
                historical_metrics=historical_metrics,
            )

        # Extract snapshot data
        snapshot_data = extract_snapshot_data(historical_data)

        # Create historical section with all data
        historical_section = {
            "title": "Historical Analysis",
            "visualizations": historical_visualizations,
            "metrics": historical_metrics,
            "snapshots": snapshot_data,
            "overview": "Analysis of historical trends in token distribution metrics.",
        }
        return historical_section
    except Exception as e:
        logger.error(f"Error generating historical visualizations: {e}")
        # Create a basic historical section if visualization fails
        return {
            "title": "Historical Analysis",
            "overview": "Historical data analysis was requested but encountered errors during processing.",
        }


def process_time_series(
    protocol: str,
    time_series: Any,
    viz_dir: str,
    timestamp: str,
    historical_visualizations: List[Dict[str, str]],
    historical_metrics: Dict[str, Any],
) -> None:
    """Process time series data and create visualizations.

    Args:
        protocol: Protocol name
        time_series: Time series data
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report
        historical_visualizations: List to append visualizations to
        historical_metrics: Dict to add metrics to
    """
    from governance_token_analyzer.visualization.historical_charts import create_time_series_chart

    # Process dictionary of DataFrames
    if isinstance(time_series, dict):
        for metric_name, metric_data in time_series.items():
            if not isinstance(metric_data, pd.DataFrame) or metric_data.empty:
                continue

            chart_file = os.path.join(viz_dir, f"{protocol}_{metric_name}_{timestamp}.png")

            try:
                create_time_series_chart(
                    time_series=metric_data,
                    output_path=chart_file,
                    metric=metric_name,
                    title=f"{protocol.upper()} {metric_name.replace('_', ' ').title()} Over Time",
                )

                historical_visualizations.append(
                    {
                        "title": f"Historical {metric_name.replace('_', ' ').title()}",
                        "path": chart_file,
                        "description": f"Time series analysis of {metric_name.replace('_', ' ')} over time.",
                    }
                )

                # Add to historical metrics
                historical_metrics[metric_name] = (
                    metric_data.iloc[-1][metric_name] if metric_name in metric_data.columns else "N/A"
                )
            except Exception as e:
                logger.error(f"Error creating time series chart for {metric_name}: {e}")

    # Process single DataFrame
    elif isinstance(time_series, pd.DataFrame) and not time_series.empty:
        for column in time_series.columns:
            if column in ["date", "timestamp"]:
                continue

            chart_file = os.path.join(viz_dir, f"{protocol}_{column}_{timestamp}.png")

            try:
                create_time_series_chart(
                    time_series=time_series,
                    output_path=chart_file,
                    metric=column,
                    title=f"{protocol.upper()} {column.replace('_', ' ').title()} Over Time",
                )

                historical_visualizations.append(
                    {
                        "title": f"Historical {column.replace('_', ' ').title()}",
                        "path": chart_file,
                        "description": f"Time series analysis of {column.replace('_', ' ')} over time.",
                    }
                )

                # Add to historical metrics
                historical_metrics[column] = time_series.iloc[-1][column] if column in time_series.columns else "N/A"
            except Exception as e:
                logger.error(f"Error creating time series chart for {column}: {e}")


def extract_snapshot_data(historical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract snapshot data from historical data.

    Args:
        historical_data: Historical data

    Returns:
        List of snapshot data
    """
    snapshot_data = []

    if "snapshots" not in historical_data or not historical_data["snapshots"]:
        return snapshot_data

    snapshots = historical_data["snapshots"]
    for snapshot in snapshots:
        if "timestamp" in snapshot and "data" in snapshot:
            data = snapshot["data"]
            metrics = data.get("metrics", {})

            snapshot_entry = {
                "date": snapshot["timestamp"],
                "gini": metrics.get("gini_coefficient", "N/A"),
                "nakamoto": metrics.get("nakamoto_coefficient", "N/A"),
                "holders": len(data.get("token_holders", [])) if "token_holders" in data else "N/A",
            }
            snapshot_data.append(snapshot_entry)

    return snapshot_data


def generate_basic_html_report(
    protocol: str,
    metrics: List[Dict[str, Any]],
    visualizations: List[Dict[str, str]],
    output_path: str,
    historical_section: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a basic HTML report when template rendering fails.

    Args:
        protocol: Protocol name
        metrics: Metrics data
        visualizations: Visualizations
        output_path: Path to save the report
        historical_section: Historical section data

    Returns:
        Path to the generated report
    """
    # Create the basic HTML structure
    html_content = create_basic_html_structure(protocol)

    # Add metrics section
    html_content += create_metrics_html_section(metrics)

    # Add visualizations section
    html_content += create_visualizations_html_section(visualizations)

    # Add historical section if provided
    if historical_section:
        html_content += create_historical_html_section(historical_section)

    # Add conclusion and footer
    html_content += create_conclusion_and_footer_html()

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_content)

    return output_path


def create_basic_html_structure(protocol: str) -> str:
    """Create the basic HTML structure for a report.

    Args:
        protocol: Protocol name

    Returns:
        HTML string
    """
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{protocol.upper()} Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .section {{ margin-bottom: 30px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>{protocol.upper()} Governance Analysis Report</h1>
            <div class="section">
                <h2>Key Metrics</h2>
    """


def create_metrics_html_section(metrics: List[Dict[str, Any]]) -> str:
    """Create HTML for the metrics section.

    Args:
        metrics: Metrics data

    Returns:
        HTML string
    """
    if not metrics:
        return "</div>\n"

    html_content = "<ul>"
    for metric in metrics:
        html_content += f"<li><strong>{metric['name']}:</strong> {metric['value']} - {metric['description']}</li>"
    html_content += "</ul>\n</div>\n"

    return html_content


def create_visualizations_html_section(visualizations: List[Dict[str, str]]) -> str:
    """Create HTML for the visualizations section.

    Args:
        visualizations: Visualizations

    Returns:
        HTML string
    """
    if not visualizations:
        return ""

    html_content = """
        <div class="section">
            <h2>Visualizations</h2>
    """

    for viz in visualizations:
        viz_path = os.path.basename(viz["path"])
        html_content += f"""
            <div>
                <h3>{viz["title"]}</h3>
                <img src="{viz_path}" alt="{viz["title"]}">
                <p>{viz["description"]}</p>
            </div>
        """

    html_content += "</div>\n"
    return html_content


def create_historical_html_section(historical_section: Dict[str, Any]) -> str:
    """Create HTML for the historical section.

    Args:
        historical_section: Historical section data

    Returns:
        HTML string
    """
    html_content = """
        <div class="section">
            <h2>Historical Analysis</h2>
    """

    # Add overview if available
    if "overview" in historical_section:
        html_content += f"<p>{historical_section['overview']}</p>"

    # Add visualizations if available
    html_content += add_historical_visualizations(historical_section)

    # Add metrics if available
    html_content += add_historical_metrics(historical_section)

    # Add snapshot data if available
    html_content += add_historical_snapshots(historical_section)

    html_content += "</div>\n"
    return html_content


def add_historical_visualizations(historical_section: Dict[str, Any]) -> str:
    """Add historical visualizations to HTML content.

    Args:
        historical_section: Historical section data

    Returns:
        HTML string
    """
    html_content = ""

    if "visualizations" in historical_section and historical_section["visualizations"]:
        for viz in historical_section["visualizations"]:
            viz_path = os.path.basename(viz["path"])
            html_content += f"""
                <div>
                    <h3>{viz["title"]}</h3>
                    <img src="{viz_path}" alt="{viz["title"]}">
                    <p>{viz["description"]}</p>
                </div>
            """

    return html_content


def add_historical_metrics(historical_section: Dict[str, Any]) -> str:
    """Add historical metrics to HTML content.

    Args:
        historical_section: Historical section data

    Returns:
        HTML string
    """
    html_content = ""

    if "metrics" in historical_section and historical_section["metrics"]:
        html_content += "<h3>Historical Metrics</h3><ul>"

        for metric_name, value in historical_section["metrics"].items():
            formatted_value = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
            html_content += f"<li><strong>{metric_name.replace('_', ' ').title()}:</strong> {formatted_value}</li>"

        html_content += "</ul>"

    return html_content


def add_historical_snapshots(historical_section: Dict[str, Any]) -> str:
    """Add historical snapshots to HTML content.

    Args:
        historical_section: Historical section data

    Returns:
        HTML string
    """
    html_content = ""

    if "snapshots" in historical_section and historical_section["snapshots"]:
        html_content += """
            <h3>Snapshot Summary</h3>
            <table border="1" cellpadding="5">
                <tr>
                    <th>Date</th>
                    <th>Gini Coefficient</th>
                    <th>Nakamoto Coefficient</th>
                    <th>Holders</th>
                </tr>
        """

        for snapshot in historical_section["snapshots"]:
            date = snapshot.get("date", "N/A")
            gini = snapshot.get("gini", "N/A")
            nakamoto = snapshot.get("nakamoto", "N/A")
            holders = snapshot.get("holders", "N/A")

            html_content += f"""
                <tr>
                    <td>{date}</td>
                    <td>{gini}</td>
                    <td>{nakamoto}</td>
                    <td>{holders}</td>
                </tr>
            """

        html_content += "</table>"

    return html_content


def create_conclusion_and_footer_html() -> str:
    """Create HTML for conclusion and footer sections.

    Returns:
        HTML string
    """
    return """
        <div class="section">
            <h2>Conclusion</h2>
            <p>This report provides insights into the governance token distribution and participation metrics.</p>
        </div>

        <div class="footer">
            <p>Generated using Governance Token Distribution Analyzer</p>
        </div>
    </body>
    </html>
    """
