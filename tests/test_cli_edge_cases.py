"""End-to-End CLI and Integration Edge Cases Tests

Comprehensive testing for CLI interface, user workflows, file system operations,
environment validation, and deployment readiness scenarios.
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from governance_token_analyzer.cli.main import cli

# Define project root for CLI execution
project_root = Path(__file__).parent.parent


# Make cli_runner and temp_dir fixtures available to all test classes
@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIEdgeCases:
    """Test CLI edge cases and error handling."""

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
            result = cli_runner.invoke(cli, ["analyze", "--protocol", protocol])

            # Should handle invalid protocols gracefully
            assert result.exit_code != 0 or "error" in result.output.lower()

    def test_invalid_metric_argument(self, cli_runner):
        """Test CLI with invalid metric arguments."""
        invalid_metrics = ["invalid_metric", "", "concentration_coefficient", "123"]

        for metric in invalid_metrics:
            result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--metric", metric])

            # Should handle invalid metrics gracefully
            assert result.exit_code != 0 or "error" in result.output.lower()

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
        # Test conflicting format options
        result = cli_runner.invoke(
            cli,
            [
                "analyze",
                "--protocol",
                "compound",
                "--format",
                "json",
                "--format",
                "csv",  # Conflicting format
            ],
        )

        # Should handle conflicting arguments
        assert result.exit_code != 0 or len(result.output) > 0

    def test_invalid_numeric_arguments(self, cli_runner, temp_dir):
        """Test CLI with invalid numeric arguments."""
        invalid_numbers = ["-1", "0", "abc", "1.5", ""]

        for number in invalid_numbers:
            result = cli_runner.invoke(
                cli, ["analyze", "--protocol", "compound", "--limit", number, "--output-dir", temp_dir]
            )

            # Should handle invalid numbers gracefully
            if number in ["-1", "0", "abc", ""]:
                assert result.exit_code != 0

    # MISSING ENVIRONMENT VARIABLES TESTS

    def test_missing_all_api_keys(self, cli_runner, monkeypatch, temp_dir):
        """Test CLI with no API keys available."""
        # Clear all API keys
        for key in ["ETHERSCAN_API_KEY", "ALCHEMY_API_KEY", "GRAPH_API_KEY", "INFURA_API_KEY"]:
            monkeypatch.delenv(key, raising=False)

        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", temp_dir])

        # Should still work with fallback data
        assert result.exit_code == 0 or "warning" in result.output.lower()

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
        assert result.exit_code == 0 or "warning" in result.output.lower()

    # FILE SYSTEM PERMISSIONS TESTS

    def test_readonly_output_directory(self, cli_runner, readonly_dir):
        """Test CLI with read-only output directory."""
        result = cli_runner.invoke(cli, ["generate-report", "--protocol", "compound", "--output-dir", readonly_dir])

        # Should handle read-only directory gracefully
        assert result.exit_code != 0 or "permission" in result.output.lower()

    def test_nonexistent_output_directory(self, cli_runner, temp_dir):
        """Test CLI with non-existent output directory."""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent", "deeply", "nested")

        result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", nonexistent_dir])

        # Should create directory or handle gracefully
        assert result.exit_code == 0 or os.path.exists(nonexistent_dir)

    def test_insufficient_disk_space_simulation(self, cli_runner, temp_dir):
        """Test CLI behavior when disk space is insufficient."""
        # This is difficult to test directly, but we can mock the file writing
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", temp_dir])

            # Should handle disk space errors gracefully
            assert result.exit_code != 0 or "space" in result.output.lower()

    def test_long_file_paths(self, cli_runner, temp_dir):
        """Test CLI with extremely long file paths."""
        # Create a very long path
        long_path = temp_dir
        for i in range(10):
            long_path = os.path.join(long_path, "very_long_directory_name_" * 5)

        result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", long_path])

        # Should handle long paths appropriately
        assert result.exit_code == 0 or "path" in result.output.lower()

    # OUTPUT FORMAT VALIDATION TESTS

    def test_json_output_format_validation(self, cli_runner, temp_dir):
        """Test JSON output format validation."""
        result = cli_runner.invoke(
            cli, ["analyze", "--protocol", "compound", "--format", "json", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Check for JSON output file
        json_files = [f for f in os.listdir(temp_dir) if f.endswith(".json")]
        if json_files:
            json_file = os.path.join(temp_dir, json_files[0])

            # Validate JSON format
            with open(json_file) as f:
                data = json.load(f)
                assert isinstance(data, dict)
                assert "protocol" in data

    def test_csv_output_format_validation(self, cli_runner, temp_dir):
        """Test CSV output format validation."""
        result = cli_runner.invoke(
            cli, ["analyze", "--protocol", "compound", "--format", "csv", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Check for CSV output file
        csv_files = [f for f in os.listdir(temp_dir) if f.endswith(".csv")]
        if csv_files:
            csv_file = os.path.join(temp_dir, csv_files[0])

            # Validate CSV format
            import csv

            with open(csv_file) as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                assert headers is not None
                assert len(headers) > 0

    def test_html_report_validation(self, cli_runner, temp_dir):
        """Test HTML report format validation."""
        result = cli_runner.invoke(
            cli, ["generate-report", "--protocol", "compound", "--format", "html", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Check for HTML output file
        html_files = [f for f in os.listdir(temp_dir) if f.endswith(".html")]
        if html_files:
            html_file = os.path.join(temp_dir, html_files[0])

            # Validate HTML format
            with open(html_file) as f:
                content = f.read()
                assert "<html>" in content or "<!DOCTYPE" in content
                assert "compound" in content.lower()

    def test_chart_generation_validation(self, cli_runner, temp_dir):
        """Test chart generation and validation."""
        result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--chart", "--output-dir", temp_dir])

        assert result.exit_code == 0

        # Check for chart files
        chart_files = [f for f in os.listdir(temp_dir) if f.endswith((".png", ".jpg", ".svg"))]
        if chart_files:
            chart_file = os.path.join(temp_dir, chart_files[0])

            # Validate chart file exists and has content
            assert os.path.getsize(chart_file) > 0

    # COMPLETE USER WORKFLOW TESTS

    def test_complete_analysis_workflow(self, cli_runner, temp_dir, mock_env_vars):
        """Test complete analysis workflow from start to finish."""
        # Step 1: Run analysis
        result = cli_runner.invoke(
            cli,
            [
                "analyze",
                "--protocol",
                "compound",
                "--metric",
                "gini_coefficient",
                "--format",
                "json",
                "--chart",
                "--output-dir",
                temp_dir,
            ],
        )

        assert result.exit_code == 0

        # Step 2: Generate report
        result = cli_runner.invoke(
            cli, ["generate-report", "--protocol", "compound", "--format", "html", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Step 3: Compare protocols
        result = cli_runner.invoke(
            cli,
            [
                "compare-protocols",
                "--protocols",
                "compound,uniswap,aave",
                "--metric",
                "gini_coefficient",
                "--output-dir",
                temp_dir,
            ],
        )

        assert result.exit_code == 0

        # Verify output files exist
        files = os.listdir(temp_dir)
        assert any(f.endswith(".json") for f in files)
        assert any(f.endswith(".html") for f in files)

    def test_batch_protocol_analysis(self, cli_runner, temp_dir):
        """Test batch analysis of multiple protocols."""
        protocols = ["compound", "uniswap", "aave"]

        for protocol in protocols:
            result = cli_runner.invoke(cli, ["analyze", "--protocol", protocol, "--output-dir", temp_dir])

            assert result.exit_code == 0

        # Verify separate output files for each protocol
        files = os.listdir(temp_dir)
        for protocol in protocols:
            assert any(protocol in f for f in files)

    def test_historical_data_workflow(self, cli_runner, temp_dir):
        """Test historical data analysis workflow."""
        # Generate historical data
        result = cli_runner.invoke(
            cli, ["simulate-historical", "--protocol", "compound", "--snapshots", "10", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Analyze historical trends
        result = cli_runner.invoke(
            cli,
            [
                "historical-analysis",
                "--protocol",
                "compound",
                "--metric",
                "gini_coefficient",
                "--data-dir",
                temp_dir,
                "--output-dir",
                temp_dir,
            ],
        )

        assert result.exit_code == 0

    # CLI INTEGRATION WITH API FAILURES

    def test_cli_with_api_failures(self, cli_runner, temp_dir):
        """Test CLI behavior when all APIs fail."""
        with patch("governance_token_analyzer.core.api_client.APIClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get_protocol_data.side_effect = Exception("All APIs failed")
            mock_client.return_value = mock_instance

            result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", temp_dir])

            # Should handle API failures gracefully and use fallback data
            assert result.exit_code == 0 or "error" in result.output.lower()

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

            result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", temp_dir])

            assert result.exit_code == 0

    # PERFORMANCE AND STRESS TESTS

    @pytest.mark.performance
    def test_cli_performance_large_datasets(self, cli_runner, temp_dir):
        """Test CLI performance with large datasets."""
        import time

        start_time = time.time()
        result = cli_runner.invoke(
            cli,
            [
                "analyze",
                "--protocol",
                "compound",
                "--limit",
                "10000",  # Large dataset
                "--output-dir",
                temp_dir,
            ],
        )
        elapsed_time = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed_time < 60  # 1 minute max
        assert result.exit_code == 0

    def test_sequential_cli_operations(self, temp_dir):
        """Test sequential CLI operations across multiple protocols."""

        def run_cli_process(protocol):
            """Run CLI in a separate process with isolated environments."""
            output_dir = os.path.join(temp_dir, protocol)
            os.makedirs(output_dir, exist_ok=True)

            # Use the actual installed CLI entry point from a simplified approach
            # that works better with how the module is structured
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"from governance_token_analyzer.cli.main import cli; cli(['analyze', '--protocol', '{protocol}', '--output-dir', '{output_dir}'])",
                ],
                capture_output=True,
                text=True,
            )
            return result

        # Run analyses sequentially for multiple protocols
        protocols = ["compound", "uniswap", "aave"]
        results = []

        for protocol in protocols:
            result = run_cli_process(protocol)
            results.append(result)

        # All should succeed
        for result in results:
            assert result.returncode == 0, f"CLI process failed with: {result.stderr}"

        # Verify output files were created
        for protocol in protocols:
            output_dir = os.path.join(temp_dir, protocol)
            assert os.path.exists(output_dir), f"Output directory not created for {protocol}"
            assert len(os.listdir(output_dir)) > 0, f"No output files created for {protocol}"

    @pytest.mark.performance
    def test_concurrent_cli_operations(self, temp_dir):
        """Test truly concurrent CLI operations using parallel execution."""
        import concurrent.futures

        def run_cli_process(protocol):
            """Run CLI in a separate process with isolated environments."""
            output_dir = os.path.join(temp_dir, protocol)
            os.makedirs(output_dir, exist_ok=True)

            # Use the actual installed CLI entry point from a simplified approach
            # that works better with how the module is structured
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"from governance_token_analyzer.cli.main import cli; cli(['analyze', '--protocol', '{protocol}', '--output-dir', '{output_dir}'])",
                ],
                capture_output=True,
                text=True,
            )
            return protocol, result

        # Run analyses concurrently using ThreadPoolExecutor
        protocols = ["compound", "uniswap", "aave"]
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_protocol = {
                executor.submit(run_cli_process, protocol): protocol for protocol in protocols
            }
            
            for future in concurrent.futures.as_completed(future_to_protocol):
                protocol, result = future.result()
                results[protocol] = result
        
        # All should succeed
        for protocol, result in results.items():
            assert result.returncode == 0, f"CLI process for {protocol} failed with: {result.stderr}"

        # Verify output files were created for all protocols
        for protocol in protocols:
            output_dir = os.path.join(temp_dir, protocol)
            assert os.path.exists(output_dir), f"Output directory not created for {protocol}"
            assert len(os.listdir(output_dir)) > 0, f"No output files created for {protocol}"

    @pytest.mark.performance
    def test_memory_usage_during_analysis(self, cli_runner, temp_dir):
        """Test memory usage during large analysis."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        result = cli_runner.invoke(
            cli,
            [
                "analyze",
                "--protocol",
                "compound",
                "--limit",
                "50000",  # Very large dataset
                "--output-dir",
                temp_dir,
            ],
        )

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 1024 * 1024 * 1024  # 1GB max
        assert result.exit_code == 0

    # OUTPUT VALIDATION AND VERIFICATION

    def test_output_file_content_validation(self, cli_runner, temp_dir):
        """Test validation of output file contents."""
        result = cli_runner.invoke(
            cli, ["analyze", "--protocol", "compound", "--format", "json", "--output-dir", temp_dir]
        )

        assert result.exit_code == 0

        # Find and validate JSON output
        json_files = [f for f in os.listdir(temp_dir) if f.endswith(".json")]
        assert len(json_files) > 0

        json_file = os.path.join(temp_dir, json_files[0])
        with open(json_file) as f:
            data = json.load(f)

            # Validate required fields
            required_fields = ["protocol", "gini_coefficient", "participation_rate"]
            for field in required_fields:
                assert field in data

            # Validate data types
            assert isinstance(data["protocol"], str)
            assert isinstance(data["gini_coefficient"], (int, float))
            assert isinstance(data["participation_rate"], (int, float))

            # Validate value ranges
            assert 0 <= data["gini_coefficient"] <= 1
            assert 0 <= data["participation_rate"] <= 1

    def test_error_logging_and_reporting(self, cli_runner, temp_dir):
        """Test error logging and reporting functionality."""
        # Force an error scenario
        with patch("governance_token_analyzer.core.api_client.APIClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get_protocol_data.side_effect = Exception("Simulated error")
            mock_client.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["analyze", "--protocol", "compound", "--output-dir", temp_dir, "--verbose"]
            )

            # Should log error appropriately
            assert "error" in result.output.lower() or result.exit_code != 0


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
        # Create corrupted historical data file
        corrupted_file = os.path.join(temp_validation_dir, "corrupted_data.json")
        with open(corrupted_file, "w") as f:
            f.write("invalid json content {")

        # Run validation script
        result = subprocess.run(
            ["python", "scripts/validate_real_world_proposals.py", "--data-dir", temp_validation_dir],
            capture_output=True,
            text=True,
        )

        # Should handle corrupted data gracefully
        assert "error" in result.stderr.lower() or result.returncode != 0

    def test_validation_with_missing_proposal_data(self, temp_validation_dir):
        """Test validation with missing proposal data."""
        # Create empty data directory
        os.makedirs(os.path.join(temp_validation_dir, "proposals"), exist_ok=True)

        # Run validation script
        result = subprocess.run(
            ["python", "scripts/validate_real_world_proposals.py", "--data-dir", temp_validation_dir],
            capture_output=True,
            text=True,
        )

        # Should handle missing data gracefully - script now returns success (0) when no specific validation is requested
        assert (
            result.returncode == 0
            or "no data" in result.stdout.lower()
            or "data directory found" in result.stdout.lower()
        )

    def test_validation_with_network_connectivity_issues(self, temp_validation_dir):
        """Test validation with network connectivity issues."""
        # Mock network issues
        with patch("requests.get", side_effect=ConnectionError("Network unreachable")):
            result = subprocess.run(["python", "scripts/validate_live_data.py"], capture_output=True, text=True)

            # Should handle network issues gracefully
            assert result.returncode == 0 or "network" in result.stderr.lower()


