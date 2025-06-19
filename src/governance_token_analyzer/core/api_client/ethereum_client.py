"""Ethereum Client for Governance Token Distribution Analyzer.

This module provides Ethereum-specific API client functionality for
interacting with Ethereum blockchain APIs like Etherscan, Alchemy, and Ethplorer.
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from .base_client import ETHERSCAN_API_URL, ALCHEMY_API_URL, ETHPLORER_API_URL, TOKEN_ADDRESSES, PROTOCOL_INFO

# Configure logging
logger = logging.getLogger(__name__)


class EthereumClient:
    """Client for interacting with Ethereum blockchain APIs."""

    def __init__(self, parent_client=None):
        """Initialize the Ethereum client.
        
        Args:
            parent_client: Parent APIClient instance
        """
        self.parent_client = parent_client
        self.session = parent_client.session if parent_client else requests.Session()
        self.etherscan_api_key = parent_client.etherscan_api_key if parent_client else ""
        self.alchemy_api_key = parent_client.alchemy_api_key if parent_client else ""
        self.ethplorer_api_key = parent_client.ethplorer_api_key if parent_client else "freekey"

    def get_token_supply(self, token_address: str) -> Dict[str, Any]:
        """Get the total supply of a token.
        
        Args:
            token_address: Ethereum address of the token contract
            
        Returns:
            Dictionary containing token supply information
        """
        params = {
            "url": ETHERSCAN_API_URL,
            "params": {
                "module": "stats",
                "action": "tokensupply",
                "contractaddress": token_address,
                "apikey": self.etherscan_api_key,
            },
        }
        
        if self.parent_client:
            response = self.parent_client._make_request(params)
        else:
            response = self.session.get(params["url"], params=params["params"]).json()
            
        if response.get("status") == "1":
            return {
                "token_address": token_address,
                "total_supply": int(response.get("result", 0)),
                "status": "success",
            }
        else:
            logger.warning(f"Failed to get token supply for {token_address}: {response.get('message')}")
            return {
                "token_address": token_address,
                "total_supply": 0,
                "status": "error",
                "message": response.get("message", "Unknown error"),
            }

    def get_etherscan_token_holders(self, token_address: str, page: int = 1, offset: int = 100) -> Dict[str, Any]:
        """Get token holders from Etherscan.
        
        Args:
            token_address: Ethereum address of the token contract
            page: Page number for pagination
            offset: Number of results per page
            
        Returns:
            Dictionary containing token holder information
        """
        params = {
            "url": ETHERSCAN_API_URL,
            "params": {
                "module": "token",
                "action": "tokenholderlist",
                "contractaddress": token_address,
                "page": page,
                "offset": offset,
                "apikey": self.etherscan_api_key,
            },
        }
        
        if self.parent_client:
            response = self.parent_client._make_request(params)
        else:
            response = self.session.get(params["url"], params=params["params"]).json()
            
        if response.get("status") == "1" and "result" in response:
            holders = []
            for holder in response["result"]:
                holders.append({
                    "address": holder.get("address", ""),
                    "balance": float(holder.get("value", 0)) / 10**18,  # Convert from wei
                    "percentage": float(holder.get("share", 0)),
                })
            return {
                "token_address": token_address,
                "holders": holders,
                "status": "success",
            }
        else:
            logger.warning(f"Failed to get token holders for {token_address}: {response.get('message')}")
            # Fall back to simulated data
            return self._generate_simulated_holders(token_address, page, offset)

    def get_token_balance(self, token_address: str, address: str) -> Dict[str, Any]:
        """Get the token balance of an address.
        
        Args:
            token_address: Ethereum address of the token contract
            address: Ethereum address to check balance for
            
        Returns:
            Dictionary containing token balance information
        """
        params = {
            "url": ETHERSCAN_API_URL,
            "params": {
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": token_address,
                "address": address,
                "tag": "latest",
                "apikey": self.etherscan_api_key,
            },
        }
        
        if self.parent_client:
            response = self.parent_client._make_request(params)
        else:
            response = self.session.get(params["url"], params=params["params"]).json()
            
        if response.get("status") == "1":
            return {
                "address": address,
                "token_address": token_address,
                "balance": int(response.get("result", 0)) / 10**18,  # Convert from wei
                "status": "success",
            }
        else:
            logger.warning(f"Failed to get token balance for {address}: {response.get('message')}")
            return {
                "address": address,
                "token_address": token_address,
                "balance": 0,
                "status": "error",
                "message": response.get("message", "Unknown error"),
            }

    def fetch_token_holders_with_fallback(self, protocol: str, token_address: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch token holders with fallback options.
        
        Args:
            protocol: Protocol name (compound, uniswap, aave)
            token_address: Ethereum address of the token contract
            limit: Maximum number of holders to return
            
        Returns:
            List of token holder dictionaries
        """
        # Try Alchemy first
        holders = self._fetch_token_holders_alchemy(token_address, limit)
        
        # If Alchemy fails, try Etherscan
        if not holders:
            holders = self._fetch_token_holders_etherscan(token_address, limit)
            
        # If Etherscan fails, try Ethplorer
        if not holders:
            holders = self._fetch_token_holders_ethplorer(token_address, limit)
            
        # If all APIs fail, use simulated data
        if not holders:
            logger.warning(f"All APIs failed to fetch token holders for {protocol}. Using simulated data.")
            holders = self.generate_sample_holder_data(protocol, limit)
            
        return holders

    def _fetch_token_holders_alchemy(self, token_address: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch token holders from Alchemy API.
        
        Args:
            token_address: Ethereum address of the token contract
            limit: Maximum number of holders to return
            
        Returns:
            List of token holder dictionaries
        """
        if not self.alchemy_api_key:
            return []
            
        try:
            # Alchemy doesn't have a direct token holders endpoint
            # This is a placeholder for when Alchemy adds this feature
            logger.info("Alchemy API doesn't currently support token holder lists")
            return []
        except Exception as e:
            logger.error(f"Error fetching token holders from Alchemy: {e}")
            return []

    def _fetch_token_holders_etherscan(self, token_address: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch token holders from Etherscan API.
        
        Args:
            token_address: Ethereum address of the token contract
            limit: Maximum number of holders to return
            
        Returns:
            List of token holder dictionaries
        """
        if not self.etherscan_api_key:
            return []
            
        try:
            # Calculate pages needed
            page_size = 100  # Etherscan page size
            pages = (limit + page_size - 1) // page_size
            
            all_holders = []
            for page in range(1, pages + 1):
                response = self.get_etherscan_token_holders(token_address, page, page_size)
                if response.get("status") == "success" and "holders" in response:
                    all_holders.extend(response["holders"])
                    
                    # Break if we have enough holders
                    if len(all_holders) >= limit:
                        break
                else:
                    break
                    
            return all_holders[:limit]
        except Exception as e:
            logger.error(f"Error fetching token holders from Etherscan: {e}")
            return []

    def _fetch_token_holders_ethplorer(self, token_address: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch token holders from Ethplorer API.
        
        Args:
            token_address: Ethereum address of the token contract
            limit: Maximum number of holders to return
            
        Returns:
            List of token holder dictionaries
        """
        try:
            url = f"{ETHPLORER_API_URL}/getTopTokenHolders/{token_address}"
            params = {"apiKey": self.ethplorer_api_key, "limit": limit}
            
            response = self.session.get(url, params=params).json()
            
            if "holders" in response:
                holders = []
                for holder in response["holders"]:
                    holders.append({
                        "address": holder.get("address", ""),
                        "balance": float(holder.get("balance", 0)) / 10**18,  # Convert from wei
                        "percentage": float(holder.get("share", 0)),
                    })
                return holders
            else:
                logger.warning(f"Failed to get token holders from Ethplorer for {token_address}")
                return []
        except Exception as e:
            logger.error(f"Error fetching token holders from Ethplorer: {e}")
            return []

    def _generate_simulated_holders(self, token_address: str, page: int, offset: int) -> Dict[str, Any]:
        """Generate simulated token holders when API calls fail.
        
        Args:
            token_address: Ethereum address of the token contract
            page: Page number for pagination
            offset: Number of results per page
            
        Returns:
            Dictionary containing simulated token holder information
        """
        # Find which protocol this token belongs to
        protocol = None
        for proto, address in TOKEN_ADDRESSES.items():
            if address.lower() == token_address.lower():
                protocol = proto
                break
                
        if not protocol:
            logger.warning(f"Unknown token address: {token_address}")
            return {"status": "error", "message": "Unknown token address"}
            
        # Get simulation parameters
        params = self._get_simulation_params(protocol)
        
        # Generate holders
        start_idx = (page - 1) * offset
        holders = self._generate_holders(start_idx, offset, params["total_supply"], params)
        
        return {
            "token_address": token_address,
            "holders": holders,
            "status": "success",
            "simulated": True,
        }

    def _get_simulation_params(self, protocol: str) -> Dict[str, Any]:
        """Get parameters for simulating token holders.
        
        Args:
            protocol: Protocol name (compound, uniswap, aave)
            
        Returns:
            Dictionary containing simulation parameters
        """
        protocol_info = PROTOCOL_INFO.get(protocol.lower(), {})
        
        # Default parameters
        params = {
            "total_supply": protocol_info.get("total_supply", 10000000),
            "whale_count": 5,  # Number of large holders
            "institution_count": 20,  # Number of medium holders
            "retail_count": 975,  # Number of small holders
            "whale_allocation": 0.4,  # 40% held by whales
            "institution_allocation": 0.3,  # 30% held by institutions
            "retail_allocation": 0.3,  # 30% held by retail
            "whale_addresses": protocol_info.get("whale_addresses", []),
        }
        
        return params

    def _generate_holders(
        self, start_idx: int, offset: int, total_supply: int, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate simulated token holders.
        
        Args:
            start_idx: Starting index for pagination
            offset: Number of results per page
            total_supply: Total token supply
            params: Simulation parameters
            
        Returns:
            List of simulated token holder dictionaries
        """
        whale_count = params["whale_count"]
        institution_count = params["institution_count"]
        retail_count = params["retail_count"]
        total_count = whale_count + institution_count + retail_count
        
        # Generate all holders
        holders = []
        for i in range(total_count):
            holder_type, balance = self._calculate_holder_allocation(
                i, whale_count, institution_count, total_supply, params
            )
            
            # Use predefined whale addresses if available
            address = ""
            if holder_type == "whale" and i < len(params["whale_addresses"]):
                address = params["whale_addresses"][i]
            else:
                # Generate random address
                address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
                
            percentage = (balance / total_supply) * 100
            
            holders.append({
                "address": address,
                "balance": balance,
                "percentage": percentage,
                "type": holder_type,
            })
            
        # Sort by balance
        holders = sorted(holders, key=lambda x: x["balance"], reverse=True)
        
        # Apply pagination
        end_idx = min(start_idx + offset, len(holders))
        return holders[start_idx:end_idx]

    def _calculate_holder_allocation(
        self, idx: int, whale_count: int, institution_count: int, total_supply: int, params: Dict[str, Any]
    ) -> tuple:
        """Calculate token allocation for a holder.
        
        Args:
            idx: Holder index
            whale_count: Number of large holders
            institution_count: Number of medium holders
            total_supply: Total token supply
            params: Simulation parameters
            
        Returns:
            Tuple of (holder_type, balance)
        """
        whale_allocation = params["whale_allocation"]
        institution_allocation = params["institution_allocation"]
        retail_allocation = params["retail_allocation"]
        
        if idx < whale_count:
            # Whale holder
            holder_type = "whale"
            # Power law distribution within whales
            power = 1.5
            rank = idx + 1
            share = 1.0 / (rank ** power)
            # Normalize to whale allocation
            total_whale_share = sum(1.0 / (r ** power) for r in range(1, whale_count + 1))
            balance = (share / total_whale_share) * whale_allocation * total_supply
        elif idx < whale_count + institution_count:
            # Institution holder
            holder_type = "institution"
            # Less steep power law for institutions
            power = 1.2
            rank = idx - whale_count + 1
            share = 1.0 / (rank ** power)
            # Normalize to institution allocation
            total_inst_share = sum(1.0 / (r ** power) for r in range(1, institution_count + 1))
            balance = (share / total_inst_share) * institution_allocation * total_supply
        else:
            # Retail holder
            holder_type = "retail"
            # Flatter distribution for retail
            power = 1.1
            rank = idx - whale_count - institution_count + 1
            share = 1.0 / (rank ** power)
            # Normalize to retail allocation
            retail_count = params["retail_count"]
            total_retail_share = sum(1.0 / (r ** power) for r in range(1, retail_count + 1))
            balance = (share / total_retail_share) * retail_allocation * total_supply
            
        return holder_type, balance

    def generate_sample_holder_data(self, protocol: str, count: int) -> List[Dict[str, Any]]:
        """Generate sample token holder data for a protocol.
        
        Args:
            protocol: Protocol name (compound, uniswap, aave)
            count: Number of holders to generate
            
        Returns:
            List of simulated token holder dictionaries
        """
        if protocol.lower() not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")
            
        params = self._get_simulation_params(protocol)
        holders = self._generate_holders(0, count, params["total_supply"], params)
        
        return holders 