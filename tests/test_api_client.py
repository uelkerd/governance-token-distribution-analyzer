"""Tests for the API Client module.
"""


import pytest

from governance_token_analyzer.core.api_client import APIClient


# Initialize API client with test configuration
@pytest.fixture
def api_client():
    return APIClient()


def test_get_token_holders(api_client):
    """Test fetching token holders for different protocols."""
    # Test Compound token holders
    comp_holders = api_client.get_token_holders("compound", limit=10)
    assert len(comp_holders) == 10
    assert comp_holders[0]["protocol"] == "compound"
    assert "balance" in comp_holders[0]
    assert "address" in comp_holders[0]

    # Test Uniswap token holders
    uni_holders = api_client.get_token_holders("uniswap", limit=10)
    assert len(uni_holders) == 10
    assert uni_holders[0]["protocol"] == "uniswap"

    # Test Aave token holders
    aave_holders = api_client.get_token_holders("aave", limit=10)
    assert len(aave_holders) == 10
    assert aave_holders[0]["protocol"] == "aave"

    # Test with invalid protocol
    with pytest.raises(ValueError):
        api_client.get_token_holders("invalid_protocol")


def test_get_governance_proposals(api_client):
    """Test fetching governance proposals for different protocols."""
    # Test Compound proposals
    comp_proposals = api_client.get_governance_proposals("compound", limit=5)
    assert len(comp_proposals) == 5
    assert comp_proposals[0]["protocol"] == "compound"
    assert "id" in comp_proposals[0]
    assert "title" in comp_proposals[0]
    assert "description" in comp_proposals[0]

    # Test Uniswap proposals
    uni_proposals = api_client.get_governance_proposals("uniswap", limit=5)
    assert len(uni_proposals) == 5
    assert uni_proposals[0]["protocol"] == "uniswap"

    # Test Aave proposals
    aave_proposals = api_client.get_governance_proposals("aave", limit=5)
    assert len(aave_proposals) == 5
    assert aave_proposals[0]["protocol"] == "aave"

    # Test with invalid protocol
    with pytest.raises(ValueError):
        api_client.get_governance_proposals("invalid_protocol")


def test_get_governance_votes(api_client):
    """Test fetching governance votes for different protocols."""
    # Get a proposal ID first
    comp_proposals = api_client.get_governance_proposals("compound", limit=1)
    proposal_id = comp_proposals[0]["id"]

    # Test Compound votes
    comp_votes = api_client.get_governance_votes("compound", proposal_id)
    assert len(comp_votes) > 0
    assert comp_votes[0]["protocol"] == "compound"
    assert "voter" in comp_votes[0]
    assert "vote_choice" in comp_votes[0]
    assert "vote_power" in comp_votes[0]

    # Test with invalid protocol
    with pytest.raises(ValueError):
        api_client.get_governance_votes("invalid_protocol", 1)


def test_get_protocol_data(api_client):
    """Test fetching complete protocol data."""
    # Test Compound data
    comp_data = api_client.get_protocol_data("compound")
    assert comp_data["protocol"] == "compound"
    assert "token_holders" in comp_data
    assert "proposals" in comp_data
    assert "votes" in comp_data
    assert "timestamp" in comp_data

    # Test with invalid protocol
    with pytest.raises(ValueError):
        api_client.get_protocol_data("invalid_protocol")
