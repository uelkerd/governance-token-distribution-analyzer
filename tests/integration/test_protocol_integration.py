from typing import Any, Dict

import pandas as pd
import pytest

from governance_token_analyzer.core import data_processor, metrics

# Import protocol modules
from governance_token_analyzer.protocols import aave, compound, uniswap
from governance_token_analyzer.visualization import charts


class TestProtocolIntegration:
    """Integration tests for protocol modules interactions."""

    @pytest.fixture
    def sample_protocol_data(self) -> Dict[str, Dict[str, Any]]:
        """Fixture to generate sample data for all protocols."""
        return {
            "compound": compound.get_sample_data(),
            "uniswap": uniswap.get_sample_data(),
            "aave": aave.get_sample_data(),
        }

    def test_cross_protocol_data_compatibility(self, sample_protocol_data):
        """Test that data from different protocols can be processed together."""
        # Extract holder data from each protocol
        compound_holders = sample_protocol_data['compound']['token_holders']
        uniswap_holders = sample_protocol_data['uniswap']['token_holders']
        aave_holders = sample_protocol_data['aave']['token_holders']

        # Verify each protocol's data structure can be converted to a common format
        compound_df = data_processor.standardize_holder_data(compound_holders, 'compound')
        uniswap_df = data_processor.standardize_holder_data(uniswap_holders, 'uniswap')
        aave_df = data_processor.standardize_holder_data(aave_holders, 'aave')

        # Check that all dataframes have the expected standard columns
        expected_columns = ["address", "balance", "percentage", "protocol"]
        for df, protocol in [
            (compound_df, "compound"),
            (uniswap_df, "uniswap"),
            (aave_df, "aave"),
        ]:
            assert isinstance(df, pd.DataFrame), (
                f"{protocol} data should be converted to DataFrame"
            )
            for col in expected_columns:
                assert col in df.columns, f"{protocol} data missing expected column: {col}"

    def test_cross_protocol_metrics_calculation(self, sample_protocol_data):
        """Test that metrics can be calculated across different protocols."""
        # Process data from each protocol
        protocol_dfs = {}
        for protocol, data in sample_protocol_data.items():
            holders = data['token_holders']
            protocol_dfs[protocol] = data_processor.standardize_holder_data(holders, protocol)

        # Calculate Gini coefficient for each protocol
        gini_results = {}
        for protocol, df in protocol_dfs.items():
            gini_results[protocol] = metrics.calculate_gini_coefficient(df['balance'])

        # Verify results are within expected range (0-1 for Gini coefficient)
        for protocol, gini in gini_results.items():
            assert 0 <= gini <= 1, f"Gini coefficient for {protocol} outside valid range: {gini}"

    def test_protocol_data_to_visualization(self, sample_protocol_data):
        """Test that protocol data can be visualized through the visualization module."""
        # Process data from each protocol
        protocol_dfs = {}
        for protocol, data in sample_protocol_data.items():
            holders = data['token_holders']
            protocol_dfs[protocol] = data_processor.standardize_holder_data(holders, protocol)

        # Generate a comparison chart
        chart = charts.create_distribution_comparison(
            protocol_dfs['compound'],
            protocol_dfs['uniswap'],
            protocol_dfs['aave'],
            title='Top Token Holder Distribution'
        )

        # Verify chart was created successfully
        assert chart is not None, "Visualization chart should be created successfully"

    def test_end_to_end_analysis_flow(self, sample_protocol_data):
        """Test the complete flow from data processing to analysis to visualization."""
        # Process all protocol data
        processed_data = {}
        for protocol, data in sample_protocol_data.items():
            processed_data[protocol] = {
                "holders_df": data_processor.standardize_holder_data(
                    data["token_holders"], protocol
                ),
                "governance_data": data.get("governance_data", {}),
            }

        # Calculate metrics for all protocols
        analysis_results = {}
        for protocol, data in processed_data.items():
            analysis_results[protocol] = {
                "gini": metrics.calculate_gini_coefficient(
                    data["holders_df"]["balance"]
                ),
                "concentration_ratio": metrics.calculate_concentration_ratio(
                    data["holders_df"], 10
                ),
                "participation_rate": metrics.calculate_participation_rate(
                    data["governance_data"].get("votes", []),
                    data["governance_data"].get("total_holders", 1000),
                ),
            }

        # Verify results structure
        for protocol, results in analysis_results.items():
            assert 'gini' in results, f"{protocol} results missing Gini coefficient"
            assert 'concentration_ratio' in results, f"{protocol} results missing concentration ratio"
            assert 'participation_rate' in results, f"{protocol} results missing participation rate"

        # Create comparative visualization
        comparison_chart = charts.create_metrics_comparison(
            analysis_results, "Protocol Governance Comparison"
        )

        assert comparison_chart is not None, "Comparison chart should be created successfully"
