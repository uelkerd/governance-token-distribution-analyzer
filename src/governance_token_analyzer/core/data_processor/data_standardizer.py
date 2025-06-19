"""Data Standardizer for Governance Token Distribution Analyzer.

This module provides functionality for standardizing data from different protocols
into a common format for analysis.
"""

import logging
from typing import Any, Dict, List, Union

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


def standardize_holder_data(holder_data: List[Dict[str, Any]], protocol_name: str) -> pd.DataFrame:
    """Standardize token holder data from different protocols into a common DataFrame format.

    Args:
        holder_data: List of token holder data dictionaries from a specific protocol
        protocol_name: Name of the protocol (compound, uniswap, aave, etc.)

    Returns:
        DataFrame with standardized columns: address, balance, percentage, protocol
    """
    logger.info(f"Standardizing holder data for {protocol_name}")
    
    # Handle different protocol data structures
    if protocol_name.lower() == "compound":
        df = _standardize_compound_holders(holder_data)
    elif protocol_name.lower() == "uniswap":
        df = _standardize_uniswap_holders(holder_data)
    elif protocol_name.lower() == "aave":
        df = _standardize_aave_holders(holder_data)
    else:
        raise ValueError(f"Unsupported protocol: {protocol_name}")

    # Add protocol column
    df["protocol"] = protocol_name

    return df


def _standardize_compound_holders(holder_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Standardize Compound token holder data."""
    # Extract required fields
    standardized = []
    for holder in holder_data:
        standardized.append(
            {
                "address": holder.get("address", ""),
                "balance": float(holder.get("balance", 0)),
                "percentage": float(holder.get("percentage", 0)),
            }
        )

    return pd.DataFrame(standardized)


def _standardize_uniswap_holders(holder_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Standardize Uniswap token holder data."""
    # Extract required fields
    standardized = []
    for holder in holder_data:
        standardized.append(
            {
                "address": holder.get("address", ""),
                "balance": float(holder.get("balance", 0)),
                "percentage": float(holder.get("percentage", 0)),
            }
        )

    return pd.DataFrame(standardized)


def _standardize_aave_holders(holder_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Standardize Aave token holder data."""
    # Extract required fields
    standardized = []
    for holder in holder_data:
        standardized.append(
            {
                "address": holder.get("address", ""),
                "balance": float(holder.get("balance", 0)),
                "percentage": float(holder.get("percentage", 0)),
            }
        )

    return pd.DataFrame(standardized)


def combine_protocol_data(protocol_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine data from multiple protocols into a single DataFrame.

    Args:
        protocol_dfs: Dictionary mapping protocol names to their DataFrames

    Returns:
        Combined DataFrame with data from all protocols
    """
    logger.info(f"Combining data from {len(protocol_dfs)} protocols")
    return pd.concat(protocol_dfs.values(), ignore_index=True)


def filter_top_holders(df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """Filter the top N holders by balance from a DataFrame.

    Args:
        df: DataFrame containing holder data
        top_n: Number of top holders to keep

    Returns:
        DataFrame with only the top N holders
    """
    logger.info(f"Filtering top {top_n} holders from {len(df)} records")
    return df.sort_values(by="balance", ascending=False).head(top_n)


def calculate_overlap(df1: pd.DataFrame, df2: pd.DataFrame, column: str = "address") -> Dict[str, Union[int, float]]:
    """Calculate the overlap between two DataFrames based on a specific column.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        column: Column to check for overlap

    Returns:
        Dictionary containing overlap count and percentage
    """
    logger.info(f"Calculating overlap between DataFrames with {len(df1)} and {len(df2)} records")
    
    set1 = set(df1[column].unique())
    set2 = set(df2[column].unique())

    overlap = set1.intersection(set2)

    return {
        "overlap_count": len(overlap),
        "overlap_percentage": len(overlap) / min(len(set1), len(set2)) * 100 if min(len(set1), len(set2)) > 0 else 0,
    } 