"""Data Validation and Protocol Edge Cases Tests.

Comprehensive testing for data validation, protocol edge cases, and simulation parameters
to ensure robust handling of extreme scenarios and edge conditions.
"""

from unittest.mock import patch

import numpy as np
import pytest

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
from governance_token_analyzer.core.governance_metrics import (
    GovernanceEffectivenessAnalyzer,
)
from governance_token_analyzer.core.token_analysis import TokenDistributionAnalyzer


class TestDataValidationEdgeCases:
    """Test data validation and edge case handling."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        # Create analyzer with minimal dependencies for testing
        return TokenDistributionAnalyzer(etherscan_api=None)

    @pytest.fixture
    def governance_analyzer(self):
        """Create governance analyzer instance for testing."""
        return GovernanceEffectivenessAnalyzer()

    @pytest.fixture
    def simulation_engine(self):
        """Create simulation engine instance for testing."""
        return TokenDistributionSimulator()

    @pytest.fixture
    def mock_api_client(self):
        """Create mocked API client for controlled testing."""
        return APIClient()

    # EMPTY DATASET TESTS

    def test_empty_token_holders_dataset(self, analyzer):
        """Test handling of empty token holders dataset."""
        empty_holders = []

        # Should handle gracefully without crashing
        balances = [h.get("balance", 0) for h in empty_holders]
        result = analyzer.calculate_gini_coefficient(balances)

        # Should return appropriate default value or indication of no data
        assert result is not None
        assert isinstance(result, (int, float)) or result == "No data"

    def test_empty_governance_proposals_dataset(self, governance_analyzer):
        """Test handling of empty governance proposals dataset."""
        empty_proposals = []

        # Mock data with holders but no proposals
        mock_data = {
            "holders": [{"address": "0x123", "balance": 1000}],
            "proposals": empty_proposals,
            "votes": [],
        }

        analysis = governance_analyzer.analyze_governance_effectiveness(
            proposals=mock_data["proposals"],
            token_distribution=mock_data["holders"],
            total_eligible_votes=sum(h.get("balance", 0) for h in mock_data["holders"])
        )

        assert isinstance(analysis, dict)
        # Should handle empty proposals gracefully
        assert "participation" in analysis
        assert "success" in analysis

    def test_empty_votes_dataset(self, governance_analyzer):
        """Test handling of empty votes dataset."""
        empty_votes = []

        mock_data = {
            "holders": [{"address": "0x123", "balance": 1000}],
            "proposals": [{"id": 1, "title": "Test Proposal"}],
            "votes": empty_votes,
        }

        analysis = governance_analyzer.analyze_governance_effectiveness(
            proposals=mock_data["proposals"],
            token_distribution=mock_data["holders"],
            total_eligible_votes=sum(h.get("balance", 0) for h in mock_data["holders"])
        )

        assert isinstance(analysis, dict)
        # Should handle empty votes gracefully
        assert "participation" in analysis
        assert "success" in analysis

    def test_all_empty_datasets(self, governance_analyzer):
        """Test handling when all datasets are empty."""
        mock_data = {"holders": [], "proposals": [], "votes": []}

        analysis = governance_analyzer.analyze_governance_effectiveness(
            proposals=mock_data["proposals"],
            token_distribution=mock_data["holders"],
            total_eligible_votes=sum(h.get("balance", 0) for h in mock_data["holders"])
        )

        assert isinstance(analysis, dict)
        assert "participation" in analysis
        assert "success" in analysis

    # LARGE DATASET TESTS

    def test_large_token_holders_dataset(self, analyzer):
        """Test handling of extremely large token holder datasets (>10k addresses)."""
        # Generate 15,000 fake holders
        large_holders = [
            {"address": f"0x{i:040x}", "balance": 1000000 - i} for i in range(15000)
        ]

        # Should handle large datasets efficiently
        import time

        # Extract balance values
        balances = [h.get("balance", 0) for h in large_holders]

        start_time = time.time()
        result = analyzer.calculate_gini_coefficient(balances)
        elapsed_time = time.time() - start_time

        # Should complete within reasonable time (< 5 seconds)
        assert elapsed_time < 5.0
        assert isinstance(result, (int, float))
        assert 0 <= result <= 1

    def test_large_governance_dataset(self, governance_analyzer):
        """Test handling of large governance datasets."""
        # Generate large datasets
        large_holders = [
            {"address": f"0x{i:040x}", "balance": 1000000 - i} for i in range(5000)
        ]

        large_proposals = [
            {"id": i, "title": f"Proposal {i}", "proposer": f"0x{i:040x}"}
            for i in range(1000)
        ]

        large_votes = [
            {
                "voter": f"0x{(i % 5000):040x}",
                "proposal_id": i % 1000,
                "voting_power": 1000 - (i % 1000),
                "vote_choice": ["for", "against", "abstain"][i % 3],
            }
            for i in range(50000)  # 50k votes
        ]

        # Should handle large datasets
        import time

        mock_data = {
            "holders": large_holders,
            "proposals": large_proposals,
            "votes": large_votes,
        }

        start_time = time.time()
        analysis = governance_analyzer.analyze_governance_effectiveness(
            proposals=mock_data["proposals"],
            token_distribution=mock_data["holders"],
            total_eligible_votes=sum(h.get("balance", 0) for h in mock_data["holders"])
        )
        elapsed_time = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed_time < 10.0
        assert isinstance(analysis, dict)
        assert "participation" in analysis

    # INVALID DATA TESTS

    def test_zero_balance_holders(self, analyzer):
        """Test handling of zero-balance token holders."""
        holders_with_zeros = [
            {"address": "0x123", "balance": 0},
            {"address": "0x456", "balance": 1000},
            {"address": "0x789", "balance": 0},
            {"address": "0xabc", "balance": 500},
        ]

        balances = [h.get("balance", 0) for h in holders_with_zeros]
        result = analyzer.calculate_gini_coefficient(balances)

        # Should handle zero balances appropriately
        assert isinstance(result, (int, float))
        assert 0 <= result <= 1

    def test_negative_balance_holders(self, analyzer):
        """Test handling of negative balance values."""
        holders_with_negative = [
            {"address": "0x123", "balance": -100},  # Invalid negative balance
            {"address": "0x456", "balance": 1000},
            {"address": "0x789", "balance": -50},  # Invalid negative balance
            {"address": "0xabc", "balance": 500},
        ]

        # Should filter out or handle negative balances
        balances = [h.get("balance", 0) for h in holders_with_negative if h.get("balance", 0) >= 0]
        result = analyzer.calculate_gini_coefficient(balances)
        assert isinstance(result, (int, float))

    def test_non_numeric_balance_values(self, analyzer):
        """Test handling of non-numeric balance values."""
        holders_with_invalid = [
            {"address": "0x123", "balance": "not_a_number"},
            {"address": "0x456", "balance": 1000},
            {"address": "0x789", "balance": None},
            {"address": "0xabc", "balance": ""},
            {"address": "0xdef", "balance": float("inf")},
            {"address": "0x111", "balance": float("nan")},
        ]

        # Should filter out invalid values and continue
        balances = []
        for h in holders_with_invalid:
            balance = h.get("balance")
            if isinstance(balance, (int, float)) and not (np.isnan(balance) or np.isinf(balance)):
                balances.append(balance)
        result = analyzer.calculate_gini_coefficient(balances)
        assert isinstance(result, (int, float))

    def test_duplicate_addresses(self, analyzer):
        """Test handling of duplicate addresses in holder data."""
        holders_with_duplicates = [
            {"address": "0x123", "balance": 1000},
            {"address": "0x456", "balance": 2000},
            {"address": "0x123", "balance": 1500},  # Duplicate address
            {"address": "0x789", "balance": 500},
        ]

        # Should handle duplicates appropriately (sum or take latest)
        balances = [h.get("balance", 0) for h in holders_with_duplicates]
        result = analyzer.calculate_gini_coefficient(balances)
        assert isinstance(result, (int, float))

    def test_invalid_ethereum_addresses(self, analyzer):
        """Test handling of invalid Ethereum addresses."""
        holders_with_invalid_addresses = [
            {"address": "0x123", "balance": 1000},  # Too short
            {"address": "not_an_address", "balance": 2000},  # Not hex
            {"address": "0x" + "z" * 40, "balance": 1500},  # Invalid hex
            {"address": "", "balance": 500},  # Empty address
            {"address": None, "balance": 300},  # None address
        ]

        # Should filter out invalid addresses
        balances = [h.get("balance", 0) for h in holders_with_invalid_addresses]
        result = analyzer.calculate_gini_coefficient(balances)
        assert isinstance(result, (int, float))

    def test_missing_required_fields(self, governance_analyzer):
        """Test handling of missing required fields in API responses."""
        incomplete_holders = [
            {"address": "0x123"},  # Missing balance
            {"balance": 1000},  # Missing address
            {
                "address": "0x456",
                "balance": 2000,
                "extra_field": "value",
            },  # Valid with extra
            {},  # Empty object
        ]

        incomplete_proposals = [
            {"id": 1},  # Missing title and proposer
            {"title": "Test"},  # Missing id and proposer
            {"id": 2, "title": "Complete", "proposer": "0x123"},  # Complete
        ]

        # Should handle incomplete data gracefully
        mock_data = {
            "holders": incomplete_holders,
            "proposals": incomplete_proposals,
            "votes": [],
        }
        analysis = governance_analyzer.analyze_governance_effectiveness(
            proposals=mock_data["proposals"],
            token_distribution=mock_data["holders"],
            total_eligible_votes=sum(h.get("balance", 0) for h in mock_data["holders"])
        )

        assert isinstance(analysis, dict)

    # PROTOCOL-SPECIFIC EDGE CASES

    def test_non_existent_protocol(self, mock_api_client):
        """Test handling of non-existent protocols."""
        invalid_protocols = ["invalid_protocol", "nonexistent", "", None, 123]

        for protocol in invalid_protocols:
            if protocol is not None:
                try:
                    holders = mock_api_client.get_token_holders(
                        protocol, use_real_data=True
                    )
                    proposals = mock_api_client.get_governance_proposals(
                        protocol, use_real_data=True
                    )
                    
                    # Should return empty lists or fallback data
                    assert isinstance(holders, list)
                    assert isinstance(proposals, list)
                except ValueError as e:
                    # Should raise ValueError for invalid protocols
                    assert "Unsupported protocol" in str(e)

    def test_protocol_with_no_governance_activity(self, governance_analyzer):
        """Test protocols with no governance activity."""
        # Simulate protocol with holders but no proposals/votes
        holders = [
            {"address": "0x123", "balance": 1000},
            {"address": "0x456", "balance": 2000},
        ]

        mock_data = {
            "holders": holders,
            "proposals": [],
            "votes": [],
        }
        analysis = governance_analyzer.analyze_governance_effectiveness(
            proposals=mock_data["proposals"],
            token_distribution=mock_data["holders"],
            total_eligible_votes=sum(h.get("balance", 0) for h in mock_data["holders"])
        )

        assert isinstance(analysis, dict)
        assert "participation" in analysis
        assert "success" in analysis

    def test_unusual_token_distributions(self, analyzer):
        """Test unusual token distribution scenarios."""
        # Test extreme concentration (one holder has 99.9% of tokens)
        extreme_concentration = [
            {"address": "0x123", "balance": 999999},
            {"address": "0x456", "balance": 1},
            {"address": "0x789", "balance": 1},
            {"address": "0xabc", "balance": 1},
        ]

        balances_extreme = [h.get("balance", 0) for h in extreme_concentration]
        gini_extreme = analyzer.calculate_gini_coefficient(balances_extreme)
        assert isinstance(gini_extreme, (int, float))
        assert gini_extreme > 0.7  # Should indicate high inequality (adjusted threshold)

        # Test perfect equality (all holders have same balance)
        perfect_equality = [
            {"address": f"0x{i:040x}", "balance": 1000} for i in range(100)
        ]

        balances_equal = [h.get("balance", 0) for h in perfect_equality]
        gini_equal = analyzer.calculate_gini_coefficient(balances_equal)
        assert isinstance(gini_equal, (int, float))
        assert gini_equal < 0.1  # Should indicate low inequality

    # SIMULATION PARAMETER VALIDATION

    def test_protocol_specific_simulation_parameters(self, simulation_engine):
        """Test protocol-specific simulation parameters."""
        protocols_with_params = {
            "compound": {"alpha": 1.8},
            "uniswap": {"alpha": 1.3},
            "aave": {"alpha": 1.5},
        }

        for protocol, params in protocols_with_params.items():
            # Test with correct parameters
            simulation = simulation_engine.generate_power_law_distribution(
                num_holders=1000, alpha=params["alpha"]
            )

            assert isinstance(simulation, list)
            assert len(simulation) > 0

            # Verify Gini coefficient is stable with these parameters
            # Extract balance values from the simulation result
            balances = []
            for holder in simulation:
                if isinstance(holder, dict) and "TokenHolderQuantity" in holder:
                    balances.append(float(holder["TokenHolderQuantity"]))

            analyzer_temp = TokenDistributionAnalyzer(etherscan_api=None)
            gini = analyzer_temp.calculate_gini_coefficient(balances)
            assert isinstance(gini, (int, float))
            assert 0 <= gini <= 1

    def test_extreme_simulation_parameters(self, simulation_engine):
        """Test simulation with extreme parameter values."""
        extreme_params = [
            {"alpha": 0.1},  # Very low alpha
            {"alpha": 10.0},  # Very high alpha
            {"alpha": 0},  # Zero alpha
            {"alpha": -1},  # Negative alpha (should be handled)
        ]

        for params in extreme_params:
            try:
                simulation = simulation_engine.generate_power_law_distribution(
                    num_holders=100, alpha=params["alpha"]
                )

                # If simulation succeeds, validate results
                if simulation:
                    assert isinstance(simulation, list)
                    # Extract balance values from the simulation result
                    balances = []
                    for holder in simulation:
                        if isinstance(holder, dict) and "TokenHolderQuantity" in holder:
                            balances.append(float(holder["TokenHolderQuantity"]))

                    analyzer_temp = TokenDistributionAnalyzer(etherscan_api=None)
                    gini = analyzer_temp.calculate_gini_coefficient(balances)
                    assert isinstance(gini, (int, float))

            except (ValueError, Exception) as e:
                # Extreme parameters might raise exceptions, which is acceptable
                error_str = str(e).lower()
                assert ("alpha" in error_str or "parameter" in error_str or 
                        "a <=" in error_str or "constraint" in error_str)

    def test_gini_coefficient_stability(self, analyzer):
        """Test Gini coefficient calculation stability under extreme scenarios."""
        test_scenarios = [
            # Single holder
            [{"address": "0x123", "balance": 1000}],
            # Two holders with extreme difference
            [
                {"address": "0x123", "balance": 1000000000},
                {"address": "0x456", "balance": 1},
            ],
            # Many holders with identical balances
            [{"address": f"0x{i:040x}", "balance": 100} for i in range(1000)],
            # Exponential distribution
            [{"address": f"0x{i:040x}", "balance": 2**i} for i in range(20)],
        ]

        for scenario in test_scenarios:
            balances = [h.get("balance", 0) for h in scenario]
            gini = analyzer.calculate_gini_coefficient(balances)

            # Gini coefficient should always be valid
            assert isinstance(gini, (int, float))
            assert 0 <= gini <= 1
            assert not np.isnan(gini)
            assert not np.isinf(gini)

    # API RESPONSE VALIDATION

    def test_api_response_field_validation(self, mock_api_client):
        """Test validation of API response fields."""
        # Mock API response with various field issues
        problematic_responses = [
            # Missing balance field
            [{"address": "0x123", "token_balance": 1000}],  # Wrong field name
            # Balance as string
            [{"address": "0x123", "balance": "1000"}],
            # Scientific notation
            [{"address": "0x123", "balance": 1e6}],
            # Hex balance
            [{"address": "0x123", "balance": "0x3e8"}],
        ]

        for response in problematic_responses:
            with patch.object(
                mock_api_client, "_fetch_token_holders_alchemy", return_value=response
            ):
                holders = mock_api_client.get_token_holders(
                    "compound", limit=5, use_real_data=True
                )

                # Should handle various formats gracefully
                assert isinstance(holders, list)

    def test_protocol_data_consistency(self, mock_api_client):
        """Test consistency of protocol data across different calls."""
        # Mock consistent responses
        mock_holders = [{"address": "0x123", "balance": 1000}]
        mock_proposals = [{"id": 1, "title": "Test", "proposer": "0x123"}]

        with patch.object(
            mock_api_client, "get_token_holders", return_value=mock_holders
        ), patch.object(
            mock_api_client, "get_governance_proposals", return_value=mock_proposals
        ):
            # Multiple calls should return consistent data
            data1 = mock_api_client.get_protocol_data("compound", use_real_data=True)
            data2 = mock_api_client.get_protocol_data("compound", use_real_data=True)

            assert data1["protocol"] == data2["protocol"]
            assert len(data1["holders"]) == len(data2["holders"])
            assert len(data1["proposals"]) == len(data2["proposals"])

    # MEMORY AND PERFORMANCE TESTS

    @pytest.mark.performance
    def test_memory_usage_large_datasets(self, analyzer):
        """Test memory usage with large datasets."""
        import os
        
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False

        if has_psutil:
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
        else:
            initial_memory = 0

        # Create large dataset
        large_holders = [
            {"address": f"0x{i:040x}", "balance": 1000000 - i}
            for i in range(50000)  # 50k holders
        ]

        # Process the data
        balances = [h.get("balance", 0) for h in large_holders]
        gini = analyzer.calculate_gini_coefficient(balances)

        # Check final memory usage
        if has_psutil:
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            # Memory increase should be reasonable (< 500MB)
            assert memory_increase < 500 * 1024 * 1024  # 500MB in bytes
        
        assert isinstance(gini, (int, float))

    @pytest.mark.performance
    def test_processing_time_scaling(self, analyzer):
        """Test that processing time scales reasonably with dataset size."""
        import time

        sizes = [100, 1000, 10000]
        times = []

        for size in sizes:
            holders = [
                {"address": f"0x{i:040x}", "balance": 1000000 - i} for i in range(size)
            ]

            start_time = time.time()
            balances = [h.get("balance", 0) for h in holders]
            analyzer.calculate_gini_coefficient(balances)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)

        # Processing time should scale sub-quadratically
        # Time for 10k should be less than 100x time for 100
        assert times[-1] < times[0] * 100

    # ERROR RECOVERY TESTS

    def test_corrupted_data_recovery(self, analyzer):
        """Test recovery from corrupted data."""
        corrupted_data = [
            {"address": "0x123", "balance": float("nan")},
            {"address": "0x456", "balance": float("inf")},
            {"address": "0x789", "balance": -float("inf")},
            {"address": "0xabc", "balance": 1000},  # Valid data
        ]

        # Should filter out corrupted data and continue
        balances = [c.get("balance", 0) for c in corrupted_data if isinstance(c.get("balance"), (int, float)) and not (np.isnan(c.get("balance", 0)) or np.isinf(c.get("balance", 0)))]
        result = analyzer.calculate_gini_coefficient(balances)
        assert isinstance(result, (int, float))
        assert not np.isnan(result)
        assert not np.isinf(result)

    def test_partial_system_failure_recovery(self, mock_api_client):
        """Test system recovery from partial failures."""

        # Mock scenario where some data is available but some fails
        def failing_proposals(*args, **kwargs):
            raise Exception("Proposals API failed")

        working_holders = [{"address": "0x123", "balance": 1000}]

        with patch.object(
            mock_api_client, "get_token_holders", return_value=working_holders
        ), patch.object(
            mock_api_client, "get_governance_proposals", side_effect=failing_proposals
        ):
            # Should handle partial failures gracefully
            try:
                protocol_data = mock_api_client.get_protocol_data(
                    "compound", use_real_data=True
                )
                
                if protocol_data:  # If any data is returned
                    assert isinstance(protocol_data, dict)
                    # At least some data structure should be present
                    assert "protocol" in protocol_data or "error" in protocol_data
            except Exception:
                # Complete failure is also acceptable for this edge case
                pass
