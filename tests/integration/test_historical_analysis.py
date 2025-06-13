import shutil
import tempfile
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from governance_token_analyzer.core import historical_data
from governance_token_analyzer.visualization import historical_charts


class TestHistoricalAnalysisIntegration:
    """Integration tests for historical data analysis functionality."""

    @pytest.fixture
    def temp_data_dir(self):
        """Fixture to create a temporary directory for historical data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def data_manager(self, temp_data_dir):
        """Fixture to create a HistoricalDataManager with a temporary directory."""
        return historical_data.HistoricalDataManager(data_dir=temp_data_dir)

    @pytest.fixture
    def sample_historical_data(self, data_manager):
        """Fixture to generate sample historical data for testing."""
        # Generate sample historical data for compound
        snapshots = historical_data.simulate_historical_data(
            "compound", num_snapshots=6, interval_days=30, data_manager=data_manager
        )

        return {
            "protocol": "compound",
            "snapshots": snapshots,
            "data_manager": data_manager,
        }

    def test_historical_data_storage_and_retrieval(self, sample_historical_data):
        """Test storing and retrieving historical data."""
        protocol = sample_historical_data["protocol"]
        data_manager = sample_historical_data["data_manager"]

        # Get snapshots from the data manager
        retrieved_snapshots = data_manager.get_snapshots(protocol)

        # Verify the number of snapshots
        assert len(retrieved_snapshots) == 6, "Should retrieve 6 snapshots"

        # Verify snapshots are ordered by timestamp
        timestamps = [
            datetime.fromisoformat(s["timestamp"]) for s in retrieved_snapshots
        ]
        assert timestamps == sorted(
            timestamps
        ), "Snapshots should be ordered by timestamp"

    def test_time_series_extraction(self, sample_historical_data):
        """Test extracting time series data from historical snapshots."""
        protocol = sample_historical_data["protocol"]
        data_manager = sample_historical_data["data_manager"]

        # Extract gini coefficient time series
        gini_series = data_manager.get_time_series_data(protocol, "gini_coefficient")

        # Verify the time series
        assert not gini_series.empty, "Time series should not be empty"
        assert (
            "gini_coefficient" in gini_series.columns
        ), "Time series should contain gini_coefficient"

        # Verify the index is a DatetimeIndex
        assert isinstance(
            gini_series.index, pd.DatetimeIndex
        ), "Index should be a DatetimeIndex"

    def test_distribution_change_calculation(self, sample_historical_data):
        """Test calculating changes in token distribution."""
        snapshots = sample_historical_data["snapshots"]

        # Get the first and last snapshots
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]

        # Convert to DataFrames
        first_df = pd.DataFrame(first_snapshot["data"]["token_holders"])
        last_df = pd.DataFrame(last_snapshot["data"]["token_holders"])

        # Calculate distribution changes
        changes = historical_data.calculate_distribution_change(
            first_df, last_df, address_col="address", balance_col="balance"
        )

        # Verify changes DataFrame
        assert not changes.empty, "Changes DataFrame should not be empty"
        assert (
            "absolute_change" in changes.columns
        ), "Changes should include absolute_change column"
        assert (
            "percent_change" in changes.columns
        ), "Changes should include percent_change column"

    def test_concentration_trends_analysis(self, sample_historical_data):
        """Test analyzing token concentration trends."""
        snapshots = sample_historical_data["snapshots"]

        # Analyze concentration trends
        trends = historical_data.analyze_concentration_trends(
            snapshots, top_n_holders=10
        )

        # Verify trends DataFrame
        assert not trends.empty, "Trends DataFrame should not be empty"
        assert (
            "top_10_concentration" in trends.columns
        ), "Trends should include top_10_concentration"
        assert (
            "gini_coefficient" in trends.columns
        ), "Trends should include gini_coefficient"

    def test_governance_participation_trends(self, sample_historical_data):
        """Test analyzing governance participation trends."""
        snapshots = sample_historical_data["snapshots"]

        # Analyze participation trends
        trends = historical_data.analyze_governance_participation_trends(snapshots)

        # Verify trends DataFrame
        assert not trends.empty, "Trends DataFrame should not be empty"
        assert (
            "participation_rate" in trends.columns
        ), "Trends should include participation_rate"

    def test_visualization_integration(self, sample_historical_data):
        """Test that visualization components work with historical data."""
        snapshots = sample_historical_data["snapshots"]
        protocol = sample_historical_data["protocol"]
        data_manager = sample_historical_data["data_manager"]

        # Get time series data
        gini_series = data_manager.get_time_series_data(protocol, "gini_coefficient")

        # Create visualization
        fig = historical_charts.plot_metric_over_time(
            gini_series,
            "gini_coefficient",
            title=f"{protocol.capitalize()} Gini Coefficient Over Time",
        )

        # Verify that a figure was created
        assert isinstance(fig, plt.Figure), "Should return a matplotlib Figure"

        # Verify that the figure has content
        assert len(fig.axes) > 0, "Figure should have at least one axis"
        assert len(fig.axes[0].lines) > 0, "Axis should have at least one line"

        # Close the figure to avoid warnings
        plt.close(fig)

    def test_protocol_comparison_visualization(self, data_manager):
        """Test visualizing data from multiple protocols."""
        # Generate sample historical data for multiple protocols
        for protocol in ["compound", "uniswap", "aave"]:
            historical_data.simulate_historical_data(
                protocol, num_snapshots=6, interval_days=30, data_manager=data_manager
            )

        # Get time series data for all protocols
        protocol_data = {}
        for protocol in ["compound", "uniswap", "aave"]:
            time_series = data_manager.get_time_series_data(
                protocol, "gini_coefficient"
            )
            protocol_data[protocol] = time_series

        # Create comparison visualization
        fig = historical_charts.plot_protocol_comparison_over_time(
            protocol_data,
            "gini_coefficient",
            title="Protocol Comparison: Gini Coefficient",
        )

        # Verify that a figure was created
        assert isinstance(fig, plt.Figure), "Should return a matplotlib Figure"

        # Verify that the figure has content
        assert len(fig.axes) > 0, "Figure should have at least one axis"
        assert (
            len(fig.axes[0].lines) >= 3
        ), "Axis should have at least three lines (one per protocol)"

        # Close the figure to avoid warnings
        plt.close(fig)

    def test_multi_metric_dashboard(self, sample_historical_data):
        """Test creating a multi-metric dashboard."""
        protocol = sample_historical_data["protocol"]
        data_manager = sample_historical_data["data_manager"]

        # Get time series data for multiple metrics
        metrics_data = {
            "gini_coefficient": data_manager.get_time_series_data(
                protocol, "gini_coefficient"
            ),
            "top_10_concentration": data_manager.get_time_series_data(
                protocol, "top_10_concentration"
            ),
        }

        # Create dashboard
        fig = historical_charts.create_multi_metric_dashboard(
            metrics_data,
            metrics=["gini_coefficient", "top_10_concentration"],
            title=f"{protocol.capitalize()} Governance Metrics Dashboard",
        )

        # Verify that a figure was created
        assert isinstance(fig, plt.Figure), "Should return a matplotlib Figure"

        # Verify that the figure has content
        assert (
            len(fig.axes) >= 2
        ), "Figure should have at least two axes (one per metric)"

        # Close the figure to avoid warnings
        plt.close(fig)
