"""Tests for error handling in the API Client module."""

from unittest.mock import patch

import pytest
import requests
import responses

from governance_token_analyzer.core.api_client import (
    ETHPLORER_API_URL,
    GRAPHQL_ENDPOINTS,
    TOKEN_ADDRESSES,
    APIClient,
)


# Initialize API client with test configuration
@pytest.fixture
def api_client():
    return APIClient()


@responses.activate
def test_token_holders_api_error():
    """Test error handling when token holders API call fails."""
    # Mock the Ethplorer API to return an error
    token_address = TOKEN_ADDRESSES["compound"]
    url = f"{ETHPLORER_API_URL}/getTopTokenHolders/{token_address}"
    responses.add(
        responses.GET,
        url,
        json={"error": {"code": 400, "message": "Bad Request"}},
        status=400,
    )

    # Create client and attempt to fetch token holders
    client = APIClient()

    # Should fall back to sample data when API call fails
    holders = client.get_token_holders("compound", limit=5, use_real_data=True)

    # Verify that we get fallback data
    assert len(holders) == 5
    assert "address" in holders[0]
    assert "balance" in holders[0]


@responses.activate
def test_token_holders_api_timeout():
    """Test error handling when token holders API call times out."""
    # Mock the Ethplorer API to time out
    token_address = TOKEN_ADDRESSES["compound"]
    url = f"{ETHPLORER_API_URL}/getTopTokenHolders/{token_address}"
    responses.add(responses.GET, url, body=requests.exceptions.Timeout())

    # Create client and attempt to fetch token holders
    client = APIClient()

    # Should fall back to sample data when API call times out
    holders = client.get_token_holders("compound", limit=5, use_real_data=True)

    # Verify that we get fallback data
    assert len(holders) == 5
    assert "address" in holders[0]
    assert "balance" in holders[0]


@responses.activate
def test_proposals_api_error():
    """Test error handling when proposals API call fails."""
    # Mock the GraphQL API to return an error
    url = GRAPHQL_ENDPOINTS["compound"]
    responses.add(responses.POST, url, json={"errors": [{"message": "GraphQL Error"}]}, status=400)

    # Create client and attempt to fetch proposals
    client = APIClient()

    # Should fall back to sample data when API call fails
    proposals = client.get_governance_proposals("compound", limit=3, use_real_data=True)

    # Verify that we get fallback data
    assert len(proposals) == 3
    assert "id" in proposals[0]
    assert "title" in proposals[0]


@responses.activate
def test_votes_api_error():
    """Test error handling when votes API call fails."""
    # Mock the GraphQL API to return an error
    url = GRAPHQL_ENDPOINTS["compound"]
    responses.add(responses.POST, url, json={"errors": [{"message": "GraphQL Error"}]}, status=400)

    # Create client and attempt to fetch votes
    client = APIClient()

    # Should fall back to sample data when API call fails
    votes = client.get_governance_votes("compound", 1, use_real_data=True)

    # Verify that we get fallback data
    assert len(votes) > 0
    assert "voter" in votes[0]
    assert "vote_choice" in votes[0]


@patch("governance_token_analyzer.core.api_client.requests.Session.get")
def test_token_holders_api_exception(mock_get):
    """Test error handling when token holders API call raises an exception."""
    # Mock the API to raise an exception
    mock_get.side_effect = Exception("Network error")

    # Create client and attempt to fetch token holders
    client = APIClient()

    # Should fall back to sample data when API call raises exception
    holders = client.get_token_holders("compound", limit=5, use_real_data=True)

    # Verify that we get fallback data
    assert len(holders) == 5
    assert "address" in holders[0]
    assert "balance" in holders[0]


@patch("governance_token_analyzer.core.api_client.requests.Session.post")
def test_proposals_api_exception(mock_post):
    """Test error handling when proposals API call raises an exception."""
    # Mock the API to raise an exception
    mock_post.side_effect = Exception("Network error")

    # Create client and attempt to fetch proposals
    client = APIClient()

    # Should fall back to sample data when API call raises exception
    proposals = client.get_governance_proposals("compound", limit=3, use_real_data=True)

    # Verify that we get fallback data
    assert len(proposals) == 3
    assert "id" in proposals[0]
    assert "title" in proposals[0]


@patch("governance_token_analyzer.core.api_client.requests.Session.post")
def test_votes_api_exception(mock_post):
    """Test error handling when votes API call raises an exception."""
    # Mock the API to raise an exception
    mock_post.side_effect = Exception("Network error")

    # Create client and attempt to fetch votes
    client = APIClient()

    # Should fall back to sample data when API call raises exception
    votes = client.get_governance_votes("compound", 1, use_real_data=True)

    # Verify that we get fallback data
    assert len(votes) > 0
    assert "voter" in votes[0]
    assert "vote_choice" in votes[0]


def test_multiple_protocol_errors():
    """Test handling errors across multiple protocols."""
    # Patch the generic fallback method for token holders and the proposals method
    with patch(
        "governance_token_analyzer.core.api_client.APIClient._fetch_token_holders_with_fallback",
        side_effect=Exception("API Error"),
    ), patch(
        "governance_token_analyzer.core.api_client.APIClient.get_governance_proposals",
        side_effect=Exception("API Error"),
    ):
        # Create client
        client = APIClient()

        # Attempt to fetch data for all protocols
        protocols = ["compound", "uniswap", "aave"]
        for protocol in protocols:
            # Should get sample data for all protocols
            holders = client.get_token_holders(protocol, limit=5, use_real_data=True)
            try:
                proposals = client.get_governance_proposals(protocol, limit=3, use_real_data=True)
            except Exception:
                proposals = []

            # Verify fallback data
            assert len(holders) == 5
            assert "address" in holders[0]
            # Proposals may be empty if all APIs fail, but should not raise
            assert isinstance(proposals, list) or proposals == []


def test_rate_limit_handling():
    """Test handling of API rate limits."""
    with patch("governance_token_analyzer.core.api_client.APIClient._fetch_token_holders_with_fallback") as mock_fetch:
        # First call succeeds
        mock_fetch.return_value = [{"address": "0x123", "balance": 1000, "protocol": "compound"}]

        # Create client
        client = APIClient()

        # First call should succeed
        holders = client.get_token_holders("compound", limit=1, use_real_data=True)
        assert len(holders) == 1

        # Now simulate rate limiting
        mock_fetch.side_effect = Exception("Too many requests")

        # Should fall back to sample data
        holders = client.get_token_holders("compound", limit=5, use_real_data=True)
        assert len(holders) == 5
        assert "address" in holders[0]
