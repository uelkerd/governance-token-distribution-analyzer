"""Advanced Concentration Metrics for Token Distribution Analysis.

This module provides advanced metrics for analyzing token distribution concentration
beyond the basic Gini coefficient and Herfindahl index.
"""

import logging
from typing import Any, Dict, List

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_gini_coefficient(balances: List[float]) -> float:
    """Calculate the Gini coefficient, which measures inequality in token distribution.

    The Gini coefficient ranges from 0 (perfect equality) to 1 (maximum inequality).

    Args:
        balances: List of token balances

    Returns:
        Gini coefficient as a float between 0 and 1

    """
    if not balances or sum(balances) == 0:
        return 0.0

    # Sort balances in ascending order
    sorted_balances = sorted(balances)
    n = len(sorted_balances)

    # Calculate the Gini coefficient using the formula:
    # G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
    total = sum(sorted_balances)
    weighted_sum = sum((i + 1) * balance for i, balance in enumerate(sorted_balances))

    gini = (2 * weighted_sum) / (n * total) - (n + 1) / n

    return max(0.0, min(1.0, gini))  # Ensure result is between 0 and 1


def calculate_herfindahl_index(balances: List[float]) -> float:
    """Calculate the Herfindahl-Hirschman Index (HHI) for token concentration.

    The HHI is the sum of the squares of market shares (percentages).
    Higher values indicate more concentration.

    Args:
        balances: List of token balances

    Returns:
        Herfindahl index as a float

    """
    if not balances or sum(balances) == 0:
        return 0.0

    total = sum(balances)

    # Calculate the sum of squared market shares
    hhi = sum((balance / total) ** 2 for balance in balances)

    return hhi * 10000  # Scale to traditional HHI range (0-10000)


def calculate_palma_ratio(balances: List[float]) -> float:
    """Calculate the Palma ratio, which is the ratio of the share of total income held by the
    top 10% to that held by the bottom 40%.

    In the context of token distribution, this measures the ratio of tokens held by the top 10%
    of holders versus the bottom 40%.

    Args:
        balances: List of token balances sorted in descending order

    Returns:
        Palma ratio as a float

    """
    if not balances or sum(balances) == 0:
        return 0.0

    # Sort balances in descending order to ensure correct calculation
    sorted_balances = sorted(balances, reverse=True)

    total = sum(sorted_balances)

    # Calculate the number of holders representing the top 10% and bottom 40%
    n = len(sorted_balances)
    top_10_count = max(1, int(n * 0.1))
    bottom_40_count = max(1, int(n * 0.4))

    # Calculate share of top 10% and bottom 40%
    top_10_share = sum(sorted_balances[:top_10_count]) / total
    bottom_40_share = sum(sorted_balances[-bottom_40_count:]) / total

    # Avoid division by zero
    if bottom_40_share == 0:
        return float("inf")  # Infinite inequality

    return top_10_share / bottom_40_share


def calculate_hoover_index(balances: List[float]) -> float:
    """Calculate the Hoover index (also known as Robin Hood index), which represents
    the proportion of tokens that would need to be redistributed to achieve perfect equality.

    Args:
        balances: List of token balances

    Returns:
        Hoover index as a float between 0 and 1

    """
    if not balances or sum(balances) == 0:
        return 0.0

    total = sum(balances)
    n = len(balances)

    # Calculate the mean balance
    mean_balance = total / n

    # Calculate the sum of absolute deviations from the mean
    sum_deviations = sum(abs(balance - mean_balance) for balance in balances)

    # The Hoover index is half of the relative mean deviation
    return sum_deviations / (2 * total)


def calculate_theil_index(balances: List[float]) -> float:
    """Calculate the Theil index, which is a measure of economic inequality.
    The Theil index can be decomposed to show inequality within and between different subgroups.

    Args:
        balances: List of token balances

    Returns:
        Theil index as a float (0 = perfect equality, higher values = more inequality)

    """
    if not balances or sum(balances) == 0:
        return 0.0

    n = len(balances)
    total = sum(balances)
    mean = total / n

    # Calculate Theil index
    theil = 0
    for balance in balances:
        if balance <= 0:
            continue  # Skip zero or negative balances

        # Calculate individual contribution to Theil index
        x_i = balance / mean
        theil += (x_i * np.log(x_i)) / n

    return theil


def calculate_nakamoto_coefficient(balances: List[float], threshold: float = 51.0) -> int:
    """Calculate the Nakamoto coefficient, which is the minimum number of entities
    required to achieve a specified threshold of control (usually 51%).

    Args:
        balances: List of token balances in descending order
        threshold: Control threshold percentage (default: 51%)

    Returns:
        Nakamoto coefficient as an integer

    """
    if not balances or sum(balances) == 0:
        return 0

    # Sort balances in descending order to ensure correct calculation
    sorted_balances = sorted(balances, reverse=True)

    total = sum(sorted_balances)
    running_sum = 0

    for i, balance in enumerate(sorted_balances):
        running_sum += balance
        if (running_sum / total * 100) >= threshold:
            return i + 1

    # If the threshold cannot be reached (unlikely in practice)
    return len(sorted_balances)


