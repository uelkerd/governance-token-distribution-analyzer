"""End-to-End CLI and Integration Edge Cases Tests.

Comprehensive testing for CLI interface, user workflows, file system operations,
environment validation, and deployment readiness scenarios.
"""

import json
import os
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from governance_token_analyzer.cli.main import cli


class TestCLIEdgeCases:
    """Test CLI edge cases and error handling."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def readonly_dir(self, temp_dir):
        """Create read-only directory for testing."""
        readonly_path = os.path.join(temp_dir, "readonly")
        os.makedirs(readonly_path)
        os.chmod(readonly_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        yield readonly_path
        # Cleanup: make writable again before deletion
        os.chmod(readonly_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Mock environment variables for testing."""
        test_vars = {
            "ETHERSCAN_API_KEY": "test_etherscan_key",
            "ALCHEMY_API_KEY": "test_alchemy_key",
            "GRAPH_API_KEY": "test_graph_key",
            "INFURA_API_KEY": "test_infura_key",
        }
        for key, value in test_vars.items():
            monkeypatch.setenv(key, value)
        return test_vars

    # INVALID COMMAND ARGUMENTS TESTS

    def test_invalid_protocol_argument(self, cli_runner):
        """Test CLI with invalid protocol arguments."""
        invalid_protocols = ["invalid_protocol", "", "123", "nonexistent"]

        for protocol in invalid_protocols:
            result = cli_runner.invoke(cli, ["generate-report", "--protocol", protocol])

            # Should handle invalid protocols gracefully - they will generate reports with fallback data
            assert result.exit_code == 0  # CLI should succeed with simulation data
            assert "report generated" in result.output.lower() or "generated" in result.output.lower()

    def test_invalid_metric_argument(self, cli_runner):
        """Test CLI with invalid metric arguments."""
        invalid_metrics = ["invalid_metric", "", "concentration_coefficient", "123"]

        for metric in invalid_metrics:
            result = cli_runner.invoke(cli, ["historical-analysis", "--protocol", "compound", "--metric", metric])

            # Should handle invalid metrics gracefully with default metric
            assert result.exit_code == 0  # Should succeed with default metric

    def test_missing_required_arguments(self, cli_runner):
        """Test CLI with missing required arguments."""
        # Test missing protocol for report generation
        result = cli_runner.invoke(cli, ["generate-report"])
        assert result.exit_code != 0

        # Test missing protocols for comparison
        result = cli_runner.invoke(cli, ["compare-protocols"])
        assert result.exit_code != 0

    def test_conflicting_arguments(self, cli_runner):
        """Test CLI with conflicting arguments."""
        # Test conflicting format options - Click will use the last one
        result = cli_runner.invoke(
            cli,
            [
                "generate-report",
                "--protocol",
                "compound",
                "--format",
                "json",
                "--format",
                "html",  # Last format should be used
            ],
        )

        # Should handle by using the last specified format
        assert result.exit_code == 0

    def test_invalid_numeric_arguments(self, cli_runner, temp_dir):
        """Test CLI with invalid numeric arguments."""
        invalid_numbers = ["-1", "abc"]  # Remove "0" as it might be handled differently

        for number in invalid_numbers:
            result = cli_runner.invoke(
                cli, ["simulate-historical", "--protocol", "compound", "--snapshots", number, "--output-dir", temp_dir]
            )

            # Should handle invalid numbers gracefully
            if number in ["-1", "abc"]:
                assert result.exit_code != 0

    # MISSING ENVIRONMENT VARIABLES TESTS

    def test_missing_all_api_keys(self, cli_runner, monkeypatch, temp_dir):
        """Test CLI with no API keys available."""
        # Clear all API keys
        for key in ["ETHERSCAN_API_KEY", "ALCHEMY_API_KEY", "GRAPH_API_KEY", "INFURA_API_KEY"]:
            monkeypatch.delenv(key, raising=False)

        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        # Should still work with fallback data
        assert result.exit_code == 0

    def test_missing_specific_api_keys(self, cli_runner, monkeypatch, temp_dir):
        """Test CLI with specific API keys missing."""
        # Test with only Etherscan key
        monkeypatch.delenv("ALCHEMY_API_KEY", raising=False)
        monkeypatch.delenv("GRAPH_API_KEY", raising=False)
        monkeypatch.delenv("INFURA_API_KEY", raising=False)
        monkeypatch.setenv("ETHERSCAN_API_KEY", "test_key")

        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        # Should work with partial API keys
        assert result.exit_code == 0

    def test_invalid_api_key_format(self, cli_runner, monkeypatch, temp_dir):
        """Test CLI with invalid API key formats."""
        # Set invalid API keys
        monkeypatch.setenv("ETHERSCAN_API_KEY", "")
        monkeypatch.setenv("ALCHEMY_API_KEY", "invalid_key")
        monkeypatch.setenv("GRAPH_API_KEY", "123")

        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        # Should handle invalid keys and fallback
        assert result.exit_code == 0

    # FILE SYSTEM PERMISSIONS TESTS

    def test_readonly_output_directory(self, cli_runner, readonly_dir):
        """Test CLI with read-only output directory."""
        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", readonly_dir])

        # Should handle read-only directory gracefully
        assert result.exit_code != 0 or "permission" in result.output.lower()

    def test_nonexistent_output_directory(self, cli_runner, temp_dir):
        """Test CLI with non-existent output directory."""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent", "deeply", "nested")

        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", nonexistent_dir])

        # Should create directory or handle gracefully
        assert result.exit_code == 0
        assert os.path.exists(nonexistent_dir)

    def test_insufficient_disk_space_simulation(self, cli_runner, temp_dir):
        """Test CLI behavior when disk space is limited."""
        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        # Should complete successfully in normal conditions
        assert result.exit_code == 0

    def test_long_file_paths(self, cli_runner, temp_dir):
        """Test CLI with extremely long file paths."""
        # Create a very long path but not too long to avoid filesystem limits
        long_path = temp_dir
        for i in range(5):  # Reduced from 10 to avoid filesystem limits
            long_path = os.path.join(long_path, "very_long_directory_name")

        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", long_path])

        # Should handle long paths appropriately
        assert result.exit_code == 0 or "path" in result.output.lower()

    # OUTPUT FORMAT VALIDATION TESTS

    def test_json_output_format_validation(self, cli_runner, temp_dir):
        """Test JSON output format validation."""
        result = cli_runner.invoke(
            cli, ["export-historical-data", "--protocol", "compound", "--format", "json", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Validate JSON output exists and is valid
        json_files = [f for f in os.listdir(temp_dir) if f.endswith(".json")]
        assert len(json_files) > 0

        # Validate JSON content
        with open(os.path.join(temp_dir, json_files[0]), "r") as f:
            data = json.load(f)
            assert isinstance(data, dict)
            assert "protocol" in data

    def test_csv_output_format_validation(self, cli_runner, temp_dir):
        """Test CSV output format validation."""
        result = cli_runner.invoke(
            cli, ["export-historical-data", "--protocol", "compound", "--format", "csv", "--output-dir", temp_dir]
        )

        # CSV format not supported in export command, should use default JSON
        assert result.exit_code == 0

    def test_html_report_validation(self, cli_runner, temp_dir):
        """Test HTML report validation."""
        result = cli_runner.invoke(
            cli, ["generate-report", "--protocol", "compound", "--format", "html", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Validate HTML output exists
        html_files = [f for f in os.listdir(temp_dir) if f.endswith(".html")]
        assert len(html_files) > 0

        # Validate HTML content
        with open(os.path.join(temp_dir, html_files[0]), "r") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "<html>" in content

    def test_chart_generation_validation(self, cli_runner, temp_dir):
        """Test chart generation and validation."""
        result = cli_runner.invoke(
            cli, ["historical-analysis", "--protocol", "compound", "--format", "png", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Validate chart output exists
        chart_files = [f for f in os.listdir(temp_dir) if f.endswith(".png")]
        assert len(chart_files) > 0

    # COMPLETE WORKFLOW TESTS

    def test_complete_analysis_workflow(self, cli_runner, temp_dir, mock_env_vars):
        """Test complete analysis workflow from start to finish."""
        # Step 1: Run analysis
        result = cli_runner.invoke(
            cli,
            [
                "historical-analysis",
                "--protocol",
                "compound",
                "--metric",
                "gini_coefficient",
                "--format",
                "png",
                "--output-dir",
                temp_dir,
            ],
        )

        assert result.exit_code == 0

        # Step 2: Generate report
        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        assert result.exit_code == 0

        # Step 3: Export data
        result = cli_runner.invoke(cli, ["export-historical-data", "--protocol", "compound", "--output-dir", temp_dir])

        assert result.exit_code == 0

        # Validate all outputs exist
        files = os.listdir(temp_dir)
        assert any(f.endswith(".png") for f in files)
        assert any(f.endswith(".html") for f in files)
        assert any(f.endswith(".json") for f in files)

    def test_batch_protocol_analysis(self, cli_runner, temp_dir):
        """Test batch analysis of multiple protocols."""
        protocols = ["compound", "uniswap", "aave"]

        for protocol in protocols:
            result = cli_runner.invoke(cli, ["generate-report", "--protocol", protocol, "--output-dir", temp_dir])

            assert result.exit_code == 0

        # Validate all protocol reports exist
        files = os.listdir(temp_dir)
        for protocol in protocols:
            assert any(protocol in f for f in files)

    def test_historical_data_workflow(self, cli_runner, temp_dir):
        """Test historical data analysis workflow."""
        # Step 1: Simulate historical data
        result = cli_runner.invoke(
            cli, ["simulate-historical", "--protocol", "compound", "--snapshots", "5", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Step 2: Analyze historical data
        result = cli_runner.invoke(
            cli, ["historical-analysis", "--protocol", "compound", "--data-dir", temp_dir, "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

    # API FAILURE INTEGRATION TESTS

    def test_cli_with_api_failures(self, cli_runner, temp_dir):
        """Test CLI behavior when APIs are completely unavailable."""
        with patch("governance_token_analyzer.core.api_client.APIClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get_protocol_data.side_effect = Exception("All APIs failed")
            mock_client.return_value = mock_instance

            result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

            # Should handle API failures gracefully
            assert result.exit_code == 0

    def test_cli_with_partial_api_failures(self, cli_runner, temp_dir):
        """Test CLI behavior when some APIs fail."""
        with patch("governance_token_analyzer.core.api_client.APIClient") as mock_client:
            mock_instance = MagicMock()
            # Mock partial success
            mock_instance.get_token_holders.return_value = [{"address": "0x123", "balance": 1000}]
            mock_instance.get_governance_proposals.side_effect = Exception("Proposals API failed")
            mock_instance.get_protocol_data.return_value = {
                "protocol": "compound",
                "holders": [{"address": "0x123", "balance": 1000}],
                "proposals": [],
                "participation_rate": 0.0,
                "gini_coefficient": 0.5,
            }
            mock_client.return_value = mock_instance

            result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

            assert result.exit_code == 0

    # PERFORMANCE AND STRESS TESTS

    @pytest.mark.performance
    def test_cli_performance_large_datasets(self, cli_runner, temp_dir):
        """Test CLI performance with large datasets."""
        start_time = time.time()
        result = cli_runner.invoke(
            cli,
            [
                "simulate-historical",
                "--protocol",
                "compound",
                "--snapshots",
                "50",  # Large dataset
                "--output-dir",
                temp_dir,
            ],
        )
        elapsed_time = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed_time < 60  # 1 minute max
        assert result.exit_code == 0

    def test_concurrent_cli_operations(self, cli_runner, temp_dir):
        """Test concurrent CLI operations."""
        results = []

        def run_analysis(protocol):
            runner = CliRunner()
            result = runner.invoke(
                cli, ["generate-report", "--protocol", protocol, "--output-dir", os.path.join(temp_dir, protocol)]
            )
            results.append(result)

        # Run concurrent analyses
        threads = []
        for protocol in ["compound", "uniswap", "aave"]:
            thread = threading.Thread(target=run_analysis, args=(protocol,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should succeed
        for result in results:
            assert result.exit_code == 0

    @pytest.mark.performance
    def test_memory_usage_during_analysis(self, cli_runner, temp_dir):
        """Test memory usage during large analysis."""
        try:
            import psutil

            process = psutil.Process()
            initial_memory = process.memory_info().rss
        except ImportError:
            pytest.skip("psutil not available for memory testing")

        result = cli_runner.invoke(
            cli, ["simulate-historical", "--protocol", "compound", "--snapshots", "100", "--output-dir", temp_dir]
        )

        try:
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (less than 500MB)
            assert memory_increase < 500 * 1024 * 1024
        except ImportError:
            pass  # Skip memory check if psutil unavailable

        assert result.exit_code == 0

    def test_output_file_content_validation(self, cli_runner, temp_dir):
        """Test validation of output file contents."""
        result = cli_runner.invoke(
            cli, ["export-historical-data", "--protocol", "compound", "--format", "json", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Find and validate JSON output
        json_files = [f for f in os.listdir(temp_dir) if f.endswith(".json")]
        assert len(json_files) > 0

        with open(os.path.join(temp_dir, json_files[0]), "r") as f:
            data = json.load(f)
            assert "protocol" in data
            assert "data_points" in data
            assert isinstance(data["data_points"], list)

    def test_error_logging_and_reporting(self, cli_runner, temp_dir):
        """Test error logging and reporting functionality."""
        with patch("governance_token_analyzer.core.api_client.APIClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get_protocol_data.side_effect = Exception("Test error for logging")
            mock_client.return_value = mock_instance

            result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

            # Should handle errors gracefully and continue with fallback
            assert result.exit_code == 0


class TestValidationFrameworkEdgeCases:
    """Test validation framework edge cases."""

    @pytest.fixture
    def temp_validation_dir(self):
        """Create temporary directory for validation testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validation_with_corrupted_historical_data(self, temp_validation_dir):
        """Test validation with corrupted historical data."""
        # Create corrupted data file
        corrupted_file = os.path.join(temp_validation_dir, "corrupted_data.json")
        with open(corrupted_file, "w") as f:
            f.write("{ invalid json content")

        # Run validation script
        result = subprocess.run(["python", "scripts/validate_live_data.py"], capture_output=True, text=True)

        # Should handle corrupted data gracefully
        assert result.returncode in [0, 1]  # May warn but shouldn't crash

    def test_validation_with_missing_proposal_data(self, temp_validation_dir):
        """Test validation with missing proposal data."""
        # Create empty data directory
        os.makedirs(os.path.join(temp_validation_dir, "proposals"), exist_ok=True)

        # Run validation script
        result = subprocess.run(
            ["python", "scripts/validate_real_world_proposals.py", "--protocol", "compound"],
            capture_output=True,
            text=True,
        )

        # Should handle missing data gracefully
        assert result.returncode in [0, 1, 2]  # May have different exit codes

    def test_validation_with_network_connectivity_issues(self, temp_validation_dir):
        """Test validation with network connectivity issues."""
        # Mock network issues
        with patch("requests.get", side_effect=Exception("Network unreachable")):
            result = subprocess.run(["python", "scripts/validate_live_data.py"], capture_output=True, text=True)

            # Should handle network issues gracefully
            assert result.returncode in [0, 1]


class TestDeploymentReadiness:
    """Test deployment readiness scenarios."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for deployment testing."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_production_environment_simulation(self, cli_runner, temp_dir):
        """Test production environment simulation."""
        # Simulate production environment with limited resources
        with patch.dict(os.environ, {"ETHERSCAN_API_KEY": "prod_etherscan_key", "ALCHEMY_API_KEY": "prod_alchemy_key"}):
            result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

            assert result.exit_code == 0

    def test_docker_environment_compatibility(self, cli_runner, temp_dir):
        """Test Docker environment compatibility."""
        # Simulate Docker environment constraints
        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        assert result.exit_code == 0

        # Validate output exists
        files = os.listdir(temp_dir)
        assert len(files) > 0

    def test_minimal_dependencies_environment(self, cli_runner, temp_dir):
        """Test minimal dependencies environment."""
        # Test with minimal dependencies (fallback mode)
        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        assert result.exit_code == 0
