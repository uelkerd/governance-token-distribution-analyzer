#!/usr/bin/env python
"""Base Report Generator for Governance Token Distribution Analysis.

This module provides the core ReportGenerator class with basic functionality
for generating reports with visualizations for governance token distribution analysis.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Configure logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Base class for generating comprehensive reports with visualizations and analysis."""

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
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

        self.template_dir = template_dir

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = self._setup_jinja_env()

    def _setup_jinja_env(self):
        """Set up Jinja2 environment with templates.

        Returns:
            Jinja2 Environment instance
        """
        # Check if template directory exists
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)

            # Create a basic template if none exists
            basic_template = self._get_basic_template()

            # Save the basic template
            with open(os.path.join(self.template_dir, "report_template.html"), "w") as f:
                f.write(basic_template)

        # Initialize Jinja2 environment
        return Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    @staticmethod
    def _get_basic_template():
        """Return a basic HTML template for reports."""
        return """<!DOCTYPE html>
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
</html>"""

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

    def generate_report(
        self,
        protocol: str,
        current_data: Dict[str, Any],
        governance_data: List[Dict[str, Any]],
        votes_data: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]] = None,
        output_format: str = "html",
        output_path: Optional[str] = None,
        include_historical: bool = False,
    ) -> str:
        """Generate a comprehensive analysis report.

        This method creates a complete analysis including current data,
        governance proposals, voting data, and historical analysis if available.

        Args:
            protocol: Protocol name
            current_data: Current distribution data
            governance_data: Governance proposals data
            votes_data: Voting data
            historical_data: Historical data dictionary
            output_format: Output format ('html', 'json', 'pdf')
            output_path: Path to save the report
            include_historical: Whether to include historical analysis

        Returns:
            Path to the generated report
        """
        # Set up output directory and report path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.output_dir if output_path is None else os.path.dirname(output_path)
        os.makedirs(report_dir, exist_ok=True)

        # Create visualization directory
        viz_dir = os.path.join(report_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)

        # Set the output path if not provided
        if output_path is None:
            output_path = os.path.join(report_dir, f"{protocol}_report_{timestamp}.{output_format.lower()}")

        # Generate the report based on format
        if output_format == "html":
            from .html_report_generator import generate_comprehensive_html_report

            return generate_comprehensive_html_report(
                self,
                protocol=protocol,
                current_data=current_data,
                governance_data=governance_data,
                votes_data=votes_data,
                historical_data=historical_data,
                output_path=output_path,
                report_dir=report_dir,
                viz_dir=viz_dir,
                timestamp=timestamp,
            )
        if output_format == "json":
            # JSON report generation
            # ... (implementation details)
            raise NotImplementedError("JSON report generation not implemented yet")
        if output_format == "pdf":
            # PDF report generation
            # ... (implementation details)
            raise NotImplementedError("PDF report generation not implemented yet")
        raise ValueError(f"Unsupported format: {output_format}")
