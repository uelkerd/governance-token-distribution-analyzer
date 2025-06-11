"""
Integration tests for API Client with real API calls.

These tests validate the integration with external APIs. 
They are skipped by default to avoid rate limiting during regular test runs.
"""
import pytest
import os
from governance_token_analyzer.core.api_client import APIClient

# Skip all tests if no API keys are available or if SKIP_INTEGRATION_TESTS is set
skip_tests = (
    os.environ.get('SKIP_INTEGRATION_TESTS', 'true').lower() == 'true' or
    not os.environ.get('ETHERSCAN_API_KEY') or
    not os.environ.get('ETHPLORER_API_KEY')
)

# Initialize API client
@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.skipif(skip_tests, reason="Integration tests skipped")
def test_get_token_holders_real_api(api_client):
    """Test fetching token holders using real API."""
    # Test Compound token holders
    comp_holders = api_client.get_token_holders('compound', limit=5, use_real_data=True)
    assert len(comp_holders) > 0
    assert 'address' in comp_holders[0]
    assert 'balance' in comp_holders[0]
    
    # Test Uniswap token holders
    uni_holders = api_client.get_token_holders('uniswap', limit=5, use_real_data=True)
    assert len(uni_holders) > 0
    assert 'address' in uni_holders[0]
    
    # Test Aave token holders
    aave_holders = api_client.get_token_holders('aave', limit=5, use_real_data=True)
    assert len(aave_holders) > 0
    assert 'address' in aave_holders[0]

@pytest.mark.skipif(skip_tests, reason="Integration tests skipped")
def test_get_governance_proposals_real_api(api_client):
    """Test fetching governance proposals using real API."""
    # Test Compound proposals
    comp_proposals = api_client.get_governance_proposals('compound', limit=3, use_real_data=True)
    assert len(comp_proposals) > 0
    assert 'id' in comp_proposals[0]
    assert 'title' in comp_proposals[0]
    
    # Test Uniswap proposals
    uni_proposals = api_client.get_governance_proposals('uniswap', limit=3, use_real_data=True)
    assert len(uni_proposals) > 0
    assert 'id' in uni_proposals[0]
    
    # Test Aave proposals
    aave_proposals = api_client.get_governance_proposals('aave', limit=3, use_real_data=True)
    assert len(aave_proposals) > 0
    assert 'id' in aave_proposals[0]

@pytest.mark.skipif(skip_tests, reason="Integration tests skipped")
def test_get_governance_votes_real_api(api_client):
    """Test fetching governance votes using real API."""
    # Get a real proposal ID first
    comp_proposals = api_client.get_governance_proposals('compound', limit=1, use_real_data=True)
    if comp_proposals:
        proposal_id = comp_proposals[0]['id']
        
        # Test Compound votes
        comp_votes = api_client.get_governance_votes('compound', proposal_id, use_real_data=True)
        assert len(comp_votes) > 0
        assert 'voter' in comp_votes[0]
        assert 'vote_choice' in comp_votes[0]
        assert 'vote_power' in comp_votes[0]

@pytest.mark.skipif(skip_tests, reason="Integration tests skipped")
def test_error_handling_invalid_api_keys(monkeypatch):
    """Test error handling with invalid API keys."""
    # Temporarily set invalid API keys
    monkeypatch.setenv('ETHERSCAN_API_KEY', 'invalid_key')
    monkeypatch.setenv('ETHPLORER_API_KEY', 'invalid_key')
    
    # Create a new client with the invalid keys
    client = APIClient()
    
    # Should fall back to sample data when API call fails
    holders = client.get_token_holders('compound', limit=5, use_real_data=True)
    assert len(holders) == 5
    assert 'address' in holders[0]
    
    # Reset environment after test
    monkeypatch.undo()

@pytest.mark.skipif(skip_tests, reason="Integration tests skipped")
def test_get_protocol_data_real_api(api_client):
    """Test fetching complete protocol data using real API."""
    # Test Compound data
    comp_data = api_client.get_protocol_data('compound', use_real_data=True)
    assert comp_data['protocol'] == 'compound'
    assert 'token_holders' in comp_data
    assert 'proposals' in comp_data
    assert len(comp_data['token_holders']) > 0
    assert 'participation_rate' in comp_data 