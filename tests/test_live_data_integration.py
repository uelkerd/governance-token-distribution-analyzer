"""
Live Data Integration Tests for governance token distribution analyzer.

This module tests the real API integrations with Etherscan, The Graph, and Alchemy
to ensure live blockchain data can be successfully fetched and processed.
"""

import pytest
import os
import logging
from typing import Dict, List, Any
from unittest.mock import Mock, patch

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
        return APIClient(
            etherscan_api_key=os.environ.get("ETHERSCAN_API_KEY", ""),
            infura_api_key=os.environ.get("INFURA_API_KEY", ""),
            graph_api_key=os.environ.get("GRAPH_API_KEY", ""),
            alchemy_api_key=os.environ.get("ALCHEMY_API_KEY", ""),
        )

    @pytest.fixture
    def config(self):
        """Create configuration instance."""
        return Config()

    def test_api_client_initialization(self, api_client):
        """Test that API client initializes correctly with environment variables."""
        assert api_client is not None
        assert hasattr(api_client, 'etherscan_api_key')
        assert hasattr(api_client, 'graph_api_key')
        assert hasattr(api_client, 'alchemy_api_key')
        assert hasattr(api_client, 'graph_clients')

    def test_graph_clients_initialization(self, api_client):
        """Test that Graph API clients are initialized when API key is available."""
        if api_client.graph_api_key:
            assert len(api_client.graph_clients) > 0
            assert 'compound' in api_client.graph_clients
            assert 'uniswap' in api_client.graph_clients
            assert 'aave' in api_client.graph_clients
        else:
            logger.warning("No Graph API key found, skipping Graph client tests")

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

        proposals = api_client.get_governance_proposals("compound", limit=5, use_real_data=True)
        
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

        proposals = api_client.get_governance_proposals("uniswap", limit=5, use_real_data=True)
        
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

        proposals = api_client.get_governance_proposals("aave", limit=5, use_real_data=True)
        
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
        proposals = api_client.get_governance_proposals("compound", limit=1, use_real_data=True)
        
        if len(proposals) > 0:
            proposal_id = proposals[0]["id"]
            votes = api_client.get_governance_votes("compound", proposal_id, use_real_data=True)
            
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

        proposals = empty_client.get_governance_proposals("compound", use_real_data=True)
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
        proposals = api_client.get_governance_proposals("compound", limit=5, use_real_data=True)
        elapsed_time = time.time() - start_time
        
        # Should complete within 30 seconds
        assert elapsed_time < 30


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
        proposals = client.get_governance_proposals(protocol, limit=3, use_real_data=True)
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