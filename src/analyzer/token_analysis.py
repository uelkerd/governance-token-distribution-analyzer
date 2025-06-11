"""
Token Analysis Module for the Governance Token Distribution Analyzer.

This module provides functions to analyze token distribution data,
including concentration metrics and governance participation.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

from .api import EtherscanAPI
from .config import PROTOCOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenDistributionAnalyzer:
    """Analyzes token distribution data for governance tokens."""
    
    def __init__(self, etherscan_api: Optional[EtherscanAPI] = None):
        """
        Initialize the token distribution analyzer.
        
        Args:
            etherscan_api: Optional EtherscanAPI instance. If None, a new instance will be created.
        """
        self.etherscan_api = etherscan_api or EtherscanAPI()
    
    def get_token_holders(self, protocol_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the top token holders for a specific protocol.
        
        Args:
            protocol_key: Key of the protocol in the PROTOCOLS dictionary.
            limit: Maximum number of holders to retrieve.
            
        Returns:
            List of token holders with their addresses and balances.
        """
        protocol = PROTOCOLS.get(protocol_key)
        if not protocol:
            logger.error(f"Protocol '{protocol_key}' not found in configuration")
            return []
        
        token_address = protocol["token_address"]
        logger.info(f"Fetching top {limit} holders for {protocol['name']} ({protocol['symbol']})")
        
        # We may need to make multiple API calls to get all holders up to the limit
        page = 1
        page_size = 100  # Maximum supported by Etherscan API
        holders = []
        
        while len(holders) < limit:
            try:
                # Get the holders for the current page
                response = self.etherscan_api.get_token_holders(
                    token_address=token_address,
                    page=page,
                    offset=min(page_size, limit - len(holders))
                )
                
                if "result" not in response or not response["result"]:
                    logger.warning(f"No more holders found for {protocol['symbol']}")
                    break
                
                # Add the holders to our list
                current_holders = response["result"]
                holders.extend(current_holders)
                
                # Check if we've reached the end of the available holders
                if len(current_holders) < page_size:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching token holders: {str(e)}")
                break
        
        return holders[:limit]
    
    def calculate_concentration_metrics(self, holders: List[Dict[str, Any]], total_supply: str) -> Dict[str, Any]:
        """
        Calculate concentration metrics for token holders.
        
        Args:
            holders: List of token holders with their addresses and balances.
            total_supply: Total token supply as a string (in smallest token units).
            
        Returns:
            Dictionary of concentration metrics.
        """
        if not holders:
            logger.warning("No holders provided for concentration metrics calculation")
            return {
                "top_holders_percentage": {},
                "gini_coefficient": None,
                "herfindahl_index": None
            }
        
        try:
            # Convert total supply to float
            total_supply_float = float(total_supply)
            
            # Convert holder balances to float and calculate percentages
            balances = []
            for holder in holders:
                balance = float(holder.get("TokenHolderQuantity", 0))
                balances.append(balance)
            
            # Sort balances in descending order
            balances.sort(reverse=True)
            
            # Calculate percentages of total supply
            if total_supply_float > 0:
                percentages = [balance / total_supply_float * 100 for balance in balances]
            else:
                logger.warning("Total supply is zero or negative")
                percentages = [0] * len(balances)
            
            # Calculate top holders percentages
            top_holders = {}
            thresholds = [1, 5, 10, 20, 50, 100]
            for threshold in thresholds:
                if threshold <= len(percentages):
                    top_holders[threshold] = sum(percentages[:threshold])
                else:
                    top_holders[threshold] = sum(percentages)
            
            # Calculate Gini coefficient
            gini = self._calculate_gini_coefficient(balances)
            
            # Calculate Herfindahl-Hirschman Index (HHI)
            hhi = self._calculate_herfindahl_index(balances, total_supply_float)
            
            return {
                "top_holders_percentage": top_holders,
                "gini_coefficient": gini,
                "herfindahl_index": hhi
            }
            
        except Exception as e:
            logger.error(f"Error calculating concentration metrics: {str(e)}")
            return {
                "top_holders_percentage": {},
                "gini_coefficient": None,
                "herfindahl_index": None
            }
    
    def _calculate_gini_coefficient(self, balances: List[float]) -> float:
        """
        Calculate the Gini coefficient for token balances.
        
        The Gini coefficient is a measure of inequality where:
        - 0 represents perfect equality (everyone has the same amount)
        - 1 represents perfect inequality (one person has everything)
        
        Args:
            balances: List of token balances.
            
        Returns:
            Gini coefficient as a float between 0 and 1.
        """
        if not balances or sum(balances) == 0:
            return 0
        
        # Sort balances in ascending order
        balances_sorted = sorted(balances)
        n = len(balances_sorted)
        
        # Calculate cumulative sum
        cum_balances = np.cumsum(balances_sorted)
        
        # Calculate Gini coefficient using the formula
        # G = (2 * sum(i * x_i) / (n * sum(x_i))) - (n + 1) / n
        indices = np.arange(1, n + 1)
        return (2 * np.sum(indices * balances_sorted) / (n * np.sum(balances_sorted)) - (n + 1) / n)
    
    def _calculate_herfindahl_index(self, balances: List[float], total_supply: float) -> float:
        """
        Calculate the Herfindahl-Hirschman Index (HHI) for token balances.
        
        HHI is a measure of market concentration, calculated as the sum of 
        squared market shares. Higher values indicate more concentration.
        
        Args:
            balances: List of token balances.
            total_supply: Total token supply.
            
        Returns:
            HHI as a float between 0 and 10000.
        """
        if not balances or total_supply == 0:
            return 0
        
        # Calculate market shares as percentages (0-100)
        market_shares = [(balance / total_supply) * 100 for balance in balances]
        
        # Calculate HHI as sum of squared market shares
        hhi = sum(share ** 2 for share in market_shares)
        
        return hhi

