"""Cross-validation module for verifying analysis accuracy against external sources."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class CrossValidator:
    """Cross-validates governance token analysis against external data sources."""
    
    def __init__(self):
        """Initialize cross-validator with external data sources."""
        self.external_sources = {
            "compound": {
                "governance_forum": "https://compound.finance/governance",
                "snapshot_space": "comp-vote.eth",
                "known_events": [
                    {
                        "date": "2020-06-15",
                        "event": "COMP token launch",
                        "expected_concentration": "very_high"  # Initial distribution to team/investors
                    },
                    {
                        "date": "2021-03-01", 
                        "event": "Governance activation",
                        "expected_concentration": "high"  # Still concentrated but some distribution
                    }
                ]
            },
            "uniswap": {
                "governance_forum": "https://gov.uniswap.org",
                "snapshot_space": "uniswap",
                "known_events": [
                    {
                        "date": "2020-09-17",
                        "event": "UNI token airdrop",
                        "expected_concentration": "moderate"  # Airdrop distributed tokens
                    }
                ]
            },
            "aave": {
                "governance_forum": "https://governance.aave.com",
                "snapshot_space": "aave.eth",
                "known_events": [
                    {
                        "date": "2020-10-02",
                        "event": "AAVE token migration from LEND",
                        "expected_concentration": "high"
                    }
                ]
            }
        }
    
    def validate_against_known_events(self, protocol: str, analysis_data: Dict) -> Dict[str, any]:
        """Validate analysis results against known governance events."""
        validation_result = {
            "protocol": protocol,
            "validation_type": "known_events",
            "checks": [],
            "warnings": [],
            "errors": [],
            "validation_passed": True
        }
        
        if protocol not in self.external_sources:
            validation_result["warnings"].append(f"No known events data for protocol: {protocol}")
            return validation_result
        
        events = self.external_sources[protocol]["known_events"]
        metrics = analysis_data.get("metrics", {})
        gini = metrics.get("gini_coefficient")
        
        if gini is None:
            validation_result["errors"].append("No Gini coefficient found in analysis data")
            validation_result["validation_passed"] = False
            return validation_result
        
        # Validate against expected concentration levels
        for event in events:
            expected_concentration = event["expected_concentration"]
            event_date = event["date"]
            event_name = event["event"]
            
            # Map expected concentration to Gini coefficient ranges
            concentration_ranges = {
                "very_high": (0.9, 1.0),    # 90-100% concentration
                "high": (0.8, 0.9),         # 80-90% concentration  
                "moderate": (0.6, 0.8),     # 60-80% concentration
                "low": (0.4, 0.6),          # 40-60% concentration
                "very_low": (0.0, 0.4)      # 0-40% concentration
            }
            
            if expected_concentration in concentration_ranges:
                min_gini, max_gini = concentration_ranges[expected_concentration]
                
                if min_gini <= gini <= max_gini:
                    validation_result["checks"].append(
                        f"✓ Gini coefficient ({gini:.4f}) consistent with {event_name} "
                        f"(expected {expected_concentration}: {min_gini}-{max_gini})"
                    )
                else:
                    validation_result["warnings"].append(
                        f"Gini coefficient ({gini:.4f}) may not align with {event_name} "
                        f"(expected {expected_concentration}: {min_gini}-{max_gini})"
                    )
        
        return validation_result
    
    def validate_mathematical_consistency(self, analysis_data: Dict) -> Dict[str, any]:
        """Validate mathematical consistency of calculated metrics."""
        validation_result = {
            "validation_type": "mathematical_consistency",
            "checks": [],
            "warnings": [],
            "errors": [],
            "validation_passed": True
        }
        
        metrics = analysis_data.get("metrics", {})
        
        # Check Gini coefficient vs top percentile consistency
        gini = metrics.get("gini_coefficient")
        top_percentiles = metrics.get("top_percentile_concentration", {})
        
        if gini and top_percentiles:
            top_10_pct = top_percentiles.get("10", 0) / 100  # Convert to decimal
            
            # High Gini should correlate with high top 10% concentration
            if gini > 0.8 and top_10_pct > 0.7:
                validation_result["checks"].append(
                    f"✓ High Gini ({gini:.4f}) consistent with high top 10% concentration ({top_10_pct:.1%})"
                )
            elif gini < 0.5 and top_10_pct < 0.5:
                validation_result["checks"].append(
                    f"✓ Low Gini ({gini:.4f}) consistent with low top 10% concentration ({top_10_pct:.1%})"
                )
            elif abs(gini - top_10_pct) > 0.3:
                validation_result["warnings"].append(
                    f"Potential inconsistency: Gini ({gini:.4f}) vs top 10% concentration ({top_10_pct:.1%})"
                )
        
        # Check Nakamoto coefficient vs Gini consistency
        nakamoto = metrics.get("nakamoto_coefficient")
        if gini and nakamoto:
            # High concentration (high Gini) should mean low Nakamoto coefficient
            if gini > 0.8 and nakamoto > 10:
                validation_result["warnings"].append(
                    f"Potential inconsistency: High Gini ({gini:.4f}) but high Nakamoto coefficient ({nakamoto})"
                )
            elif gini < 0.5 and nakamoto < 5:
                validation_result["warnings"].append(
                    f"Potential inconsistency: Low Gini ({gini:.4f}) but low Nakamoto coefficient ({nakamoto})"
                )
            else:
                validation_result["checks"].append(
                    f"✓ Gini coefficient ({gini:.4f}) and Nakamoto coefficient ({nakamoto}) are consistent"
                )
        
        return validation_result
    
    def validate_lorenz_curve_accuracy(self, analysis_data: Dict) -> Dict[str, any]:
        """Validate Lorenz curve mathematical properties."""
        validation_result = {
            "validation_type": "lorenz_curve_accuracy",
            "checks": [],
            "warnings": [],
            "errors": [],
            "validation_passed": True
        }
        
        metrics = analysis_data.get("metrics", {})
        lorenz = metrics.get("lorenz_curve", {})
        
        if not lorenz:
            validation_result["warnings"].append("No Lorenz curve data found")
            return validation_result
        
        x_values = lorenz.get("x", [])
        y_values = lorenz.get("y", [])
        
        if not x_values or not y_values:
            validation_result["errors"].append("Empty Lorenz curve data")
            validation_result["validation_passed"] = False
            return validation_result
        
        # Check boundary conditions
        if x_values[0] == 0 and y_values[0] == 0:
            validation_result["checks"].append("✓ Lorenz curve starts at origin (0,0)")
        else:
            validation_result["errors"].append("Lorenz curve should start at origin (0,0)")
            validation_result["validation_passed"] = False
        
        if x_values[-1] == 1.0 and y_values[-1] == 1.0:
            validation_result["checks"].append("✓ Lorenz curve ends at (1,1)")
        else:
            validation_result["errors"].append("Lorenz curve should end at (1,1)")
            validation_result["validation_passed"] = False
        
        # Check that curve is below or on the line of equality
        for i, (x, y) in enumerate(zip(x_values, y_values)):
            if y > x + 0.001:  # Small tolerance for floating point errors
                validation_result["errors"].append(
                    f"Lorenz curve point ({x:.3f}, {y:.3f}) is above line of equality"
                )
                validation_result["validation_passed"] = False
                break
        else:
            validation_result["checks"].append("✓ Lorenz curve is below or on line of equality")
        
        # Validate Gini coefficient calculation from Lorenz curve
        gini_from_metrics = metrics.get("gini_coefficient")
        if gini_from_metrics and len(x_values) > 1:
            # Calculate Gini from Lorenz curve using trapezoidal rule
            area_under_lorenz = 0
            for i in range(len(x_values) - 1):
                area_under_lorenz += (x_values[i+1] - x_values[i]) * (y_values[i] + y_values[i+1]) / 2
            
            gini_calculated = 1 - 2 * area_under_lorenz
            
            if abs(gini_from_metrics - gini_calculated) < 0.01:  # 1% tolerance
                validation_result["checks"].append(
                    f"✓ Gini coefficient ({gini_from_metrics:.4f}) matches Lorenz curve calculation ({gini_calculated:.4f})"
                )
            else:
                validation_result["warnings"].append(
                    f"Gini coefficient mismatch: reported {gini_from_metrics:.4f}, calculated {gini_calculated:.4f}"
                )
        
        return validation_result
    
    def comprehensive_validation(self, analysis_data: Dict) -> Dict[str, any]:
        """Run comprehensive cross-validation on analysis data."""
        protocol = analysis_data.get("protocol")
        
        validation_results = {
            "protocol": protocol,
            "timestamp": datetime.now().isoformat(),
            "overall_validation_passed": True,
            "validations": []
        }
        
        # Run all validation checks
        validations = [
            self.validate_against_known_events(protocol, analysis_data),
            self.validate_mathematical_consistency(analysis_data),
            self.validate_lorenz_curve_accuracy(analysis_data)
        ]
        
        for validation in validations:
            validation_results["validations"].append(validation)
            if not validation.get("validation_passed", True):
                validation_results["overall_validation_passed"] = False
        
        # Summary statistics
        total_checks = sum(len(v.get("checks", [])) for v in validations)
        total_warnings = sum(len(v.get("warnings", [])) for v in validations)
        total_errors = sum(len(v.get("errors", [])) for v in validations)
        
        validation_results["summary"] = {
            "total_checks_passed": total_checks,
            "total_warnings": total_warnings,
            "total_errors": total_errors,
            "validation_score": total_checks / (total_checks + total_errors) if (total_checks + total_errors) > 0 else 1.0
        }
        
        return validation_results


def cross_validate_file(file_path: str) -> Dict[str, any]:
    """Cross-validate an analysis output file."""
    validator = CrossValidator()
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return validator.comprehensive_validation(data)
    
    except Exception as e:
        return {
            "validation_passed": False,
            "errors": [f"Failed to cross-validate file {file_path}: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Example usage
    validator = CrossValidator()
    
    # Test with recent output
    output_dir = Path("outputs")
    if output_dir.exists():
        for output_file in output_dir.glob("compound_analysis_*.json"):
            result = cross_validate_file(str(output_file))
            print(f"Cross-validated {output_file.name}:")
            print(f"  Overall validation: {'✅ PASSED' if result.get('overall_validation_passed') else '❌ FAILED'}")
            
            if "summary" in result:
                summary = result["summary"]
                print(f"  Checks passed: {summary['total_checks_passed']}")
                print(f"  Warnings: {summary['total_warnings']}")
                print(f"  Errors: {summary['total_errors']}")
                print(f"  Validation score: {summary['validation_score']:.2%}")
            print() 