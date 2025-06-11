"""
Integration tests for the interaction between historical data, visualization, and report generation.
These tests verify that historical data can be properly visualized and included in reports.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

from governance_token_analyzer.core import historical_data
from governance_token_analyzer.visualization import historical_charts
from governance_token_analyzer.visualization import report_generator


@pytest.fixture
def temp_data_dir():
    """Fixture to create a temporary directory for historical data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_output_dir():
    """Fixture to create a temporary directory for reports and charts."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def data_manager(temp_data_dir):
    """Fixture to create a HistoricalDataManager with a temporary directory."""
    return historical_data.HistoricalDataManager(data_dir=temp_data_dir)


@pytest.fixture
def sample_snapshots(data_manager):
    """Generate sample historical snapshots for testing."""
    snapshots = historical_data.simulate_historical_data(
        'compound',
        num_snapshots=5,
        interval_days=7,
        data_manager=data_manager
    )
    return snapshots


class TestVisualizationAndReportingIntegration:
    """Integration tests for visualization and reporting components."""
    
    def test_time_series_visualization(self, data_manager, sample_snapshots, temp_output_dir):
        """Test that historical data can be visualized in time series charts."""
        # Get time series data from snapshots
        time_series = data_manager.get_time_series_data('compound', 'gini_coefficient')
        
        # Create a visualization
        fig = historical_charts.plot_metric_over_time(
            time_series_data=time_series,
            metric_name='gini_coefficient',
            title='Gini Coefficient Over Time'
        )
        
        # Verify that a figure was created
        assert isinstance(fig, plt.Figure)
        
        # Save the figure
        output_path = os.path.join(temp_output_dir, 'gini_over_time.png')
        fig.savefig(output_path)
        
        # Verify that the file was created
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_multi_protocol_comparison(self, data_manager, temp_output_dir):
        """Test that historical data from multiple protocols can be compared visually."""
        # Simulate data for multiple protocols
        for protocol in ['compound', 'uniswap', 'aave']:
            historical_data.simulate_historical_data(
                protocol,
                num_snapshots=5,
                interval_days=7,
                data_manager=data_manager
            )
        
        # Get time series data for each protocol
        protocol_data = {}
        for protocol in ['compound', 'uniswap', 'aave']:
            protocol_data[protocol] = data_manager.get_time_series_data(protocol, 'gini_coefficient')
        
        # Create a comparison visualization
        fig = historical_charts.plot_protocol_comparison_over_time(
            protocol_data=protocol_data,
            metric_name='gini_coefficient',
            title='Gini Coefficient Comparison Across Protocols'
        )
        
        # Verify that a figure was created
        assert isinstance(fig, plt.Figure)
        
        # Save the figure
        output_path = os.path.join(temp_output_dir, 'protocol_comparison.png')
        fig.savefig(output_path)
        
        # Verify that the file was created
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_report_generation_with_historical_data(self, data_manager, sample_snapshots, temp_output_dir):
        """Test that historical data can be included in generated reports."""
        # Get time series data
        time_series = data_manager.get_time_series_data('compound', 'gini_coefficient')
        
        # Create a report
        report_path = os.path.join(temp_output_dir, 'historical_report.html')
        report_generator.generate_historical_analysis_report(
            protocol='compound',
            time_series_data=time_series,
            snapshots=sample_snapshots,
            output_path=report_path
        )
        
        # Verify that the report was created
        assert os.path.exists(report_path)
        assert os.path.getsize(report_path) > 0
        
        # Verify report contains expected content
        with open(report_path, 'r') as f:
            content = f.read()
            assert 'Gini Coefficient' in content
            assert 'Historical Analysis' in content
    
    def test_full_workflow_integration(self, data_manager, temp_output_dir):
        """Test the full workflow from data collection to report generation."""
        # 1. Simulate data collection for a protocol
        snapshots = historical_data.simulate_historical_data(
            'compound',
            num_snapshots=12,
            interval_days=30,
            data_manager=data_manager
        )
        
        # 2. Extract time series data
        time_series = data_manager.get_time_series_data('compound', 'gini_coefficient')
        concentration_series = data_manager.get_time_series_data('compound', 'top_10_concentration')
        
        # 3. Create visualizations
        gini_fig = historical_charts.plot_metric_over_time(
            time_series_data=time_series,
            metric_name='gini_coefficient'
        )
        
        concentration_fig = historical_charts.plot_metric_over_time(
            time_series_data=concentration_series,
            metric_name='top_10_concentration'
        )
        
        # 4. Save visualizations
        gini_path = os.path.join(temp_output_dir, 'gini_trend.png')
        concentration_path = os.path.join(temp_output_dir, 'concentration_trend.png')
        
        gini_fig.savefig(gini_path)
        concentration_fig.savefig(concentration_path)
        
        # 5. Generate a comprehensive report
        report_path = os.path.join(temp_output_dir, 'comprehensive_report.html')
        report_generator.generate_comprehensive_report(
            protocol='compound',
            snapshots=snapshots,
            time_series_data={
                'gini_coefficient': time_series,
                'top_10_concentration': concentration_series
            },
            visualization_paths={
                'gini_coefficient': gini_path,
                'top_10_concentration': concentration_path
            },
            output_path=report_path
        )
        
        # 6. Verify the entire workflow produced the expected output
        assert os.path.exists(gini_path)
        assert os.path.exists(concentration_path)
        assert os.path.exists(report_path)
        
        # 7. Verify report content
        with open(report_path, 'r') as f:
            content = f.read()
            assert 'Gini Coefficient' in content
            assert 'Concentration' in content
            assert 'Historical Analysis' in content
            assert 'Compound' in content 