def analyze_compound_token() -> Dict[str, Any]:
    """
    Analyze the Compound (COMP) token distribution as a proof of concept.
    
    Returns:
        Dictionary containing the analysis results.
    """
    logger.info("Starting Compound (COMP) token analysis")
    
    try:
        # Create API client
        etherscan_api = EtherscanAPI()
        
        # Get token info from config
        protocol_key = "compound"
        protocol = PROTOCOLS.get(protocol_key)
        if not protocol:
            logger.error(f"Protocol '{protocol_key}' not found in configuration")
            return {"error": "Protocol not found"}
        
        token_address = protocol["token_address"]
        
        # Get token supply
        supply_response = etherscan_api.get_token_supply(token_address)
        if "result" not in supply_response:
            logger.error(f"Failed to get token supply: {supply_response.get('error', 'Unknown error')}")
            return {"error": "Failed to get token supply"}
        
        total_supply = supply_response["result"]
        
        # Create analyzer and get token holders
        analyzer = TokenDistributionAnalyzer(etherscan_api)
        holders = analyzer.get_token_holders(protocol_key, limit=100)
        
        if not holders:
            logger.error("Failed to get token holders")
            return {"error": "Failed to get token holders"}
        
        # Calculate concentration metrics
        metrics = analyzer.calculate_concentration_metrics(holders, total_supply)
        
        # Format the results
        top_holders = holders[:10]
        formatted_holders = []
        for i, holder in enumerate(top_holders, 1):
            address = holder.get("TokenHolderAddress", "N/A")
            quantity = holder.get("TokenHolderQuantity", "0")
            percentage = float(quantity) / float(total_supply) * 100 if total_supply else 0
            formatted_holders.append({
                "rank": i,
                "address": address,
                "tokens": quantity,
                "percentage": percentage
            })
        
        return {
            "protocol": protocol_key,
            "name": protocol["name"],
            "symbol": protocol["symbol"],
            "token_address": token_address,
            "total_supply": total_supply,
            "top_holders": formatted_holders,
            "concentration_metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error analyzing Compound token: {str(e)}")
        return {"error": str(e)} 