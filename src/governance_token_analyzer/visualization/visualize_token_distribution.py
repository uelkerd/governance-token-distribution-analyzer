#!/usr/bin/env python
"""Token Distribution Visualization.

This script generates visualizations of token distribution data for DeFi governance tokens.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Add the src directory to the Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(src_dir))

from src.analyzer.config import DEFAULT_OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_token_data(protocol: str) -> dict:
    """Load token analysis data from JSON file.

    Args:
        protocol: Protocol name (e.g., 'compound')

    Returns:
        Dictionary containing token analysis data

    """
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    file_path = output_dir / f"{protocol}_analysis.json"

    if not file_path.exists():
        logger.error(f"Analysis file not found: {file_path}")
        raise FileNotFoundError(f"No analysis data for {protocol}")

    try:
        with open(file_path) as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in analysis file: {file_path}")
        raise ValueError(f"Invalid analysis data for {protocol}")


def create_pie_chart(data: dict, output_dir: Path):
    """Create a pie chart showing token distribution.

    Args:
        data: Token analysis data
        output_dir: Directory to save the visualization

    """
    top_holders = data["top_holders"]

    # Extract top 5 holders plus "Others"
    labels = [f"#{h['rank']}: {h['address'][:6]}...{h['address'][-4:]}" for h in top_holders[:5]]
    sizes = [h["percentage"] for h in top_holders[:5]]

    # Add "Others" slice
    others_pct = 100 - sum(sizes)
    labels.append("Others")
    sizes.append(others_pct)

    # Create figure with a specific size
    plt.figure(figsize=(10, 7))

    # Create pie chart
    explode = [0.1] + [0] * 5  # Explode the first slice
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(sizes)))

    plt.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        shadow=True,
        startangle=90,
        textprops={"fontsize": 12},
    )
    plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Add title
    plt.title(f"{data['name']} ({data['symbol']}) Token Distribution", fontsize=16)

    # Save the chart
    output_file = output_dir / f"{data['protocol']}_distribution_pie.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    logger.info(f"Pie chart saved to {output_file}")

    # Show the chart
    plt.close()


def create_concentration_bar_chart(data: dict, output_dir: Path):
    """Create a bar chart showing token concentration metrics.

    Args:
        data: Token analysis data
        output_dir: Directory to save the visualization

    """
    top_percentages = data["concentration_metrics"]["top_holders_percentage"]

    categories = list(map(str, sorted([int(k) for k in top_percentages.keys()])))
    percentages = [top_percentages[k] for k in categories]

    plt.figure(figsize=(10, 6))

    # Create the bar chart
    bars = plt.bar(
        categories,
        percentages,
        color=plt.cm.viridis(np.linspace(0.1, 0.9, len(categories))),
    )

    # Add percentage labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.annotate(
            f"{height:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),  # 3 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
        )

    # Add labels and title
    plt.xlabel("Number of Top Holders", fontsize=12)
    plt.ylabel("Percentage of Total Supply", fontsize=12)
    plt.title(f"{data['name']} ({data['symbol']}) Token Concentration", fontsize=16)

    # Add a horizontal line at 50% for reference
    plt.axhline(y=50, color="r", linestyle="--", alpha=0.5)
    plt.text(0, 51, "50% Threshold", color="r")

    # Save the chart
    output_file = output_dir / f"{data['protocol']}_concentration_bar.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    logger.info(f"Bar chart saved to {output_file}")

    # Show the chart
    plt.close()


def visualize_holder_distribution(analysis_results, output_dir="plots"):
    """Create a pie chart visualization of token holder distribution.

    Args:
        analysis_results: Token analysis results dictionary
        output_dir: Directory to save the plot

    """
    token_name = analysis_results["token"]
    holders = analysis_results["holders"]

    # Sort holders by balance
    holders = sorted(holders, key=lambda x: float(x["balance"]), reverse=True)

    # Extract top 10 holders
    top_holders = holders[:10]

    # Calculate total for others
    total_balance = sum(float(holder["balance"]) for holder in holders)
    top_balance = sum(float(holder["balance"]) for holder in top_holders)
    others_balance = total_balance - top_balance

    # Prepare data for pie chart
    labels = [f"Holder {i + 1}" for i in range(len(top_holders))]
    if others_balance > 0:
        labels.append("Others")

    values = [float(holder["balance"]) for holder in top_holders]
    if others_balance > 0:
        values.append(others_balance)

    # Create pie chart
    plt.figure(figsize=(10, 8))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(f"{token_name} Token Distribution")

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{token_name.lower()}_distribution_{timestamp}.png")
    plt.savefig(filename)
    plt.close()

    print(f"Holder distribution visualization saved to {filename}")


def visualize_concentration_metrics(analysis_results, output_dir="plots"):
    """Create a bar chart visualization of token concentration metrics.

    Args:
        analysis_results: Token analysis results dictionary
        output_dir: Directory to save the plot

    """
    token_name = analysis_results["token"]
    metrics = analysis_results["metrics"]

    # Prepare data for bar chart
    metrics_labels = ["Gini Coefficient", "Herfindahl Index / 10000"]
    metrics_values = [
        metrics["gini_coefficient"],
        metrics["herfindahl_index"] / 10000,  # Scale to 0-1 for comparison
    ]

    # Create bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(metrics_labels, metrics_values)
    plt.title(f"{token_name} Token Concentration Metrics")
    plt.ylabel("Value (0-1 scale)")
    plt.ylim(0, 1)

    # Add value labels on top of bars
    for i, v in enumerate(metrics_values):
        plt.text(i, v + 0.02, f"{v:.4f}", ha="center")

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{token_name.lower()}_metrics_{timestamp}.png")
    plt.savefig(filename)
    plt.close()

    print(f"Concentration metrics visualization saved to {filename}")


def visualize_historical_gini(token_name, historical_data, output_dir="plots"):
    """Create a line chart of historical Gini coefficient values.

    Args:
        token_name: Name of the token
        historical_data: List of historical data points
        output_dir: Directory to save the plot

    """
    if not historical_data:
        print(f"No historical data found for {token_name}")
        return

    # Extract dates and gini values
    dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
    gini_values = [data["metrics"]["gini_coefficient"] for data in historical_data]

    # Create line chart
    plt.figure(figsize=(12, 6))
    plt.plot(dates, gini_values, marker="o", linestyle="-", linewidth=2)

    # Format the x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()  # Rotate date labels

    plt.title(f"{token_name} Token Gini Coefficient Over Time")
    plt.ylabel("Gini Coefficient")
    plt.ylim(0, 1)  # Gini is between 0 and 1
    plt.grid(True, linestyle="--", alpha=0.7)

    # Add trend line
    if len(dates) > 1:
        z = np.polyfit(mdates.date2num(dates), gini_values, 1)
        p = np.poly1d(z)
        plt.plot(
            dates,
            p(mdates.date2num(dates)),
            "r--",
            alpha=0.8,
            label=f"Trend (slope: {z[0]:.6f})",
        )
        plt.legend()

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{token_name.lower()}_gini_trend_{timestamp}.png")
    plt.savefig(filename)
    plt.close()

    print(f"Gini coefficient trend visualization saved to {filename}")


def visualize_historical_herfindahl(token_name, historical_data, output_dir="plots"):
    """Create a line chart of historical Herfindahl index values.

    Args:
        token_name: Name of the token
        historical_data: List of historical data points
        output_dir: Directory to save the plot

    """
    if not historical_data:
        print(f"No historical data found for {token_name}")
        return

    # Extract dates and herfindahl values
    dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
    hhi_values = [data["metrics"]["herfindahl_index"] for data in historical_data]

    # Create line chart
    plt.figure(figsize=(12, 6))
    plt.plot(dates, hhi_values, marker="o", linestyle="-", linewidth=2)

    # Format the x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()  # Rotate date labels

    plt.title(f"{token_name} Token Herfindahl-Hirschman Index Over Time")
    plt.ylabel("Herfindahl Index")
    plt.grid(True, linestyle="--", alpha=0.7)

    # Add trend line
    if len(dates) > 1:
        z = np.polyfit(mdates.date2num(dates), hhi_values, 1)
        p = np.poly1d(z)
        plt.plot(
            dates,
            p(mdates.date2num(dates)),
            "r--",
            alpha=0.8,
            label=f"Trend (slope: {z[0]:.6f})",
        )
        plt.legend()

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{token_name.lower()}_herfindahl_trend_{timestamp}.png")
    plt.savefig(filename)
    plt.close()

    print(f"Herfindahl index trend visualization saved to {filename}")


def visualize_historical_concentration(token_name, historical_data, output_dir="plots"):
    """Create a line chart of historical concentration percentages.

    Args:
        token_name: Name of the token
        historical_data: List of historical data points
        output_dir: Directory to save the plot

    """
    if not historical_data:
        print(f"No historical data found for {token_name}")
        return

    # Extract dates and concentration values
    dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
    top5_values = [data["metrics"]["concentration"]["top_5_pct"] for data in historical_data]
    top10_values = [data["metrics"]["concentration"]["top_10_pct"] for data in historical_data]
    top20_values = [data["metrics"]["concentration"]["top_20_pct"] for data in historical_data]

    # Create line chart
    plt.figure(figsize=(12, 6))
    plt.plot(
        dates,
        top5_values,
        marker="o",
        linestyle="-",
        linewidth=2,
        label="Top 5 Holders",
    )
    plt.plot(
        dates,
        top10_values,
        marker="s",
        linestyle="-",
        linewidth=2,
        label="Top 10 Holders",
    )
    plt.plot(
        dates,
        top20_values,
        marker="^",
        linestyle="-",
        linewidth=2,
        label="Top 20 Holders",
    )

    # Format the x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()  # Rotate date labels

    plt.title(f"{token_name} Token Concentration Percentages Over Time")
    plt.ylabel("Percentage of Total Supply")
    plt.ylim(0, 100)  # Percentage scale
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{token_name.lower()}_concentration_trend_{timestamp}.png")
    plt.savefig(filename)
    plt.close()

    print(f"Concentration trend visualization saved to {filename}")


def visualize_metrics_dashboard(token_name, historical_data, output_dir="plots"):
    """Create a dashboard of all metrics in a single figure.

    Args:
        token_name: Name of the token
        historical_data: List of historical data points
        output_dir: Directory to save the plot

    """
    if not historical_data:
        print(f"No historical data found for {token_name}")
        return

    # Extract dates and metrics
    dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
    gini_values = [data["metrics"]["gini_coefficient"] for data in historical_data]
    hhi_values = [data["metrics"]["herfindahl_index"] / 10000 for data in historical_data]  # Scale to 0-1
    top5_values = [data["metrics"]["concentration"]["top_5_pct"] / 100 for data in historical_data]  # Scale to 0-1
    top10_values = [data["metrics"]["concentration"]["top_10_pct"] / 100 for data in historical_data]  # Scale to 0-1

    # Create dashboard with 4 subplots
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f"{token_name} Token Governance Metrics Dashboard", fontsize=16)

    # Plot 1: Gini Coefficient
    axs[0, 0].plot(dates, gini_values, marker="o", linestyle="-", linewidth=2, color="blue")
    axs[0, 0].set_title("Gini Coefficient (Equality/Inequality)")
    axs[0, 0].set_ylim(0, 1)
    axs[0, 0].grid(True, linestyle="--", alpha=0.7)

    # Plot 2: Herfindahl Index
    axs[0, 1].plot(dates, hhi_values, marker="s", linestyle="-", linewidth=2, color="red")
    axs[0, 1].set_title("Herfindahl Index (Market Concentration)")
    axs[0, 1].set_ylim(0, 1)
    axs[0, 1].grid(True, linestyle="--", alpha=0.7)

    # Plot 3: Concentration Percentages
    axs[1, 0].plot(
        dates,
        top5_values,
        marker="^",
        linestyle="-",
        linewidth=2,
        color="green",
        label="Top 5",
    )
    axs[1, 0].plot(
        dates,
        top10_values,
        marker="d",
        linestyle="-",
        linewidth=2,
        color="purple",
        label="Top 10",
    )
    axs[1, 0].set_title("Holdings Concentration")
    axs[1, 0].set_ylim(0, 1)
    axs[1, 0].grid(True, linestyle="--", alpha=0.7)
    axs[1, 0].legend()

    # Plot 4: Comparative Metrics
    bar_width = 0.35
    index = np.arange(3)

    # Use the latest values for the bar chart
    latest_gini = gini_values[-1]
    latest_hhi = hhi_values[-1]
    latest_top5 = top5_values[-1]

    axs[1, 1].bar(
        index,
        [latest_gini, latest_hhi, latest_top5],
        bar_width,
        color=["blue", "red", "green"],
    )
    axs[1, 1].set_title("Latest Metrics Comparison")
    axs[1, 1].set_xticks(index)
    axs[1, 1].set_xticklabels(["Gini", "HHI/10000", "Top 5 %"])
    axs[1, 1].set_ylim(0, 1)

    # Add value labels on top of bars
    for i, v in enumerate([latest_gini, latest_hhi, latest_top5]):
        axs[1, 1].text(i, v + 0.02, f"{v:.3f}", ha="center")

    # Format all x-axes to show dates nicely
    for i in range(2):
        for j in range(2):
            if i != 1 or j != 1:  # Skip the bar chart
                axs[i, j].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
                axs[i, j].xaxis.set_major_locator(mdates.MonthLocator(interval=6))

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to make room for the suptitle

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{token_name.lower()}_metrics_dashboard_{timestamp}.png")
    plt.savefig(filename)
    plt.close()

    print(f"Metrics dashboard visualization saved to {filename}")


def visualize_comparative_analysis(tokens, historical_data_dict, output_dir="plots"):
    """Create comparative visualizations of multiple tokens.

    Args:
        tokens: List of token names
        historical_data_dict: Dictionary mapping token names to their historical data
        output_dir: Directory to save the plots

    """
    if not tokens or not historical_data_dict:
        print("No data available for comparative analysis")
        return

    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Gini Coefficient Comparison
    plt.figure(figsize=(12, 6))

    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
            gini_values = [data["metrics"]["gini_coefficient"] for data in historical_data]
            plt.plot(dates, gini_values, marker="o", linestyle="-", linewidth=2, label=token)

    plt.title("Gini Coefficient Comparison Across Tokens")
    plt.ylabel("Gini Coefficient")
    plt.ylim(0, 1)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()

    # Format the x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()

    filename = os.path.join(output_dir, f"comparative_gini_{timestamp}.png")
    plt.savefig(filename)
    plt.close()
    print(f"Comparative Gini coefficient visualization saved to {filename}")

    # 2. Concentration Comparison (Top 5 holders)
    plt.figure(figsize=(12, 6))

    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
            top5_values = [data["metrics"]["concentration"]["top_5_pct"] for data in historical_data]
            plt.plot(dates, top5_values, marker="o", linestyle="-", linewidth=2, label=token)

    plt.title("Top 5 Holders Concentration Comparison")
    plt.ylabel("Percentage of Total Supply")
    plt.ylim(0, 100)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()

    # Format the x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()

    filename = os.path.join(output_dir, f"comparative_top5_{timestamp}.png")
    plt.savefig(filename)
    plt.close()
    print(f"Comparative Top 5 concentration visualization saved to {filename}")

    # 3. Herfindahl Index Comparison
    plt.figure(figsize=(12, 6))

    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
            hhi_values = [data["metrics"]["herfindahl_index"] for data in historical_data]
            plt.plot(dates, hhi_values, marker="o", linestyle="-", linewidth=2, label=token)

    plt.title("Herfindahl Index Comparison Across Tokens")
    plt.ylabel("Herfindahl Index")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()

    # Format the x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()

    filename = os.path.join(output_dir, f"comparative_hhi_{timestamp}.png")
    plt.savefig(filename)
    plt.close()
    print(f"Comparative Herfindahl index visualization saved to {filename}")

    # 4. Comprehensive Dashboard
    # Create a 2x2 subplot dashboard with comparisons
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Governance Token Comparative Analysis", fontsize=16)

    # Plot 1: Gini Coefficient Comparison
    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
            gini_values = [data["metrics"]["gini_coefficient"] for data in historical_data]
            axs[0, 0].plot(dates, gini_values, marker="o", linestyle="-", linewidth=2, label=token)

    axs[0, 0].set_title("Gini Coefficient")
    axs[0, 0].set_ylim(0, 1)
    axs[0, 0].grid(True, linestyle="--", alpha=0.7)
    axs[0, 0].legend()

    # Plot 2: Herfindahl Index Comparison
    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
            hhi_values = [data["metrics"]["herfindahl_index"] / 10000 for data in historical_data]  # Scale to 0-1
            axs[0, 1].plot(dates, hhi_values, marker="s", linestyle="-", linewidth=2, label=token)

    axs[0, 1].set_title("Herfindahl Index (scaled)")
    axs[0, 1].set_ylim(0, 1)
    axs[0, 1].grid(True, linestyle="--", alpha=0.7)
    axs[0, 1].legend()

    # Plot 3: Top 5 Holders Comparison
    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            dates = [datetime.strptime(data["timestamp"].split("T")[0], "%Y-%m-%d") for data in historical_data]
            top5_values = [
                data["metrics"]["concentration"]["top_5_pct"] / 100 for data in historical_data
            ]  # Scale to 0-1
            axs[1, 0].plot(dates, top5_values, marker="^", linestyle="-", linewidth=2, label=token)

    axs[1, 0].set_title("Top 5 Holders Concentration (scaled)")
    axs[1, 0].set_ylim(0, 1)
    axs[1, 0].grid(True, linestyle="--", alpha=0.7)
    axs[1, 0].legend()

    # Plot 4: Latest Metrics Bar Chart
    bar_width = 0.35
    x = np.arange(3)  # 3 metrics: Gini, HHI, Top 5

    # Get the latest values for each token
    latest_metrics = {}
    for token in tokens:
        if token in historical_data_dict and historical_data_dict[token]:
            historical_data = historical_data_dict[token]
            latest_data = historical_data[-1]
            latest_metrics[token] = {
                "gini": latest_data["metrics"]["gini_coefficient"],
                "hhi": latest_data["metrics"]["herfindahl_index"] / 10000,  # Scale to 0-1
                "top5": latest_data["metrics"]["concentration"]["top_5_pct"] / 100,  # Scale to 0-1
            }

    # Plot the bars
    for i, token in enumerate(latest_metrics.keys()):
        metrics = latest_metrics[token]
        axs[1, 1].bar(
            x + i * bar_width / len(latest_metrics),
            [metrics["gini"], metrics["hhi"], metrics["top5"]],
            bar_width / len(latest_metrics),
            label=token,
        )

    axs[1, 1].set_title("Latest Metrics Comparison")
    axs[1, 1].set_xticks(x + bar_width / 2 - bar_width / (2 * len(latest_metrics)))
    axs[1, 1].set_xticklabels(["Gini", "HHI (scaled)", "Top 5 (scaled)"])
    axs[1, 1].set_ylim(0, 1)
    axs[1, 1].legend()

    # Format all x-axes to show dates nicely
    for i in range(2):
        for j in range(2):
            if i != 1 or j != 1:  # Skip the bar chart
                axs[i, j].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
                axs[i, j].xaxis.set_major_locator(mdates.MonthLocator(interval=6))

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    filename = os.path.join(output_dir, f"comparative_dashboard_{timestamp}.png")
    plt.savefig(filename)
    plt.close()
    print(f"Comparative dashboard visualization saved to {filename}")


def main():
    """Run the visualization process."""
    # Paths to data files
    comp_file = "data/comp_analysis_latest.json"
    comp_historical_file = "data/historical/comp_historical_metrics.json"
    uni_historical_file = "data/historical/uni_historical_metrics.json"

    # Check if COMP analysis file exists
    if os.path.exists(comp_file):
        with open(comp_file) as f:
            comp_data = json.load(f)

        # Visualize single token distribution and metrics
        visualize_holder_distribution(comp_data)
        visualize_concentration_metrics(comp_data)
    else:
        print(f"Analysis data file not found: {comp_file}")

    # Load historical data for COMP if available
    comp_historical_data = []
    if os.path.exists(comp_historical_file):
        with open(comp_historical_file) as f:
            comp_historical = json.load(f)
            comp_historical_data = comp_historical.get("data_points", [])

        # Visualize historical trends
        visualize_historical_gini("COMP", comp_historical_data)
        visualize_historical_herfindahl("COMP", comp_historical_data)
        visualize_historical_concentration("COMP", comp_historical_data)
        visualize_metrics_dashboard("COMP", comp_historical_data)
    else:
        print("No historical data found for COMP")

    # Load historical data for UNI if available
    uni_historical_data = []
    if os.path.exists(uni_historical_file):
        with open(uni_historical_file) as f:
            uni_historical = json.load(f)
            uni_historical_data = uni_historical.get("data_points", [])

        # Visualize historical trends
        visualize_historical_gini("UNI", uni_historical_data)
        visualize_historical_herfindahl("UNI", uni_historical_data)
        visualize_historical_concentration("UNI", uni_historical_data)
        visualize_metrics_dashboard("UNI", uni_historical_data)
    else:
        print("No historical data found for UNI")

    # Create comparative analysis if both tokens have data
    if comp_historical_data and uni_historical_data:
        historical_data_dict = {
            "COMP": comp_historical_data,
            "UNI": uni_historical_data,
        }
        visualize_comparative_analysis(["COMP", "UNI"], historical_data_dict)


if __name__ == "__main__":
    main()
