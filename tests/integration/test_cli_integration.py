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
    for protocol in ["compound", "uniswap", "aave"]:
        historical_data.simulate_historical_data(protocol, num_snapshots=5, interval_days=7, data_manager=data_manager)
    return data_manager.data_dir


class TestCliIntegration:
    """Integration tests for CLI components."""

    def test_historical_analysis_command(self, sample_data, temp_output_dir):
        """Test that the historical-analysis command works correctly."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            "historical-analysis",
            "--protocol",
            "compound",
            "--metric",
            "gini_coefficient",
            "--data-dir",
            sample_data,
            "--output-dir",
            temp_output_dir,
            "--output-format",
            "png",
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        # The file name includes a timestamp, so we need to check for any file matching the pattern
        import glob

        output_files = glob.glob(os.path.join(temp_output_dir, "compound_gini_coefficient_*.png"))
        assert len(output_files) > 0, f"No output files found in {temp_output_dir}"
        assert os.path.getsize(output_files[0]) > 0

    def test_compare_protocols_command(self, sample_data, temp_output_dir):
        """Test that the compare-protocols command works correctly with historical data."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            "compare-protocols",
            "--protocols",
            "compound,uniswap,aave",
            "--metric",
            "gini_coefficient",
            "--historical",
            "--data-dir",
            sample_data,
            "--output-dir",
            temp_output_dir,
            "--output-format",
            "png",
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that the output file was created
        output_files = os.listdir(temp_output_dir)
        assert any(f.startswith("protocol_comparison_") and f.endswith(".png") for f in output_files)

    def test_generate_report_command(self, sample_data, temp_output_dir):
        """Test that the generate-report command works correctly with historical data."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            "generate-report",
            "--protocol",
            "compound",
            "--include-historical",
            "--data-dir",
            sample_data,
            "--output-dir",
            temp_output_dir,
            "--output-format",
            "html",
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        # The file name includes a timestamp, so we need to check for any file matching the pattern
        import glob

        output_files = glob.glob(os.path.join(temp_output_dir, "compound_report_*.html"))
        assert len(output_files) > 0, f"No output files found in {temp_output_dir}"
        assert os.path.getsize(output_files[0]) > 0

        # Verify report contains historical analysis section
        with open(output_files[0]) as f:
            content = f.read()
            assert "Historical Analysis" in content

    def test_export_historical_data_command(self, sample_data, temp_output_dir):
        """Test that the export-historical-data command works correctly."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            "export-historical-data",
            "--protocol",
            "compound",
            "--metric",
            "gini_coefficient",
            "--data-dir",
            sample_data,
            "--output-dir",
            temp_output_dir,
            "--output-format",
            "json",
            "--include-historical",
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check that output files were created
        # The file name includes a timestamp, so we need to check for any file matching the pattern
        import glob

        output_files = glob.glob(os.path.join(temp_output_dir, "compound_gini_coefficient_historical*.json"))
        assert len(output_files) > 0, f"No output files found in {temp_output_dir}"
        assert os.path.getsize(output_files[0]) > 0

        # Verify the JSON content
        with open(output_files[0]) as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) > 0
            # JSON should be a list of records with gini_coefficient and timestamp
            first_record = data[0]
            assert "gini_coefficient" in first_record
            assert "timestamp" in first_record or "date" in first_record or "index" in first_record

    def test_simulate_historical_command(self, temp_data_dir, temp_output_dir):
        """Test that the simulate-historical command works correctly."""
        runner = CliRunner()

        # Create a test command
        cmd = [
            "simulate-historical",
            "--protocol",
            "compound",
            "--snapshots",
            "3",
            "--interval",
            "30",
            "--data-dir",
            temp_data_dir,
            "--output-dir",
            temp_output_dir,
        ]

        # Run the command
        result = runner.invoke(main.cli, cmd)

        # Check that the command executed successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Verify that snapshots were created
        data_manager = historical_data.HistoricalDataManager(data_dir=temp_data_dir)
        snapshots = data_manager.get_snapshots("compound")
        assert len(snapshots) == 3
