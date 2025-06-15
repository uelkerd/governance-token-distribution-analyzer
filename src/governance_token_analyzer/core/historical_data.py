"""Historical Data Analysis Module for tracking token distribution changes over time.
This module provides functionality to collect, process, and analyze historical
token distribution and governance participation data.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from governance_token_analyzer.core.exceptions import (
    DataAccessError,
    DataFormatError,
    DataStorageError,
    HistoricalDataError,
    MetricNotFoundError,
    ProtocolNotSupportedError,
)

# Configure logging
logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Manages the collection, storage, and retrieval of historical token distribution data."""

    # Supported protocols - can be extended as more protocols are added
    SUPPORTED_PROTOCOLS = {"compound", "uniswap", "aave"}

    def __init__(self, data_dir: str = "data/historical"):
        """Initialize the historical data manager.

        Args:
            data_dir: Directory where historical data will be stored

        Raises:
            DataStorageError: If there's an issue creating the data directory

        """
        self.data_dir = data_dir
        try:
            self._ensure_data_dir_exists()
        except OSError as e:
            logger.error(f"Failed to create data directory: {e}")
            raise DataStorageError(f"Failed to create data directory: {e}") from e

    def _ensure_data_dir_exists(self) -> None:
        """Create data directory if it doesn't exist.

        Raises:
            OSError: If there's an issue creating the directory

        """
        os.makedirs(self.data_dir, exist_ok=True)
        for protocol in self.SUPPORTED_PROTOCOLS:
            os.makedirs(os.path.join(self.data_dir, protocol), exist_ok=True)

    def _validate_protocol(self, protocol: str) -> None:
        """Validate that the protocol is supported.

        Args:
            protocol: Name of the protocol to validate

        Raises:
            ProtocolNotSupportedError: If the protocol is not supported

        """
        if protocol not in self.SUPPORTED_PROTOCOLS:
            logger.warning(f"Unsupported protocol requested: {protocol}")
            raise ProtocolNotSupportedError(protocol, supported_protocols=list(self.SUPPORTED_PROTOCOLS))

    def store_snapshot(self, protocol: str, data: Dict[str, Any], timestamp: Optional[datetime] = None) -> None:
        """Store a snapshot of token distribution data.

        Args:
            protocol: Name of the protocol (e.g., 'compound', 'uniswap', 'aave')
            data: Token distribution data to store
            timestamp: Timestamp for the snapshot (defaults to current time)

        Raises:
            ProtocolNotSupportedError: If the protocol is not supported
            DataStorageError: If there's an issue storing the data
            DataFormatError: If the data is not in the expected format

        """
        self._validate_protocol(protocol)

        if not isinstance(data, dict):
            logger.error(f"Invalid data format: expected dict, got {type(data)}")
            raise DataFormatError(f"Invalid data format: expected dict, got {type(data)}")

        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                logger.error(f"Invalid timestamp format: {timestamp}")
                raise DataFormatError(f"Invalid timestamp format: {timestamp}")

        # Format timestamp for filename
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

        # Create filename and path
        filename = f"{protocol}_snapshot_{timestamp_str}.json"
        filepath = os.path.join(self.data_dir, protocol, filename)

        # Add timestamp to data
        data_with_timestamp = {"timestamp": timestamp.isoformat(), "data": data}

        # Save data to file
        try:
            with open(filepath, "w") as f:
                json.dump(data_with_timestamp, f, indent=2)
            logger.info(f"Stored snapshot for {protocol} at {timestamp_str}")
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to store snapshot for {protocol}: {e}")
            raise DataStorageError(f"Failed to store snapshot for {protocol}: {e}") from e

    def get_snapshots(
        self,
        protocol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical snapshots for a specific protocol.

        Args:
            protocol: Name of the protocol
            start_date: Start date for filtering snapshots
            end_date: End date for filtering snapshots

        Returns:
            List of snapshots ordered by timestamp

        Raises:
            ProtocolNotSupportedError: If the protocol is not supported
            DataAccessError: If there's an issue accessing the data

        """
        self._validate_protocol(protocol)

        protocol_dir = os.path.join(self.data_dir, protocol)

        if not os.path.exists(protocol_dir):
            logger.warning(f"Data directory for {protocol} does not exist")
            return []

        snapshots = []

        try:
            for filename in os.listdir(protocol_dir):
                if not filename.endswith(".json"):
                    continue

                filepath = os.path.join(protocol_dir, filename)

                try:
                    with open(filepath) as f:
                        snapshot = json.load(f)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON in {filepath}: {e}")
                    continue

                # Validate snapshot format
                if "timestamp" not in snapshot or "data" not in snapshot:
                    logger.warning(f"Invalid snapshot format in {filepath}")
                    continue

                # Parse timestamp
                try:
                    snapshot_time = datetime.fromisoformat(snapshot["timestamp"])
                except ValueError as e:
                    logger.warning(f"Invalid timestamp in {filepath}: {e}")
                    continue

                # Filter by date range if specified
                if (start_date and snapshot_time < start_date) or (end_date and snapshot_time > end_date):
                    continue

                snapshots.append(snapshot)

            # Sort by timestamp
            snapshots.sort(key=lambda x: x["timestamp"])

            logger.info(f"Retrieved {len(snapshots)} snapshots for {protocol}")
            return snapshots

        except OSError as e:
            logger.error(f"Failed to access snapshots for {protocol}: {e}")
            raise DataAccessError(f"Failed to access snapshots for {protocol}: {e}") from e

    def get_time_series_data(
        self,
        protocol: str,
        metric: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Extract a time series for a specific metric from historical snapshots.

        Args:
            protocol: Name of the protocol
            metric: Name of the metric to extract (e.g., 'gini_coefficient')
            start_date: Start date for filtering snapshots
            end_date: End date for filtering snapshots

        Returns:
            DataFrame with timestamp and metric values

        Raises:
            ProtocolNotSupportedError: If the protocol is not supported
            DataAccessError: If there's an issue accessing the data
            MetricNotFoundError: If the metric is not found in any snapshot

        """
        self._validate_protocol(protocol)

        try:
            snapshots = self.get_snapshots(protocol, start_date, end_date)

            if not snapshots:
                logger.info(f"No snapshots found for {protocol}")
                return pd.DataFrame(columns=["timestamp", metric])

            # Extract timestamps and metric values
            data = []
            available_metrics = set()

            for snapshot in snapshots:
                timestamp = datetime.fromisoformat(snapshot["timestamp"])

                # Track available metrics for error reporting
                if isinstance(snapshot["data"], dict):
                    available_metrics.update(snapshot["data"].keys())
                    if "metrics" in snapshot["data"] and isinstance(snapshot["data"]["metrics"], dict):
                        available_metrics.update(snapshot["data"]["metrics"].keys())

                # Navigate nested dictionaries if necessary
                value = None
                if metric in snapshot["data"]:
                    value = snapshot["data"][metric]
                elif "metrics" in snapshot["data"] and metric in snapshot["data"]["metrics"]:
                    value = snapshot["data"]["metrics"][metric]

                if value is not None:
                    data.append({"timestamp": timestamp, metric: value})

            # Check if we found any data points
            if not data:
                logger.warning(f"Metric '{metric}' not found in any snapshots for {protocol}")
                # Only raise an error if snapshots exist but metric doesn't
                if snapshots and available_metrics:
                    raise MetricNotFoundError(metric, available_metrics=list(available_metrics))
                return pd.DataFrame(columns=["timestamp", metric])

            # Convert to DataFrame
            df = pd.DataFrame(data)

            if not df.empty:
                df.set_index("timestamp", inplace=True)

            logger.info(f"Retrieved time series data for {protocol} with {len(df)} data points")
            return df

        except Exception as e:
            if isinstance(e, (ProtocolNotSupportedError, DataAccessError, MetricNotFoundError)):
                raise
            logger.error(f"Failed to retrieve time series data: {e}")
            raise HistoricalDataError(f"Failed to retrieve time series data: {e}") from e

    def get_available_metrics(self, protocol: str) -> Set[str]:
        """Get a set of all available metrics for a protocol.

        Args:
            protocol: Name of the protocol

        Returns:
            Set of metric names found in snapshots

        Raises:
            ProtocolNotSupportedError: If the protocol is not supported
            DataAccessError: If there's an issue accessing the data

        """
        self._validate_protocol(protocol)

        metrics = set()
        snapshots = self.get_snapshots(protocol)

        for snapshot in snapshots:
            data = snapshot.get("data", {})
            if "metrics" in data:
                metrics.update(data["metrics"].keys())

        logger.info(f"Found {len(metrics)} metrics for {protocol}")
        return metrics

    def load_snapshot(self, protocol: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """Load a specific snapshot by protocol and timestamp.

        Args:
            protocol: Name of the protocol
            timestamp: ISO format timestamp of the snapshot to load

        Returns:
            Snapshot data or None if not found

        Raises:
            ProtocolNotSupportedError: If the protocol is not supported
            DataAccessError: If there's an issue accessing the data

        """
        self._validate_protocol(protocol)

        protocol_dir = os.path.join(self.data_dir, protocol)

        if not os.path.exists(protocol_dir):
            logger.warning(f"Data directory for {protocol} does not exist")
            return None

        try:
            # Convert timestamp to filename format
            if "T" in timestamp:  # ISO format
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(timestamp)

            timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
            filename = f"{protocol}_snapshot_{timestamp_str}.json"
            filepath = os.path.join(protocol_dir, filename)

            if not os.path.exists(filepath):
                logger.warning(f"Snapshot file not found: {filepath}")
                return None

            with open(filepath) as f:
                snapshot = json.load(f)

            # Return the data portion of the snapshot
            return snapshot.get("data", {})

        except (OSError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load snapshot for {protocol} at {timestamp}: {e}")
            raise DataAccessError(f"Failed to load snapshot for {protocol} at {timestamp}: {e}") from e


def calculate_distribution_change(
    old_distribution: pd.DataFrame,
    new_distribution: pd.DataFrame,
    address_col: str = "address",
    balance_col: str = "balance",
) -> pd.DataFrame:
    """Calculate changes in token distribution between two snapshots.

    Args:
        old_distribution: DataFrame containing older distribution data
        new_distribution: DataFrame containing newer distribution data
        address_col: Column name for addresses
        balance_col: Column name for token balances

    Returns:
        DataFrame with changes in token balances

    Raises:
        DataFormatError: If the input DataFrames don't have the expected columns
        HistoricalDataError: If there's an issue calculating the changes

    """
    # Validate input DataFrames
    for name, df in [
        ("old_distribution", old_distribution),
        ("new_distribution", new_distribution),
    ]:
        if not isinstance(df, pd.DataFrame):
            logger.error(f"Invalid input: {name} is not a DataFrame")
            raise DataFormatError(f"Invalid input: {name} is not a DataFrame")

        for col in [address_col, balance_col]:
            if col not in df.columns:
                logger.error(f"Column '{col}' not found in {name}")
                raise DataFormatError(f"Column '{col}' not found in {name}")

    try:
        # Create dictionaries mapping addresses to balances
        old_balances = dict(zip(old_distribution[address_col], old_distribution[balance_col]))
        new_balances = dict(zip(new_distribution[address_col], new_distribution[balance_col]))

        # Get all unique addresses
        all_addresses = set(old_balances.keys()) | set(new_balances.keys())

        # Calculate changes
        changes = []
        for address in all_addresses:
            old_balance = old_balances.get(address, 0)
            new_balance = new_balances.get(address, 0)
            change = new_balance - old_balance

            # Handle division by zero
            if old_balance > 0:
                percent_change = change / old_balance * 100
            else:
                percent_change = float("inf") if change > 0 else 0

            changes.append(
                {
                    "address": address,
                    "old_balance": old_balance,
                    "new_balance": new_balance,
                    "absolute_change": change,
                    "percent_change": percent_change,
                }
            )

        # Convert to DataFrame and sort by absolute change
        changes_df = pd.DataFrame(changes)
        if not changes_df.empty:
            changes_df.sort_values("absolute_change", ascending=False, inplace=True)

        logger.info(f"Calculated distribution changes for {len(changes_df)} addresses")
        return changes_df

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to calculate distribution changes: {e}")
        raise HistoricalDataError(f"Failed to calculate distribution changes: {e}") from e


def analyze_concentration_trends(snapshots: List[Dict[str, Any]], top_n_holders: int = 10) -> pd.DataFrame:
    """Analyze trends in token concentration over time.

    Args:
        snapshots: List of historical snapshots
        top_n_holders: Number of top holders to track

    Returns:
        DataFrame with concentration metrics over time

    Raises:
        DataFormatError: If the snapshots don't have the expected format
        HistoricalDataError: If there's an issue analyzing the trends

    """
    if not snapshots:
        logger.info("No snapshots provided for concentration trend analysis")
        return pd.DataFrame()

    try:
        # Extract timestamps and concentration metrics
        data = []

        for snapshot in snapshots:
            # Validate snapshot format
            if "timestamp" not in snapshot or "data" not in snapshot:
                logger.warning("Invalid snapshot format: missing required fields")
                continue

            try:
                timestamp = datetime.fromisoformat(snapshot["timestamp"])
            except ValueError as e:
                logger.warning(f"Invalid timestamp in snapshot: {e}")
                continue

            # Extract or calculate concentration metrics
            metrics = {}

            # Check if metrics are already calculated
            if "metrics" in snapshot["data"] and isinstance(snapshot["data"]["metrics"], dict):
                metrics = snapshot["data"]["metrics"]

            # Get concentration of top N holders if available
            top_n_concentration = metrics.get(f"top_{top_n_holders}_concentration")
            gini = metrics.get("gini_coefficient")

            data.append(
                {
                    "timestamp": timestamp,
                    f"top_{top_n_holders}_concentration": top_n_concentration,
                    "gini_coefficient": gini,
                }
            )

        # Convert to DataFrame
        df = pd.DataFrame(data)

        if not df.empty:
            df.set_index("timestamp", inplace=True)
            logger.info(f"Analyzed concentration trends across {len(df)} snapshots")
        else:
            logger.warning("No valid concentration metrics found in snapshots")

        return df

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to analyze concentration trends: {e}")
        raise HistoricalDataError(f"Failed to analyze concentration trends: {e}") from e


def analyze_governance_participation_trends(
    snapshots: List[Dict[str, Any]],
) -> pd.DataFrame:
    """Analyze trends in governance participation over time.

    Args:
        snapshots: List of historical snapshots

    Returns:
        DataFrame with governance participation metrics over time

    Raises:
        DataFormatError: If the snapshots don't have the expected format
        HistoricalDataError: If there's an issue analyzing the trends

    """
    if not snapshots:
        logger.info("No snapshots provided for governance participation analysis")
        return pd.DataFrame()

    try:
        # Extract timestamps and participation metrics
        data = []

        for snapshot in snapshots:
            # Validate snapshot format
            if "timestamp" not in snapshot or "data" not in snapshot:
                logger.warning("Invalid snapshot format: missing required fields")
                continue

            try:
                timestamp = datetime.fromisoformat(snapshot["timestamp"])
            except ValueError as e:
                logger.warning(f"Invalid timestamp in snapshot: {e}")
                continue

            # Extract participation metrics if available
            metrics = {}

            if "metrics" in snapshot["data"] and isinstance(snapshot["data"]["metrics"], dict):
                metrics = snapshot["data"]["metrics"]

            # Get participation metrics
            participation_rate = metrics.get("governance_participation_rate")
            voter_count = metrics.get("active_voter_count")
            proposal_count = metrics.get("active_proposal_count")

            data.append(
                {
                    "timestamp": timestamp,
                    "participation_rate": participation_rate,
                    "active_voter_count": voter_count,
                    "active_proposal_count": proposal_count,
                }
            )

        # Convert to DataFrame
        df = pd.DataFrame(data)

        if not df.empty:
            df.set_index("timestamp", inplace=True)
            logger.info(f"Analyzed governance participation trends across {len(df)} snapshots")
        else:
            logger.warning("No valid participation metrics found in snapshots")

        return df

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to analyze governance participation trends: {e}")
        raise HistoricalDataError(f"Failed to analyze governance participation trends: {e}") from e


def simulate_historical_data(
    protocol: str,
    num_snapshots: int = 12,
    interval_days: int = 30,
    data_manager: Optional[HistoricalDataManager] = None,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Simulate historical data for testing and development purposes.

    Args:
        protocol: Name of the protocol to simulate
        num_snapshots: Number of historical snapshots to generate
        interval_days: Number of days between snapshots
        data_manager: HistoricalDataManager for storing snapshots (optional)
        seed: Random seed for reproducibility (optional)

    Returns:
        List of simulated snapshots

    Raises:
        ProtocolNotSupportedError: If the protocol is not supported
        HistoricalDataError: If there's an issue generating the data

    """
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)

    # Create data manager if not provided
    if data_manager is None:
        try:
            data_manager = HistoricalDataManager()
        except DataStorageError as e:
            logger.error(f"Failed to create data manager for simulation: {e}")
            raise HistoricalDataError(f"Failed to create data manager for simulation: {e}") from e

    # Validate protocol
    try:
        data_manager._validate_protocol(protocol)
    except ProtocolNotSupportedError:
        logger.error(f"Unsupported protocol for simulation: {protocol}")
        raise

    try:
        # Generate simulated data
        snapshots = []

        # Start from 'num_snapshots' * 'interval_days' days ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=num_snapshots * interval_days)

        for i in range(num_snapshots):
            # Calculate timestamp for this snapshot
            timestamp = start_date + timedelta(days=i * interval_days)

            # Simulate token holders (100 addresses with different balances)
            num_holders = 100
            addresses = [f"0x{j:040x}" for j in range(num_holders)]

            # Create power law distribution for token balances
            # Exponent between 1.5 and 2.5 (realistic for crypto)
            exponent = np.random.uniform(1.5, 2.5)
            raw_balances = np.random.pareto(exponent, num_holders)

            # Normalize to a total supply of 10 million tokens
            total_supply = 10_000_000
            balances = raw_balances / raw_balances.sum() * total_supply

            # Add some time-based variation to make trends
            time_factor = 1.0 + 0.05 * np.sin(i / 3)  # Small sinusoidal variation
            balances = balances * time_factor

            # Sort by balance (descending)
            holder_data = sorted(zip(addresses, balances), key=lambda x: x[1], reverse=True)

            # Create token holder list
            token_holders = []
            for address, balance in holder_data:
                percentage = balance / total_supply * 100
                token_holders.append(
                    {
                        "address": address,
                        "balance": float(balance),
                        "percentage": float(percentage),
                    }
                )

            # Calculate metrics
            # Gini coefficient (higher means more concentration)
            balances_array = np.array([h["balance"] for h in token_holders])
            balances_sorted = np.sort(balances_array)
            indices = np.arange(1, len(balances_array) + 1)
            n = len(balances_array)
            gini = (2 * np.sum(indices * balances_sorted)) / (n * np.sum(balances_array)) - (n + 1) / n

            # Top 10 concentration
            top_10_concentration = sum(h["percentage"] for h in token_holders[:10])

            # Nakamoto coefficient (number of addresses needed to reach 51%)
            cum_percent = 0
            nakamoto = 0
            for holder in token_holders:
                cum_percent += holder["percentage"]
                nakamoto += 1
                if cum_percent > 51:
                    break

            # Governance participation (simulated)
            participation_rate = np.random.uniform(0.1, 0.5)  # 10-50% participation
            active_voter_count = int(num_holders * participation_rate)

            # Create snapshot data
            data = {
                "token_holders": token_holders,
                "metrics": {
                    "gini_coefficient": float(gini),
                    "top_10_concentration": float(top_10_concentration),
                    "nakamoto_coefficient": nakamoto,
                    "governance_participation_rate": float(participation_rate),
                    "active_voter_count": active_voter_count,
                    "active_proposal_count": np.random.randint(1, 10),
                },
            }

            # Store snapshot
            data_manager.store_snapshot(protocol, data, timestamp=timestamp)

            # Add to results
            snapshot = {"timestamp": timestamp.isoformat(), "data": data}
            snapshots.append(snapshot)

        logger.info(f"Generated {num_snapshots} simulated snapshots for {protocol}")
        return snapshots

    except Exception as e:
        if isinstance(e, ProtocolNotSupportedError):
            raise
        logger.error(f"Failed to simulate historical data: {e}")
        raise HistoricalDataError(f"Failed to simulate historical data: {e}") from e


def load_historical_snapshots(protocol: str, data_dir: str = "data/historical") -> List[Dict[str, Any]]:
    """Load historical snapshots for a given protocol.

    Args:
        protocol: Name of the protocol
        data_dir: Directory containing historical data

    Returns:
        List of snapshots ordered by timestamp

    Raises:
        DataAccessError: If there's an issue accessing the data
    """
    try:
        # Initialize data manager
        data_manager = HistoricalDataManager(data_dir)

        # Get snapshots
        snapshots = data_manager.get_snapshots(protocol)

        return snapshots
    except (DataAccessError, ProtocolNotSupportedError) as e:
        logger.error(f"Failed to load historical snapshots for {protocol}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading historical snapshots for {protocol}: {e}")
        return []
        logger.error(f"Failed to load historical snapshots for {protocol}: {e}")
        return []