def calculate_lorenz_curve(balances: List[float]) -> Dict[str, List[float]]:
    """Calculate the Lorenz curve coordinates for token distribution.

    The Lorenz curve plots the cumulative share of tokens (y-axis) against
    the cumulative share of holders (x-axis).

    Args:
        balances: List of token balances

    Returns:
        Dictionary with 'x' and 'y' coordinates for the Lorenz curve

    """
    if not balances or sum(balances) == 0:
        return {"x": [0, 1], "y": [0, 1]}

    # Sort balances in ascending order for Lorenz curve calculation
    sorted_balances = sorted(balances)

    n = len(sorted_balances)
    total = sum(sorted_balances)

    # Initialize with origin point
    x_values = [0]
    y_values = [0]

    # Calculate cumulative percentages
    cum_balance = 0
    for i, balance in enumerate(sorted_balances):
        cum_balance += balance
        x_values.append((i + 1) / n)
        y_values.append(cum_balance / total)

    return {"x": x_values, "y": y_values}


def calculate_top_percentiles(balances: List[float], percentiles: List[int] = None) -> Dict[str, float]:
    """Calculate the percentage of tokens held by the top X% of holders for specified percentiles.

    Args:
        balances: List of token balances
        percentiles: List of percentiles to calculate

    Returns:
        Dictionary mapping percentiles to concentration percentages

    """
    if percentiles is None:
        percentiles = [1, 5, 10, 20, 50]

    if not balances or sum(balances) == 0:
        return {str(p): 0.0 for p in percentiles}

    # Sort balances in descending order
    sorted_balances = sorted(balances, reverse=True)

    total = sum(sorted_balances)
    n = len(sorted_balances)

    result = {}
    for p in percentiles:
        # Calculate the number of holders in the top p%
        holder_count = max(1, int(n * p / 100))

        # Calculate the percentage of tokens held by these holders
        top_p_balance = sum(sorted_balances[:holder_count])
        result[str(p)] = (top_p_balance / total) * 100

    return result


def calculate_all_concentration_metrics(balances: List[float]) -> Dict[str, Any]:
    """Calculate all concentration metrics available in this module.

    Args:
        balances: List of token balances

    Returns:
        Dictionary of concentration metrics

    """
    # Convert to float and ensure positive balances for calculations
    try:
        numeric_balances = []
        for b in balances:
            try:
                # Handle various string formats
                if isinstance(b, str):
                    # Remove common formatting characters
                    clean_balance = b.replace(",", "").replace("$", "").replace(" ", "")
                    if clean_balance:
                        numeric_balances.append(float(clean_balance))
                elif isinstance(b, (int, float)):
                    numeric_balances.append(float(b))
            except (ValueError, TypeError):
                # Skip invalid values
                continue

        positive_balances = [b for b in numeric_balances if b > 0]
    except Exception as e:
        logger.error(f"Error processing balances: {str(e)}")
        positive_balances = []

    if not positive_balances:
        logger.warning("No positive balances provided for concentration metrics calculation")
        return {
            "gini_coefficient": 0,
            "herfindahl_index": 0,
            "palma_ratio": 0,
            "hoover_index": 0,
            "theil_index": 0,
            "nakamoto_coefficient": 0,
            "top_percentile_concentration": {},
            "lorenz_curve": {"x": [0, 1], "y": [0, 1]},
        }

    # Sort balances in descending order for consistent calculations
    sorted_balances = sorted(positive_balances, reverse=True)

    try:
        # Calculate all metrics
        return {
            "gini_coefficient": calculate_gini_coefficient(sorted_balances),
            "herfindahl_index": calculate_herfindahl_index(sorted_balances),
            "palma_ratio": calculate_palma_ratio(sorted_balances),
            "hoover_index": calculate_hoover_index(sorted_balances),
            "theil_index": calculate_theil_index(sorted_balances),
            "nakamoto_coefficient": calculate_nakamoto_coefficient(sorted_balances),
            "top_percentile_concentration": calculate_top_percentiles(sorted_balances),
            "lorenz_curve": calculate_lorenz_curve(sorted_balances),
        }
    except Exception as e:
        logger.error(f"Error calculating concentration metrics: {str(e)}")
        # Return empty metrics in case of calculation error
        return {
            "gini_coefficient": None,
            "herfindahl_index": None,
            "palma_ratio": None,
            "hoover_index": None,
            "theil_index": None,
            "nakamoto_coefficient": None,
            "top_percentile_concentration": {},
            "lorenz_curve": {"x": [0, 1], "y": [0, 1]},
        }
