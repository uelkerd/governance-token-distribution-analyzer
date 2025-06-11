"""
Integration tests for historical data analysis.
This is a smaller version of the full test suite that can run quickly.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta

from governance_token_analyzer.core import historical_data
from governance_token_analyzer.protocols import compound


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
        data_manager.store_snapshot('compound', data)
        
        # Retrieve snapshots
        snapshots = data_manager.get_snapshots('compound')
        
        # Verify snapshot was stored
        assert len(snapshots) == 1, "One snapshot should be stored"
        assert 'data' in snapshots[0], "Snapshot should contain data"
        assert 'timestamp' in snapshots[0], "Snapshot should contain timestamp"
    
    def test_simulate_historical_data(self, data_manager):
        """Test simulating historical data."""
        # Simulate historical data
        snapshots = historical_data.simulate_historical_data(
            'compound',
            num_snapshots=3,
            interval_days=7,
            data_manager=data_manager
        )
        
        # Verify snapshots were created
        assert len(snapshots) == 3, "Three snapshots should be created"
        
        # Verify snapshots were stored
        stored_snapshots = data_manager.get_snapshots('compound')
        assert len(stored_snapshots) == 3, "Three snapshots should be stored"
    
    def test_get_time_series_data(self, data_manager):
        """Test extracting time series data."""
        # Simulate historical data
        historical_data.simulate_historical_data(
            'compound',
            num_snapshots=3,
            interval_days=7,
            data_manager=data_manager
        )
        
        # Get time series for gini coefficient
        time_series = data_manager.get_time_series_data('compound', 'gini_coefficient')
        
        # Verify time series
        assert not time_series.empty, "Time series should not be empty"
        assert 'gini_coefficient' in time_series.columns, "Time series should contain gini_coefficient"
        assert len(time_series) == 3, "Time series should have 3 data points" 