"""
Report Generator Module for creating comprehensive governance token analysis reports.
This module provides functionality to generate HTML, PDF, and JSON reports
with visualizations and insights about token distribution and governance.
"""

import os
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import visualization modules
from . import charts
from . import historical_charts


class ReportGenerator:
    """
    Generates comprehensive reports with visualizations and analysis.
    """
    
    def __init__(self, output_dir: str = "reports", template_dir: str = None):
        """
        Initialize the report generator.
        
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
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate_snapshot_report(
        self,
        protocol_data: Dict[str, Any],
        protocol_name: str,
        output_format: str = "html",
        include_visualizations: bool = True
    ) -> str:
        """
        Generate a report for a single protocol snapshot.
        
        Args:
            protocol_data: Protocol data snapshot
            protocol_name: Name of the protocol
            output_format: Output format (html, pdf, json)
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
        if output_format == "html":
            report_path = self._generate_html_report(
                protocol_name=protocol_name,
                metrics=metrics,
                visualizations=visualizations,
                report_dir=report_dir,
                timestamp=timestamp
            )
        elif output_format == "json":
            report_path = self._generate_json_report(
                protocol_name=protocol_name,
                metrics=metrics,
                visualizations=visualizations,
                report_dir=report_dir,
                timestamp=timestamp
            )
        elif output_format == "pdf":
            # PDF generation would require additional dependencies
            # like weasyprint or a similar library
            raise NotImplementedError("PDF report generation not implemented yet")
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        return report_path
    
    def generate_historical_report(
        self,
        snapshots: List[Dict[str, Any]],
        protocol_name: str,
        output_format: str = "html"
    ) -> str:
        """
        Generate a historical analysis report.
        
        Args:
            snapshots: List of historical snapshots
            protocol_name: Name of the protocol
            output_format: Output format (html, pdf, json)
            
        Returns:
            Path to the generated report
        """
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
        latest_metrics = self._extract_metrics(snapshots[-1]['data'])
        
        # Generate historical visualizations
        historical_visualizations = self._generate_historical_visualizations(snapshots, viz_dir)
        
        # Generate report based on format
        if output_format == "html":
            report_path = self._generate_html_report(
                protocol_name=protocol_name,
                metrics=latest_metrics,
                visualizations=[],  # No snapshot visualizations, only historical
                historical_analysis={
                    'overview': f"Historical analysis of {protocol_name} token distribution over time",
                    'visualizations': historical_visualizations
                },
                report_dir=report_dir,
                timestamp=timestamp
            )
        elif output_format == "json":
            report_path = self._generate_json_report(
                protocol_name=protocol_name,
                metrics=latest_metrics,
                visualizations=[],
                historical_analysis={
                    'overview': f"Historical analysis of {protocol_name} token distribution over time",
                    'visualizations': historical_visualizations
                },
                report_dir=report_dir,
                timestamp=timestamp
            )
        elif output_format == "pdf":
            raise NotImplementedError("PDF report generation not implemented yet")
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        return report_path
    
    def generate_comparison_report(
        self,
        protocol_data: Dict[str, Dict[str, Any]],
        output_format: str = "html"
    ) -> str:
        """
        Generate a comparison report for multiple protocols.
        
        Args:
            protocol_data: Dictionary mapping protocol names to their data
            output_format: Output format (html, pdf, json)
            
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
        if output_format == "html":
            report_path = self._generate_html_report(
                protocol_name="Multiple Protocols",
                metrics=[],  # No single protocol metrics
                visualizations=[],  # No single protocol visualizations
                comparison={
                    'overview': f"Comparison of token distribution across {', '.join(protocol_data.keys())}",
                    'visualizations': comparison_visualizations,
                    'protocol_metrics': protocol_metrics
                },
                report_dir=report_dir,
                timestamp=timestamp
            )
        elif output_format == "json":
            report_path = self._generate_json_report(
                protocol_name="Multiple Protocols",
                metrics=[],
                visualizations=[],
                comparison={
                    'overview': f"Comparison of token distribution across {', '.join(protocol_data.keys())}",
                    'visualizations': comparison_visualizations,
                    'protocol_metrics': protocol_metrics
                },
                report_dir=report_dir,
                timestamp=timestamp
            )
        elif output_format == "pdf":
            raise NotImplementedError("PDF report generation not implemented yet")
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        return report_path
    
    def _extract_metrics(self, protocol_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key metrics from protocol data."""
        metrics = []
        
        # Extract metrics if available
        if 'metrics' in protocol_data:
            for key, value in protocol_data['metrics'].items():
                metric = {
                    'name': key.replace('_', ' ').title(),
                    'value': value,
                    'description': self._get_metric_description(key)
                }
                metrics.append(metric)
        
        # Add token holder count
        if 'token_holders' in protocol_data:
            metrics.append({
                'name': 'Token Holder Count',
                'value': len(protocol_data['token_holders']),
                'description': 'Total number of token holders'
            })
        
        # Add governance participation if available
        if 'governance_data' in protocol_data and 'participation_rate' in protocol_data['governance_data']:
            metrics.append({
                'name': 'Governance Participation Rate',
                'value': f"{protocol_data['governance_data']['participation_rate']:.2f}%",
                'description': 'Percentage of token supply that participates in governance'
            })
        
        return metrics
    
    def _get_metric_description(self, metric_name: str) -> str:
        """Get description for a specific metric."""
        descriptions = {
            'gini_coefficient': 'Measure of inequality in token distribution (0=equal, 1=unequal)',
            'top_10_concentration': 'Percentage of tokens held by top 10 holders',
            'participation_rate': 'Percentage of token supply that participates in governance',
            'proposal_count': 'Number of governance proposals',
        }
        
        return descriptions.get(metric_name, 'No description available')
    
    def _generate_snapshot_visualizations(
        self, 
        protocol_data: Dict[str, Any],
        viz_dir: str
    ) -> List[Dict[str, str]]:
        """Generate visualizations for a protocol snapshot."""
        visualizations = []
        
        # Create distribution chart
        if 'token_holders' in protocol_data:
            holder_df = pd.DataFrame(protocol_data['token_holders'])
            
            # Distribution chart
            fig = charts.create_distribution_chart(holder_df, title="Token Holder Distribution")
            dist_chart_path = os.path.join(viz_dir, "distribution_chart.png")
            fig.savefig(dist_chart_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Token Holder Distribution',
                'path': os.path.relpath(dist_chart_path, start=os.path.dirname(viz_dir)),
                'description': 'Distribution of tokens among holders'
            })
            
            # Lorenz curve
            fig = charts.create_lorenz_curve(holder_df['balance'], title="Token Distribution Lorenz Curve")
            lorenz_path = os.path.join(viz_dir, "lorenz_curve.png")
            fig.savefig(lorenz_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Lorenz Curve',
                'path': os.path.relpath(lorenz_path, start=os.path.dirname(viz_dir)),
                'description': 'Lorenz curve showing inequality in token distribution'
            })
        
        return visualizations
    
    def _generate_historical_visualizations(
        self, 
        snapshots: List[Dict[str, Any]],
        viz_dir: str
    ) -> List[Dict[str, str]]:
        """Generate visualizations for historical data."""
        visualizations = []
        
        # Create a time series from snapshots
        time_series_data = []
        for snapshot in snapshots:
            timestamp = datetime.fromisoformat(snapshot['timestamp'])
            
            # Extract metrics
            metrics = snapshot['data'].get('metrics', {})
            
            # Add governance data if available
            governance_data = snapshot['data'].get('governance_data', {})
            participation_rate = governance_data.get('participation_rate')
            
            time_series_data.append({
                'timestamp': timestamp,
                'gini_coefficient': metrics.get('gini_coefficient'),
                'top_10_concentration': metrics.get('top_10_concentration'),
                'participation_rate': participation_rate
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(time_series_data)
        df.set_index('timestamp', inplace=True)
        
        # Generate gini coefficient over time chart
        if 'gini_coefficient' in df.columns:
            fig = historical_charts.plot_metric_over_time(
                df, 
                'gini_coefficient',
                title="Gini Coefficient Over Time"
            )
            gini_path = os.path.join(viz_dir, "gini_over_time.png")
            fig.savefig(gini_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Gini Coefficient Over Time',
                'path': os.path.relpath(gini_path, start=os.path.dirname(viz_dir)),
                'description': 'Changes in token distribution inequality over time'
            })
        
        # Generate top 10 concentration over time chart
        if 'top_10_concentration' in df.columns:
            fig = historical_charts.plot_metric_over_time(
                df, 
                'top_10_concentration',
                title="Top 10 Holder Concentration Over Time"
            )
            top10_path = os.path.join(viz_dir, "top10_over_time.png")
            fig.savefig(top10_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Top 10 Holder Concentration Over Time',
                'path': os.path.relpath(top10_path, start=os.path.dirname(viz_dir)),
                'description': 'Changes in token concentration among top 10 holders over time'
            })
        
        # Generate participation rate over time chart
        if 'participation_rate' in df.columns:
            fig = historical_charts.plot_metric_over_time(
                df, 
                'participation_rate',
                title="Governance Participation Rate Over Time"
            )
            participation_path = os.path.join(viz_dir, "participation_over_time.png")
            fig.savefig(participation_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Governance Participation Rate Over Time',
                'path': os.path.relpath(participation_path, start=os.path.dirname(viz_dir)),
                'description': 'Changes in governance participation over time'
            })
        
        # Generate concentration heatmap
        fig = historical_charts.create_concentration_heatmap(snapshots)
        heatmap_path = os.path.join(viz_dir, "concentration_heatmap.png")
        fig.savefig(heatmap_path)
        plt.close(fig)
        
        visualizations.append({
            'title': 'Token Concentration Heatmap',
            'path': os.path.relpath(heatmap_path, start=os.path.dirname(viz_dir)),
            'description': 'Heatmap showing changes in token concentration over time'
        })
        
        # Create multi-metric dashboard
        metrics_to_include = [col for col in df.columns if not df[col].isnull().all()]
        if len(metrics_to_include) >= 2:
            fig = historical_charts.create_multi_metric_dashboard(
                {metric: df[[metric]] for metric in metrics_to_include},
                metrics=metrics_to_include,
                title="Governance Metrics Dashboard"
            )
            dashboard_path = os.path.join(viz_dir, "metrics_dashboard.png")
            fig.savefig(dashboard_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Governance Metrics Dashboard',
                'path': os.path.relpath(dashboard_path, start=os.path.dirname(viz_dir)),
                'description': 'Dashboard showing multiple governance metrics over time'
            })
        
        return visualizations
    
    def _generate_comparison_visualizations(
        self, 
        protocol_data: Dict[str, Dict[str, Any]],
        viz_dir: str
    ) -> List[Dict[str, str]]:
        """Generate visualizations comparing multiple protocols."""
        visualizations = []
        
        # Extract metrics for each protocol
        metrics_data = {}
        for protocol, data in protocol_data.items():
            metrics = data.get('metrics', {})
            metrics_data[protocol] = metrics
        
        # Create bar chart comparing gini coefficients
        if all('gini_coefficient' in metrics for metrics in metrics_data.values()):
            protocols = list(protocol_data.keys())
            gini_values = [metrics_data[p]['gini_coefficient'] for p in protocols]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(protocols, gini_values)
            ax.set_xlabel('Protocol')
            ax.set_ylabel('Gini Coefficient')
            ax.set_title('Gini Coefficient Comparison')
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for i, v in enumerate(gini_values):
                ax.text(i, v + 0.01, f"{v:.3f}", ha='center')
            
            gini_path = os.path.join(viz_dir, "gini_comparison.png")
            fig.savefig(gini_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Gini Coefficient Comparison',
                'path': os.path.relpath(gini_path, start=os.path.dirname(viz_dir)),
                'description': 'Comparison of token distribution inequality across protocols'
            })
        
        # Create bar chart comparing top 10 holder concentration
        if all('top_10_concentration' in metrics for metrics in metrics_data.values()):
            protocols = list(protocol_data.keys())
            top10_values = [metrics_data[p]['top_10_concentration'] for p in protocols]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(protocols, top10_values)
            ax.set_xlabel('Protocol')
            ax.set_ylabel('Top 10 Concentration (%)')
            ax.set_title('Top 10 Holder Concentration Comparison')
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for i, v in enumerate(top10_values):
                ax.text(i, v + 1, f"{v:.1f}%", ha='center')
            
            top10_path = os.path.join(viz_dir, "top10_comparison.png")
            fig.savefig(top10_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Top 10 Holder Concentration Comparison',
                'path': os.path.relpath(top10_path, start=os.path.dirname(viz_dir)),
                'description': 'Comparison of token concentration among top 10 holders across protocols'
            })
        
        # Create radar chart for multiple metrics
        # First, check which metrics are available for all protocols
        common_metrics = ['gini_coefficient', 'top_10_concentration']
        
        if all(any(m in metrics_data[p] for m in common_metrics) for p in protocol_data.keys()):
            # Create radar chart data
            metric_labels = [m.replace('_', ' ').title() for m in common_metrics]
            
            # Normalize values for radar chart
            normalized_values = {}
            for protocol in protocol_data.keys():
                values = []
                for metric in common_metrics:
                    if metric in metrics_data[protocol]:
                        # Normalize based on metric type
                        if metric == 'gini_coefficient':
                            # Gini is already 0-1
                            values.append(metrics_data[protocol][metric])
                        elif metric == 'top_10_concentration':
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
            angles = np.linspace(0, 2*np.pi, len(common_metrics), endpoint=False).tolist()
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
            ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            
            radar_path = os.path.join(viz_dir, "protocol_comparison_radar.png")
            fig.savefig(radar_path)
            plt.close(fig)
            
            visualizations.append({
                'title': 'Protocol Comparison Radar Chart',
                'path': os.path.relpath(radar_path, start=os.path.dirname(viz_dir)),
                'description': 'Radar chart comparing key metrics across protocols'
            })
        
        return visualizations
    
    def _generate_html_report(
        self,
        protocol_name: str,
        metrics: List[Dict[str, Any]],
        visualizations: List[Dict[str, str]],
        report_dir: str,
        timestamp: str,
        historical_analysis: Optional[Dict[str, Any]] = None,
        comparison: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate an HTML report."""
        # Get the template
        template = self.jinja_env.get_template("report_template.html")
        
        # Prepare template context
        context = {
            'title': f"{protocol_name} Governance Token Analysis Report",
            'generation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'overview': f"Analysis of governance token distribution for {protocol_name}",
            'metrics': metrics,
            'visualizations': visualizations,
            'historical_analysis': historical_analysis,
            'comparison': comparison,
            'conclusion': "This report provides insights into the token distribution and governance of the protocol."
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Save to file
        output_path = os.path.join(report_dir, "report.html")
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_json_report(
        self,
        protocol_name: str,
        metrics: List[Dict[str, Any]],
        visualizations: List[Dict[str, str]],
        report_dir: str,
        timestamp: str,
        historical_analysis: Optional[Dict[str, Any]] = None,
        comparison: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a JSON report."""
        report_data = {
            'title': f"{protocol_name} Governance Token Analysis Report",
            'generation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'overview': f"Analysis of governance token distribution for {protocol_name}",
            'metrics': metrics,
            'visualizations': visualizations,
            'historical_analysis': historical_analysis,
            'comparison': comparison,
            'conclusion': "This report provides insights into the token distribution and governance of the protocol."
        }
        
        # Save to file
        output_path = os.path.join(report_dir, "report.json")
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return output_path 