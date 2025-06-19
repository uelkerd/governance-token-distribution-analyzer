#!/usr/bin/env python
"""Historical Report Generator for Governance Token Distribution Analysis.

This module provides functions for generating historical analysis reports
for governance token distribution analysis.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


def generate_historical_analysis_report(
    protocol: str,
    historical_data: Dict[str, Any],
    output_dir: str = "reports",
    output_format: str = "html",
    output_path: Optional[str] = None,
) -> str:
    """Generate a historical analysis report.

    Args:
        protocol: Protocol name
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
        output_path = os.path.join(report_dir, f"{protocol}_historical_report_{timestamp}.{output_format.lower()}")

    # Generate report based on format
    if output_format == "html":
        return _generate_historical_html_report(
            protocol=protocol,
            historical_data=historical_data,
            output_path=output_path,
            viz_dir=viz_dir,
            timestamp=timestamp,
        )
    if output_format == "json":
        # JSON report generation
        # ... (implementation details)
        return "JSON report generation not implemented yet"
    if output_format == "pdf":
        # PDF report generation
        # ... (implementation details)
        raise NotImplementedError("PDF report generation not implemented yet")
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def _generate_historical_html_report(
    protocol: str,
    historical_data: Dict[str, Any],
    output_path: str,
    viz_dir: str,
    timestamp: str,
) -> str:
    """Generate a historical analysis HTML report.

    Args:
        protocol: Protocol name
        historical_data: Historical data dictionary
        output_path: Path to save the report
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Path to the generated report
    """
    # Create HTML content
    html_content = create_historical_report_header(protocol)

    # Process time series data with validation
    time_series = historical_data.get("time_series")
    if time_series is not None:
        if isinstance(time_series, (list, dict)):  # Adjust type as needed
            html_content += create_time_series_section(protocol, time_series, viz_dir, timestamp)
        else:
            logging.warning("Expected 'time_series' to be a list or dict, got %s", type(time_series).__name__)
    else:
        logging.info("'time_series' key not found in historical_data; skipping time series section.")

    # Process snapshot data
    if "snapshots" in historical_data:
        html_content += create_snapshots_section(protocol, historical_data["snapshots"])

    # Add conclusion
    html_content += """
    <div class="section">
        <h2>Conclusion</h2>
        <p>This historical analysis provides insights into how governance token distribution and participation metrics 
        have changed over time.</p>
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


def create_historical_report_header(protocol: str) -> str:
    """Create the header section of the historical report.

    Args:
        protocol: Protocol name

    Returns:
        HTML string for the header section
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{protocol.upper()} Historical Analysis Report</title>
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
        <h1>{protocol.upper()} Historical Analysis Report</h1>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="section">
            <h2>Overview</h2>
            <p>This report provides historical analysis of governance token distribution metrics for {protocol.upper()}.
            It includes time series analysis and snapshot comparisons to show how metrics have changed over time.</p>
        </div>
    """


def create_time_series_section(
    protocol: str, time_series_data: Union[Dict[str, pd.DataFrame], pd.DataFrame], viz_dir: str, timestamp: str
) -> str:
    """Create the time series section of the historical report.

    Args:
        protocol: Protocol name
        time_series_data: Time series data (DataFrame or Dict of DataFrames)
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        HTML string for the time series section
    """
    if time_series_data is None:
        return ""

    html_content = """
    <div class="section">
        <h2>Time Series Analysis</h2>
    """

    # Process time series data and create visualizations
    visualizations = []
    tables_html = ""

    # Handle dictionary of DataFrames
    if isinstance(time_series_data, dict):
        tables_html = create_dataframe_time_series_tables(time_series_data)
        for metric_name, df in time_series_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            viz_path = _create_time_series_chart(protocol, df, metric_name, viz_dir, timestamp)
            if viz_path:
                visualizations.append(
                    {
                        "title": f"{metric_name.replace('_', ' ').title()} Over Time",
                        "path": viz_path,
                        "description": f"Historical trend of {metric_name.replace('_', ' ')} over time.",
                    }
                )

    # Handle single DataFrame
    elif isinstance(time_series_data, pd.DataFrame) and not time_series_data.empty:
        tables_html = create_dict_time_series_tables({"metrics": time_series_data})
        for column in time_series_data.columns:
            if column in ["date", "timestamp"]:
                continue
            viz_path = _create_time_series_chart(protocol, time_series_data, column, viz_dir, timestamp)
            if viz_path:
                visualizations.append(
                    {
                        "title": f"{column.replace('_', ' ').title()} Over Time",
                        "path": viz_path,
                        "description": f"Historical trend of {column.replace('_', ' ')} over time.",
                    }
                )

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

    # Add tables to HTML content
    html_content += tables_html
    html_content += "</div>\n"

    return html_content


def create_dataframe_time_series_tables(time_series_data: Dict[str, pd.DataFrame]) -> str:
    """Create HTML tables for time series data stored in DataFrames.

    Args:
        time_series_data: Dictionary of DataFrames

    Returns:
        HTML string with tables
    """
    html_content = ""

    for metric_name, df in time_series_data.items():
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue

        html_content += f"""
        <h3>{metric_name.replace("_", " ").title()} Data</h3>
        <div style="max-height: 300px; overflow-y: auto;">
            <table>
                <tr>
        """

        # Add column headers
        for col in df.columns:
            html_content += f"<th>{col.replace('_', ' ').title()}</th>"
        html_content += "</tr>\n"

        # Add rows (limit to 100 rows to prevent huge tables)
        for _, row in df.head(100).iterrows():
            html_content += "<tr>"
            for col in df.columns:
                value = row[col]
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.4f}" if col not in ["date", "timestamp"] else str(value)
                else:
                    formatted_value = str(value)
                html_content += f"<td>{formatted_value}</td>"
            html_content += "</tr>\n"

        html_content += """
            </table>
        </div>
        """

    return html_content


def create_dict_time_series_tables(time_series_data: Dict[str, Any]) -> str:
    """Create HTML tables for time series data stored in dictionaries.

    Args:
        time_series_data: Dictionary of time series data

    Returns:
        HTML string with tables
    """
    html_content = ""

    for metric_name, data in time_series_data.items():
        if isinstance(data, pd.DataFrame) and not data.empty:
            html_content += f"""
            <h3>{metric_name.replace("_", " ").title()} Data</h3>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <tr>
            """

            # Add column headers
            for col in data.columns:
                html_content += f"<th>{col.replace('_', ' ').title()}</th>"
            html_content += "</tr>\n"

            # Add rows (limit to 100 rows to prevent huge tables)
            for _, row in data.head(100).iterrows():
                html_content += "<tr>"
                for col in data.columns:
                    value = row[col]
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:.4f}" if col not in ["date", "timestamp"] else str(value)
                    else:
                        formatted_value = str(value)
                    html_content += f"<td>{formatted_value}</td>"
                html_content += "</tr>\n"

            html_content += """
                </table>
            </div>
            """

    return html_content


def create_snapshots_section(protocol: str, snapshots: List[Dict[str, Any]]) -> str:
    """Create the snapshots section of the historical report.

    Args:
        protocol: Protocol name
        snapshots: List of snapshot data

    Returns:
        HTML string for the snapshots section
    """
    if not snapshots:
        return ""

    html_content = """
    <div class="section">
        <h2>Historical Snapshots</h2>
        <p>This section compares key metrics across different points in time.</p>

        <table>
            <tr>
                <th>Date</th>
                <th>Gini Coefficient</th>
                <th>Nakamoto Coefficient</th>
                <th>Top 10 Concentration</th>
                <th>Token Holders</th>
            </tr>
    """

    for snapshot in snapshots:
        if "timestamp" in snapshot and "data" in snapshot:
            data = snapshot["data"]
            metrics = data.get("metrics", {})

            html_content += f"""
            <tr>
                <td>{snapshot["timestamp"]}</td>
                <td>{metrics.get("gini_coefficient", "N/A")}</td>
                <td>{metrics.get("nakamoto_coefficient", "N/A")}</td>
                <td>{metrics.get("top_10_concentration", "N/A")}</td>
                <td>{len(data.get("token_holders", [])) if "token_holders" in data else "N/A"}</td>
            </tr>
            """

    html_content += """
        </table>
    </div>
    """

    return html_content


def _create_time_series_chart(
    protocol: str, df: pd.DataFrame, metric: str, viz_dir: str, timestamp: str
) -> Optional[str]:
    """Create a time series chart for a specific metric.

    Args:
        protocol: Protocol name
        df: DataFrame with time series data
        metric: Metric name
        viz_dir: Directory for visualizations
        timestamp: Timestamp for the report

    Returns:
        Path to the generated chart or None if failed
    """
    try:
        from governance_token_analyzer.visualization.historical_charts import create_time_series_chart

        chart_file = os.path.join(viz_dir, f"{protocol}_{metric}_{timestamp}.png")

        create_time_series_chart(
            time_series=df,
            output_path=chart_file,
            metric=metric,
            title=f"{protocol.upper()} {metric.replace('_', ' ').title()} Over Time",
        )

        return chart_file
    except Exception as e:
        logger.error(f"Error creating time series chart for {metric}: {e}")
        return None
