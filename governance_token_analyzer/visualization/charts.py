"""
Charts Module for visualizing governance token data.
This module provides functions to create various visualizations
for token distribution and governance metrics.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union


def create_distribution_comparison(
    *dfs: pd.DataFrame, title: str = "Token Holder Distribution Comparison"
) -> plt.Figure:
    """
    Create a comparison chart of token holder distributions for multiple protocols.
    
    Args:
        *dfs: DataFrames containing token holder data for different protocols
        title: Chart title
        
    Returns:
        Matplotlib Figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each protocol's distribution
    for i, df in enumerate(dfs):
        if 'protocol' in df.columns:
            protocol_name = df['protocol'].iloc[0]
        else:
            protocol_name = f"Protocol {i+1}"
        
        # Sort by balance and calculate cumulative percentage
        sorted_df = df.sort_values(by='balance', ascending=False).reset_index(drop=True)
        sorted_df['cumulative_percentage'] = sorted_df['percentage'].cumsum()
        
        # Plot the Lorenz curve
        x = np.linspace(0, 100, len(sorted_df))
        ax.plot(x, sorted_df['cumulative_percentage'], label=protocol_name)
    
    # Add perfect equality line
    ax.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Perfect Equality')
    
    # Set labels and title
    ax.set_xlabel('Percentage of Token Holders')
    ax.set_ylabel('Cumulative Percentage of Tokens')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig


def create_metrics_comparison(
    metrics_dict: Dict[str, Dict[str, float]], title: str = "Governance Metrics Comparison"
) -> plt.Figure:
    """
    Create a bar chart comparing governance metrics across protocols.
    
    Args:
        metrics_dict: Dictionary mapping protocol names to their metrics
        title: Chart title
        
    Returns:
        Matplotlib Figure object
    """
    # Extract protocol names and metrics
    protocols = list(metrics_dict.keys())
    metrics = list(metrics_dict[protocols[0]].keys())
    
    # Create figure with subplots for each metric
    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 4 * len(metrics)))
    
    # If there's only one metric, axes will not be a list
    if len(metrics) == 1:
        axes = [axes]
    
    # Plot each metric
    for i, metric in enumerate(metrics):
        ax = axes[i]
        values = [metrics_dict[protocol].get(metric, 0) for protocol in protocols]
        
        # Create bar chart
        bars = ax.bar(protocols, values)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom')
        
        # Set labels and title
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_title(f"{metric.replace('_', ' ').title()} by Protocol")
        ax.grid(True, alpha=0.3, axis='y')
    
    # Set overall title
    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    
    return fig


def create_participation_trend(
    participation_data: Dict[str, List[Dict[str, Any]]], title: str = "Governance Participation Trends"
) -> plt.Figure:
    """
    Create a line chart showing governance participation trends over time.
    
    Args:
        participation_data: Dictionary mapping protocol names to their participation data
        title: Chart title
        
    Returns:
        Matplotlib Figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each protocol's participation trend
    for protocol, data in participation_data.items():
        # Extract dates and participation rates
        dates = [item.get('date') for item in data]
        rates = [item.get('participation_rate', 0) for item in data]
        
        # Plot the trend
        ax.plot(dates, rates, marker='o', label=protocol)
    
    # Set labels and title
    ax.set_xlabel('Date')
    ax.set_ylabel('Participation Rate (%)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    fig.tight_layout()
    
    return fig


def create_whale_influence_chart(
    whale_data: Dict[str, Dict[str, float]], title: str = "Whale Influence by Protocol"
) -> plt.Figure:
    """
    Create a chart showing whale influence metrics by protocol.
    
    Args:
        whale_data: Dictionary mapping protocol names to their whale metrics
        title: Chart title
        
    Returns:
        Matplotlib Figure object
    """
    # Extract protocol names
    protocols = list(whale_data.keys())
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Plot whale percentage of holders
    whale_percentages = [whale_data[protocol].get('whale_percentage', 0) for protocol in protocols]
    ax1.bar(protocols, whale_percentages)
    ax1.set_ylabel('Percentage of Holders (%)')
    ax1.set_title('Whales as Percentage of Total Holders')
    
    # Plot whale holdings percentage
    holdings_percentages = [whale_data[protocol].get('holdings_percentage', 0) for protocol in protocols]
    ax2.bar(protocols, holdings_percentages)
    ax2.set_ylabel('Percentage of Total Supply (%)')
    ax2.set_title('Whale Holdings as Percentage of Total Supply')
    
    # Set overall title
    fig.suptitle(title, fontsize=16)
    
    # Add grid lines
    ax1.grid(True, alpha=0.3, axis='y')
    ax2.grid(True, alpha=0.3, axis='y')
    
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    
    return fig


def save_chart(fig: plt.Figure, filename: str, dpi: int = 300) -> None:
    """
    Save a chart to a file.
    
    Args:
        fig: Matplotlib Figure object
        filename: Output filename
        dpi: Resolution in dots per inch
        
    Returns:
        None
    """
    fig.savefig(filename, dpi=dpi, bbox_inches='tight')
    plt.close(fig) 