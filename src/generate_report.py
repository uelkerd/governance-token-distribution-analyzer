#!/usr/bin/env python
"""Governance Token Distribution Report Generator.

This script generates comprehensive reports on governance token distribution patterns
including visualizations, metrics, and insights across multiple protocols.
"""

import os
import sys
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.gridspec as gridspec
import numpy as np

# Add the src directory to the Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(src_dir))

# Import project modules
from src.analyzer.config import Config, DEFAULT_OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive reports on governance token distribution."""

    def __init__(self, output_dir: str = "reports"):
        """Initialize the report generator.

        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.config = Config()

        # Set up styling for plots
        self._setup_plot_style()

    def _setup_plot_style(self):
        """Configure plot styling for consistent report aesthetics."""
        # Use seaborn styling
        sns.set_theme(style="whitegrid")

        # Set color palette
        self.colors = sns.color_palette("viridis", 10)

        # Custom style for matplotlib
        plt.rcParams.update(
            {
                "figure.figsize": (10, 6),
                "axes.labelsize": 12,
                "axes.titlesize": 14,
                "xtick.labelsize": 10,
                "ytick.labelsize": 10,
                "legend.fontsize": 10,
                "font.family": "sans-serif",
            }
        )

    def load_protocol_data(self, protocols: List[str]) -> Dict[str, Dict]:
        """Load analysis data for multiple protocols.

        Args:
            protocols: List of protocol names to include in the report

        Returns:
            Dictionary mapping protocol names to their analysis data
        """
        data = {}
        for protocol in protocols:
            try:
                logger.info(f"Loading data for {protocol}")
                # Load data from JSON file
                file_path = Path(DEFAULT_OUTPUT_DIR) / f"{protocol}_analysis.json"

                if not file_path.exists():
                    logger.error(f"Analysis file not found: {file_path}")
                    continue

                with open(file_path, "r") as f:
                    protocol_data = json.load(f)

                data[protocol] = protocol_data
            except Exception as e:
                logger.error(f"Error loading data for {protocol}: {str(e)}")

        return data

    def generate_comparative_concentration_chart(
        self, protocol_data: Dict[str, Dict]
    ) -> str:
        """Generate a comparative chart of concentration metrics across protocols.

        Args:
            protocol_data: Dictionary of protocol analysis data

        Returns:
            Path to the saved chart
        """
        # Extract Gini coefficients and Herfindahl indices
        protocols = []
        gini_values = []
        hhi_values = []

        for protocol, data in protocol_data.items():
            protocols.append(data.get("symbol", protocol.upper()))

            # Extract metrics (with fallbacks if not available)
            metrics = data.get("concentration_metrics", {})
            gini_values.append(metrics.get("gini_coefficient", 0))
            hhi_values.append(
                metrics.get("herfindahl_index", 0) / 10000
            )  # Normalize HHI to 0-1

        # Create a DataFrame for easier plotting
        df = pd.DataFrame(
            {
                "Protocol": protocols,
                "Gini Coefficient": gini_values,
                "Normalized HHI": hhi_values,
            }
        )

        # Sort by Gini coefficient
        df = df.sort_values("Gini Coefficient")

        # Create the plot
        plt.figure(figsize=(12, 8))

        # Create a grouped bar chart
        bar_width = 0.35
        r1 = np.arange(len(protocols))
        r2 = [x + bar_width for x in r1]

        plt.bar(
            r1,
            df["Gini Coefficient"],
            width=bar_width,
            label="Gini Coefficient",
            color=self.colors[0],
        )
        plt.bar(
            r2,
            df["Normalized HHI"],
            width=bar_width,
            label="Normalized HHI",
            color=self.colors[2],
        )

        # Add labels and title
        plt.xlabel("Protocol")
        plt.ylabel("Concentration Value (0-1 scale)")
        plt.title("Governance Token Concentration Comparison", fontsize=16)
        plt.xticks([r + bar_width / 2 for r in range(len(protocols))], df["Protocol"])
        plt.legend()

        # Add a reference line for high concentration
        plt.axhline(y=0.6, color="r", linestyle="--", alpha=0.7)
        plt.text(len(protocols) - 1, 0.62, "High Concentration Threshold", color="r")

        # Save the chart
        chart_path = self.output_dir / "comparative_concentration.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300)
        plt.close()

        logger.info(f"Comparative concentration chart saved to {chart_path}")
        return str(chart_path)

    def generate_distribution_comparison(self, protocol_data: Dict[str, Dict]) -> str:
        """Generate a comparison of token distribution patterns across protocols.

        Args:
            protocol_data: Dictionary of protocol analysis data

        Returns:
            Path to the saved chart
        """
        # Set up the figure with subplots for each protocol
        fig = plt.figure(figsize=(15, 10))

        # Create a grid layout based on the number of protocols
        n_protocols = len(protocol_data)
        if n_protocols <= 2:
            rows, cols = 1, n_protocols
        elif n_protocols <= 4:
            rows, cols = 2, 2
        else:
            rows = (n_protocols + 2) // 3  # Ceiling division
            cols = 3

        # Create pie charts for each protocol
        for i, (protocol, data) in enumerate(protocol_data.items()):
            ax = plt.subplot(rows, cols, i + 1)

            # Extract top holders data
            top_holders = data.get("top_holders", [])

            if not top_holders:
                ax.text(
                    0.5,
                    0.5,
                    f"No holder data for {protocol}",
                    horizontalalignment="center",
                    verticalalignment="center",
                )
                continue

            # Extract top 5 holders plus "Others"
            labels = [f"#{h.get('rank', i + 1)}" for i, h in enumerate(top_holders[:5])]
            sizes = [h.get("percentage", 0) for h in top_holders[:5]]

            # Add "Others" slice
            others_pct = 100 - sum(sizes)
            if others_pct > 0:
                labels.append("Others")
                sizes.append(others_pct)

            # Create pie chart
            explode = [0.1] + [0] * (len(sizes) - 1)  # Explode the first slice
            wedges, texts, autotexts = ax.pie(
                sizes,
                explode=explode,
                labels=None,
                autopct="%1.1f%%",
                shadow=True,
                startangle=90,
                colors=self.colors,
            )

            # Add legend and title
            ax.legend(
                wedges,
                labels,
                title="Holders",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
            )
            ax.set_title(f"{data.get('name', protocol)} ({data.get('symbol', '')})")

        # Add overall title
        plt.suptitle("Governance Token Distribution Comparison", fontsize=16, y=0.98)

        # Save the chart
        chart_path = self.output_dir / "distribution_comparison.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"Distribution comparison chart saved to {chart_path}")
        return str(chart_path)

    def generate_top_holders_bar_chart(self, protocol_data: Dict[str, Dict]) -> str:
        """Generate a bar chart comparing top holders across protocols.

        Args:
            protocol_data: Dictionary of protocol analysis data

        Returns:
            Path to the saved chart
        """
        # Extract top holders data
        protocols = []
        top5_pct = []
        top10_pct = []
        top20_pct = []

        for protocol, data in protocol_data.items():
            protocols.append(data.get("symbol", protocol.upper()))

            # Extract top holders percentages
            metrics = data.get("concentration_metrics", {})
            percentages = metrics.get("top_holders_percentage", {})

            top5_pct.append(percentages.get("5", 0) if "5" in percentages else 0)
            top10_pct.append(percentages.get("10", 0) if "10" in percentages else 0)
            top20_pct.append(percentages.get("20", 0) if "20" in percentages else 0)

        # Create DataFrame for plotting
        df = pd.DataFrame(
            {
                "Protocol": protocols,
                "Top 5 Holders": top5_pct,
                "Top 10 Holders": top10_pct,
                "Top 20 Holders": top20_pct,
            }
        )

        # Sort by top 5 holders percentage
        df = df.sort_values("Top 5 Holders")

        # Create the plot
        plt.figure(figsize=(12, 8))

        # Set position of bars on X axis
        x_pos = np.arange(len(protocols))
        bar_width = 0.25

        # Create bars
        plt.bar(
            x_pos - bar_width,
            df["Top 5 Holders"],
            width=bar_width,
            label="Top 5 Holders",
            color=self.colors[0],
        )
        plt.bar(
            x_pos,
            df["Top 10 Holders"],
            width=bar_width,
            label="Top 10 Holders",
            color=self.colors[2],
        )
        plt.bar(
            x_pos + bar_width,
            df["Top 20 Holders"],
            width=bar_width,
            label="Top 20 Holders",
            color=self.colors[4],
        )

        # Add labels and title
        plt.xlabel("Protocol")
        plt.ylabel("Percentage of Total Supply")
        plt.title("Top Holders Comparison Across Governance Tokens", fontsize=16)
        plt.xticks(x_pos, df["Protocol"])
        plt.legend()

        # Add a reference line at 50% for majority control
        plt.axhline(y=50, color="r", linestyle="--", alpha=0.7)
        plt.text(len(protocols) - 1, 52, "50% Control Threshold", color="r")

        # Save the chart
        chart_path = self.output_dir / "top_holders_comparison.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300)
        plt.close()

        logger.info(f"Top holders comparison chart saved to {chart_path}")
        return str(chart_path)

    def generate_html_report(self, protocol_data: Dict[str, Dict]) -> str:
        """Generate an HTML report with charts and analysis.

        Args:
            protocol_data: Dictionary of protocol analysis data

        Returns:
            Path to the saved HTML report
        """
        # Generate charts
        concentration_chart = self.generate_comparative_concentration_chart(
            protocol_data
        )
        distribution_chart = self.generate_distribution_comparison(protocol_data)
        top_holders_chart = self.generate_top_holders_bar_chart(protocol_data)

        # Prepare HTML content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Governance Token Distribution Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .chart-container {{
                    margin: 30px 0;
                    text-align: center;
                }}
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                .summary {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #4285f4;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                .footer {{
                    margin-top: 40px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <h1>Governance Token Distribution Analysis Report</h1>
            <p>Generated on: {timestamp}</p>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p>This report provides an analysis of token distribution patterns across {len(protocol_data)} governance tokens
                in the DeFi ecosystem. The analysis focuses on concentration metrics, distribution patterns, and comparative insights.</p>
            </div>
            
            <h2>Protocols Analyzed</h2>
            <table>
                <tr>
                    <th>Protocol</th>
                    <th>Token Symbol</th>
                    <th>Gini Coefficient</th>
                    <th>Top 10 Holders %</th>
                </tr>
        """

        # Add protocol data rows
        for protocol, data in protocol_data.items():
            symbol = data.get("symbol", "N/A")
            gini = data.get("concentration_metrics", {}).get("gini_coefficient", "N/A")

            # Get top 10 holders percentage
            top_10_pct = "N/A"
            top_holders_pct = data.get("concentration_metrics", {}).get(
                "top_holders_percentage", {}
            )
            if top_holders_pct and "10" in top_holders_pct:
                top_10_pct = f"{top_holders_pct['10']:.2f}%"

            html_content += f"""
                <tr>
                    <td>{data.get("name", protocol)}</td>
                    <td>{symbol}</td>
                    <td>{gini if isinstance(gini, str) else f"{gini:.4f}"}</td>
                    <td>{top_10_pct}</td>
                </tr>
            """

        html_content += """
            </table>
            
            <h2>Comparative Analysis</h2>
            
            <div class="chart-container">
                <h3>Token Concentration Comparison</h3>
                <img src="comparative_concentration.png" alt="Token Concentration Comparison">
                <p>Comparison of concentration metrics (Gini Coefficient and Herfindahl Index)
                across governance tokens. Higher values indicate more concentrated token distribution.</p>
            </div>
            
            <div class="chart-container">
                <h3>Token Distribution Comparison</h3>
                <img src="distribution_comparison.png" alt="Token Distribution Comparison">
                <p>Pie charts showing the percentage of tokens held by top holders for each protocol.</p>
            </div>
            
            <div class="chart-container">
                <h3>Top Holders Comparison</h3>
                <img src="top_holders_comparison.png" alt="Top Holders Comparison">
                <p>Comparison of token percentages held by top 5, 10, and 20 holders across protocols.</p>
            </div>
            
            <h2>Key Findings</h2>
            <ul>
        """

        # Generate key findings based on the data
        # Find most concentrated protocol
        most_concentrated = max(
            protocol_data.items(),
            key=lambda x: x[1]
            .get("concentration_metrics", {})
            .get("gini_coefficient", 0),
        )
        most_concentrated_name = most_concentrated[1].get("name", most_concentrated[0])
        most_concentrated_gini = (
            most_concentrated[1]
            .get("concentration_metrics", {})
            .get("gini_coefficient", 0)
        )

        # Find least concentrated protocol
        least_concentrated = min(
            protocol_data.items(),
            key=lambda x: x[1]
            .get("concentration_metrics", {})
            .get("gini_coefficient", 1),
        )
        least_concentrated_name = least_concentrated[1].get(
            "name", least_concentrated[0]
        )
        least_concentrated_gini = (
            least_concentrated[1]
            .get("concentration_metrics", {})
            .get("gini_coefficient", 0)
        )

        html_content += f"""
                <li>{most_concentrated_name} shows the highest token concentration with a Gini coefficient of {most_concentrated_gini:.4f}</li>
                <li>{least_concentrated_name} shows the lowest token concentration with a Gini coefficient of {least_concentrated_gini:.4f}</li>
        """

        # Add more findings based on available metrics
        for protocol, data in protocol_data.items():
            metrics = data.get("concentration_metrics", {})
            top_holders_pct = metrics.get("top_holders_percentage", {})

            if top_holders_pct and "5" in top_holders_pct and top_holders_pct["5"] > 50:
                html_content += f"""
                    <li>In {data.get("name", protocol)}, the top 5 holders control {top_holders_pct["5"]:.2f}% of tokens, 
                    which could lead to governance centralization risks</li>
                """

        html_content += """
            </ul>
            
            <h2>Recommendations</h2>
            <ol>
                <li>Protocols with high concentration should consider mechanisms to encourage wider token distribution</li>
                <li>Governance systems should implement safeguards against concentration of voting power</li>
                <li>Regular monitoring of token distribution trends is essential for maintaining decentralized governance</li>
                <li>Consider implementing token delegation mechanisms to increase governance participation</li>
            </ol>
            
            <div class="footer">
                <p>Generated by Governance Token Distribution Analyzer | © 2023</p>
            </div>
        </body>
        </html>
        """

        # Save the HTML report
        report_path = self.output_dir / "governance_token_analysis_report.html"
        with open(report_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to {report_path}")
        return str(report_path)

    def generate_full_report(self, protocols: List[str] = None) -> str:
        """Generate a full report including all protocols.

        Args:
            protocols: List of protocol names to include (default: all available)

        Returns:
            Path to the generated report
        """
        if protocols is None:
            protocols = ["compound", "uniswap", "aave"]

        # Load data for all protocols
        protocol_data = self.load_protocol_data(protocols)

        if not protocol_data:
            logger.error("No protocol data available for report generation")
            return None

        # Generate HTML report
        report_path = self.generate_html_report(protocol_data)

        return report_path


def main():
    """Execute the report generation process."""
    logger.info("Starting governance token distribution report generation")

    try:
        # Initialize report generator
        generator = ReportGenerator()

        # Generate report for all available protocols
        report_path = generator.generate_full_report()

        if report_path:
            print(f"\nReport successfully generated at: {report_path}")
            return 0
        else:
            print("\nFailed to generate report")
            return 1

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
