"""
Integration tests for historical data analysis.
This is a smaller version of the full test suite that can run quickly.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from pandas import Timestamp

from governance_token_analyzer.core import historical_data
from governance_token_analyzer.protocols import compound
from governance_token_analyzer.core.exceptions import (
    ProtocolNotSupportedError,
    MetricNotFoundError,
)


class TestHistoricalDataIntegration:
    """Integration tests for historical data functionality."""

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

    def test_store_and_retrieve_snapshot(self, data_manager):
        """Test storing and retrieving a snapshot."""
        # Get sample data
        data = compound.get_sample_data()

        # Store snapshot
        data_manager.store_snapshot("compound", data)

        # Retrieve snapshots
        snapshots = data_manager.get_snapshots("compound")

        # Verify snapshot was stored
        assert len(snapshots) == 1, "One snapshot should be stored"
        assert "data" in snapshots[0], "Snapshot should contain data"
        assert "timestamp" in snapshots[0], "Snapshot should contain timestamp"

    def test_simulate_historical_data(self, data_manager):
        """Test simulating historical data."""
        # Simulate historical data
        snapshots = historical_data.simulate_historical_data(
            "compound", num_snapshots=3, interval_days=7, data_manager=data_manager
        )

        # Verify snapshots were created
        assert len(snapshots) == 3, "Three snapshots should be created"

        # Verify snapshots were stored
        stored_snapshots = data_manager.get_snapshots("compound")
        assert len(stored_snapshots) == 3, "Three snapshots should be stored"

    def test_get_time_series_data(self, data_manager):
        """Test extracting time series data."""
        # Simulate historical data
        historical_data.simulate_historical_data(
            "compound", num_snapshots=3, interval_days=7, data_manager=data_manager
        )

        # Get time series for gini coefficient
        time_series = data_manager.get_time_series_data("compound", "gini_coefficient")

        # Verify time series
        assert not time_series.empty, "Time series should not be empty"
        assert "gini_coefficient" in time_series.columns, (
            "Time series should contain gini_coefficient"
        )
        assert len(time_series) == 3, "Time series should have 3 data points"

    def test_date_range_filtering(self, data_manager):
        """Test filtering snapshots by date range."""
        # Create snapshots with different dates
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)

        data = compound.get_sample_data()

        # Store snapshots with different timestamps
        data_manager.store_snapshot("compound", data, timestamp=last_week)
        data_manager.store_snapshot("compound", data, timestamp=yesterday)
        data_manager.store_snapshot("compound", data, timestamp=today)

        # Get snapshots with date range
        snapshots = data_manager.get_snapshots(
            "compound",
            start_date=yesterday - timedelta(hours=1),
            end_date=today + timedelta(hours=1),
        )

        # Should only return the last two snapshots
        assert len(snapshots) == 2, "Should return exactly 2 snapshots"

        # Get snapshots for only today
        today_snapshots = data_manager.get_snapshots(
            "compound",
            start_date=today - timedelta(hours=1),
            end_date=today + timedelta(hours=1),
        )

        assert len(today_snapshots) == 1, "Should return exactly 1 snapshot"

    def test_nonexistent_protocol(self, data_manager):
        """Test behavior with a nonexistent protocol."""
        # Get snapshots for a protocol that doesn't exist
        snapshots = data_manager.get_snapshots("nonexistent_protocol")

        # Should return an empty list, not raise an exception
        assert snapshots == [], "Should return an empty list for nonexistent protocol"

        # Get time series for a protocol that doesn't exist
        time_series = data_manager.get_time_series_data(
            "nonexistent_protocol", "gini_coefficient"
        )

        # Should return an empty DataFrame, not raise an exception
        assert time_series.empty, (
            "Should return an empty DataFrame for nonexistent protocol"
        )

    def test_nonexistent_metric(self, data_manager):
        """Test behavior with a nonexistent metric."""
        # Simulate historical data
        historical_data.simulate_historical_data(
            "compound", num_snapshots=3, interval_days=7, data_manager=data_manager
        )

        # Get time series for a metric that doesn't exist
        time_series = data_manager.get_time_series_data(
            "compound", "nonexistent_metric"
        )

        # Should return an empty DataFrame with the correct columns
        assert time_series.empty, (
            "Should return an empty DataFrame for nonexistent metric"
        )
        assert "nonexistent_metric" in time_series.columns, (
            "DataFrame should contain the requested metric column"
        )

    def test_calculate_distribution_change(self):
        """Test calculation of distribution changes between snapshots."""
        # Create test data
        old_data = pd.DataFrame(
            {"address": ["0x1", "0x2", "0x3"], "balance": [100, 200, 300]}
        )

        new_data = pd.DataFrame(
            {
                "address": ["0x1", "0x2", "0x4"],  # 0x3 removed, 0x4 added
                "balance": [150, 180, 400],  # 0x1 increased, 0x2 decreased
            }
        )

        # Calculate changes
        changes = historical_data.calculate_distribution_change(old_data, new_data)

        # Verify changes
        assert len(changes) == 4, "Should include all addresses from both datasets"

        # Check specific changes
        addr1_change = changes[changes["address"] == "0x1"].iloc[0]
        assert addr1_change["absolute_change"] == 50, (
            "0x1 balance should increase by 50"
        )
        assert addr1_change["percent_change"] == 50.0, "0x1 should increase by 50%"

        addr2_change = changes[changes["address"] == "0x2"].iloc[0]
        assert addr2_change["absolute_change"] == -20, (
            "0x2 balance should decrease by 20"
        )
        assert addr2_change["percent_change"] == -10.0, "0x2 should decrease by 10%"

        addr3_change = changes[changes["address"] == "0x3"].iloc[0]
        assert addr3_change["absolute_change"] == -300, (
            "0x3 balance should decrease by 300"
        )
        assert addr3_change["percent_change"] == -100.0, "0x3 should decrease by 100%"

        addr4_change = changes[changes["address"] == "0x4"].iloc[0]
        assert addr4_change["absolute_change"] == 400, (
            "0x4 balance should increase by 400"
        )
        assert addr4_change["percent_change"] == float("inf"), (
            "0x4 percent change should be infinity"
        )

    def test_empty_snapshots(self, data_manager):
        """Test behavior with empty snapshots."""
        # Try to analyze concentration trends with empty snapshots
        trends = historical_data.analyze_concentration_trends([])

        # Should return an empty DataFrame
        assert isinstance(trends, pd.DataFrame), "Should return a DataFrame"
        assert trends.empty, "Should return an empty DataFrame for empty snapshots"
