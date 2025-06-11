"""
Metrics Module for analyzing governance token distributions.
This module provides functions to calculate various metrics for
assessing token distribution and governance effectiveness.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union


def calculate_gini_coefficient(
    balances: Union[List[float], np.ndarray, pd.Series],
) -> float:
    """
    Calculate Gini coefficient to measure inequality in token distribution.

    The Gini coefficient is a measure of statistical dispersion representing
    the income or wealth inequality within a group. A value of 0 expresses
    perfect equality, while a value of 1 expresses maximal inequality.

    Args:
        balances: Array-like of token balances

    Returns:
        Gini coefficient as a float between 0 and 1
    """
    # Convert to numpy array and ensure no negative values
    balances_array = np.array(balances)
    balances_array = np.abs(balances_array)

    # Handle edge cases
    if len(balances_array) <= 1 or np.sum(balances_array) == 0:
        return 0.0

    # Sort balances
    balances_array = np.sort(balances_array)

    # Calculate Gini coefficient
    n = len(balances_array)
    index = np.arange(1, n + 1)
    return ((2 * np.sum(index * balances_array)) / (n * np.sum(balances_array))) - (
        (n + 1) / n
    )


def calculate_concentration_ratio(df: pd.DataFrame, n: int = 10) -> float:
    """
    Calculate the concentration ratio of the top N token holders.

    The concentration ratio is the percentage of total tokens held by the
    top N holders. It's a measure of market concentration.

    Args:
        df: DataFrame containing token holder data with 'balance' column
        n: Number of top holders to consider

    Returns:
        Concentration ratio as a percentage (0-100)
    """
    # Sort by balance in descending order
    sorted_df = df.sort_values(by="balance", ascending=False).reset_index(drop=True)

    # Calculate total balance
    total_balance = sorted_df["balance"].sum()

    # Calculate sum of top N balances
    top_n_balance = sorted_df.head(n)["balance"].sum()

    # Return concentration ratio as percentage
    return (top_n_balance / total_balance * 100) if total_balance > 0 else 0.0


def calculate_participation_rate(
    votes: List[Dict[str, Any]], total_holders: int
) -> float:
    """
    Calculate governance participation rate.

    Participation rate is the percentage of token holders who participated
    in governance voting.

    Args:
        votes: List of vote records
        total_holders: Total number of token holders

    Returns:
        Participation rate as a percentage (0-100)
    """
    if not votes or total_holders <= 0:
        return 0.0

    # Count unique voters
    unique_voters = set(
        vote.get("voter_address") for vote in votes if vote.get("voter_address")
    )

    # Calculate participation rate
    return len(unique_voters) / total_holders * 100


def calculate_vote_distribution(votes: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the distribution of votes (for/against/abstain).

    Args:
        votes: List of vote records with 'vote' field

    Returns:
        Dictionary with percentages for each vote type
    """
    if not votes:
        return {"for": 0.0, "against": 0.0, "abstain": 0.0}

    # Count votes by type
    vote_counts = {"for": 0, "against": 0, "abstain": 0}

    for vote in votes:
        vote_type = vote.get("vote", "").lower()
        if vote_type in vote_counts:
            vote_counts[vote_type] += 1

    # Calculate percentages
    total_votes = sum(vote_counts.values())
    vote_percentages = {
        k: (v / total_votes * 100) if total_votes > 0 else 0.0
        for k, v in vote_counts.items()
    }

    return vote_percentages


def calculate_whale_influence(
    df: pd.DataFrame, threshold_percentage: float = 1.0
) -> Dict[str, Any]:
    """
    Calculate whale influence metrics.

    "Whales" are defined as holders with more than threshold_percentage of the total supply.

    Args:
        df: DataFrame containing token holder data with 'balance' and 'percentage' columns
        threshold_percentage: Percentage threshold to define a whale

    Returns:
        Dictionary with whale metrics
    """
    # Identify whales
    whales = df[df["percentage"] >= threshold_percentage]

    # Calculate metrics
    total_holders = len(df)
    whale_count = len(whales)
    whale_percentage = (whale_count / total_holders * 100) if total_holders > 0 else 0.0
    whale_holdings = whales["balance"].sum()
    total_holdings = df["balance"].sum()
    holdings_percentage = (
        (whale_holdings / total_holdings * 100) if total_holdings > 0 else 0.0
    )

    return {
        "whale_count": whale_count,
        "whale_percentage": whale_percentage,
        "holdings_percentage": holdings_percentage,
    }
