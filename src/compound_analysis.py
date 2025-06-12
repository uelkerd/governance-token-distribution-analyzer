#!/usr/bin/env python
"""
Compound Token Analysis Proof of Concept

This script demonstrates the analysis of the Compound (COMP) governance token distribution.
It retrieves data from Etherscan and calculates basic concentration metrics.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(src_dir))

from src.analyzer.token_analysis import (
    analyze_compound_token,
    TokenDistributionAnalyzer,
)
from src.analyzer.config import Config, DEFAULT_OUTPUT_DIR
from src.analyzer.api import EtherscanAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the Compound token analysis."""
    logger.info("Starting Compound token analysis proof of concept")

    try:
        # Analyze Compound token
        results = analyze_compound_token()

        if "error" in results:
            logger.error(f"Analysis failed: {results['error']}")
            return 1

        # Print the results
        logger.info(f"Analysis completed for {results['name']} ({results['symbol']})")

        # Display top 10 holders
        logger.info("\nTop 10 Token Holders:")
        print(f"{'Rank':<5} {'Address':<42} {'Tokens':<20} {'Percentage':>10}")
        print("-" * 80)

        for holder in results["top_holders"]:
            print(
                f"{holder['rank']:<5} {holder['address']:<42} {holder['tokens']:<20} {holder['percentage']:>10.2f}%"
            )

        # Display concentration metrics
        logger.info("\nConcentration Metrics:")
        print(
            f"Top 1 holder percentage: {results['concentration_metrics']['top_holders_percentage'].get(1, 'N/A'):>10.2f}%"
        )
        print(
            f"Top 5 holders percentage: {results['concentration_metrics']['top_holders_percentage'].get(5, 'N/A'):>10.2f}%"
        )
        print(
            f"Top 10 holders percentage: {results['concentration_metrics']['top_holders_percentage'].get(10, 'N/A'):>10.2f}%"
        )
        print(
            f"Top 20 holders percentage: {results['concentration_metrics']['top_holders_percentage'].get(20, 'N/A'):>10.2f}%"
        )
        print(
            f"Top 50 holders percentage: {results['concentration_metrics']['top_holders_percentage'].get(50, 'N/A'):>10.2f}%"
        )
        print(
            f"Top 100 holders percentage: {results['concentration_metrics']['top_holders_percentage'].get(100, 'N/A'):>10.2f}%"
        )

        print(
            f"Gini Coefficient (0-1): {results['concentration_metrics']['gini_coefficient']:.4f}"
        )
        print(
            f"Herfindahl Index (0-10000): {results['concentration_metrics']['herfindahl_index']:.2f}"
        )

        # Save the results to a JSON file
        output_dir = Path(DEFAULT_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "compound_analysis.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_file}")
        return 0

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
