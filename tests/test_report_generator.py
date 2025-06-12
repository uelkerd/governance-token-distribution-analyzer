import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.generate_report import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """Test the report generator functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test outputs
        self.test_output_dir = os.path.join(tempfile.gettempdir(), "test_reports")
        os.makedirs(self.test_output_dir, exist_ok=True)

        # Initialize the report generator
        self.generator = ReportGenerator(output_dir=self.test_output_dir)

        # Sample protocol data for testing
        self.sample_data = {
            "compound": {
                "name": "Compound",
                "symbol": "COMP",
                "concentration_metrics": {
                    "gini_coefficient": 0.82,
                    "herfindahl_index": 1500,
                    "top_holders_percentage": {
                        "5": 65.2,
                        "10": 78.9,
                        "20": 88.5,
                        "50": 95.1,
                    },
                },
                "top_holders": [
                    {"rank": 1, "address": "0x123abc", "percentage": 25.3},
                    {"rank": 2, "address": "0x456def", "percentage": 15.8},
                    {"rank": 3, "address": "0x789ghi", "percentage": 10.5},
                    {"rank": 4, "address": "0xabcdef", "percentage": 8.7},
                    {"rank": 5, "address": "0xghijkl", "percentage": 4.9},
                ],
            },
            "uniswap": {
                "name": "Uniswap",
                "symbol": "UNI",
                "concentration_metrics": {
                    "gini_coefficient": 0.74,
                    "herfindahl_index": 1200,
                    "top_holders_percentage": {
                        "5": 52.4,
                        "10": 67.2,
                        "20": 79.8,
                        "50": 92.3,
                    },
                },
                "top_holders": [
                    {"rank": 1, "address": "0xuni1", "percentage": 18.7},
                    {"rank": 2, "address": "0xuni2", "percentage": 12.3},
                    {"rank": 3, "address": "0xuni3", "percentage": 9.8},
                    {"rank": 4, "address": "0xuni4", "percentage": 7.2},
                    {"rank": 5, "address": "0xuni5", "percentage": 4.4},
                ],
            },
        }

    def tearDown(self):
        """Clean up after each test method."""
        # Remove test files if they exist
        for filename in [
            "comparative_concentration.png",
            "distribution_comparison.png",
            "top_holders_comparison.png",
            "governance_token_analysis_report.html",
        ]:
            filepath = os.path.join(self.test_output_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        # Try to remove the test directory
        try:
            os.rmdir(self.test_output_dir)
        except OSError:
            pass  # Directory not empty or doesn't exist

    @patch("matplotlib.pyplot.savefig")
    def test_generate_comparative_concentration_chart(self, mock_savefig):
        """Test that the comparative concentration chart can be generated."""
        # Call the method we're testing
        chart_path = self.generator.generate_comparative_concentration_chart(
            self.sample_data
        )

        # Verify savefig was called
        mock_savefig.assert_called_once()

        # Verify the returned path
        expected_path = os.path.join(
            self.test_output_dir, "comparative_concentration.png"
        )
        self.assertEqual(chart_path, expected_path)

    @patch("matplotlib.pyplot.savefig")
    def test_generate_distribution_comparison(self, mock_savefig):
        """Test that the distribution comparison chart can be generated."""
        # Call the method we're testing
        chart_path = self.generator.generate_distribution_comparison(self.sample_data)

        # Verify savefig was called
        mock_savefig.assert_called_once()

        # Verify the returned path
        expected_path = os.path.join(
            self.test_output_dir, "distribution_comparison.png"
        )
        self.assertEqual(chart_path, expected_path)

    @patch("matplotlib.pyplot.savefig")
    def test_generate_top_holders_bar_chart(self, mock_savefig):
        """Test that the top holders bar chart can be generated."""
        # Call the method we're testing
        chart_path = self.generator.generate_top_holders_bar_chart(self.sample_data)

        # Verify savefig was called
        mock_savefig.assert_called_once()

        # Verify the returned path
        expected_path = os.path.join(self.test_output_dir, "top_holders_comparison.png")
        self.assertEqual(chart_path, expected_path)

    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "src.generate_report.ReportGenerator.generate_comparative_concentration_chart"
    )
    @patch("src.generate_report.ReportGenerator.generate_distribution_comparison")
    @patch("src.generate_report.ReportGenerator.generate_top_holders_bar_chart")
    def test_generate_html_report(
        self, mock_top_holders, mock_distribution, mock_concentration, mock_file
    ):
        """Test that the HTML report can be generated."""
        # Configure mocks to return valid paths
        mock_concentration.return_value = os.path.join(
            self.test_output_dir, "comparative_concentration.png"
        )
        mock_distribution.return_value = os.path.join(
            self.test_output_dir, "distribution_comparison.png"
        )
        mock_top_holders.return_value = os.path.join(
            self.test_output_dir, "top_holders_comparison.png"
        )

        # Call the method we're testing
        report_path = self.generator.generate_html_report(self.sample_data)

        # Verify charts were generated
        mock_concentration.assert_called_once_with(self.sample_data)
        mock_distribution.assert_called_once_with(self.sample_data)
        mock_top_holders.assert_called_once_with(self.sample_data)

        # Verify file was opened for writing
        expected_path = os.path.join(
            self.test_output_dir, "governance_token_analysis_report.html"
        )
        mock_file.assert_called_once()
        self.assertEqual(
            mock_file.call_args[0][1], "w"
        )  # Second argument should be mode 'w'
        # Path should be equivalent (different object type but same string value)
        self.assertEqual(str(mock_file.call_args[0][0]), expected_path)

    @patch("src.generate_report.ReportGenerator.load_protocol_data")
    @patch("src.generate_report.ReportGenerator.generate_html_report")
    def test_generate_full_report(self, mock_html_report, mock_load_data):
        """Test that the full report generation process works."""
        # Configure mocks
        mock_load_data.return_value = self.sample_data
        mock_html_report.return_value = os.path.join(
            self.test_output_dir, "governance_token_analysis_report.html"
        )

        # Call the method we're testing
        report_path = self.generator.generate_full_report(["compound", "uniswap"])

        # Verify data was loaded
        mock_load_data.assert_called_once_with(["compound", "uniswap"])

        # Verify HTML report was generated
        mock_html_report.assert_called_once_with(self.sample_data)

        # Verify the returned path
        expected_path = os.path.join(
            self.test_output_dir, "governance_token_analysis_report.html"
        )
        self.assertEqual(report_path, expected_path)


if __name__ == "__main__":
    unittest.main()
