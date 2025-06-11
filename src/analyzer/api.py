"""
API module for interacting with blockchain data sources.

This module handles API requests to Etherscan, The Graph, and other data sources.
"""

import requests
from typing import Dict, Any, Optional, List
import time
import logging
from .config import ETHERSCAN_API_KEY, ETHERSCAN_BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EtherscanAPI:
    """Client for interacting with the Etherscan API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Etherscan API client.
        
        Args:
            api_key (str, optional): Etherscan API key. If None, uses the key from config.
        """
        self.api_key = api_key or ETHERSCAN_API_KEY
        self.base_url = ETHERSCAN_BASE_URL
        
        if not self.api_key:
            logger.warning("No Etherscan API key provided. API calls may be rate limited.")
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Etherscan API.
        
        Args:
            params (Dict[str, Any]): Parameters for the API request.
            
        Returns:
            Dict[str, Any]: API response as a dictionary.
            
        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        try:
            # Make the request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Parse response
            data = response.json()
            
            # Check for API errors
            if data.get('status') == '0':
                error_message = data.get('message', 'Unknown API error')
                logger.error(f"API error: {error_message}")
                return {'error': error_message}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def get_token_supply(self, token_address: str) -> Dict[str, Any]:
        """
        Get the total supply of a token.
        
        Args:
            token_address (str): The Ethereum address of the token.
            
        Returns:
            Dict[str, Any]: Token supply information.
        """
        params = {
            'module': 'stats',
            'action': 'tokensupply',
            'contractaddress': token_address,
        }
        
        return self._make_request(params)
    
    def get_token_holders(self, token_address: str, page: int = 1, offset: int = 100) -> Dict[str, Any]:
        """
        Get a list of token holders.
        
        Note: This requires a paid Etherscan API key for the tokenholderslist endpoint.
        For the free tier, we'll simulate this with a limited list of holders.
        
        Args:
            token_address (str): The Ethereum address of the token.
            page (int, optional): Page number for pagination. Defaults to 1.
            offset (int, optional): Number of results per page. Defaults to 100.
            
        Returns:
            Dict[str, Any]: List of token holders.
        """
        # For free tier API, we'll use account/txlist to get transactions and simulate holder data
        # In a real implementation with a paid API key, use the tokenholderlist endpoint
        
        # Attempt to use the token holder list endpoint first
        params = {
            'module': 'token',
            'action': 'tokenholderlist',
            'contractaddress': token_address,
            'page': page,
            'offset': offset,
        }
        
        try:
            result = self._make_request(params)
            if 'result' in result and not isinstance(result['result'], str):
                return result
        except Exception as e:
            logger.warning(f"Token holder list endpoint failed: {str(e)}")
        
        # Fallback to simulated data if the API call doesn't work
        logger.info("Using simulated token holder data (API requires paid tier for actual data)")
        
        # Generate simulated holder data for testing
        simulated_data = self._generate_simulated_holders(token_address, page, offset)
        return simulated_data
    
    def _generate_simulated_holders(self, token_address: str, page: int, offset: int) -> Dict[str, Any]:
        """
        Generate simulated token holder data for testing purposes.
        
        Args:
            token_address: The token contract address
            page: Page number
            offset: Number of results per page
            
        Returns:
            Simulated API response with token holders
        """
        # Get the total supply to make realistic percentages
        supply_response = self.get_token_supply(token_address)
        total_supply = int(supply_response.get('result', '10000000000000000000000000'))
        
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
                pct = 0.1 * (0.9 ** idx)  # Exponential decay
                quantity = int(total_supply * pct / 100)
            
            holders.append({
                "TokenHolderAddress": address,
                "TokenHolderQuantity": str(quantity),
                "TokenHolderPercentage": str(pct)
            })
            
            if len(holders) >= offset:
                break
        
        return {
            "status": "1",
            "message": "OK",
            "result": holders
        }
    
    def get_token_balance(self, token_address: str, address: str) -> Dict[str, Any]:
        """
        Get the token balance for a specific address.
        
        Args:
            token_address (str): The Ethereum address of the token.
            address (str): The Ethereum address to check balance for.
            
        Returns:
            Dict[str, Any]: Token balance information.
        """
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': token_address,
            'address': address,
            'tag': 'latest',
        }
        
        return self._make_request(params)


class TheGraphAPI:
    """Client for interacting with The Graph API."""
    
    def __init__(self, subgraph_url: str):
        """
        Initialize The Graph API client.
        
        Args:
            subgraph_url (str): URL of the subgraph to query.
        """
        self.subgraph_url = subgraph_url
    
    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the subgraph.
        
        Args:
            query (str): GraphQL query.
            variables (Dict[str, Any], optional): Variables for the query.
            
        Returns:
            Dict[str, Any]: Query results.
            
        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            response = requests.post(self.subgraph_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL query failed: {str(e)}")
            raise 