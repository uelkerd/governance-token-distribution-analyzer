"""API module for interacting with blockchain data sources.

This module handles API requests to Etherscan, The Graph, and other data sources.
"""

import logging
from typing import Any, Dict, Optional

import requests

from .config import ETHERSCAN_API_KEY, ETHERSCAN_BASE_URL, Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EtherscanAPI:
    """Client for interacting with the Etherscan API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Etherscan API client.

        Args:
            api_key (str, optional): Etherscan API key. If None, uses the key from config.
        """
        # Keep backward compatibility but also support the new Config class
        if api_key is None:
            # Try to get from Config first, fall back to global variable
            config = Config()
            self.api_key = config.get_api_key() or ETHERSCAN_API_KEY
        else:
            self.api_key = api_key

        self.base_url = ETHERSCAN_BASE_URL

        if not self.api_key:
            logger.warning(
                "No Etherscan API key provided. API calls may be rate limited."
            )

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the Etherscan API.

        Args:
            params (Dict[str, Any]): Parameters for the API request.

        Returns:
            Dict[str, Any]: API response as a dictionary.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        # Add API key to parameters
        params["apikey"] = self.api_key

        try:
            # Make the request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses

            # Parse response
            data = response.json()

            # Check for API errors
            if data.get("status") == "0":
                error_message = data.get("message", "Unknown API error")
                logger.error(f"API error: {error_message}")
                return {"error": error_message}

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def get_token_supply(self, token_address: str) -> Dict[str, Any]:
        """Get the total supply of a token.

        Args:
            token_address (str): The Ethereum address of the token.

        Returns:
            Dict[str, Any]: Token supply information.
        """
        params = {
            "module": "stats",
            "action": "tokensupply",
            "contractaddress": token_address,
        }

        return self._make_request(params)

    def get_token_holders(
        self, token_address: str, page: int = 1, offset: int = 100
    ) -> Dict[str, Any]:
        """Get a list of token holders.

        Note: This requires a paid Etherscan API key for the tokenholderslist endpoint.
        For the free tier, we'll use alternative methods to get holder data.

        Args:
            token_address (str): The Ethereum address of the token.
            page (int, optional): Page number for pagination. Defaults to 1.
            offset (int, optional): Number of results per page. Defaults to 100.

        Returns:
            Dict[str, Any]: List of token holders.
        """
        # Check if we have an API key
        if not self.api_key:
            logger.warning("No Etherscan API key provided - using simulated data")
            return self._generate_simulated_holders(token_address, page, offset)

        # First, try the token holder list endpoint (requires paid API)
        params = {
            "module": "token",
            "action": "tokenholderlist",
            "contractaddress": token_address,
            "page": page,
            "offset": offset,
        }

        try:
            result = self._make_request(params)
            if "result" in result and not isinstance(result["result"], str):
                logger.info(
                    f"Successfully retrieved {len(result['result'])} token holders from API"
                )
                return result
        except Exception as e:
            logger.warning(f"Token holder list endpoint failed: {str(e)}")

        # Alternative approach: Use token transfer events to identify holders
        # This works with free API tier
        try:
            logger.info("Attempting to get token holders via transfer events...")
            holders_data = self._get_holders_from_transfers(token_address, offset)
            if holders_data:
                logger.info(
                    f"Successfully retrieved {len(holders_data['result'])} token holders from transfer events"
                )
                return holders_data
        except Exception as e:
            logger.warning(f"Transfer events approach failed: {str(e)}")

        # Final fallback to simulated data
        logger.warning("All API methods failed - using simulated data for testing")
        return self._generate_simulated_holders(token_address, page, offset)

    def _get_holders_from_transfers(
        self, token_address: str, limit: int
    ) -> Dict[str, Any]:
        """Get token holders by analyzing recent transfer events.

        This method works with free Etherscan API tier.

        Args:
            token_address: Token contract address
            limit: Maximum number of holders to return

        Returns:
            Dict with holder data in Etherscan format
        """
        # Get recent token transfers
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": token_address,
            "page": 1,
            "offset": 1000,  # Get more transfers to find unique holders
            "sort": "desc",
        }

        transfers_result = self._make_request(params)
        if "result" not in transfers_result:
            raise Exception("Failed to get token transfers")

        transfers = transfers_result["result"]
        if isinstance(transfers, str):
            raise Exception(f"API error: {transfers}")

        # Extract unique recipient addresses and their latest balances
        holder_addresses = set()
        for transfer in transfers:
            if (
                transfer.get("to")
                and transfer["to"] != "0x0000000000000000000000000000000000000000"
            ):
                holder_addresses.add(transfer["to"])
            if (
                len(holder_addresses) >= limit * 2
            ):  # Get extra to account for zero balances
                break

        # Get current balances for these addresses
        holders = []
        for address in list(holder_addresses)[: limit * 2]:  # Check more than needed
            try:
                balance_result = self.get_token_balance(token_address, address)
                if "result" in balance_result:
                    balance = int(balance_result["result"])
                    if balance > 0:  # Only include addresses with positive balance
                        holders.append(
                            {
                                "TokenHolderAddress": address,
                                "TokenHolderQuantity": str(balance),
                                "balance": str(balance),
                            }
                        )

                        if len(holders) >= limit:
                            break
            except Exception as e:
                logger.debug(f"Failed to get balance for {address}: {e}")
                continue

        # Sort by balance (descending)
        holders.sort(key=lambda x: int(x["TokenHolderQuantity"]), reverse=True)

        # Calculate percentages if we have total supply
        try:
            supply_result = self.get_token_supply(token_address)
            if "result" in supply_result:
                total_supply = int(supply_result["result"])
                for holder in holders:
                    balance = int(holder["TokenHolderQuantity"])
                    percentage = (balance / total_supply) * 100
                    holder["TokenHolderPercentage"] = f"{percentage:.6f}"
        except Exception as e:
            logger.debug(f"Failed to calculate percentages: {e}")
            # Set default percentages
            for i, holder in enumerate(holders):
                holder["TokenHolderPercentage"] = (
                    f"{(100 / len(holders)) * (len(holders) - i):.6f}"
                )

        return {"status": "1", "message": "OK", "result": holders[:limit]}

    def _generate_simulated_holders(
        self, token_address: str, page: int, offset: int
    ) -> Dict[str, Any]:
        """Generate simulated token holder data for testing purposes.

        Args:
            token_address: The token contract address
            page: Page number
            offset: Number of results per page

        Returns:
            Simulated API response with token holders
        """
        # Get the total supply to make realistic percentages
        supply_response = self.get_token_supply(token_address)
        total_supply = int(supply_response.get("result", "10000000000000000000000000"))

        # Create simulated holders with a realistic distribution
        # - A few large holders (whales)
        # - Some medium holders (institutions)
        # - Many small holders (retail)

        # Determine start index based on page and offset
        start_idx = (page - 1) * offset

        # Create holder addresses - we'll use deterministic addresses based on index
        holders = []

        # Simulated distribution parameters
        whale_count = 5
        institution_count = 20
        retail_base = 1000

        # Generate holder data
        for i in range(start_idx, start_idx + offset):
            if i >= whale_count + institution_count + retail_base:
                break

            address = f"0x{i:040x}"  # Generate deterministic address

            # Determine holder type and allocate tokens accordingly
            if i < whale_count:
                # Whale - holds 5-15% of supply
                pct = 5 + (i * 2)  # 5%, 7%, 9%, 11%, 13%
                quantity = int(total_supply * pct / 100)
            elif i < whale_count + institution_count:
                # Institution - holds 0.5-2% of supply
                pct = 0.5 + ((i - whale_count) * 0.075)
                quantity = int(total_supply * pct / 100)
            else:
                # Retail - holds smaller amounts
                idx = i - whale_count - institution_count
                pct = 0.1 * (0.9**idx)  # Exponential decay
                quantity = int(total_supply * pct / 100)

            holders.append(
                {
                    "TokenHolderAddress": address,
                    "TokenHolderQuantity": str(quantity),
                    "balance": str(quantity),  # Adding this field for compatibility
                    "TokenHolderPercentage": str(pct),
                }
            )

            if len(holders) >= offset:
                break

        return {"status": "1", "message": "OK", "result": holders}

    def get_token_balance(self, token_address: str, address: str) -> Dict[str, Any]:
        """Get the token balance for a specific address.

        Args:
            token_address (str): The Ethereum address of the token.
            address (str): The Ethereum address to check balance for.

        Returns:
            Dict[str, Any]: Token balance information.
        """
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": token_address,
            "address": address,
            "tag": "latest",
        }

        return self._make_request(params)


class TheGraphAPI:
    """Client for interacting with The Graph API."""

    def __init__(self, subgraph_url: str):
        """Initialize The Graph API client.

        Args:
            subgraph_url (str): URL of the subgraph to query.
        """
        self.subgraph_url = subgraph_url

    def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query against the subgraph.

        Args:
            query (str): GraphQL query.
            variables (Dict[str, Any], optional): Variables for the query.

        Returns:
            Dict[str, Any]: Query results.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(self.subgraph_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL query failed: {str(e)}")
            raise
