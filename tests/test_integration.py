"""Integration tests for the Governance Token Distribution Analyzer.

These tests verify that the package components can be imported and work together correctly.
"""

import os
import sys

import pytest

# Ensure the package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_imports():
    """Test that all components can be imported correctly."""
    # Main package

    # Core components
    from governance_token_analyzer.core import (
        advanced_metrics,
        data_simulator,
        token_analysis,
    )

    # Protocol-specific components
    # Visualization

    # Verify we can access classes and functions from the modules
    assert hasattr(advanced_metrics, "calculate_all_concentration_metrics")
    assert hasattr(data_simulator, "TokenDistributionSimulator")
    assert hasattr(token_analysis, "TokenDistributionAnalyzer")


def test_simulator_integration():
    """Test that the simulator can generate data and be analyzed with metrics."""
    from governance_token_analyzer.core.advanced_metrics import (
        calculate_all_concentration_metrics,
    )
    from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator

    simulator = TokenDistributionSimulator(seed=42)
    holders = simulator.generate_power_law_distribution(num_holders=100)

    # Extract token quantities
    quantities = [float(h["TokenHolderQuantity"]) for h in holders]

    # Calculate metrics
    metrics = calculate_all_concentration_metrics(quantities)

    # Verify we got reasonable results
    assert "nakamoto_coefficient" in metrics
    assert metrics["nakamoto_coefficient"] > 0
    assert "palma_ratio" in metrics
    assert "hoover_index" in metrics
    assert "lorenz_curve" in metrics


if __name__ == "__main__":
    pytest.main(["-v", __file__])
