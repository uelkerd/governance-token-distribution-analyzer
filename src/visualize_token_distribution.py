#!/usr/bin/env python
"""
Token Distribution Visualization

This script generates visualizations of token distribution data for DeFi governance tokens.
"""

import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add the src directory to the Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(src_dir))

from src.analyzer.config import DEFAULT_OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_token_data(protocol: str) -> dict:
    """
    Load token analysis data from JSON file.
    
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
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in analysis file: {file_path}")
        raise ValueError(f"Invalid analysis data for {protocol}")

def create_pie_chart(data: dict, output_dir: Path):
    """
    Create a pie chart showing token distribution.
    
    Args:
        data: Token analysis data
        output_dir: Directory to save the visualization
    """
    top_holders = data['top_holders']
    
    # Extract top 5 holders plus "Others"
    labels = [f"#{h['rank']}: {h['address'][:6]}...{h['address'][-4:]}" for h in top_holders[:5]]
    sizes = [h['percentage'] for h in top_holders[:5]]
    
    # Add "Others" slice
    others_pct = 100 - sum(sizes)
    labels.append("Others")
    sizes.append(others_pct)
    
    # Create figure with a specific size
    plt.figure(figsize=(10, 7))
    
    # Create pie chart
    explode = [0.1] + [0] * 5  # Explode the first slice
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(sizes)))
    
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90, textprops={'fontsize': 12})
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
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
    """
    Create a bar chart showing token concentration metrics.
    
    Args:
        data: Token analysis data
        output_dir: Directory to save the visualization
    """
    top_percentages = data['concentration_metrics']['top_holders_percentage']
    
    categories = list(map(str, sorted([int(k) for k in top_percentages.keys()])))
    percentages = [top_percentages[k] for k in categories]
    
    plt.figure(figsize=(10, 6))
    
    # Create the bar chart
    bars = plt.bar(categories, percentages, color=plt.cm.viridis(np.linspace(0.1, 0.9, len(categories))))
    
    # Add percentage labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    # Add labels and title
    plt.xlabel('Number of Top Holders', fontsize=12)
    plt.ylabel('Percentage of Total Supply', fontsize=12)
    plt.title(f"{data['name']} ({data['symbol']}) Token Concentration", fontsize=16)
    
    # Add a horizontal line at 50% for reference
    plt.axhline(y=50, color='r', linestyle='--', alpha=0.5)
    plt.text(0, 51, '50% Threshold', color='r')
    
    # Save the chart
    output_file = output_dir / f"{data['protocol']}_concentration_bar.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    logger.info(f"Bar chart saved to {output_file}")
    
    # Show the chart
    plt.close()

def main():
    """Main function to run the visualization script."""
    logger.info("Starting token distribution visualization")
    
    try:
        # Load compound data
        protocol = 'compound'
        data = load_token_data(protocol)
        
        # Create output directory
        output_dir = Path(DEFAULT_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate visualizations
        create_pie_chart(data, output_dir)
        create_concentration_bar_chart(data, output_dir)
        
        logger.info("Visualization complete")
        return 0
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 