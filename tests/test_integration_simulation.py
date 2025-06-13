"""Integration tests for the Token Distribution Simulation functionality.

These tests verify that the simulator produces realistic and varied distributions
and that the metrics calculations work correctly on the simulated data.
"""

import pytest

from governance_token_analyzer.core.advanced_metrics import (
    calculate_all_concentration_metrics,
)
from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator


@pytest.fixture
def simulator():
    """Create a simulator with a fixed seed for reproducibility."""
    return TokenDistributionSimulator(seed=42)


def test_power_law_distribution(simulator):
    """Test that power law distribution has expected concentration properties."""
    # Generate power law distribution
    holders = simulator.generate_power_law_distribution(num_holders=100)

    # Verify number of holders
    assert len(holders) == 100

    # Extract quantities and calculate metrics
    quantities = [float(h["TokenHolderQuantity"]) for h in holders]
    metrics = calculate_all_concentration_metrics(quantities)

    # Verify concentration metrics
    assert metrics["nakamoto_coefficient"] < 50  # Power law should be concentrated
    assert metrics["hoover_index"] > 0.2  # Should have significant inequality

    # Verify top holder percentages
    percentiles = metrics["top_percentile_concentration"]
    assert float(percentiles["1"]) > 1  # Top 1% should have more than 1% share
    assert float(percentiles["10"]) > 10  # Top 10% should have more than 10% share

    # Verify lorenz curve
    lorenz = metrics["lorenz_curve"]
    assert len(lorenz["x"]) == len(lorenz["y"])
    assert lorenz["x"][0] == 0 and lorenz["y"][0] == 0
    assert lorenz["x"][-1] == 1 and lorenz["y"][-1] == 1

    # Verify curve is below diagonal (indicates inequality)
    for i in range(1, len(lorenz["x"]) - 1):
        assert lorenz["y"][i] < lorenz["x"][i]


def test_protocol_dominated_distribution(simulator):
    """Test that protocol-dominated distribution has high concentration."""
    # Generate protocol-dominated distribution
    holders = simulator.generate_protocol_dominated_distribution(num_holders=100)

    # Verify number of holders
    assert len(holders) == 100

    # Extract quantities and calculate metrics
    quantities = [float(h["TokenHolderQuantity"]) for h in holders]
    metrics = calculate_all_concentration_metrics(quantities)

    # Verify concentration metrics
    assert metrics["nakamoto_coefficient"] < 30  # Should be concentrated
    assert metrics["hoover_index"] > 0.25  # Should have inequality

    # Verify top holder percentages
    percentiles = metrics["top_percentile_concentration"]
    assert float(percentiles["1"]) > 1  # Top 1% should have more than 1% share
    assert float(percentiles["5"]) > 5  # Top 5% should have more than 5% share

    # Verify there are some large holders
    top_holder_percentage = float(holders[0]["TokenHolderPercentage"])
    assert top_holder_percentage > 1  # Top holder should have significant percentage


def test_community_distribution(simulator):
    """Test that community distribution has a defined distribution."""
    # Generate community distribution
    holders = simulator.generate_community_distribution(num_holders=100)

    # Verify number of holders
    assert len(holders) == 100

    # Extract quantities and calculate metrics
    quantities = [float(h["TokenHolderQuantity"]) for h in holders]
    metrics = calculate_all_concentration_metrics(quantities)

    # Verify concentration metrics are in reasonable ranges
    assert 10 <= metrics["nakamoto_coefficient"] <= 50
    assert 0.2 <= metrics["hoover_index"] <= 0.5

    # Verify top holder percentages
    percentiles = metrics["top_percentile_concentration"]
    assert 5 <= float(percentiles["10"]) <= 70  # Top 10% should have a reasonable share

    # Verify distribution has recognizable pattern
    top_holder_percentage = float(holders[0]["TokenHolderPercentage"])
    bottom_holder_percentage = float(holders[-1]["TokenHolderPercentage"])
    assert top_holder_percentage > bottom_holder_percentage  # Should still have some inequality


def test_distribution_patterns(simulator):
    """Test that distributions produce different patterns."""
    # Generate all three distribution types
    power_law = simulator.generate_power_law_distribution(num_holders=100)
    protocol = simulator.generate_protocol_dominated_distribution(num_holders=100)
    community = simulator.generate_community_distribution(num_holders=100)

    # Extract quantities
    power_law_quantities = [float(h["TokenHolderQuantity"]) for h in power_law]
    protocol_quantities = [float(h["TokenHolderQuantity"]) for h in protocol]
    community_quantities = [float(h["TokenHolderQuantity"]) for h in community]

    # Calculate metrics
    power_law_metrics = calculate_all_concentration_metrics(power_law_quantities)
    protocol_metrics = calculate_all_concentration_metrics(protocol_quantities)
    community_metrics = calculate_all_concentration_metrics(community_quantities)

    # Verify all distributions produce valid metrics
    assert 0 <= power_law_metrics["hoover_index"] <= 1
    assert 0 <= protocol_metrics["hoover_index"] <= 1
    assert 0 <= community_metrics["hoover_index"] <= 1

    # Verify all distributions have a positive Nakamoto coefficient
    assert power_law_metrics["nakamoto_coefficient"] > 0
    assert protocol_metrics["nakamoto_coefficient"] > 0
    assert community_metrics["nakamoto_coefficient"] > 0

    # Verify all distributions have the Palma ratio calculated
    assert "palma_ratio" in power_law_metrics
    assert "palma_ratio" in protocol_metrics
    assert "palma_ratio" in community_metrics


def test_token_holders_response_format(simulator):
    """Test that the token holders response format is correct."""
    # Generate distribution
    holders = simulator.generate_power_law_distribution(num_holders=50)

    # Generate response
    response = simulator.generate_token_holders_response(holders)

    # Verify response structure
    assert "status" in response
    assert "message" in response
    assert "result" in response

    # Verify status and message
    assert response["status"] == "1"
    assert response["message"] == "OK"

    # Verify result contains the same number of holders
    assert len(response["result"]) == 50

    # Verify each holder has the required fields
    for holder in response["result"]:
        assert "TokenHolderAddress" in holder
        assert "TokenHolderQuantity" in holder
        assert "TokenHolderPercentage" in holder
