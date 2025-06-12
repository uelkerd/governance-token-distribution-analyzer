import sys
import unittest
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.analyzer.advanced_metrics import (
    calculate_all_concentration_metrics,
    calculate_hoover_index,
    calculate_lorenz_curve,
    calculate_nakamoto_coefficient,
    calculate_palma_ratio,
    calculate_theil_index,
)


class TestAdvancedMetrics(unittest.TestCase):
    """Test cases for the advanced metrics functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test data: power law distribution
        self.test_balances = [1000, 500, 250, 100, 50, 25, 10, 5, 2, 1]

    def test_extreme_inequality(self):
        """Test metrics with extreme inequality."""
        # One holder has everything
        extreme_balances = [1000, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Calculate individual metrics
        hoover = calculate_hoover_index(extreme_balances)
        nakamoto = calculate_nakamoto_coefficient(extreme_balances)

        # Verify expected values
        self.assertAlmostEqual(
            hoover, 0.9, places=1
        )  # Should be close to 1 (complete inequality)
        self.assertEqual(nakamoto, 1)  # Only 1 entity needed for control

    def test_perfect_equality(self):
        """Test metrics with perfectly equal distribution."""
        equal_balances = [100] * 10  # 10 holders with equal balances

        # Calculate individual metrics
        palma = calculate_palma_ratio(equal_balances)
        hoover = calculate_hoover_index(equal_balances)
        theil = calculate_theil_index(equal_balances)
        nakamoto = calculate_nakamoto_coefficient(equal_balances)

        # Verify expected values for equal distribution
        self.assertAlmostEqual(
            palma, 0.25
        )  # For equal distribution with this calculation method
        self.assertAlmostEqual(hoover, 0.0)  # Perfect equality = 0
        self.assertAlmostEqual(theil, 0.0)  # Perfect equality = 0
        self.assertEqual(nakamoto, 6)  # Need 6 out of 10 holders for 51% control

    def test_nakamoto_coefficient(self):
        """Test Nakamoto coefficient with different thresholds."""
        # Calculate for different thresholds
        nak_33 = calculate_nakamoto_coefficient(self.test_balances, threshold=33.0)
        nak_51 = calculate_nakamoto_coefficient(self.test_balances, threshold=51.0)
        nak_67 = calculate_nakamoto_coefficient(self.test_balances, threshold=67.0)

        # Verify expected values (more concentration = lower Nakamoto coefficient)
        self.assertEqual(nak_33, 1)  # Need 1 holder for 33% control

        # For 51% control, we need to verify that the first holder has more than 51%
        # or that we need 2 holders
        total = sum(self.test_balances)
        top_holder_percentage = (self.test_balances[0] / total) * 100
        if top_holder_percentage > 51.0:
            self.assertEqual(nak_51, 1)  # With our test data, top holder has >51%
        else:
            self.assertEqual(nak_51, 2)  # Need 2 holders for 51% control

        # Similarly for 67% control
        top_two_percentage = (
            (self.test_balances[0] + self.test_balances[1]) / total
        ) * 100
        if top_two_percentage > 67.0:
            self.assertEqual(nak_67, 2)  # With our test data, top 2 holders have >67%
        else:
            self.assertEqual(nak_67, 3)  # Need 3 holders for 67% control

    def test_lorenz_curve(self):
        """Test Lorenz curve calculation."""
        # Calculate Lorenz curve
        lorenz = calculate_lorenz_curve(self.test_balances)

        # Verify structure and properties
        self.assertIn("x", lorenz)
        self.assertIn("y", lorenz)
        self.assertEqual(len(lorenz["x"]), len(lorenz["y"]))
        self.assertEqual(lorenz["x"][0], 0)  # First x value should be 0
        self.assertEqual(lorenz["y"][0], 0)  # First y value should be 0
        self.assertEqual(lorenz["x"][-1], 1)  # Last x value should be 1
        self.assertEqual(lorenz["y"][-1], 1)  # Last y value should be 1

        # Verify that the curve is below the diagonal (inequality)
        for i in range(1, len(lorenz["x"]) - 1):
            self.assertLess(lorenz["y"][i], lorenz["x"][i])

    def test_all_concentration_metrics(self):
        """Test the combined metrics calculation function."""
        # Calculate all metrics
        metrics = calculate_all_concentration_metrics(self.test_balances)

        # Verify all expected metrics are present
        self.assertIn("palma_ratio", metrics)
        self.assertIn("hoover_index", metrics)
        self.assertIn("theil_index", metrics)
        self.assertIn("nakamoto_coefficient", metrics)
        self.assertIn("top_percentile_concentration", metrics)
        self.assertIn("lorenz_curve", metrics)

        # Verify the metrics have reasonable values
        self.assertGreater(metrics["palma_ratio"], 0)
        self.assertGreater(metrics["hoover_index"], 0)
        self.assertGreater(metrics["theil_index"], 0)
        self.assertGreater(metrics["nakamoto_coefficient"], 0)

        # Verify top percentiles
        percentiles = metrics["top_percentile_concentration"]
        self.assertIn("1", percentiles)
        self.assertIn("5", percentiles)
        self.assertIn("10", percentiles)
        self.assertIn("20", percentiles)
        self.assertIn("50", percentiles)


if __name__ == "__main__":
    unittest.main()
