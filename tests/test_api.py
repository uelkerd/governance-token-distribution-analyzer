"""Tests for the API module.

These tests validate the API client functionality.
"""

from unittest.mock import MagicMock, patch

from src.analyzer.api import EtherscanAPI, TheGraphAPI


class TestEtherscanAPI:
    """Tests for the EtherscanAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = EtherscanAPI(api_key="test_api_key")
        self.token_address = "0x1234567890123456789012345678901234567890"

    @patch("src.analyzer.api.requests.get")
    def test_get_token_supply(self, mock_get):
        """Test getting token supply."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": "1000000000000000000000000",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call method
        result = self.api.get_token_supply(self.token_address)

        # Assertions
        assert result["result"] == "1000000000000000000000000"
        mock_get.assert_called_once()

        # Check API parameters
        _, kwargs = mock_get.call_args
        params = kwargs["params"]
        assert params["module"] == "stats"
        assert params["action"] == "tokensupply"
        assert params["contractaddress"] == self.token_address

    @patch("src.analyzer.api.requests.get")
    def test_get_token_holders(self, mock_get):
        """Test getting token holders."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": [
                {"TokenHolderAddress": "0xabc", "TokenHolderQuantity": "1000"},
                {"TokenHolderAddress": "0xdef", "TokenHolderQuantity": "500"},
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call method
        result = self.api.get_token_holders(self.token_address, page=1, offset=10)

        # Assertions
        assert len(result["result"]) == 2
        mock_get.assert_called_once()

        # Check API parameters
        _, kwargs = mock_get.call_args
        params = kwargs["params"]
        assert params["module"] == "token"
        assert params["action"] == "tokenholderlist"
        assert params["contractaddress"] == self.token_address
        assert params["page"] == 1
        assert params["offset"] == 10

    @patch("src.analyzer.api.requests.get")
    def test_api_error_handling(self, mock_get):
        """Test error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "0",
            "message": "Error! Invalid API Key",
            "result": None,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call method
        result = self.api.get_token_supply(self.token_address)

        # Assertions
        assert "error" in result
        assert result["error"] == "Error! Invalid API Key"


class TestTheGraphAPI:
    """Tests for the TheGraphAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = TheGraphAPI(
            subgraph_url="https://api.thegraph.com/subgraphs/name/test"
        )

    @patch("src.analyzer.api.requests.post")
    def test_execute_query(self, mock_post):
        """Test executing a GraphQL query."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "tokens": [{"id": "0x1234", "name": "Test Token", "symbol": "TEST"}]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Query and variables
        query = "{ tokens { id name symbol } }"
        variables = {"first": 10}

        # Call method
        result = self.api.execute_query(query, variables)

        # Assertions
        assert "data" in result
        assert "tokens" in result["data"]
        assert result["data"]["tokens"][0]["symbol"] == "TEST"

        # Check API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.thegraph.com/subgraphs/name/test"
        assert kwargs["json"]["query"] == query
        assert kwargs["json"]["variables"] == variables
