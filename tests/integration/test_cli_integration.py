"""Integration tests for the CLI components that interact with historical data analysis and reporting.
These tests verify that CLI commands correctly utilize the historical data and report generation functionality.
"""

import json
import os
import shutil
import tempfile

import pytest
from click.testing import CliRunner

from governance_token_analyzer.cli import main
from governance_token_analyzer.core import historical_data


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
def sample_data(data_manager):
    """Generate sample historical data for testing."""
    for protocol in ['compound', 'uniswap', 'aave']:
        historical_data.simulate_historical_data(
            protocol,
            num_snapshots=5,
            interval_days=7,
            data_manager=data_manager
        )
    return data_manager.data_dir


class TestCliIntegration:
    """Integration tests for CLI components."""

    def test_historical_analysis_command(self, sample_data, temp_output_dir):
        """Test that the historical-analysis command works correctly."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            'historical-analysis',
            '--protocol', 'compound',
            '--metric', 'gini_coefficient',
            '--data-dir', sample_data,
            '--output-dir', temp_output_dir,
            '--format', 'png'
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        expected_output = os.path.join(
            temp_output_dir,
            'compound_gini_coefficient.png'
        )
        assert os.path.exists(expected_output)
        assert os.path.getsize(expected_output) > 0

    def test_compare_protocols_command(self, sample_data, temp_output_dir):
        """Test that the compare-protocols command works correctly with historical data."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            'compare-protocols',
            '--protocols', 'compound,uniswap,aave',
            '--metric', 'gini_coefficient',
            '--historical',
            '--data-dir', sample_data,
            '--output-dir', temp_output_dir,
            '--format', 'png'
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        expected_output = os.path.join(
            temp_output_dir,
            'protocol_comparison_gini_coefficient.png'
        )
        assert os.path.exists(expected_output)
        assert os.path.getsize(expected_output) > 0

    def test_generate_report_command(self, sample_data, temp_output_dir):
        """Test that the generate-report command works correctly with historical data."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            'generate-report',
            '--protocol', 'compound',
            '--include-historical',
            '--data-dir', sample_data,
            '--output-dir', temp_output_dir,
            '--format', 'html'
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        expected_output = os.path.join(
            temp_output_dir,
            'compound_report.html'
        )
        assert os.path.exists(expected_output)
        assert os.path.getsize(expected_output) > 0

        # Verify report contains historical analysis section
        with open(expected_output) as f:
            content = f.read()
            assert 'Historical Analysis' in content

    def test_export_historical_data_command(self, sample_data, temp_output_dir):
        """Test that the export-historical-data command works correctly."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            'export-historical-data',
            '--protocol', 'compound',
            '--metric', 'gini_coefficient',
            '--data-dir', sample_data,
            '--output-dir', temp_output_dir,
            '--format', 'json'
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        expected_output = os.path.join(
            temp_output_dir,
            'compound_gini_coefficient_historical.json'
        )
        assert os.path.exists(expected_output)
        assert os.path.getsize(expected_output) > 0

        # Verify the JSON content
        with open(expected_output) as f:
            data = json.load(f)
            assert 'protocol' in data
            assert data['protocol'] == 'compound'
            assert 'metric' in data
            assert data['metric'] == 'gini_coefficient'
            assert 'data_points' in data
            assert len(data['data_points']) > 0

    def test_simulate_historical_command(self, temp_data_dir, temp_output_dir):
        """Test that the simulate-historical command works correctly."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            'simulate-historical',
            '--protocol', 'compound',
            '--snapshots', '3',
            '--interval', '30',
            '--data-dir', temp_data_dir,
            '--output-dir', temp_output_dir
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Verify that snapshots were created
        data_manager = historical_data.HistoricalDataManager(data_dir=temp_data_dir)
        snapshots = data_manager.get_snapshots('compound')
        assert len(snapshots) == 3
