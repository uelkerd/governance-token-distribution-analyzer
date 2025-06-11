"""
Main entry point for the Governance Token Distribution Analyzer.

This module contains the main function for running the analyzer.
"""

import logging
import sys
from typing import Dict, Any, List

from .config import PROTOCOLS
from .api import EtherscanAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fetch_token_data(protocol_key: str) -> Dict[str, Any]:
    """
    Fetch basic token data for a protocol.
    
    Args:
        protocol_key (str): Key of the protocol in the PROTOCOLS dictionary.
        
    Returns:
        Dict[str, Any]: Token data including supply and other information.
    """
    protocol = PROTOCOLS.get(protocol_key)
    if not protocol:
        logger.error(f"Protocol '{protocol_key}' not found in configuration")
        return {}
    
    logger.info(f"Fetching data for {protocol['name']} ({protocol['symbol']})")
    
    etherscan = EtherscanAPI()
    token_address = protocol["token_address"]
    
    # Get token supply
    try:
        supply_data = etherscan.get_token_supply(token_address)
        logger.info(f"Successfully fetched token supply for {protocol['symbol']}")
        
        # Return combined data
        return {
            "protocol": protocol_key,
            "name": protocol["name"],
            "symbol": protocol["symbol"],
            "token_address": token_address,
            "supply": supply_data.get("result"),
        }
    except Exception as e:
        logger.error(f"Error fetching token data for {protocol['symbol']}: {str(e)}")
        return {
            "protocol": protocol_key,
            "name": protocol["name"],
            "symbol": protocol["symbol"],
            "token_address": token_address,
            "error": str(e)
        }

def analyze_protocols(protocol_keys: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze the specified protocols.
    
    Args:
        protocol_keys (List[str]): List of protocol keys to analyze.
        
    Returns:
        List[Dict[str, Any]]: Analysis results for each protocol.
    """
    results = []
    
    for protocol_key in protocol_keys:
        token_data = fetch_token_data(protocol_key)
        results.append(token_data)
        
    return results

def main():
    """Main function to run the analyzer."""
    logger.info("Starting Governance Token Distribution Analyzer")
    
    # Use all protocols defined in config by default
    protocol_keys = list(PROTOCOLS.keys())
    
    # Analyze protocols
    results = analyze_protocols(protocol_keys)
    
    # Display results
    for result in results:
        protocol_name = result.get("name")
        symbol = result.get("symbol")
        supply = result.get("supply", "Unknown")
        
        if "error" in result:
            logger.warning(f"{protocol_name} ({symbol}): Error fetching data - {result['error']}")
        else:
            logger.info(f"{protocol_name} ({symbol}): Token Supply = {supply}")
    
    logger.info("Analysis complete")
    return results

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1) 