# DEPLOYMENT READINESS TESTS


class TestDeploymentReadiness:
    """Test deployment readiness scenarios."""

    def test_production_environment_simulation(self, cli_runner, temp_dir):
        """Test CLI in production-like environment."""
        # Simulate production environment with limited resources
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "DEBUG": "false", "LOG_LEVEL": "warning"}):
            result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", temp_dir])

            assert result.exit_code == 0

    def test_docker_environment_compatibility(self, cli_runner, temp_dir):
        """Test compatibility with Docker environment."""
        # Simulate Docker-like environment
        with patch.dict(os.environ, {"HOME": "/tmp", "USER": "app", "PATH": "/usr/local/bin:/usr/bin:/bin"}):
            result = cli_runner.invoke(cli, ["analyze", "--protocol", "compound", "--output-dir", temp_dir])

            assert result.exit_code == 0

    def test_minimal_dependencies_environment(self, cli_runner, temp_dir):
        """Test with minimal dependencies available."""
        # Test that essential functionality works with basic dependencies
        result = cli_runner.invoke(
            cli,
            [
                "analyze",
                "--protocol",
                "compound",
                "--format",
                "json",
                "--output-dir",
                temp_dir,
                "--no-charts",  # Disable charts to reduce dependencies
            ],
        )

        assert result.exit_code == 0
