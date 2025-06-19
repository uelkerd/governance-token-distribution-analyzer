"""Response Parser for Governance Token Distribution Analyzer.

This module provides utilities for parsing responses from various blockchain APIs
and standardizing them into a consistent format.
"""

import logging
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class ResponseParser:
    """Parser for standardizing API responses."""

    @staticmethod
    def parse_token_holders(response: Dict[str, Any], api_type: str) -> List[Dict[str, Any]]:
        """Parse token holder response from various APIs.
        
        Args:
            response: API response dictionary
            api_type: Type of API (etherscan, ethplorer, alchemy)
            
        Returns:
            Standardized list of token holder dictionaries
        """
        holders = []
        
        try:
            if api_type == "etherscan":
                if "result" in response and isinstance(response["result"], list):
                    for holder in response["result"]:
                        holders.append({
                            "address": holder.get("address", ""),
                            "balance": float(holder.get("value", 0)) / 10**18,  # Convert from wei
                            "percentage": float(holder.get("share", 0)),
                        })
            elif api_type == "ethplorer":
                if "holders" in response and isinstance(response["holders"], list):
                    for holder in response["holders"]:
                        holders.append({
                            "address": holder.get("address", ""),
                            "balance": float(holder.get("balance", 0)) / 10**18,  # Convert from wei
                            "percentage": float(holder.get("share", 0)),
                        })
            elif api_type == "alchemy":
                # Alchemy doesn't currently have a token holders endpoint
                # This is a placeholder for when Alchemy adds this feature
                pass
            else:
                logger.warning(f"Unknown API type: {api_type}")
        except Exception as e:
            logger.error(f"Error parsing token holders from {api_type}: {e}")
            
        return holders

    @staticmethod
    def parse_governance_proposals(response: Dict[str, Any], api_type: str) -> List[Dict[str, Any]]:
        """Parse governance proposal response from various APIs.
        
        Args:
            response: API response dictionary
            api_type: Type of API (graph, compound, uniswap, aave)
            
        Returns:
            Standardized list of governance proposal dictionaries
        """
        proposals = []
        
        try:
            if api_type == "graph":
                if "data" in response and "proposals" in response["data"]:
                    for proposal in response["data"]["proposals"]:
                        # Standardize proposal format
                        standardized = {
                            "id": proposal.get("id", ""),
                            "title": proposal.get("title", ""),
                            "description": proposal.get("description", ""),
                            "proposer": proposal.get("proposer", ""),
                            "forVotes": proposal.get("forVotes", "0"),
                            "againstVotes": proposal.get("againstVotes", "0"),
                            "abstainVotes": proposal.get("abstainVotes", "0"),
                            "canceled": proposal.get("canceled", False),
                            "executed": proposal.get("executed", False),
                            "startBlock": proposal.get("startBlock", "0"),
                            "endBlock": proposal.get("endBlock", "0"),
                            "createdAt": proposal.get("createdAt", "0"),
                        }
                        proposals.append(standardized)
            else:
                logger.warning(f"Unknown API type: {api_type}")
        except Exception as e:
            logger.error(f"Error parsing governance proposals from {api_type}: {e}")
            
        return proposals

    @staticmethod
    def parse_governance_votes(response: Dict[str, Any], api_type: str) -> List[Dict[str, Any]]:
        """Parse governance votes response from various APIs.
        
        Args:
            response: API response dictionary
            api_type: Type of API (graph, compound, uniswap, aave)
            
        Returns:
            Standardized list of governance vote dictionaries
        """
        votes = []
        
        try:
            if api_type == "graph":
                if "data" in response and "votes" in response["data"]:
                    for vote in response["data"]["votes"]:
                        # Standardize vote format
                        standardized = {
                            "id": vote.get("id", ""),
                            "voter": vote.get("voter", ""),
                            "support": vote.get("support", 0),
                            "votingPower": vote.get("votingPower", "0"),
                            "reason": vote.get("reason", ""),
                            "blockNumber": vote.get("blockNumber", "0"),
                            "blockTimestamp": vote.get("blockTimestamp", "0"),
                        }
                        votes.append(standardized)
            else:
                logger.warning(f"Unknown API type: {api_type}")
        except Exception as e:
            logger.error(f"Error parsing governance votes from {api_type}: {e}")
            
        return votes

    @staticmethod
    def parse_token_supply(response: Dict[str, Any], api_type: str) -> int:
        """Parse token supply response from various APIs.
        
        Args:
            response: API response dictionary
            api_type: Type of API (etherscan, ethplorer, alchemy)
            
        Returns:
            Token supply as an integer
        """
        try:
            if api_type == "etherscan":
                if "result" in response:
                    return int(response["result"])
            elif api_type == "ethplorer":
                if "totalSupply" in response:
                    return int(float(response["totalSupply"]))
            elif api_type == "alchemy":
                # Alchemy doesn't currently have a token supply endpoint
                # This is a placeholder for when Alchemy adds this feature
                pass
            else:
                logger.warning(f"Unknown API type: {api_type}")
        except Exception as e:
            logger.error(f"Error parsing token supply from {api_type}: {e}")
            
        return 0

    @staticmethod
    def parse_token_balance(response: Dict[str, Any], api_type: str) -> float:
        """Parse token balance response from various APIs.
        
        Args:
            response: API response dictionary
            api_type: Type of API (etherscan, ethplorer, alchemy)
            
        Returns:
            Token balance as a float
        """
        try:
            if api_type == "etherscan":
                if "result" in response:
                    return float(response["result"]) / 10**18  # Convert from wei
            elif api_type == "ethplorer":
                if "balance" in response:
                    return float(response["balance"]) / 10**18  # Convert from wei
            elif api_type == "alchemy":
                if "result" in response:
                    return float(response["result"]) / 10**18  # Convert from wei
            else:
                logger.warning(f"Unknown API type: {api_type}")
        except Exception as e:
            logger.error(f"Error parsing token balance from {api_type}: {e}")
            
        return 0.0 