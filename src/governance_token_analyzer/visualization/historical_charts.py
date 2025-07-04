"""Historical Charts Module for visualizing token distribution changes over time.
This module provides functions to create visualizations for historical
token distribution and governance participation data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from governance_token_analyzer.core.exceptions import (
    DataFormatError,
    VisualizationError,
)

# Configure logging
logger = logging.getLogger(__name__)


def create_time_series_chart(
    time_series: pd.DataFrame,
    output_path: str,
    title: Optional[str] = None,
    metric: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
) -> str:
    """Create and save a time series chart for historical data.

    Args:
        time_series: DataFrame with time series data
        output_path: Path to save the chart
        title: Chart title (optional)
        metric: Metric to plot (optional, will use first numeric column if not provided)
        figsize: Figure size

    Returns:
        Path to the saved chart

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization
    """
    try:
        # Validate input data
        if not isinstance(time_series, pd.DataFrame):
            logger.error("Invalid input: time_series is not a DataFrame")
            raise DataFormatError("Input data must be a pandas DataFrame")

        if time_series.empty:
            logger.warning("Empty time series data provided")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title(title or "No data available")
            ax.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            return output_path

        # Determine which metric to plot
        if metric is None:
            # Find first numeric column
            numeric_cols = time_series.select_dtypes(include=np.number).columns
            if len(numeric_cols) == 0:
                logger.error("No numeric columns found in time series data")
                raise DataFormatError("No numeric columns found in time series data")
            metric = numeric_cols[0]

        if metric not in time_series.columns:
            logger.error(f"Metric '{metric}' not found in time series data")
            raise DataFormatError(
                f"Metric '{metric}' not found in time series data. Available metrics: {list(time_series.columns)}"
            )

        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)

        # Check if the index is a datetime type
        if not isinstance(time_series.index, pd.DatetimeIndex):
            logger.debug("Converting timestamp index to datetime")
            time_series = time_series.reset_index()
            # Try to convert the index to datetime
            try:
                time_series["index"] = pd.to_datetime(time_series["index"])
                time_series.set_index("index", inplace=True)
            except:
                # If conversion fails, use numeric index
                logger.warning("Could not convert index to datetime, using numeric index")
                time_series.set_index("index", inplace=True)

        # Plot the metric
        ax.plot(
            time_series.index,
            time_series[metric],
            marker="o",
            linestyle="-",
            linewidth=2,
        )

        # Add a trend line (linear regression) if we have enough data points
        if len(time_series) > 1:
            try:
                # If index is datetime, convert to numeric for polyfit
                if isinstance(time_series.index, pd.DatetimeIndex):
                    x = mdates.date2num(time_series.index)
                else:
                    x = np.arange(len(time_series))

                y = time_series[metric].values
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)

                if isinstance(time_series.index, pd.DatetimeIndex):
                    ax.plot(time_series.index, p(x), "r--", alpha=0.7, linewidth=1.5, label="Trend")
                else:
                    ax.plot(
                        time_series.index,
                        p(np.arange(len(time_series))),
                        "r--",
                        alpha=0.7,
                        linewidth=1.5,
                        label="Trend",
                    )

                ax.legend()
            except Exception as e:
                logger.warning(f"Could not create trend line: {e}")

        # Set labels and title
        ax.set_xlabel("Date")
        ax.set_ylabel(metric.replace("_", " ").title())

        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"{metric.replace('_', ' ').title()} Over Time")

        # Format x-axis dates if applicable
        if isinstance(time_series.index, pd.DatetimeIndex):
            plt.gcf().autofmt_xdate()
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            if len(time_series) > 10:
                ax.xaxis.set_major_locator(mdates.MonthLocator())
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(time_series) // 10)))

        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save the figure
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Created time series chart saved to {output_path}")
        return output_path

    except Exception as e:
        if isinstance(e, (DataFormatError, VisualizationError)):
            raise
        logger.error(f"Failed to create time series chart: {e}")
        raise VisualizationError(f"Failed to create visualization: {e}") from e


def plot_metric_over_time(
    time_series_data: pd.DataFrame,
    metric_name: str,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """Plot a single metric over time.

    Args:
        time_series_data: DataFrame with time index and metric values
        metric_name: Name of the metric to plot
        title: Plot title
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization

    """
    try:
        # Validate input data
        if not isinstance(time_series_data, pd.DataFrame):
            logger.error("Invalid input: time_series_data is not a DataFrame")
            raise DataFormatError("Input data must be a pandas DataFrame")

        if time_series_data.empty:
            logger.warning("Empty time series data provided")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title(title or f"No data available for {metric_name}")
            ax.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        if metric_name not in time_series_data.columns:
            logger.error(f"Metric '{metric_name}' not found in time series data")
            raise DataFormatError(
                f"Metric '{metric_name}' not found in time series data. Available metrics: {list(time_series_data.columns)}"
            )

        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)

        # Check if the index is a datetime type
        if not isinstance(time_series_data.index, pd.DatetimeIndex):
            logger.debug("Converting timestamp index to datetime")
            time_series_data = time_series_data.reset_index()
            time_series_data["timestamp"] = pd.to_datetime(time_series_data["timestamp"])
            time_series_data.set_index("timestamp", inplace=True)

        # Plot the metric
        ax.plot(
            time_series_data.index,
            time_series_data[metric_name],
            marker="o",
            linestyle="-",
        )

        # Add a trend line (linear regression) if we have enough data points
        if len(time_series_data) > 1:
            try:
                z = np.polyfit(
                    mdates.date2num(time_series_data.index),
                    time_series_data[metric_name],
                    1,
                )
                p = np.poly1d(z)
                ax.plot(
                    time_series_data.index,
                    p(mdates.date2num(time_series_data.index)),
                    "r--",
                    alpha=0.8,
                )
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not create trend line: {e}")

        # Set labels and title
        ax.set_xlabel("Date")
        ax.set_ylabel(metric_name.replace("_", " ").title())

        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"{metric_name.replace('_', ' ').title()} Over Time")

        # Format x-axis dates
        plt.gcf().autofmt_xdate()
        ax.grid(True, alpha=0.3)

        logger.info(f"Created time series plot for metric: {metric_name}")
        return fig

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to create metric time series plot: {e}")
        raise VisualizationError(f"Failed to create visualization: {e}") from e


def plot_protocol_comparison_over_time(
    protocol_data: Dict[str, pd.DataFrame],
    metric_name: str,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """Plot a comparison of a metric across multiple protocols over time.

    Args:
        protocol_data: Dictionary mapping protocol names to their time series DataFrames
        metric_name: Name of the metric to compare
        title: Plot title
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization

    """
    try:
        # Validate input data
        if not isinstance(protocol_data, dict):
            logger.error("Invalid input: protocol_data is not a dictionary")
            raise DataFormatError("Protocol data must be a dictionary mapping protocol names to DataFrames")

        if not protocol_data:
            logger.warning("Empty protocol data provided")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title(title or f"No data available for {metric_name}")
            ax.text(
                0.5,
                0.5,
                "No protocol data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)

        # Plot each protocol's data
        valid_protocols = []

        for protocol, data in protocol_data.items():
            if not isinstance(data, pd.DataFrame):
                logger.warning(f"Skipping protocol '{protocol}': data is not a DataFrame")
                continue

            if data.empty:
                logger.warning(f"Skipping protocol '{protocol}': empty DataFrame")
                continue

            if metric_name not in data.columns:
                logger.warning(f"Skipping protocol '{protocol}': metric '{metric_name}' not found")
                continue

            # Check if the index is a datetime type
            if not isinstance(data.index, pd.DatetimeIndex):
                logger.debug(f"Converting timestamp index to datetime for protocol '{protocol}'")
                data = data.reset_index()
                data["timestamp"] = pd.to_datetime(data["timestamp"])
                data.set_index("timestamp", inplace=True)

            ax.plot(
                data.index,
                data[metric_name],
                marker="o",
                linestyle="-",
                label=protocol.capitalize(),
            )
            valid_protocols.append(protocol)

        if not valid_protocols:
            logger.warning(f"No valid data found for metric '{metric_name}' in any protocol")
            ax.set_title(title or f"No valid data for {metric_name}")
            ax.text(
                0.5,
                0.5,
                f"No valid data for metric '{metric_name}'",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Set labels and title
        ax.set_xlabel("Date")
        ax.set_ylabel(metric_name.replace("_", " ").title())

        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"{metric_name.replace('_', ' ').title()} Comparison")

        # Format x-axis dates
        plt.gcf().autofmt_xdate()
        ax.grid(True, alpha=0.3)
        ax.legend()

        logger.info(
            f"Created protocol comparison plot for metric '{metric_name}' with {len(valid_protocols)} protocols"
        )
        return fig

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to create protocol comparison plot: {e}")
        raise VisualizationError(f"Failed to create protocol comparison visualization: {e}") from e


def create_concentration_heatmap(snapshots: List[Dict[str, Any]], figsize: Tuple[int, int] = (14, 8)) -> plt.Figure:
    """Create a heatmap showing token concentration changes over time.

    Args:
        snapshots: List of historical snapshots
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization

    """
    try:
        if not snapshots:
            logger.warning("No snapshots provided for concentration heatmap")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title("Token Concentration Over Time")
            ax.text(
                0.5,
                0.5,
                "No snapshot data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Extract top holder concentration data over time
        data = []
        min_holders_count = float("inf")  # Track the minimum number of holders across snapshots

        for i, snapshot in enumerate(snapshots):
            # Validate snapshot format
            if "timestamp" not in snapshot or "data" not in snapshot:
                logger.warning(f"Skipping snapshot {i}: Invalid format (missing required fields)")
                continue

            if "token_holders" not in snapshot["data"] or not snapshot["data"]["token_holders"]:
                logger.warning(f"Skipping snapshot {i}: No token holder data")
                continue

            try:
                timestamp = datetime.fromisoformat(snapshot["timestamp"])
            except ValueError as e:
                logger.warning(f"Skipping snapshot {i}: Invalid timestamp format: {e}")
                continue

            # Get top holders
            try:
                holders = sorted(
                    [h for h in snapshot["data"]["token_holders"] if "balance" in h and "percentage" in h],
                    key=lambda x: x["balance"],
                    reverse=True,
                )[:10]  # Top 10 holders

                # Update minimum holders count
                min_holders_count = min(min_holders_count, len(holders))

            except (KeyError, TypeError) as e:
                logger.warning(f"Skipping snapshot {i}: Error sorting token holders: {e}")
                continue

            if not holders:
                logger.warning(f"Skipping snapshot {i}: No valid token holders found")
                continue

            # Create a row for each timestamp
            row = {"timestamp": timestamp}
            for j, holder in enumerate(holders):
                if "percentage" not in holder:
                    logger.warning(f"Skipping holder {j} in snapshot {i}: Missing percentage field")
                    continue
                row[f"Holder {j + 1}"] = holder["percentage"]

            data.append(row)

        if not data:
            logger.warning("No valid data extracted from snapshots")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title("Token Concentration Over Time")
            ax.text(
                0.5,
                0.5,
                "No valid data in snapshots",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Check if we have any holder columns
        holder_columns = [col for col in df.columns if col.startswith("Holder ")]
        if not holder_columns:
            logger.warning("No holder data found in snapshots")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title("Token Concentration Over Time")
            ax.text(
                0.5,
                0.5,
                "No holder data found in snapshots",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Set timestamp as index
        df.set_index("timestamp", inplace=True)

        # Make sure all rows have the same number of columns
        # This is important for the heatmap to work correctly
        for i in range(1, min(MAX_TOP_HOLDERS, min_holders_count) + 1):
            col_name = f"Holder {i}"
            if col_name not in df.columns:
                df[col_name] = np.nan

        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)

        # Plot heatmap
        try:
            im = ax.imshow(df.values, aspect="auto", cmap="YlOrRd")

            # Set labels
            ax.set_yticks(range(len(df.index)))
            ax.set_yticklabels([ts.strftime("%Y-%m-%d") for ts in df.index])
            ax.set_xticks(range(len(df.columns)))
            ax.set_xticklabels(df.columns)

            # Add colorbar
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label("Percentage of Total Supply")

            # Set title
            ax.set_title("Top 10 Holder Concentration Over Time")

            # Rotate x-axis labels for better readability
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        except Exception as e:
            logger.error(f"Error creating heatmap visualization: {e}")
            # Close the figure and create a simple error message
            plt.close(fig)
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5, 0.5, f"Error creating heatmap: {str(e)[:100]}...", ha="center", va="center", transform=ax.transAxes
            )
            ax.set_title("Token Concentration Over Time (Error)")
            return fig

        logger.info(f"Created concentration heatmap with {len(df)} time points")
        return fig

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to create concentration heatmap: {e}")
        raise VisualizationError(f"Failed to create concentration heatmap: {e}") from e


def create_holder_movement_plot(
    old_snapshot: Dict[str, Any],
    new_snapshot: Dict[str, Any],
    top_n: int = 20,
    figsize: Tuple[int, int] = (12, 8),
) -> plt.Figure:
    """Create a plot showing movement of top token holders between two snapshots.

    Args:
        old_snapshot: Older snapshot data
        new_snapshot: Newer snapshot data
        top_n: Number of top holders to display
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization

    """
    try:
        # Validate input data
        for name, snapshot in [
            ("old_snapshot", old_snapshot),
            ("new_snapshot", new_snapshot),
        ]:
            if not isinstance(snapshot, dict):
                logger.error(f"Invalid {name}: not a dictionary")
                raise DataFormatError(f"{name} must be a dictionary")

            if "data" not in snapshot or "token_holders" not in snapshot["data"]:
                logger.error(f"Invalid {name}: missing token_holders data")
                raise DataFormatError(f"{name} missing token_holders data")

            if not snapshot["data"]["token_holders"]:
                logger.warning(f"{name} contains no token holders")

        # Extract holder data
        try:
            old_holders = {
                h["address"]: h
                for h in old_snapshot["data"]["token_holders"]
                if "address" in h and "percentage" in h and "balance" in h
            }

            new_holders = {
                h["address"]: h
                for h in new_snapshot["data"]["token_holders"]
                if "address" in h and "percentage" in h and "balance" in h
            }
        except KeyError as e:
            logger.error(f"Error extracting holder data: {e}")
            raise DataFormatError(f"Error extracting holder data: {e}")

        # Get addresses present in both snapshots
        common_addresses = set(old_holders.keys()) & set(new_holders.keys())

        if not common_addresses:
            logger.warning("No common addresses found between snapshots")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title("Token Holder Movement")
            ax.text(
                0.5,
                0.5,
                "No common addresses between snapshots",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Calculate changes for common addresses
        changes = []
        for addr in common_addresses:
            old_pct = old_holders[addr]["percentage"]
            new_pct = new_holders[addr]["percentage"]
            pct_change = new_pct - old_pct
            abs_change = new_holders[addr]["balance"] - old_holders[addr]["balance"]

            changes.append(
                {
                    "address": addr,
                    "old_percentage": old_pct,
                    "new_percentage": new_pct,
                    "percentage_change": pct_change,
                    "absolute_change": abs_change,
                }
            )

        # Sort by absolute change
        changes.sort(key=lambda x: abs(x["absolute_change"]), reverse=True)

        # Take top N changes
        top_changes = changes[: min(top_n, len(changes))]

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        # Create bar positions
        y_pos = np.arange(len(top_changes))

        # Plot bars
        bars = ax.barh(
            y_pos,
            [c["percentage_change"] for c in top_changes],
            color=["green" if c["percentage_change"] >= 0 else "red" for c in top_changes],
        )

        # Add address labels
        addresses = [c["address"][:10] + "..." for c in top_changes]
        ax.set_yticks(y_pos)
        ax.set_yticklabels(addresses)

        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            label_x_pos = width + 0.1 if width >= 0 else width - 0.1
            ha = "left" if width >= 0 else "right"
            ax.text(
                label_x_pos,
                bar.get_y() + bar.get_height() / 2,
                f"{top_changes[i]['percentage_change']:.2f}%",
                ha=ha,
                va="center",
            )

        # Set labels and title
        ax.set_xlabel("Percentage Change")
        ax.set_title("Top Token Holder Movement")
        ax.grid(True, alpha=0.3)

        # Add a vertical line at x=0
        ax.axvline(x=0, color="black", linestyle="-", alpha=0.3)

        logger.info(f"Created holder movement plot with {len(top_changes)} holders")
        return fig

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to create holder movement plot: {e}")
        raise VisualizationError(f"Failed to create holder movement plot: {e}") from e


def create_governance_participation_plot(
    snapshots: List[Dict[str, Any]], figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """Create a plot showing governance participation rates over time.

    Args:
        snapshots: List of historical snapshots
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization

    """
    try:
        if not snapshots:
            logger.warning("No snapshots provided for governance participation plot")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title("Governance Participation Over Time")
            ax.text(
                0.5,
                0.5,
                "No snapshot data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Extract participation data
        data = []

        for i, snapshot in enumerate(snapshots):
            # Validate snapshot format
            if "timestamp" not in snapshot or "data" not in snapshot:
                logger.warning(f"Skipping snapshot {i}: Invalid format (missing required fields)")
                continue

            try:
                timestamp = datetime.fromisoformat(snapshot["timestamp"])
            except ValueError as e:
                logger.warning(f"Skipping snapshot {i}: Invalid timestamp format: {e}")
                continue

            # Check for metrics in different locations in the data structure
            participation_rate = None

            # Look in governance_data first
            governance_data = snapshot["data"].get("governance_data", {})
            if isinstance(governance_data, dict):
                participation_rate = governance_data.get("participation_rate")

            # If not found, look in metrics
            if participation_rate is None and "metrics" in snapshot["data"]:
                metrics = snapshot["data"].get("metrics", {})
                if isinstance(metrics, dict):
                    participation_rate = metrics.get("governance_participation_rate")

            # If still not found, skip this snapshot
            if participation_rate is None:
                logger.warning(f"Skipping snapshot {i}: No participation rate data found")
                continue

            data.append({"timestamp": timestamp, "participation_rate": participation_rate})

        if not data:
            logger.warning("No valid participation data found in snapshots")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_title("Governance Participation Over Time")
            ax.text(
                0.5,
                0.5,
                "No valid participation data in snapshots",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        # Convert to DataFrame
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        # Plot participation rate
        ax.plot(df.index, df["participation_rate"], marker="o", linestyle="-", color="blue")

        # Add trend line if we have enough data points
        if len(df) > 1:
            try:
                z = np.polyfit(mdates.date2num(df.index), df["participation_rate"], 1)
                p = np.poly1d(z)
                ax.plot(df.index, p(mdates.date2num(df.index)), "r--", alpha=0.8)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not create trend line: {e}")

        # Set labels and title
        ax.set_xlabel("Date")
        ax.set_ylabel("Participation Rate (%)")
        ax.set_title("Governance Participation Rate Over Time")

        # Format x-axis dates
        plt.gcf().autofmt_xdate()
        ax.grid(True, alpha=0.3)

        logger.info(f"Created governance participation plot with {len(df)} time points")
        return fig

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to create governance participation plot: {e}")
        raise VisualizationError(f"Failed to create governance participation plot: {e}") from e


def create_multi_metric_dashboard(
    time_series_data: Dict[str, pd.DataFrame],
    metrics: List[str],
    title: str = "Governance Metrics Dashboard",
    figsize: Tuple[int, int] = (15, 10),
) -> plt.Figure:
    """Create a dashboard with multiple metrics plotted over time.

    Args:
        time_series_data: Dictionary mapping metric names to their time series DataFrames
        metrics: List of metrics to include in the dashboard
        title: Dashboard title
        figsize: Figure size

    Returns:
        Matplotlib Figure object

    Raises:
        DataFormatError: If input data is not in the expected format
        VisualizationError: If there's an issue creating the visualization

    """
    try:
        # Validate input data
        if not isinstance(time_series_data, dict):
            logger.error("Invalid input: time_series_data is not a dictionary")
            raise DataFormatError("time_series_data must be a dictionary mapping metric names to DataFrames")

        if not isinstance(metrics, list) or not metrics:
            logger.error("Invalid input: metrics must be a non-empty list")
            raise DataFormatError("metrics must be a non-empty list of metric names")

        # Validate that we have data for each metric
        valid_metrics = []
        for metric in metrics:
            if metric not in time_series_data:
                logger.warning(f"No data found for metric '{metric}', skipping")
                continue

            df = time_series_data[metric]
            if not isinstance(df, pd.DataFrame):
                logger.warning(f"Data for metric '{metric}' is not a DataFrame, skipping")
                continue

            if df.empty:
                logger.warning(f"Empty DataFrame for metric '{metric}', skipping")
                continue

            # Check if the metric column exists in the DataFrame
            if metric not in df.columns:
                logger.warning(f"Metric '{metric}' not found in its DataFrame, skipping")
                continue

            valid_metrics.append(metric)

        if not valid_metrics:
            logger.error("No valid metrics found for dashboard")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No valid metric data available", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(title)
            return fig

        # Use only valid metrics
        metrics = valid_metrics
        n_metrics = len(metrics)

        # Calculate grid dimensions
        n_cols = min(2, n_metrics)
        n_rows = (n_metrics + n_cols - 1) // n_cols  # Ceiling division

        # Create figure
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)

        # Convert to numpy array for consistent indexing
        if n_rows == 1 and n_cols == 1:
            # Special case: single plot
            axes = np.array([[axes]])
        elif n_rows == 1:
            # Single row
            axes = np.array([axes])
        elif n_cols == 1:
            # Single column
            axes = np.array([[ax] for ax in axes])

        # Plot each metric
        metrics_plotted = 0

        for i, metric in enumerate(metrics):
            row = i // n_cols
            col = i % n_cols

            # Get the current axis
            ax = axes[row, col]

            # Get data for this metric
            df = time_series_data[metric]

            # Ensure index is datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                logger.debug(f"Converting timestamp index to datetime for metric '{metric}'")
                df = df.reset_index()
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df.set_index("timestamp", inplace=True)
                else:
                    logger.warning(f"No timestamp column found for metric '{metric}'")
                    ax.text(
                        0.5,
                        0.5,
                        f"No timestamp data for '{metric}'",
                        ha="center",
                        va="center",
                        transform=ax.transAxes,
                    )
                    continue

            # Plot the metric
            try:
                ax.plot(df.index, df[metric], marker="o", linestyle="-")
                metrics_plotted += 1

                # Add a trend line if we have enough data points
                if len(df) > 1:
                    try:
                        z = np.polyfit(mdates.date2num(df.index), df[metric], 1)
                        p = np.poly1d(z)
                        ax.plot(df.index, p(mdates.date2num(df.index)), "r--", alpha=0.8)
                    except (TypeError, ValueError, np.linalg.LinAlgError) as e:
                        logger.warning(f"Could not create trend line for metric '{metric}': {e}")

                # Set labels and title
                ax.set_xlabel("Date")
                ax.set_ylabel(metric.replace("_", " ").title())
                ax.set_title(f"{metric.replace('_', ' ').title()}")

                # Format x-axis dates
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                ax.grid(True, alpha=0.3)
            except Exception as e:
                logger.warning(f"Error plotting metric '{metric}': {e}")
                ax.text(
                    0.5,
                    0.5,
                    f"Error plotting '{metric}': {str(e)[:50]}...",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )

        # Hide any unused subplots
        for i in range(n_metrics, n_rows * n_cols):
            row = i // n_cols
            col = i % n_cols
            axes[row, col].axis("off")

        # Set overall title
        fig.suptitle(title, fontsize=16)

        # Adjust layout
        fig.tight_layout(rect=[0, 0, 1, 0.95])

        logger.info(f"Created multi-metric dashboard with {metrics_plotted} metrics plotted")
        return fig

    except Exception as e:
        if isinstance(e, DataFormatError):
            raise
        logger.error(f"Failed to create multi-metric dashboard: {e}")
        raise VisualizationError(f"Failed to create multi-metric dashboard: {e}") from e
