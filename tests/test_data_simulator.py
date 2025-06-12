import sys
import unittest
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.analyzer.data_simulator import TokenDistributionSimulator


class TestTokenDistributionSimulator(unittest.TestCase):
    """Test the token distribution simulator functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create simulator with fixed seed for reproducible tests
        self.simulator = TokenDistributionSimulator(seed=42)

    def test_power_law_distribution(self):
        """Test that power law distribution generates expected data structure."""
        # Generate distribution
        holders = self.simulator.generate_power_law_distribution(num_holders=50)

        # Verify structure and properties
        self.assertEqual(len(holders), 50)
        self.assertIn("TokenHolderAddress", holders[0])
        self.assertIn("TokenHolderQuantity", holders[0])
        self.assertIn("TokenHolderPercentage", holders[0])

        # Verify sorting (descending order by quantity)
        quantities = [float(holder["TokenHolderQuantity"]) for holder in holders]
        self.assertEqual(quantities, sorted(quantities, reverse=True))

        # Verify total adds up to total supply (allowing for small rounding errors)
        total_quantity = sum(float(holder["TokenHolderQuantity"]) for holder in holders)
        self.assertAlmostEqual(
            total_quantity, 10_000_000, delta=30
        )  # Allow small delta for rounding

        # Verify percentages add up to approximately 100%
        total_percentage = sum(
            float(holder["TokenHolderPercentage"]) for holder in holders
        )
        self.assertAlmostEqual(total_percentage, 100.0, delta=0.1)

    def test_protocol_dominated_distribution(self):
        """Test that protocol dominated distribution generates expected data structure."""
        # Generate distribution
        holders = self.simulator.generate_protocol_dominated_distribution(
            num_holders=50, protocol_percentage=30.0
        )

        # Verify structure and properties
        self.assertLessEqual(
            len(holders), 50
        )  # Can be slightly less due to protocol wallets
        self.assertIn("TokenHolderAddress", holders[0])
        self.assertIn("TokenHolderQuantity", holders[0])
        self.assertIn("TokenHolderPercentage", holders[0])

        # Verify top holders (protocol wallets) have expected percentage
        top_5_percentage = sum(
            float(holder["TokenHolderPercentage"]) for holder in holders[:5]
        )
        self.assertGreaterEqual(
            top_5_percentage, 25.0
        )  # Protocol wallets should have significant holdings

        # Verify total adds up to total supply
        total_quantity = sum(float(holder["TokenHolderQuantity"]) for holder in holders)
        self.assertAlmostEqual(total_quantity, 10_000_000, delta=30)

        # Verify percentages add up to approximately 100%
        total_percentage = sum(
            float(holder["TokenHolderPercentage"]) for holder in holders
        )
        self.assertAlmostEqual(total_percentage, 100.0, delta=0.1)

    def test_community_distribution(self):
        """Test that community distribution generates expected data structure."""
        # Generate distribution with target Gini coefficient
        holders = self.simulator.generate_community_distribution(
            num_holders=50, gini_target=0.5
        )

        # Verify structure and properties
        self.assertEqual(len(holders), 50)
        self.assertIn("TokenHolderAddress", holders[0])
        self.assertIn("TokenHolderQuantity", holders[0])
        self.assertIn("TokenHolderPercentage", holders[0])

        # Verify top holders have less concentration than power law
        top_5_percentage = sum(
            float(holder["TokenHolderPercentage"]) for holder in holders[:5]
        )
        self.assertLessEqual(
            top_5_percentage, 60.0
        )  # Community distribution should be more equal

        # Verify total adds up to total supply
        total_quantity = sum(float(holder["TokenHolderQuantity"]) for holder in holders)
        self.assertAlmostEqual(total_quantity, 10_000_000, delta=30)

        # Verify percentages add up to approximately 100%
        total_percentage = sum(
            float(holder["TokenHolderPercentage"]) for holder in holders
        )
        self.assertAlmostEqual(total_percentage, 100.0, delta=0.1)

    def test_historical_distribution(self):
        """Test that historical distribution generates a time series of distributions."""
        # Generate historical distribution
        historical = self.simulator.generate_historical_distribution(
            distribution_type="power_law",
            num_periods=6,
            num_holders=50,
            concentration_trend="decreasing",
        )

        # Verify structure and properties
        self.assertEqual(len(historical), 6)  # 6 time periods

        # Verify each time period has the expected structure
        for date, response in historical.items():
            self.assertIn("status", response)
            self.assertIn("message", response)
            self.assertIn("result", response)
            self.assertEqual(response["status"], "1")
            self.assertEqual(response["message"], "OK")
            self.assertEqual(len(response["result"]), 50)

    def test_trends_in_historical_data(self):
        """Test that concentration trends actually work as expected."""
        # Generate increasing concentration
        increasing = self.simulator.generate_historical_distribution(
            distribution_type="power_law",
            num_periods=6,
            num_holders=50,
            concentration_trend="increasing",
        )

        # Generate decreasing concentration
        decreasing = self.simulator.generate_historical_distribution(
            distribution_type="power_law",
            num_periods=6,
            num_holders=50,
            concentration_trend="decreasing",
        )

        # Calculate concentration for first and last period in each trend
        dates_increasing = sorted(increasing.keys())
        first_period_increasing = increasing[dates_increasing[0]]["result"]
        last_period_increasing = increasing[dates_increasing[-1]]["result"]

        dates_decreasing = sorted(decreasing.keys())
        first_period_decreasing = decreasing[dates_decreasing[0]]["result"]
        last_period_decreasing = decreasing[dates_decreasing[-1]]["result"]

        # Compare top holder percentages
        top_holder_first_increasing = float(
            first_period_increasing[0]["TokenHolderPercentage"]
        )
        top_holder_last_increasing = float(
            last_period_increasing[0]["TokenHolderPercentage"]
        )

        top_holder_first_decreasing = float(
            first_period_decreasing[0]["TokenHolderPercentage"]
        )
        top_holder_last_decreasing = float(
            last_period_decreasing[0]["TokenHolderPercentage"]
        )

        # For increasing concentration, the top holder should have a higher percentage in the last period
        self.assertGreater(top_holder_last_increasing, top_holder_first_increasing)

        # For decreasing concentration, the top holder should have a lower percentage in the last period
        self.assertLess(top_holder_last_decreasing, top_holder_first_decreasing)


if __name__ == "__main__":
    unittest.main()
