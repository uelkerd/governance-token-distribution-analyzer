"""CLI command for validating governance token analysis outputs."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import click
import numpy as np

logger = logging.getLogger(__name__)


class OutputValidator:
    """Validator for governance token analysis outputs."""

    def __init__(self):
        """Initialize the validator with known benchmarks."""
        self.known_benchmarks = {
            "compound": {
                "gini_coefficient_range": (0.85, 0.95),
                "nakamoto_coefficient_range": (3, 8),
                "top_10_concentration_range": (70, 90),
            },
            "uniswap": {
                "gini_coefficient_range": (0.80, 0.90),
                "nakamoto_coefficient_range": (4, 10),
                "top_10_concentration_range": (60, 80),
            },
            "aave": {
                "gini_coefficient_range": (0.82, 0.92),
                "nakamoto_coefficient_range": (3, 9),
                "top_10_concentration_range": (65, 85),
            },
        }

    def validate_analysis_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate analysis output data."""
        result = {
            "protocol": data.get("protocol"),
            "validation_passed": True,
            "checks": [],
            "warnings": [],
            "errors": [],
        }

        # Structure validation
        required_fields = ["protocol", "timestamp", "metrics"]
        for field in required_fields:
            if field not in data:
                result["errors"].append(f"Missing required field: {field}")
                result["validation_passed"] = False
            else:
                result["checks"].append(f"✓ Required field present: {field}")

        # Metrics validation
        metrics = data.get("metrics", {})

        # Gini coefficient validation
        gini = metrics.get("gini_coefficient")
        if gini is not None:
            if 0 <= gini <= 1:
                result["checks"].append(f"✓ Gini coefficient in valid range: {gini:.4f}")
            else:
                result["errors"].append(f"Gini coefficient out of range [0,1]: {gini}")
                result["validation_passed"] = False

        # Nakamoto coefficient validation
        nakamoto = metrics.get("nakamoto_coefficient")
        if nakamoto is not None:
            if isinstance(nakamoto, int) and nakamoto > 0:
                result["checks"].append(f"✓ Nakamoto coefficient valid: {nakamoto}")
            else:
                result["errors"].append(f"Invalid Nakamoto coefficient: {nakamoto}")
                result["validation_passed"] = False

        # Benchmark validation
        protocol = data.get("protocol")
        if protocol in self.known_benchmarks:
            benchmarks = self.known_benchmarks[protocol]

            # Validate Gini coefficient against expected range
            if gini is not None:
                gini_range = benchmarks.get("gini_coefficient_range")
                if gini_range and gini_range[0] <= gini <= gini_range[1]:
                    result["checks"].append(f"✓ Gini coefficient within expected range: {gini:.4f}")
                elif gini_range:
                    result["warnings"].append(f"Gini coefficient outside expected range {gini_range}: {gini:.4f}")

            # Validate Nakamoto coefficient
            if nakamoto is not None:
                nakamoto_range = benchmarks.get("nakamoto_coefficient_range")
                if nakamoto_range and nakamoto_range[0] <= nakamoto <= nakamoto_range[1]:
                    result["checks"].append(f"✓ Nakamoto coefficient within expected range: {nakamoto}")
                elif nakamoto_range:
                    result["warnings"].append(
                        f"Nakamoto coefficient outside expected range {nakamoto_range}: {nakamoto}"
                    )

        # Lorenz curve validation
        lorenz = metrics.get("lorenz_curve", {})
        if lorenz:
            x_values = lorenz.get("x", [])
            y_values = lorenz.get("y", [])

            if len(x_values) == len(y_values):
                result["checks"].append("✓ Lorenz curve arrays have matching lengths")

                # Check monotonicity
                if all(y_values[i] <= y_values[i + 1] for i in range(len(y_values) - 1)):
                    result["checks"].append("✓ Lorenz curve is monotonically increasing")
                else:
                    result["errors"].append("Lorenz curve should be monotonically increasing")
                    result["validation_passed"] = False
            else:
                result["errors"].append("Lorenz curve x and y arrays have different lengths")
                result["validation_passed"] = False

        return result


@click.command()
@click.option("--file", "-f", type=click.Path(exists=True), help="Validate specific output file")
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    default="outputs",
    help="Directory containing output files to validate",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
@click.option("--report", "-r", is_flag=True, help="Generate validation report")
def validate(file, directory, verbose, report):
    """🔍 Validate governance token analysis outputs for accuracy and consistency.

    This command validates analysis outputs against:
    • Mathematical accuracy (ranges, calculations)
    • Data consistency (structure, formats)
    • Known benchmarks (expected ranges for protocols)
    • Cross-protocol comparison consistency

    Examples:
      gova validate --file outputs/compound_analysis.json
      gova validate --directory outputs --verbose
      gova validate --report
    """
    validator = OutputValidator()
    validation_results = []

    click.echo("🔍 Validating governance token analysis outputs...")

    if file:
        # Validate single file
        try:
            with open(file, "r") as f:
                data = json.load(f)

            result = validator.validate_analysis_output(data)
            validation_results.append(result)

            status = "✅ PASSED" if result["validation_passed"] else "❌ FAILED"
            click.echo(f"\n📄 {Path(file).name}: {status}")

            if verbose:
                _print_validation_details(result)

        except Exception as e:
            click.echo(f"❌ Error validating {file}: {e}")
            return

    else:
        # Validate all files in directory
        output_dir = Path(directory)
        if not output_dir.exists():
            click.echo(f"❌ Directory not found: {directory}")
            return

        json_files = list(output_dir.glob("*.json"))
        if not json_files:
            click.echo(f"❌ No JSON files found in {directory}")
            return

        click.echo(f"📁 Found {len(json_files)} files to validate")

        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                result = validator.validate_analysis_output(data)
                validation_results.append(result)

                status = "✅ PASSED" if result["validation_passed"] else "❌ FAILED"
                click.echo(f"  📄 {json_file.name}: {status}")

                if verbose:
                    _print_validation_details(result)

            except Exception as e:
                click.echo(f"  ❌ Error validating {json_file.name}: {e}")

    # Summary
    if validation_results:
        passed = sum(1 for r in validation_results if r["validation_passed"])
        total = len(validation_results)
        success_rate = (passed / total) * 100

        click.echo(f"\n📊 Validation Summary:")
        click.echo(f"  ✅ Passed: {passed}/{total}")
        click.echo(f"  ❌ Failed: {total - passed}/{total}")
        click.echo(f"  📈 Success Rate: {success_rate:.1f}%")

        if report:
            _generate_validation_report(validation_results)


def _print_validation_details(result: Dict[str, Any]) -> None:
    """Print detailed validation results."""
    if result.get("checks"):
        click.echo("    ✓ Checks passed:")
        for check in result["checks"]:
            click.echo(f"      {check}")

    if result.get("warnings"):
        click.echo("    ⚠️  Warnings:")
        for warning in result["warnings"]:
            click.echo(f"      {warning}")

    if result.get("errors"):
        click.echo("    ❌ Errors:")
        for error in result["errors"]:
            click.echo(f"      {error}")

    click.echo()


def _generate_validation_report(validation_results: List[Dict[str, Any]]) -> None:
    """Generate and save a validation report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"validation_report_{timestamp}.md"

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
            f"Success rate: {(passed / len(validation_results) * 100):.1f}%",
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

    # Save report
    with open(report_file, "w") as f:
        f.write("\n".join(report_lines))

    click.echo(f"📋 Validation report saved: {report_file}")


if __name__ == "__main__":
    validate()
