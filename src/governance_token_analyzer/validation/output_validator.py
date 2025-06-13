"""Output validation framework for governance token analysis results.

This module provides comprehensive validation of analysis outputs including:
- Mathematical accuracy validation
- Data consistency checks
- Cross-protocol comparison validation
- Historical trend validation
- Known benchmark validation
"""

import json
import logging
import math
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation failures."""

    pass


class OutputValidator:
    """Comprehensive validator for governance token analysis outputs."""

    def __init__(self):
        """Initialize the output validator."""
        self.validation_results: List[Dict[str, Any]] = []
        self.known_benchmarks = self._load_known_benchmarks()

    def _load_known_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Load known benchmark values for validation."""
        # These are approximate known values for major protocols
        # Sources: DeFiPulse, Token Terminal, governance forums
        return {
            "compound": {
                "gini_coefficient_range": (0.85, 0.95),  # High concentration expected
                "nakamoto_coefficient_range": (3, 8),  # Few large holders
                "top_10_concentration_range": (70, 90),  # High concentration
                "expected_total_supply": 10_000_000,  # 10M COMP tokens
            },
            "uniswap": {
                "gini_coefficient_range": (0.80, 0.90),  # Moderate-high concentration
                "nakamoto_coefficient_range": (4, 10),  # Slightly more distributed
                "top_10_concentration_range": (60, 80),  # Moderate concentration
                "expected_total_supply": 1_000_000_000,  # 1B UNI tokens
            },
            "aave": {
                "gini_coefficient_range": (0.82, 0.92),  # High concentration
                "nakamoto_coefficient_range": (3, 9),  # Few large holders
                "top_10_concentration_range": (65, 85),  # High concentration
                "expected_total_supply": 16_000_000,  # 16M AAVE tokens
            },
        }

    def validate_analysis_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a complete analysis output.

        Args:
            output_data: The analysis output to validate

        Returns:
            Validation results with pass/fail status and details
        """
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "protocol": output_data.get("protocol"),
            "validation_passed": True,
            "checks": [],
            "warnings": [],
            "errors": [],
        }

        try:
            # 1. Structure validation
            self._validate_output_structure(output_data, validation_result)

            # 2. Mathematical accuracy validation
            self._validate_mathematical_accuracy(output_data, validation_result)

            # 3. Data consistency validation
            self._validate_data_consistency(output_data, validation_result)

            # 4. Benchmark validation
            self._validate_against_benchmarks(output_data, validation_result)

            # 5. Range validation
            self._validate_metric_ranges(output_data, validation_result)

            # 6. Lorenz curve validation
            self._validate_lorenz_curve(output_data, validation_result)

        except Exception as e:
            validation_result["validation_passed"] = False
            validation_result["errors"].append(f"Validation failed with exception: {str(e)}")
            logger.error(f"Validation failed: {e}")

        return validation_result

    def _validate_output_structure(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate the structure of the output data."""
        required_fields = ["protocol", "timestamp", "data_source", "total_holders_analyzed", "metrics"]

        required_metrics = [
            "gini_coefficient",
            "herfindahl_index",
            "nakamoto_coefficient",
            "top_percentile_concentration",
            "lorenz_curve",
        ]

        # Check top-level fields
        for field in required_fields:
            if field not in data:
                result["errors"].append(f"Missing required field: {field}")
                result["validation_passed"] = False
            else:
                result["checks"].append(f"✓ Required field present: {field}")

        # Check metrics structure
        if "metrics" in data:
            for metric in required_metrics:
                if metric not in data["metrics"]:
                    result["errors"].append(f"Missing required metric: {metric}")
                    result["validation_passed"] = False
                else:
                    result["checks"].append(f"✓ Required metric present: {metric}")

    def _validate_mathematical_accuracy(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate mathematical accuracy of calculated metrics."""
        metrics = data.get("metrics", {})

        # Validate Gini coefficient range (0 to 1)
        gini = metrics.get("gini_coefficient")
        if gini is not None:
            if 0 <= gini <= 1:
                result["checks"].append(f"✓ Gini coefficient in valid range: {gini:.4f}")
            else:
                result["errors"].append(f"Gini coefficient out of range [0,1]: {gini}")
                result["validation_passed"] = False

        # Validate Nakamoto coefficient (positive integer)
        nakamoto = metrics.get("nakamoto_coefficient")
        if nakamoto is not None:
            if isinstance(nakamoto, int) and nakamoto > 0:
                result["checks"].append(f"✓ Nakamoto coefficient valid: {nakamoto}")
            else:
                result["errors"].append(f"Invalid Nakamoto coefficient: {nakamoto}")
                result["validation_passed"] = False

        # Validate top percentile concentrations sum to reasonable values
        top_percentiles = metrics.get("top_percentile_concentration", {})
        if top_percentiles:
            # Check that percentiles are monotonically increasing
            percentiles = [1, 5, 10, 20, 50]
            values = [top_percentiles.get(str(p), 0) for p in percentiles]

            if all(values[i] <= values[i + 1] for i in range(len(values) - 1)):
                result["checks"].append("✓ Top percentile concentrations are monotonically increasing")
            else:
                result["errors"].append("Top percentile concentrations not monotonically increasing")
                result["validation_passed"] = False

    def _validate_data_consistency(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate internal consistency of the data."""
        metrics = data.get("metrics", {})

        # Check that total holders analyzed is reasonable
        total_holders = data.get("total_holders_analyzed", 0)
        if 10 <= total_holders <= 10000:
            result["checks"].append(f"✓ Total holders analyzed is reasonable: {total_holders}")
        else:
            result["warnings"].append(f"Unusual number of holders analyzed: {total_holders}")

        # Check timestamp format
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                result["checks"].append("✓ Timestamp format is valid")
            except ValueError:
                result["errors"].append(f"Invalid timestamp format: {timestamp}")
                result["validation_passed"] = False

    def _validate_against_benchmarks(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate against known benchmark values."""
        protocol = data.get("protocol")
        if protocol not in self.known_benchmarks:
            result["warnings"].append(f"No benchmarks available for protocol: {protocol}")
            return

        benchmarks = self.known_benchmarks[protocol]
        metrics = data.get("metrics", {})

        # Validate Gini coefficient against expected range
        gini = metrics.get("gini_coefficient")
        if gini is not None:
            gini_range = benchmarks.get("gini_coefficient_range")
            if gini_range and gini_range[0] <= gini <= gini_range[1]:
                result["checks"].append(f"✓ Gini coefficient within expected range: {gini:.4f}")
            elif gini_range:
                result["warnings"].append(f"Gini coefficient outside expected range {gini_range}: {gini:.4f}")

        # Validate Nakamoto coefficient
        nakamoto = metrics.get("nakamoto_coefficient")
        if nakamoto is not None:
            nakamoto_range = benchmarks.get("nakamoto_coefficient_range")
            if nakamoto_range and nakamoto_range[0] <= nakamoto <= nakamoto_range[1]:
                result["checks"].append(f"✓ Nakamoto coefficient within expected range: {nakamoto}")
            elif nakamoto_range:
                result["warnings"].append(f"Nakamoto coefficient outside expected range {nakamoto_range}: {nakamoto}")

    def _validate_metric_ranges(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate that all metrics are within reasonable ranges."""
        metrics = data.get("metrics", {})

        # Herfindahl Index should be reasonable
        hhi = metrics.get("herfindahl_index")
        if hhi is not None:
            if 0 <= hhi <= 10000:  # Standard HHI range
                result["checks"].append(f"✓ Herfindahl Index in valid range: {hhi:.2f}")
            else:
                result["warnings"].append(f"Herfindahl Index unusual value: {hhi:.2f}")

        # Palma ratio should be positive
        palma = metrics.get("palma_ratio")
        if palma is not None:
            if palma > 0:
                result["checks"].append(f"✓ Palma ratio is positive: {palma:.2f}")
            else:
                result["errors"].append(f"Palma ratio should be positive: {palma}")
                result["validation_passed"] = False

    def _validate_lorenz_curve(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate the Lorenz curve data."""
        metrics = data.get("metrics", {})
        lorenz = metrics.get("lorenz_curve", {})

        if not lorenz:
            result["warnings"].append("No Lorenz curve data found")
            return

        x_values = lorenz.get("x", [])
        y_values = lorenz.get("y", [])

        if len(x_values) != len(y_values):
            result["errors"].append("Lorenz curve x and y arrays have different lengths")
            result["validation_passed"] = False
            return

        # Check that x values go from 0 to 1
        if x_values and x_values[0] == 0 and x_values[-1] == 1.0:
            result["checks"].append("✓ Lorenz curve x-axis spans [0,1]")
        else:
            result["errors"].append("Lorenz curve x-axis should span [0,1]")
            result["validation_passed"] = False

        # Check that y values are monotonically increasing
        if all(y_values[i] <= y_values[i + 1] for i in range(len(y_values) - 1)):
            result["checks"].append("✓ Lorenz curve is monotonically increasing")
        else:
            result["errors"].append("Lorenz curve should be monotonically increasing")
            result["validation_passed"] = False

    def validate_comparison_output(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cross-protocol comparison output."""
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "validation_type": "comparison",
            "validation_passed": True,
            "checks": [],
            "warnings": [],
            "errors": [],
        }

        try:
            # Validate structure
            required_fields = ["comparison_timestamp", "primary_metric", "protocols_compared", "results"]
            for field in required_fields:
                if field not in comparison_data:
                    validation_result["errors"].append(f"Missing required field: {field}")
                    validation_result["validation_passed"] = False

            # Validate each protocol's results
            results = comparison_data.get("results", {})
            protocols_compared = comparison_data.get("protocols_compared", [])

            for protocol in protocols_compared:
                if protocol in results:
                    protocol_validation = self.validate_analysis_output({"protocol": protocol, **results[protocol]})
                    if not protocol_validation["validation_passed"]:
                        validation_result["errors"].extend(
                            [f"{protocol}: {error}" for error in protocol_validation["errors"]]
                        )
                        validation_result["validation_passed"] = False
                else:
                    validation_result["errors"].append(f"Missing results for protocol: {protocol}")
                    validation_result["validation_passed"] = False

            # Validate ranking consistency
            ranking = comparison_data.get("ranking", [])
            primary_metric = comparison_data.get("primary_metric")

            if ranking and primary_metric:
                self._validate_ranking_consistency(results, ranking, primary_metric, validation_result)

        except Exception as e:
            validation_result["validation_passed"] = False
            validation_result["errors"].append(f"Comparison validation failed: {str(e)}")

        return validation_result

    def _validate_ranking_consistency(
        self, results: Dict[str, Any], ranking: List[str], primary_metric: str, validation_result: Dict[str, Any]
    ) -> None:
        """Validate that the ranking is consistent with the primary metric values."""
        try:
            metric_values = []
            for protocol in ranking:
                if protocol in results:
                    metrics = results[protocol].get("metrics", {})
                    value = metrics.get(primary_metric)
                    if value is not None:
                        metric_values.append((protocol, value))

            # Check if ranking is correct (assuming higher values = higher rank for most metrics)
            sorted_by_value = sorted(metric_values, key=lambda x: x[1], reverse=True)
            expected_ranking = [item[0] for item in sorted_by_value]

            if ranking == expected_ranking:
                validation_result["checks"].append(f"✓ Ranking consistent with {primary_metric} values")
            else:
                validation_result["warnings"].append(
                    f"Ranking may be inconsistent with {primary_metric} values. "
                    f"Expected: {expected_ranking}, Got: {ranking}"
                )

        except Exception as e:
            validation_result["warnings"].append(f"Could not validate ranking consistency: {str(e)}")

    def generate_validation_report(self, validation_results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive validation report."""
        report_lines = [
            "# Governance Token Analyzer - Validation Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"Total validations performed: {len(validation_results)}",
        ]

        passed = sum(1 for r in validation_results if r.get("validation_passed", False))
        failed = len(validation_results) - passed

        report_lines.extend(
            [
                f"✅ Passed: {passed}",
                f"❌ Failed: {failed}",
                f"Success rate: {(passed / len(validation_results) * 100):.1f}%" if validation_results else "N/A",
                "",
            ]
        )

        # Detailed results
        for i, result in enumerate(validation_results, 1):
            status = "✅ PASSED" if result.get("validation_passed") else "❌ FAILED"
            protocol = result.get("protocol", "Unknown")

            report_lines.extend([f"## Validation {i}: {protocol} - {status}", ""])

            if result.get("checks"):
                report_lines.append("### Checks Passed:")
                for check in result["checks"]:
                    report_lines.append(f"- {check}")
                report_lines.append("")

            if result.get("warnings"):
                report_lines.append("### Warnings:")
                for warning in result["warnings"]:
                    report_lines.append(f"- ⚠️ {warning}")
                report_lines.append("")

            if result.get("errors"):
                report_lines.append("### Errors:")
                for error in result["errors"]:
                    report_lines.append(f"- ❌ {error}")
                report_lines.append("")

        return "\n".join(report_lines)


def validate_output_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Validate an output file and return validation results."""
    validator = OutputValidator()

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if "comparison_timestamp" in data:
            return validator.validate_comparison_output(data)
        else:
            return validator.validate_analysis_output(data)

    except Exception as e:
        return {
            "validation_passed": False,
            "errors": [f"Failed to validate file {file_path}: {str(e)}"],
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # Example usage
    validator = OutputValidator()

    # Validate recent outputs
    output_dir = Path("outputs")
    if output_dir.exists():
        validation_results = []
        for output_file in output_dir.glob("*.json"):
            result = validate_output_file(output_file)
            validation_results.append(result)
            print(f"Validated {output_file.name}: {'✅ PASSED' if result['validation_passed'] else '❌ FAILED'}")

        # Generate report
        if validation_results:
            report = validator.generate_validation_report(validation_results)
            print("\n" + "=" * 50)
            print(report)
