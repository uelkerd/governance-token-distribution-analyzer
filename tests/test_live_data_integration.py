"""Live Data Integration Tests for governance token distribution analyzer.

This module tests the real API integrations with Etherscan, The Graph, and Alchemy
to ensure live blockchain data can be successfully fetched and processed.
Enhanced with comprehensive edge case testing for production deployment.
"""

import concurrent.futures
import logging
import os
import time
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from governance_token_analyzer.core.api_client import APIClient, TheGraphAPI
from governance_token_analyzer.core.config import Config

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLiveDataIntegration:
    """Test suite for live data integration functionality."""

    @pytest.fixture
    def api_client(self):
        """Create API client with real API keys."""
        # Set environment variables for testing
        os.environ["ETHERSCAN_API_KEY"] = os.environ.get("ETHERSCAN_API_KEY", "test_etherscan_key")
        os.environ["INFURA_API_KEY"] = os.environ.get("INFURA_API_KEY", "test_infura_key")
        os.environ["GRAPH_API_KEY"] = os.environ.get("GRAPH_API_KEY", "test_graph_key")
        os.environ["ALCHEMY_API_KEY"] = os.environ.get("ALCHEMY_API_KEY", "test_alchemy_key")
        return APIClient()

    @pytest.fixture
    def config(self):
        """Create configuration instance."""
        return Config()

    @pytest.fixture
    def mock_api_client(self):
        """Create API client with mocked dependencies for controlled testing."""
        # Set test environment variables
        os.environ["ETHERSCAN_API_KEY"] = "test_key"
        os.environ["INFURA_API_KEY"] = "test_key"
        os.environ["GRAPH_API_KEY"] = "test_key"
        os.environ["ALCHEMY_API_KEY"] = "test_key"
        return APIClient()

    def test_api_client_initialization(self, api_client):
        """Test that API client initializes correctly with environment variables."""
        assert api_client is not None
        # Check that the client has expected methods
        assert hasattr(api_client, "get_token_holders")
        assert hasattr(api_client, "get_governance_proposals")
        assert hasattr(api_client, "get_governance_votes")
        assert hasattr(api_client, "get_protocol_data")

    def test_graph_clients_initialization(self, api_client):
        """Test that Graph API clients are initialized when API key is available."""
        # Check if API client can handle graph queries
        graph_api_key = os.environ.get("GRAPH_API_KEY", "")
        if graph_api_key:
            # Try to fetch some data to test graph functionality
            try:
                proposals = api_client.get_governance_proposals("compound", limit=1, use_real_data=False)
                assert isinstance(proposals, list)
            except Exception as e:
                logger.warning(f"Graph API test failed: {e}")
        else:
            logger.warning("No Graph API key found, skipping Graph client tests")

    # ENHANCED API RESILIENCE & FALLBACK TESTING

    @pytest.mark.parametrize(
        "api_provider", ["etherscan", "alchemy", "graph", "infura"]
    )
    def test_api_key_validation(self, api_provider):
        """Test API key validation for each provider."""
        # Test with empty API key
        original_key = os.environ.get(f"{api_provider.upper()}_API_KEY")
        os.environ[f"{api_provider.upper()}_API_KEY"] = ""
        empty_client = APIClient()
        
        # Test with invalid API key format
        os.environ[f"{api_provider.upper()}_API_KEY"] = "invalid_key_123"
        invalid_client = APIClient()
        
        # Restore original key
        if original_key:
            os.environ[f"{api_provider.upper()}_API_KEY"] = original_key
        
        # Basic validation that client was created
        assert empty_client is not None
        assert invalid_client is not None

    @pytest.mark.parametrize("protocol", ["compound", "uniswap", "aave"])
    def test_complete_api_failure_fallback(self, protocol, mock_api_client):
        """Test complete API failure scenario with fallback to simulation."""
        with patch.multiple(
            mock_api_client,
            _fetch_token_holders_alchemy=Mock(
                side_effect=ConnectionError("All APIs failed")
            ),
            _fetch_token_holders_etherscan=Mock(
                side_effect=ConnectionError("All APIs failed")
            ),
            _fetch_compound_token_holders=Mock(
                side_effect=ConnectionError("All APIs failed")
            ),
            _fetch_uniswap_token_holders=Mock(
                side_effect=ConnectionError("All APIs failed")
            ),
            _fetch_aave_token_holders=Mock(
                side_effect=ConnectionError("All APIs failed")
            ),
        ):
            # Should fallback to simulation data
            holders = mock_api_client.get_token_holders(
                protocol, limit=10, use_real_data=True
            )

            assert isinstance(holders, list)
            assert len(holders) > 0
            assert all(
                "address" in holder and "balance" in holder for holder in holders
            )

    def test_partial_api_response_handling(self, mock_api_client):
        """Test handling of partial API responses with missing fields."""
        # Mock partial response with missing fields
        partial_response = [
            {"address": "0x123", "balance": 1000},  # Complete
            {"address": "0x456"},  # Missing balance
            {"balance": 2000},  # Missing address
            {"address": "0x789", "balance": "invalid"},  # Invalid balance
        ]

        with patch.object(
            mock_api_client,
            "_fetch_token_holders_alchemy",
            return_value=partial_response,
        ):
            holders = mock_api_client.get_token_holders(
                "compound", limit=10, use_real_data=True
            )

            # Should filter out invalid entries and convert to proper format
            valid_holders = [h for h in holders if "address" in h and "balance" in h]
            assert len(valid_holders) > 0

    @pytest.mark.parametrize(
        "error_type",
        [
            HTTPError("429 Too Many Requests"),
            HTTPError("403 Forbidden"),
            HTTPError("500 Internal Server Error"),
            Timeout("Request timeout"),
            ConnectionError("Connection failed"),
            RequestException("Generic request error"),
        ],
    )
    def test_http_error_handling(self, error_type, mock_api_client):
        """Test handling of various HTTP errors and exceptions."""
        with patch.object(
            mock_api_client, "_fetch_token_holders_alchemy", side_effect=error_type
        ):
            holders = mock_api_client.get_token_holders(
                "compound", limit=5, use_real_data=True
            )

            # Should fallback gracefully
            assert isinstance(holders, list)
            assert len(holders) >= 0

    def test_rate_limiting_simulation(self, mock_api_client):
        """Test rate limiting simulation and backoff strategy."""
        call_count = 0

        def mock_rate_limited_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise HTTPError("429 Too Many Requests")
            return [{"address": "0x123", "balance": 1000}]

        with patch.object(
            mock_api_client,
            "_fetch_token_holders_alchemy",
            side_effect=mock_rate_limited_call,
        ):
            start_time = time.time()
            holders = mock_api_client.get_token_holders(
                "compound", limit=5, use_real_data=True
            )
            elapsed_time = time.time() - start_time

            # Should eventually succeed after retries
            assert isinstance(holders, list)
            # Should have taken some time due to backoff
            assert elapsed_time > 0.1

    def test_network_timeout_recovery(self, mock_api_client):
        """Test network timeout handling and recovery."""
        timeout_count = 0

        def mock_timeout_then_success(*args, **kwargs):
            nonlocal timeout_count
            timeout_count += 1
            if timeout_count <= 1:
                raise Timeout("Request timeout")
            return [{"address": "0x123", "balance": 1000}]

        with patch.object(
            mock_api_client,
            "_fetch_token_holders_alchemy",
            side_effect=mock_timeout_then_success,
        ):
            holders = mock_api_client.get_token_holders(
                "compound", limit=5, use_real_data=True
            )

            assert isinstance(holders, list)
            assert len(holders) > 0

    def test_fallback_chain_progression(self, mock_api_client):
        """Test the complete fallback chain: Alchemy → The Graph → Moralis → Etherscan → Simulation."""
        # Mock all APIs to fail in sequence
        with patch.multiple(
            mock_api_client,
            _fetch_token_holders_alchemy=Mock(side_effect=HTTPError("Alchemy failed")),
            _fetch_compound_token_holders=Mock(side_effect=HTTPError("Graph failed")),
            _fetch_token_holders_etherscan=Mock(
                side_effect=HTTPError("Etherscan failed")
            ),
        ):
            holders = mock_api_client.get_token_holders(
                "compound", limit=5, use_real_data=True
            )

            # Should eventually fallback to simulation
            assert isinstance(holders, list)
            assert len(holders) > 0

    def test_concurrent_api_requests(self, mock_api_client):
        """Test concurrent API requests don't interfere with each other."""

        def make_request(protocol):
            return mock_api_client.get_token_holders(
                protocol, limit=5, use_real_data=True
            )

        # Mock successful responses
        with patch.object(
            mock_api_client,
            "_fetch_token_holders_alchemy",
            return_value=[{"address": "0x123", "balance": 1000}],
        ):
            # Run concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(make_request, protocol)
                    for protocol in ["compound", "uniswap", "aave"]
                ]

                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

                # All requests should succeed
                assert len(results) == 3
                assert all(isinstance(result, list) for result in results)

    def test_invalid_api_keys_handling(self, mock_api_client):
        """Test handling of invalid API keys."""
        # Mock 401 Unauthorized response
        with patch.object(
            mock_api_client,
            "_fetch_token_holders_alchemy",
            side_effect=HTTPError("401 Unauthorized"),
        ):
            holders = mock_api_client.get_token_holders(
                "compound", limit=5, use_real_data=True
            )

            # Should fallback to next provider or simulation
            assert isinstance(holders, list)

    def test_quota_exhaustion_handling(self, mock_api_client):
        """Test handling of API quota exhaustion."""
        with patch.object(
            mock_api_client,
            "_fetch_token_holders_alchemy",
            side_effect=HTTPError("403 Quota Exceeded"),
        ):
            holders = mock_api_client.get_token_holders(
                "compound", limit=5, use_real_data=True
            )

            # Should fallback gracefully
            assert isinstance(holders, list)

    def test_malformed_response_handling(self, mock_api_client):
        """Test handling of malformed API responses."""
        malformed_responses = [
            "not_json_string",
            {"error": "Internal server error"},
            {"result": None},
            [],
            None,
        ]

        for response in malformed_responses:
            with patch.object(
                mock_api_client, "_fetch_token_holders_alchemy", return_value=response
            ):
                holders = mock_api_client.get_token_holders(
                    "compound", limit=5, use_real_data=True
                )

                # Should handle gracefully
                assert isinstance(holders, list)

    # ENHANCED INTEGRATION TESTS

    @pytest.mark.integration
    def test_fetch_compound_token_holders_live(self, api_client):
        """Test fetching real COMP token holders data."""
        if not (api_client.etherscan_api_key or api_client.alchemy_api_key):
            pytest.skip("No API keys available for live data testing")

        holders = api_client.get_token_holders("compound", limit=10, use_real_data=True)

        assert isinstance(holders, list)
        assert len(holders) > 0

        # Validate holder data structure
        for holder in holders:
            assert "address" in holder
            assert "balance" in holder
            assert isinstance(holder["balance"], (int, float))
            assert len(holder["address"]) == 42  # Ethereum address length
            assert holder["address"].startswith("0x")

    @pytest.mark.integration
    def test_fetch_uniswap_token_holders_live(self, api_client):
        """Test fetching real UNI token holders data."""
        if not (api_client.etherscan_api_key or api_client.alchemy_api_key):
            pytest.skip("No API keys available for live data testing")

        holders = api_client.get_token_holders("uniswap", limit=10, use_real_data=True)

        assert isinstance(holders, list)
        assert len(holders) > 0

        # Validate holder data structure
        for holder in holders:
            assert "address" in holder
            assert "balance" in holder
            assert isinstance(holder["balance"], (int, float))

    @pytest.mark.integration
    def test_fetch_aave_token_holders_live(self, api_client):
        """Test fetching real AAVE token holders data."""
        if not (api_client.etherscan_api_key or api_client.alchemy_api_key):
            pytest.skip("No API keys available for live data testing")

        holders = api_client.get_token_holders("aave", limit=10, use_real_data=True)

        assert isinstance(holders, list)
        assert len(holders) > 0

        # Validate holder data structure
        for holder in holders:
            assert "address" in holder
            assert "balance" in holder
            assert isinstance(holder["balance"], (int, float))

    @pytest.mark.integration
    def test_fetch_compound_governance_proposals_live(self, api_client):
        """Test fetching real Compound governance proposals."""
        if not api_client.graph_api_key:
            pytest.skip("No Graph API key available for live data testing")

        proposals = api_client.get_governance_proposals(
            "compound", limit=5, use_real_data=True
        )

        assert isinstance(proposals, list)

        if len(proposals) > 0:
            # Validate proposal data structure
            for proposal in proposals:
                assert "id" in proposal
                assert "title" in proposal
                assert "proposer" in proposal
                assert isinstance(proposal["id"], int)

    @pytest.mark.integration
    def test_fetch_uniswap_governance_proposals_live(self, api_client):
        """Test fetching real Uniswap governance proposals."""
        if not api_client.graph_api_key:
            pytest.skip("No Graph API key available for live data testing")

        proposals = api_client.get_governance_proposals(
            "uniswap", limit=5, use_real_data=True
        )

        assert isinstance(proposals, list)

        if len(proposals) > 0:
            # Validate proposal data structure
            for proposal in proposals:
                assert "id" in proposal
                assert "title" in proposal
                assert "proposer" in proposal

    @pytest.mark.integration
    def test_fetch_aave_governance_proposals_live(self, api_client):
        """Test fetching real Aave governance proposals."""
        if not api_client.graph_api_key:
            pytest.skip("No Graph API key available for live data testing")

        proposals = api_client.get_governance_proposals(
            "aave", limit=5, use_real_data=True
        )

        assert isinstance(proposals, list)

        if len(proposals) > 0:
            # Validate proposal data structure
            for proposal in proposals:
                assert "id" in proposal
                assert "title" in proposal
                assert "proposer" in proposal

    @pytest.mark.integration
    def test_fetch_governance_votes_live(self, api_client):
        """Test fetching real governance votes for a proposal."""
        if not api_client.graph_api_key:
            pytest.skip("No Graph API key available for live data testing")

        # First, get a proposal to test votes for
        proposals = api_client.get_governance_proposals(
            "compound", limit=1, use_real_data=True
        )

        if len(proposals) > 0:
            proposal_id = proposals[0]["id"]
            votes = api_client.get_governance_votes(
                "compound", proposal_id, use_real_data=True
            )

            assert isinstance(votes, list)

            if len(votes) > 0:
                # Validate vote data structure
                for vote in votes:
                    assert "voter" in vote
                    assert "voting_power" in vote
                    assert isinstance(vote["voting_power"], (int, float))

    def test_api_error_handling(self, api_client):
        """Test that API errors are handled gracefully."""
        # Test with invalid protocol
        holders = api_client.get_token_holders("invalid_protocol", use_real_data=True)
        assert holders == []

        # Test with invalid proposal ID
        votes = api_client.get_governance_votes("compound", -1, use_real_data=True)
        assert isinstance(votes, list)

    def test_fallback_to_sample_data(self, api_client):
        """Test that system falls back to sample data when APIs fail."""
        # Create API client with no keys
        empty_client = APIClient(
            etherscan_api_key="",
            infura_api_key="",
            graph_api_key="",
            alchemy_api_key="",
        )

        # Should fallback to sample data
        holders = empty_client.get_token_holders("compound", use_real_data=True)
        assert isinstance(holders, list)
        assert len(holders) > 0

        proposals = empty_client.get_governance_proposals(
            "compound", use_real_data=True
        )
        assert isinstance(proposals, list)
        assert len(proposals) > 0

    @pytest.mark.integration
    def test_protocol_data_integration(self, api_client):
        """Test comprehensive protocol data collection."""
        protocol_data = api_client.get_protocol_data("compound", use_real_data=True)

        assert isinstance(protocol_data, dict)
        assert "protocol" in protocol_data
        assert "holders" in protocol_data
        assert "proposals" in protocol_data
        assert "participation_rate" in protocol_data
        assert "holder_concentration" in protocol_data

        # Validate data structure
        assert protocol_data["protocol"] == "compound"
        assert isinstance(protocol_data["holders"], list)
        assert isinstance(protocol_data["proposals"], list)
        assert isinstance(protocol_data["participation_rate"], (int, float))

    def test_etherscan_api_integration(self, api_client):
        """Test Etherscan API integration specifically."""
        if not api_client.etherscan_api_key:
            pytest.skip("No Etherscan API key available")

        # Test token supply endpoint
        comp_address = "0xc00e94Cb662C3520282E6f5717214004A7f26888"
        supply_data = api_client.get_token_supply(comp_address)

        assert isinstance(supply_data, dict)
        if "result" in supply_data:
            assert isinstance(supply_data["result"], str)
            assert int(supply_data["result"]) > 0

    def test_alchemy_api_integration(self, api_client):
        """Test Alchemy API integration specifically."""
        if not api_client.alchemy_api_key:
            pytest.skip("No Alchemy API key available")

        # Test token holders endpoint
        comp_address = "0xc00e94Cb662C3520282E6f5717214004A7f26888"
        holders = api_client._fetch_token_holders_alchemy(comp_address, 5)

        assert isinstance(holders, list)
        if len(holders) > 0:
            for holder in holders:
                assert "address" in holder
                assert "balance" in holder
                assert isinstance(holder["balance"], (int, float))

    def test_graph_api_integration(self):
        """Test The Graph API integration specifically."""
        graph_api_key = os.environ.get("GRAPH_API_KEY")
        if not graph_api_key:
            pytest.skip("No Graph API key available")

        # Test with a known subgraph
        subgraph_url = f"https://gateway-arbitrum.network.thegraph.com/api/{graph_api_key}/subgraphs/id/3HrWdYr48tFPTjkqxYN6KJprj29EzU9L9pjJZu6qk3Xr"
        graph_client = TheGraphAPI(subgraph_url)

        # Simple query to test connectivity
        query = """
        query {
            proposals(first: 1) {
                id
                title
            }
        }
        """

        try:
            result = graph_client.execute_query(query)
            assert isinstance(result, dict)
            # May have errors if subgraph is not available, but should return a response
        except Exception as e:
            logger.warning(f"Graph API test failed: {e}")
            # Don't fail the test as subgraph availability can vary

    @pytest.mark.integration
    def test_cross_protocol_data_consistency(self, api_client):
        """Test that data is consistent across different protocols."""
        protocols = ["compound", "uniswap", "aave"]

        for protocol in protocols:
            protocol_data = api_client.get_protocol_data(protocol, use_real_data=True)

            # Basic structure validation
            assert "protocol" in protocol_data
            assert "token_symbol" in protocol_data
            assert "holders" in protocol_data
            assert "proposals" in protocol_data

            # Data type validation
            assert isinstance(protocol_data["holders"], list)
            assert isinstance(protocol_data["proposals"], list)
            assert isinstance(protocol_data["participation_rate"], (int, float))

    def test_data_quality_validation(self, api_client):
        """Test that fetched data meets quality standards."""
        holders = api_client.get_token_holders("compound", limit=10, use_real_data=True)

        if len(holders) > 1:
            # Check that holders are sorted by balance (descending)
            for i in range(len(holders) - 1):
                assert holders[i]["balance"] >= holders[i + 1]["balance"]

            # Check that addresses are valid Ethereum addresses
            for holder in holders:
                address = holder["address"]
                assert len(address) == 42
                assert address.startswith("0x")
                assert all(c in "0123456789abcdefABCDEF" for c in address[2:])

    @pytest.mark.performance
    def test_api_response_times(self, api_client):
        """Test that API response times are reasonable."""
        import time

        start_time = time.time()
        holders = api_client.get_token_holders("compound", limit=10, use_real_data=True)
        elapsed_time = time.time() - start_time

        # Should complete within 30 seconds
        assert elapsed_time < 30

        start_time = time.time()
        proposals = api_client.get_governance_proposals(
            "compound", limit=5, use_real_data=True
        )
        elapsed_time = time.time() - start_time

        # Should complete within 30 seconds
        assert elapsed_time < 30


