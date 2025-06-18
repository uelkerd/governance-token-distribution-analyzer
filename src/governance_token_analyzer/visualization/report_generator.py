"""Report Generator Module for creating comprehensive governance token analysis reports.
This module provides functionality to generate HTML, PDF, and JSON reports
with visualizations and insights about token distribution and governance.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import visualization modules
from . import charts, historical_charts


class ReportGenerator:
    """Generates comprehensive reports with visualizations and analysis."""

    def __init__(self, output_dir: str = "reports", template_dir: str = None):
        """Initialize the report generator.

        Args:
            output_dir: Directory where reports will be saved
            template_dir: Directory containing Jinja2 templates

        """
        self.output_dir = output_dir

        # Use default template dir if not provided
        if template_dir is None:
            # Use templates in the same directory as this module
            template_dir = os.path.join(os.path.dirname(__file__), "templates")

        self.template_dir = template_dir

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize Jinja2 environment
        self._setup_jinja_env()

    def _setup_jinja_env(self):
        """Set up Jinja2 environment with templates."""
        # Check if template directory exists
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)

            # Create a basic template if none exists
            basic_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ title }}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1, h2, h3 { color: #333; }
                    .metrics { margin: 20px 0; }
                    .visualization { margin: 30px 0; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>{{ title }}</h1>
                <p>Generated on {{ generation_date }}</p>

                <div class="overview">
                    <h2>Overview</h2>
                    <p>{{ overview }}</p>
                </div>

                <div class="metrics">
                    <h2>Key Metrics</h2>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Description</th>
                        </tr>
                        {% for metric in metrics %}
                        <tr>
                            <td>{{ metric.name }}</td>
                            <td>{{ metric.value }}</td>
                            <td>{{ metric.description }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>

                <div class="visualizations">
                    <h2>Visualizations</h2>
                    {% for viz in visualizations %}
                    <div class="visualization">
                        <h3>{{ viz.title }}</h3>
                        <img src="{{ viz.path }}" alt="{{ viz.title }}" width="100%">
                        <p>{{ viz.description }}</p>
                    </div>
                    {% endfor %}
                </div>

                {% if historical_analysis %}
                <div class="historical-analysis">
                    <h2>Historical Analysis</h2>
                    <p>{{ historical_analysis.overview }}</p>
                    {% for viz in historical_analysis.visualizations %}
                    <div class="visualization">
                        <h3>{{ viz.title }}</h3>
                        <img src="{{ viz.path }}" alt="{{ viz.title }}" width="100%">
                        <p>{{ viz.description }}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                {% if comparison %}
                <div class="comparison">
                    <h2>Protocol Comparison</h2>
                    <p>{{ comparison.overview }}</p>
                    {% for viz in comparison.visualizations %}
                    <div class="visualization">
                        <h3>{{ viz.title }}</h3>
                        <img src="{{ viz.path }}" alt="{{ viz.title }}" width="100%">
                        <p>{{ viz.description }}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                <div class="conclusion">
                    <h2>Conclusion</h2>
                    <p>{{ conclusion }}</p>
                </div>

                <div class="footer">
                    <p>Generated using Governance Token Distribution Analyzer</p>
                </div>
            </body>
            </html>
            """

            # Save the basic template
            with open(os.path.join(self.template_dir, "report_template.html"), "w") as f:
                f.write(basic_template)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate_snapshot_report(
        self,
        protocol_data: Dict[str, Any],
        protocol_name: str,
        format: str = "html",
        include_visualizations: bool = True,
    ) -> str:
        """Generate a report for a single protocol snapshot.

        Args:
            protocol_data: Protocol data snapshot
            protocol_name: Name of the protocol
            format: Output format (html, pdf, json)
            include_visualizations: Whether to include visualizations

        Returns:
            Path to the generated report

        """
        # Create a timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output filename
        filename_base = f"{protocol_name}_snapshot_report_{timestamp}"

        # Create folder for this report
        report_dir = os.path.join(self.output_dir, filename_base)
        os.makedirs(report_dir, exist_ok=True)

        # Create folder for visualizations if needed
        if include_visualizations:
            viz_dir = os.path.join(report_dir, "visualizations")
            os.makedirs(viz_dir, exist_ok=True)

        # Extract metrics from protocol data
        metrics = self._extract_metrics(protocol_data)

        # Generate visualizations if requested
        visualizations = []
        if include_visualizations:
            visualizations = self._generate_snapshot_visualizations(protocol_data, viz_dir)

        # Generate report based on format
        if format == "html":
            return self._generate_html_report(
                protocol_name=protocol_name,
                metrics=metrics,
                visualizations=visualizations,
                report_dir=report_dir,
                timestamp=timestamp,
            )
        if format == "json":
            return self._generate_json_report(
                protocol_name=protocol_name,
                metrics=metrics,
                visualizations=visualizations,
                report_dir=report_dir,
                timestamp=timestamp,
            )
        if format == "pdf":
            # PDF generation would go here
            return "PDF generation not yet implemented"
        raise ValueError(f"Unsupported format: {format}")

    def generate_historical_report(
        self,
        snapshots: List[Dict[str, Any]],
        protocol_name: str,
        format: str = "html",
    ) -> str:
        """Generate a report for historical data analysis.

        Args:
            snapshots: List of historical data snapshots
            protocol_name: Name of the protocol
            format: Output format (html, pdf, json)

        Returns:
            Path to the generated report

        Raises:
            ValueError: If snapshots list is empty or contains invalid data
        """
        # Validate input
        if not snapshots:
            raise ValueError("Cannot generate historical report: snapshots list is empty")

        # Validate snapshot format
        for i, snapshot in enumerate(snapshots):
            if "timestamp" not in snapshot or "data" not in snapshot:
                raise ValueError(f"Invalid snapshot format at index {i}: missing required fields")

        # Create a timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output filename
        filename_base = f"{protocol_name}_historical_report_{timestamp}"

        # Create folder for this report
        report_dir = os.path.join(self.output_dir, filename_base)
        os.makedirs(report_dir, exist_ok=True)

        # Create folder for visualizations
        viz_dir = os.path.join(report_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)

        # Extract latest metrics from most recent snapshot
        try:
            latest_metrics = self._extract_metrics(snapshots[-1]["data"])
        except (KeyError, IndexError, TypeError) as e:
            import logging

            logging.warning(f"Could not extract latest metrics: {e}")
            latest_metrics = []

        # Generate historical visualizations
        historical_visualizations = self._generate_historical_visualizations(snapshots, viz_dir)

        # Check if we have any visualizations
        if not historical_visualizations:
            import logging

            logging.warning("No historical visualizations were generated")

        # Generate report based on format
        if format == "html":
            report_path = self._generate_html_report(
                protocol_name=protocol_name,
                metrics=latest_metrics,
                visualizations=[],  # No snapshot visualizations, only historical
                historical_analysis={
                    "overview": f"Historical analysis of {protocol_name} token distribution over time",
                    "visualizations": historical_visualizations,
                },
                report_dir=report_dir,
                timestamp=timestamp,
            )
        elif format == "json":
            report_path = self._generate_json_report(
                protocol_name=protocol_name,
                metrics=latest_metrics,
                visualizations=[],
                historical_analysis={
                    "overview": f"Historical analysis of {protocol_name} token distribution over time",
                    "visualizations": historical_visualizations,
                },
                report_dir=report_dir,
                timestamp=timestamp,
            )
        elif format == "pdf":
            raise NotImplementedError("PDF report generation not implemented yet")
        else:
            raise ValueError(f"Unsupported format: {format}")

        return report_path

    def generate_comparison_report(self, protocol_data: Dict[str, Dict[str, Any]], format: str = "html") -> str:
        """Generate a report comparing multiple protocols.

        Args:
            protocol_data: Dictionary of protocol data keyed by protocol name
            format: Output format (html, pdf, json)

        Returns:
            Path to the generated report

        """
        # Create a timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output filename
        filename_base = f"protocol_comparison_report_{timestamp}"

        # Create folder for this report
        report_dir = os.path.join(self.output_dir, filename_base)
        os.makedirs(report_dir, exist_ok=True)

        # Create folder for visualizations
        viz_dir = os.path.join(report_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)

        # Extract metrics for each protocol
        protocol_metrics = {}
        for protocol, data in protocol_data.items():
            protocol_metrics[protocol] = self._extract_metrics(data)

        # Generate comparison visualizations
        comparison_visualizations = self._generate_comparison_visualizations(protocol_data, viz_dir)

        # Generate report based on format
        if format == "html":
            report_path = self._generate_html_report(
                protocol_name="Multiple Protocols",
                metrics=[],  # No single protocol metrics
                visualizations=[],  # No single protocol visualizations
                comparison={
                    "overview": f"Comparison of token distribution across {', '.join(protocol_data.keys())}",
                    "visualizations": comparison_visualizations,
                    "protocol_metrics": protocol_metrics,
                },
                report_dir=report_dir,
                timestamp=timestamp,
            )
        elif format == "json":
            report_path = self._generate_json_report(
                protocol_name="Multiple Protocols",
                metrics=[],
                visualizations=[],
                comparison={
                    "overview": f"Comparison of token distribution across {', '.join(protocol_data.keys())}",
                    "visualizations": comparison_visualizations,
                    "protocol_metrics": protocol_metrics,
                },
                report_dir=report_dir,
                timestamp=timestamp,
            )
        elif format == "pdf":
            raise NotImplementedError("PDF report generation not implemented yet")
        else:
            raise ValueError(f"Unsupported format: {format}")

        return report_path

    def _extract_metrics(self, protocol_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key metrics from protocol data."""
        metrics = []

        # Extract metrics if available
        if "metrics" in protocol_data:
            for key, value in protocol_data["metrics"].items():
                metric = {
                    "name": key.replace("_", " ").title(),
                    "value": value,
                    "description": self._get_metric_description(key),
                }
                metrics.append(metric)

        # Add token holder count
        if "token_holders" in protocol_data:
            metrics.append(
                {
                    "name": "Token Holder Count",
                    "value": len(protocol_data["token_holders"]),
                    "description": "Total number of token holders",
                }
            )

        # Add governance participation if available
        if "governance_data" in protocol_data and "participation_rate" in protocol_data["governance_data"]:
            metrics.append(
                {
                    "name": "Governance Participation Rate",
                    "value": f"{protocol_data['governance_data']['participation_rate']:.2f}%",
                    "description": "Percentage of token supply that participates in governance",
                }
            )

        return metrics

    @staticmethod
    def _get_metric_description(metric_name: str) -> str:
        """Get description for a specific metric."""
        descriptions = {
            "gini_coefficient": "Measure of inequality in token distribution (0=equal, 1=unequal)",
            "top_10_concentration": "Percentage of tokens held by top 10 holders",
            "participation_rate": "Percentage of token supply that participates in governance",
            "proposal_count": "Number of governance proposals",
        }

        return descriptions.get(metric_name, "No description available")

    @staticmethod
    def _generate_snapshot_visualizations(protocol_data: Dict[str, Any], viz_dir: str) -> List[Dict[str, str]]:
        """Generate visualizations for a protocol snapshot."""
        visualizations = []

        # Create distribution chart
        if "token_holders" in protocol_data:
            holder_df = pd.DataFrame(protocol_data["token_holders"])

            # Distribution chart
            fig = charts.create_distribution_chart(holder_df, title="Token Holder Distribution")
            dist_chart_path = os.path.join(viz_dir, "distribution_chart.png")
            fig.savefig(dist_chart_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Token Holder Distribution",
                    "path": os.path.relpath(dist_chart_path, start=os.path.dirname(viz_dir)),
                    "description": "Distribution of tokens among holders",
                }
            )

            # Lorenz curve
            fig = charts.create_lorenz_curve(holder_df["balance"], title="Token Distribution Lorenz Curve")
            lorenz_path = os.path.join(viz_dir, "lorenz_curve.png")
            fig.savefig(lorenz_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Lorenz Curve",
                    "path": os.path.relpath(lorenz_path, start=os.path.dirname(viz_dir)),
                    "description": "Lorenz curve showing inequality in token distribution",
                }
            )

        return visualizations

    @staticmethod
    def _generate_historical_visualizations(snapshots: List[Dict[str, Any]], viz_dir: str) -> List[Dict[str, str]]:
        """Generate visualizations for historical data."""
        visualizations = []

        # Create a time series from snapshots
        time_series_data = []
        for snapshot in snapshots:
            timestamp = datetime.fromisoformat(snapshot["timestamp"])

            # Extract metrics
            metrics = snapshot["data"].get("metrics", {})

            # Add governance data if available
            governance_data = snapshot["data"].get("governance_data", {})
            participation_rate = governance_data.get("participation_rate")

            time_series_data.append(
                {
                    "timestamp": timestamp,
                    "gini_coefficient": metrics.get("gini_coefficient"),
                    "top_10_concentration": metrics.get("top_10_concentration"),
                    "participation_rate": participation_rate,
                }
            )

        # Convert to DataFrame
        df = pd.DataFrame(time_series_data)
        df.set_index("timestamp", inplace=True)

        # Generate gini coefficient over time chart
        if "gini_coefficient" in df.columns:
            fig = historical_charts.plot_metric_over_time(df, "gini_coefficient", title="Gini Coefficient Over Time")
            gini_path = os.path.join(viz_dir, "gini_over_time.png")
            fig.savefig(gini_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Gini Coefficient Over Time",
                    "path": os.path.relpath(gini_path, start=os.path.dirname(viz_dir)),
                    "description": "Changes in token distribution inequality over time",
                }
            )

        # Generate top 10 concentration over time chart
        if "top_10_concentration" in df.columns:
            fig = historical_charts.plot_metric_over_time(
                df,
                "top_10_concentration",
                title="Top 10 Holder Concentration Over Time",
            )
            top10_path = os.path.join(viz_dir, "top10_over_time.png")
            fig.savefig(top10_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Top 10 Holder Concentration Over Time",
                    "path": os.path.relpath(top10_path, start=os.path.dirname(viz_dir)),
                    "description": "Changes in token concentration among top 10 holders over time",
                }
            )

        # Generate participation rate over time chart
        if "participation_rate" in df.columns:
            fig = historical_charts.plot_metric_over_time(
                df,
                "participation_rate",
                title="Governance Participation Rate Over Time",
            )
            participation_path = os.path.join(viz_dir, "participation_over_time.png")
            fig.savefig(participation_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Governance Participation Rate Over Time",
                    "path": os.path.relpath(participation_path, start=os.path.dirname(viz_dir)),
                    "description": "Changes in governance participation over time",
                }
            )

        # Generate concentration heatmap
        fig = historical_charts.create_concentration_heatmap(snapshots)
        heatmap_path = os.path.join(viz_dir, "concentration_heatmap.png")
        fig.savefig(heatmap_path)
        plt.close(fig)

        visualizations.append(
            {
                "title": "Token Concentration Heatmap",
                "path": os.path.relpath(heatmap_path, start=os.path.dirname(viz_dir)),
                "description": "Heatmap showing changes in token concentration over time",
            }
        )

        # Create multi-metric dashboard
        metrics_to_include = [col for col in df.columns if not df[col].isnull().all()]
        if len(metrics_to_include) >= 2:
            try:
                # Create a dictionary mapping each metric to the full DataFrame
                # This is the correct format expected by create_multi_metric_dashboard
                metrics_data = {}
                for metric in metrics_to_include:
                    # Create a copy of the DataFrame with only the relevant metric column
                    metric_df = pd.DataFrame(df[metric].copy())
                    # Rename the column to match what the function expects
                    metric_df.columns = [metric]
                    metrics_data[metric] = metric_df

                fig = historical_charts.create_multi_metric_dashboard(
                    metrics_data,
                    metrics=metrics_to_include,
                    title="Governance Metrics Dashboard",
                )
                dashboard_path = os.path.join(viz_dir, "metrics_dashboard.png")
                fig.savefig(dashboard_path)
                plt.close(fig)

                visualizations.append(
                    {
                        "title": "Governance Metrics Dashboard",
                        "path": os.path.relpath(dashboard_path, start=os.path.dirname(viz_dir)),
                        "description": "Dashboard showing multiple governance metrics over time",
                    }
                )
            except Exception as e:
                # Log the error but continue with other visualizations
                import logging

                logging.error(f"Failed to create multi-metric dashboard: {e}")
                # Don't add this visualization to the list

        return visualizations

    @staticmethod
    def _generate_comparison_visualizations(
        protocol_data: Dict[str, Dict[str, Any]], viz_dir: str
    ) -> List[Dict[str, str]]:
        """Generate visualizations comparing multiple protocols."""
        visualizations = []

        # Extract metrics for each protocol
        metrics_data = {}
        for protocol, data in protocol_data.items():
            metrics = data.get("metrics", {})
            metrics_data[protocol] = metrics

        # Create bar chart comparing gini coefficients
        if all("gini_coefficient" in metrics for metrics in metrics_data.values()):
            protocols = list(protocol_data.keys())
            gini_values = [metrics_data[p]["gini_coefficient"] for p in protocols]

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(protocols, gini_values)
            ax.set_xlabel("Protocol")
            ax.set_ylabel("Gini Coefficient")
            ax.set_title("Gini Coefficient Comparison")
            ax.grid(axis="y", alpha=0.3)

            # Add value labels
            for i, v in enumerate(gini_values):
                ax.text(i, v + 0.01, f"{v:.3f}", ha="center")

            gini_path = os.path.join(viz_dir, "gini_comparison.png")
            fig.savefig(gini_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Gini Coefficient Comparison",
                    "path": os.path.relpath(gini_path, start=os.path.dirname(viz_dir)),
                    "description": "Comparison of token distribution inequality across protocols",
                }
            )

        # Create bar chart comparing top 10 holder concentration
        if all("top_10_concentration" in metrics for metrics in metrics_data.values()):
            protocols = list(protocol_data.keys())
            top10_values = [metrics_data[p]["top_10_concentration"] for p in protocols]

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(protocols, top10_values)
            ax.set_xlabel("Protocol")
            ax.set_ylabel("Top 10 Concentration (%)")
            ax.set_title("Top 10 Holder Concentration Comparison")
            ax.grid(axis="y", alpha=0.3)

            # Add value labels
            for i, v in enumerate(top10_values):
                ax.text(i, v + 1, f"{v:.1f}%", ha="center")

            top10_path = os.path.join(viz_dir, "top10_comparison.png")
            fig.savefig(top10_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Top 10 Holder Concentration Comparison",
                    "path": os.path.relpath(top10_path, start=os.path.dirname(viz_dir)),
                    "description": "Comparison of token concentration among top 10 holders across protocols",
                }
            )

        # Create radar chart for multiple metrics
        # First, check which metrics are available for all protocols
        common_metrics = ["gini_coefficient", "top_10_concentration"]

        if all(any(m in metrics_data[p] for m in common_metrics) for p in protocol_data):
            # Create radar chart data
            metric_labels = [m.replace("_", " ").title() for m in common_metrics]

            # Normalize values for radar chart
            normalized_values = {}
            for protocol in protocol_data:
                values = []
                for metric in common_metrics:
                    if metric in metrics_data[protocol]:
                        # Normalize based on metric type
                        if metric == "gini_coefficient":
                            # Gini is already 0-1
                            values.append(metrics_data[protocol][metric])
                        elif metric == "top_10_concentration":
                            # Convert percentage to 0-1
                            values.append(metrics_data[protocol][metric] / 100)
                        else:
                            values.append(metrics_data[protocol].get(metric, 0))
                    else:
                        values.append(0)
                normalized_values[protocol] = values

            # Create radar chart
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, polar=True)

            # Set the angle of each metric
            angles = np.linspace(0, 2 * np.pi, len(common_metrics), endpoint=False).tolist()
            # Make the plot a full circle
            angles += angles[:1]

            # Plot each protocol
            for protocol, values in normalized_values.items():
                # Complete the loop
                values += values[:1]
                ax.plot(angles, values, linewidth=2, label=protocol.capitalize())
                ax.fill(angles, values, alpha=0.1)

            # Set labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metric_labels)

            # Set y-limits
            ax.set_ylim(0, 1)

            # Add legend
            ax.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))

            radar_path = os.path.join(viz_dir, "protocol_comparison_radar.png")
            fig.savefig(radar_path)
            plt.close(fig)

            visualizations.append(
                {
                    "title": "Protocol Comparison Radar Chart",
                    "path": os.path.relpath(radar_path, start=os.path.dirname(viz_dir)),
                    "description": "Radar chart comparing key metrics across protocols",
                }
            )

        return visualizations

    def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate an HTML report from report data.

        Args:
            report_data: Dictionary containing report data including protocol info,
                        metrics, visualizations, etc.

        Returns:
            Path to the generated HTML report
        """
        # Extract data from report_data
        protocol_name = report_data.get("protocol", "Unknown")
        protocol_info = report_data.get("protocol_info", {})
        current_metrics = report_data.get("current_metrics", {})
        timestamp = report_data.get("timestamp", datetime.now().isoformat())

        # Convert metrics to the expected format
        metrics = []
        for key, value in current_metrics.items():
            metrics.append(
                {
                    "name": key.replace("_", " ").title(),
                    "value": f"{value:.4f}" if isinstance(value, (int, float)) else str(value),
                    "description": self._get_metric_description(key),
                }
            )

        # Format holders count and total supply safely
        holders_count = report_data.get("holders_count", "N/A")
        if isinstance(holders_count, (int, float)):
            holders_display = f"{holders_count:,g}"
        else:
            holders_display = str(holders_count)

        total_supply = report_data.get("total_supply", "N/A")
        if isinstance(total_supply, (int, float)):
            supply_display = f"{total_supply:,.2f} tokens"
        else:
            supply_display = str(total_supply)

        # Create basic HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{protocol_name.upper()} Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                .metrics {{ margin: 20px 0; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
                .metric-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #007acc; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007acc; }}
                .protocol-info {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏛️ {protocol_name.upper()} Governance Token Analysis</h1>
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Total Holders:</strong> {holders_display}</p>
                <p><strong>Total Supply:</strong> {supply_display}</p>
            </div>

            <div class="protocol-info">
                <h2>📋 Protocol Information</h2>
                <p><strong>Name:</strong> {protocol_info.get("name", protocol_name.title())}</p>
                <p><strong>Description:</strong> {protocol_info.get("description", "Decentralized governance protocol")}</p>
                <p><strong>Website:</strong> <a href="{protocol_info.get("website", "#")}">{protocol_info.get("website", "N/A")}</a></p>
            </div>

            <div class="metrics">
                <h2>📊 Key Concentration Metrics</h2>
                <div class="metric-grid">
        """

        # Add metric cards
        for metric in metrics:
            html_content += f"""
                    <div class="metric-card">
                        <h3>{metric["name"]}</h3>
                        <div class="metric-value">{metric["value"]}</div>
                        <p>{metric["description"]}</p>
                    </div>
            """

        html_content += """
                </div>
            </div>

            <div class="analysis">
                <h2>🔍 Analysis Summary</h2>
                <table>
                    <tr>
                        <th>Aspect</th>
                        <th>Assessment</th>
                        <th>Interpretation</th>
                    </tr>
        """

        # Add analysis rows based on metrics
        gini = current_metrics.get("gini_coefficient", 0)
        nakamoto = current_metrics.get("nakamoto_coefficient", 0)

        # Gini coefficient analysis
        if gini < 0.5:
            gini_assessment = "Low Concentration"
            gini_interpretation = "Token distribution is relatively decentralized"
        elif gini < 0.7:
            gini_assessment = "Moderate Concentration"
            gini_interpretation = "Token distribution shows moderate concentration"
        else:
            gini_assessment = "High Concentration"
            gini_interpretation = "Token distribution is highly concentrated"

        html_content += f"""
                    <tr>
                        <td>Token Distribution (Gini)</td>
                        <td>{gini_assessment}</td>
                        <td>{gini_interpretation}</td>
                    </tr>
        """

        # Nakamoto coefficient analysis
        if nakamoto >= 50:
            nakamoto_assessment = "Highly Decentralized"
            nakamoto_interpretation = "Requires many entities to control 51% of tokens"
        elif nakamoto >= 20:
            nakamoto_assessment = "Moderately Decentralized"
            nakamoto_interpretation = "Moderate number of entities needed for control"
        else:
            nakamoto_assessment = "Centralized"
            nakamoto_interpretation = "Few entities could potentially control the protocol"

        html_content += f"""
                    <tr>
                        <td>Governance Decentralization</td>
                        <td>{nakamoto_assessment}</td>
                        <td>{nakamoto_interpretation}</td>
                    </tr>
                </table>
            </div>
        """

        # Add historical analysis if available
        if report_data.get("include_historical") or report_data.get("historical_data"):
            html_content += """
            <div class="historical">
                <h2>📈 Historical Analysis</h2>
                <p>Historical data shows trends in token concentration over time.</p>
                <p>Historical trend analysis helps understand how token concentration has evolved over time.</p>
            </div>
            """

        html_content += """
            <div class="footer">
                <p>Generated using Governance Token Distribution Analyzer v1.0.0</p>
                <p>Report includes mathematical validation and cross-protocol benchmarking.</p>
            </div>
        </body>
        </html>
        """

        # Save the HTML content to a file
        output_path = report_data.get("output_path")
        if not output_path:
            # Create a default output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"{protocol_name.lower()}_report.html")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the HTML content to the file
        with open(output_path, "w") as f:
            f.write(html_content)

        return output_path

    def _generate_html_report(
        self,
        protocol_name: str,
        metrics: List[Dict[str, Any]],
        visualizations: List[Dict[str, str]],
        report_dir: str,
        timestamp: str,
        historical_analysis: Optional[Dict[str, Any]] = None,
        comparison: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate an HTML report."""
        # Get the template
        template = self.jinja_env.get_template("report_template.html")

        # Prepare template context
        context = {
            "title": f"{protocol_name} Governance Token Analysis Report",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overview": f"Analysis of governance token distribution for {protocol_name}",
            "metrics": metrics,
            "visualizations": visualizations,
            "historical_analysis": historical_analysis,
            "comparison": comparison,
            "conclusion": "This report provides insights into the token distribution and governance of the protocol.",
        }

        # Render template
        html_content = template.render(**context)

        # Save to file
        output_path = os.path.join(report_dir, "report.html")
        with open(output_path, "w") as f:
            f.write(html_content)

        return output_path

    @staticmethod
    def _generate_json_report(
        protocol_name: str,
        metrics: List[Dict[str, Any]],
        visualizations: List[Dict[str, str]],
        report_dir: str,
        timestamp: str,
        historical_analysis: Optional[Dict[str, Any]] = None,
        comparison: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a JSON report."""
        report_data = {
            "title": f"{protocol_name} Governance Token Analysis Report",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overview": f"Analysis of governance token distribution for {protocol_name}",
            "metrics": metrics,
            "visualizations": visualizations,
            "historical_analysis": historical_analysis,
            "comparison": comparison,
            "conclusion": "This report provides insights into the token distribution and governance of the protocol.",
        }

        # Save to file
        output_path = os.path.join(report_dir, "report.json")
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        return output_path

    def generate_report(
        self,
        protocol: str,
        current_data: Dict[str, Any],
        governance_data: List[Dict[str, Any]],
        votes_data: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]] = None,
        format: str = "html",
        output_path: Optional[str] = None,
        include_historical: bool = False,
    ) -> str:
        """Generate a comprehensive analysis report.

        Args:
            protocol: Protocol name
            current_data: Current token distribution data
            governance_data: Governance proposal data
            votes_data: Voting data
            historical_data: Historical data dictionary
            format: Output format (html, json)
            output_path: Path to save the report (optional)
            include_historical: Whether to include historical analysis

        Returns:
            Path to the generated report
        """
        # Create a timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Set default output path if not provided
        if output_path is None:
            output_path = os.path.join(self.output_dir, f"{protocol}_report_{timestamp}.html")

        # Prepare the report data
        report_data = {
            "title": f"{protocol.upper()} Governance Token Analysis Report",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "protocol": protocol.upper(),
            "overview": f"This report provides a comprehensive analysis of {protocol.upper()} governance token distribution and governance participation.",
            "metrics": [],
            "visualizations": [],
            "include_historical": include_historical,
            "conclusion": f"This analysis of {protocol.upper()} governance token distribution and governance participation provides insights into the current state of decentralization and governance activity.",
        }

        # Extract metrics from current data
        if current_data:
            metrics = self._extract_metrics(current_data)
            report_data["metrics"].extend(metrics)

        # Create visualization directory
        viz_dir = os.path.join(os.path.dirname(output_path), "visualizations")
        os.makedirs(viz_dir, exist_ok=True)

        # Generate visualizations
        visualizations = []

        # Add distribution visualizations
        if current_data and "token_holders" in current_data:
            try:
                # Generate token distribution chart
                viz_path = os.path.join(viz_dir, f"{protocol}_token_distribution.png")
                charts.create_token_distribution_chart(
                    token_holders=current_data["token_holders"],
                    output_path=viz_path,
                    title=f"{protocol.upper()} Token Distribution",
                )

                visualizations.append(
                    {
                        "title": f"{protocol.upper()} Token Distribution",
                        "path": viz_path,
                        "description": "Distribution of tokens among top token holders.",
                    }
                )
            except Exception as e:
                print(f"Error generating token distribution chart: {e}")

        # Add governance visualizations
        if governance_data and votes_data:
            try:
                # Generate governance participation chart
                viz_path = os.path.join(viz_dir, f"{protocol}_governance_participation.png")
                charts.create_governance_participation_chart(
                    proposals=governance_data,
                    votes=votes_data,
                    output_path=viz_path,
                    title=f"{protocol.upper()} Governance Participation",
                )

                visualizations.append(
                    {
                        "title": f"{protocol.upper()} Governance Participation",
                        "path": viz_path,
                        "description": "Participation rates in governance proposals.",
                    }
                )
            except Exception as e:
                print(f"Error generating governance participation chart: {e}")

        # Add historical analysis if available
        historical_analysis = None
        if historical_data:
            historical_analysis = {
                "overview": f"Historical analysis of {protocol.upper()} token distribution and governance metrics.",
                "visualizations": [],
            }

            try:
                # Generate historical metrics chart
                for metric in ["gini_coefficient", "nakamoto_coefficient"]:
                    if metric in historical_data:
                        viz_path = os.path.join(viz_dir, f"{protocol}_{metric}_historical.png")
                        historical_charts.create_time_series_chart(
                            time_series=historical_data[metric],
                            output_path=viz_path,
                            title=f"{protocol.upper()} Historical {metric.replace('_', ' ').title()}",
                        )

                        historical_analysis["visualizations"].append(
                            {
                                "title": f"{protocol.upper()} Historical {metric.replace('_', ' ').title()}",
                                "path": viz_path,
                                "description": f"Historical trend of {metric.replace('_', ' ').title()} over time.",
                            }
                        )
            except Exception as e:
                print(f"Error generating historical charts: {e}")

        # Add visualizations to report data
        report_data["visualizations"] = visualizations

        # Add historical analysis if available
        if historical_analysis:
            report_data["historical_analysis"] = historical_analysis

        # Generate the report based on format
        if format == "html":
            # Add output path to report data
            report_data["output_path"] = output_path
            return self.generate_html_report(report_data)
        if format == "json":
            return self._generate_json_report(
                protocol_name=protocol,
                metrics=report_data["metrics"],
                visualizations=report_data["visualizations"],
                report_dir=os.path.dirname(output_path),
                timestamp=timestamp,
def generate_historical_analysis_report(protocol, snapshots, output_path):
            )
        raise ValueError(f"Unsupported format: {format}")


def generate_historical_analysis_report(protocol, time_series_data, snapshots, output_path):
    """Generate a historical analysis report."""
    # Create the report generator
    report_dir = os.path.dirname(output_path)
    report_gen = ReportGenerator(output_dir=report_dir)

    # Generate the report
    return report_gen.generate_historical_report(snapshots=snapshots, protocol_name=protocol, format="html")


def generate_comprehensive_report(protocol, snapshots, time_series_data, visualization_paths, output_path):
    """Generate a comprehensive report with all analysis components.

    This is a standalone function that creates a comprehensive report with
    all available analysis components including current state, historical trends,
    and visualizations.

    Args:
        protocol: Name of the protocol
        snapshots: List of historical snapshots
        time_series_data: Dictionary mapping metric names to their time series DataFrames
        visualization_paths: Dictionary mapping metric names to their visualization file paths
        output_path: Path to save the report

    Returns:
        Path to the generated report

    """
    # Create a report generator instance
    report_gen = ReportGenerator(output_dir=os.path.dirname(output_path))

    # Get the latest snapshot
    latest_snapshot = snapshots[-1] if snapshots else None

    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{protocol.capitalize()} Comprehensive Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            .metric {{ margin-bottom: 15px; }}
            img {{ max-width: 100%; height: auto; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>{protocol.capitalize()} Comprehensive Governance Analysis Report</h1>
        <div class="section">
            <h2>Overview</h2>
            <p>This report provides a comprehensive analysis of the {protocol.capitalize()} governance token distribution and historical trends.</p>
        </div>
    """

    # Add visualizations
    if visualization_paths:
        html_content += """
        <div class="section">
            <h2>Visualizations</h2>
        """

        for metric, path in visualization_paths.items():
            # Create a relative path for the image
            rel_path = os.path.basename(path)

            # Skip copying if source and destination are the same
            dest_path = os.path.join(os.path.dirname(output_path), rel_path)
            if os.path.abspath(path) != os.path.abspath(dest_path):
                # Copy the image to the output directory
                shutil.copy(path, dest_path)

            html_content += f"""
            <div class="metric">
                <h3>{metric.replace("_", " ").title()}</h3>
                <img src="{rel_path}" alt="{metric} visualization">
            </div>
            """

        html_content += "</div>"

    # Add historical data
    if time_series_data:
        html_content += """
        <div class="section">
            <h2>Historical Analysis</h2>
        """

        for metric, data in time_series_data.items():
            html_content += f"""
            <div class="metric">
                <h3>{metric.replace("_", " ").title()}</h3>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Value</th>
                    </tr>
            """

            for idx, row in data.iterrows():
                date_str = idx.strftime("%Y-%m-%d") if isinstance(idx, pd.Timestamp) else str(idx)
                value = row[metric] if metric in row else "N/A"
                formatted_value = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
                html_content += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{formatted_value}</td>
                    </tr>
                """

            html_content += """
                </table>
            </div>
            """

        html_content += "</div>"

    # Add latest snapshot data
    if latest_snapshot:
        html_content += """
        <div class="section">
            <h2>Current Distribution</h2>
        """

        # Add metrics
        if "metrics" in latest_snapshot.get("data", {}):
            html_content += """
            <div class="metric">
                <h3>Key Metrics</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
            """

            for metric, value in latest_snapshot["data"]["metrics"].items():
                formatted_value = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
                html_content += f"""
                    <tr>
                        <td>{metric.replace("_", " ").title()}</td>
                        <td>{formatted_value}</td>
                    </tr>
                """

            html_content += """
                </table>
            </div>
            """

        html_content += "</div>"

    # Close HTML
    html_content += """
    </body>
    </html>
    """

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_content)

    return output_path
