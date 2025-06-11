"""
API module for interacting with blockchain data sources.

This module handles API requests to Etherscan, The Graph, and other data sources.
"""

import requests
from typing import Dict, Any, Optional
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
        
        Args:
            token_address (str): The Ethereum address of the token.
            page (int, optional): Page number for pagination. Defaults to 1.
            offset (int, optional): Number of results per page. Defaults to 100.
            
        Returns:
            Dict[str, Any]: List of token holders.
        """
        params = {
            'module': 'token',
            'action': 'tokenholderlist',
            'contractaddress': token_address,
            'page': page,
            'offset': offset,
        }
        
        return self._make_request(params)
    
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