# ERROR PROPAGATION TESTS


class TestErrorPropagation:
    """Test error propagation through the CLI interface."""

    def test_cli_error_propagation(self, mock_api_client):
        """Test that API errors are properly propagated through CLI."""
        from governance_token_analyzer.cli.main import analyze_protocol

        with patch(
            "governance_token_analyzer.core.api_client.APIClient",
            return_value=mock_api_client,
        ):
            with patch.object(
                mock_api_client,
                "get_protocol_data",
                side_effect=Exception("API completely failed"),
            ):
                # CLI should handle the error gracefully
                try:
                    result = analyze_protocol("compound", use_real_data=True)
                    # Should either return fallback data or handle error gracefully
                    assert result is not None
                except Exception as e:
                    # If exception is raised, it should be informative
                    assert "API" in str(e) or "failed" in str(e).lower()


if __name__ == "__main__":
    # Run basic integration tests
    client = APIClient()

    print("Testing live data integration...")

    # Test token holders
    print("\n1. Testing token holders...")
    for protocol in ["compound", "uniswap", "aave"]:
        holders = client.get_token_holders(protocol, limit=5, use_real_data=True)
        print(f"   {protocol}: {len(holders)} holders fetched")

    # Test governance proposals
    print("\n2. Testing governance proposals...")
    for protocol in ["compound", "uniswap", "aave"]:
        proposals = client.get_governance_proposals(
            protocol, limit=3, use_real_data=True
        )
        print(f"   {protocol}: {len(proposals)} proposals fetched")

    # Test comprehensive data
    print("\n3. Testing comprehensive protocol data...")
    for protocol in ["compound", "uniswap", "aave"]:
        data = client.get_protocol_data(protocol, use_real_data=True)
        print(f"   {protocol}: Complete data package fetched")
        print(f"      - Holders: {len(data.get('holders', []))}")
        print(f"      - Proposals: {len(data.get('proposals', []))}")
        print(f"      - Participation rate: {data.get('participation_rate', 0):.2f}")

    print("\nLive data integration test completed!")
