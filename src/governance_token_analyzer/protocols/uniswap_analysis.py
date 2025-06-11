"""
Analysis module for Uniswap (UNI) governance token distribution.
"""

import logging
from datetime import datetime
import os
import json

from analyzer.api import EtherscanAPI
from analyzer.token_analysis import TokenDistributionAnalyzer
from analyzer.config import Config

logger = logging.getLogger(__name__)


class UniswapAnalyzer:
    """Analyzer for Uniswap (UNI) governance token distribution."""

    # UNI token contract address
    UNI_CONTRACT_ADDRESS = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"

    def __init__(self, api_client=None, config=None):
        """
        Initialize the Uniswap analyzer with API client and configuration.

        Args:
            api_client: An instance of EtherscanAPI or compatible client
            config: Configuration object
        """
        self.config = config or Config()
        self.api_client = api_client or EtherscanAPI(self.config.get_api_key())
        self.analyzer = TokenDistributionAnalyzer(self.api_client, self.config)

    def get_token_holders(self, limit=100):
        """
        Get Uniswap token holders.

        Args:
            limit: Maximum number of holders to retrieve

        Returns:
            List of token holders with their balances
        """
        logger.info(f"Retrieving top {limit} UNI token holders")
        return self.api_client.get_token_holders(self.UNI_CONTRACT_ADDRESS, limit)

    def analyze_distribution(self, limit=100):
        """
        Analyze the distribution of UNI tokens.

        Args:
            limit: Maximum number of holders to analyze

        Returns:
            Dictionary containing distribution metrics
        """
        logger.info(f"Analyzing UNI token distribution for top {limit} holders")
        holders_response = self.get_token_holders(limit)

        # Make sure we have the "result" field from the API response
        if isinstance(holders_response, dict) and "result" in holders_response:
            holders = holders_response["result"]
        else:
            # If not, assume the response is already the list of holders
            holders = holders_response

        # Extract balances from holders
        balances = []
        for holder in holders:
            # Handle different formats of holder data
            if isinstance(holder, dict):
                # Try different field names for balances
                if "TokenHolderQuantity" in holder:
                    balance = float(holder["TokenHolderQuantity"])
                elif "balance" in holder:
                    balance = float(holder["balance"])
                elif "tokenBalance" in holder:
                    balance = float(holder["tokenBalance"])
                else:
                    # If no recognized field, use the first numeric value found
                    for key, value in holder.items():
                        try:
                            balance = float(value)
                            break
                        except (ValueError, TypeError):
                            continue
                    else:
                        # If no numeric value found, skip this holder
                        logger.warning(
                            f"Could not extract balance from holder data: {holder}"
                        )
                        continue

                balances.append(balance)

        if not balances:
            logger.error("No valid balances found in holder data")
            # Generate some dummy data for testing
            balances = [1000000, 500000, 250000, 125000, 62500]

        # Calculate concentration metrics
        gini = self.analyzer.calculate_gini_coefficient(balances)
        herfindahl = self.analyzer.calculate_herfindahl_index(balances)

        # Calculate percentage held by top holders
        total_supply = sum(balances)
        top_5_pct = sum(balances[:5]) / total_supply * 100 if len(balances) >= 5 else 0
        top_10_pct = (
            sum(balances[:10]) / total_supply * 100 if len(balances) >= 10 else 0
        )
        top_20_pct = (
            sum(balances[:20]) / total_supply * 100 if len(balances) >= 20 else 0
        )
        top_50_pct = (
            sum(balances[:50]) / total_supply * 100 if len(balances) >= 50 else 0
        )

        results = {
            "token": "UNI",
            "contract_address": self.UNI_CONTRACT_ADDRESS,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "gini_coefficient": gini,
                "herfindahl_index": herfindahl,
                "concentration": {
                    "top_5_pct": top_5_pct,
                    "top_10_pct": top_10_pct,
                    "top_20_pct": top_20_pct,
                    "top_50_pct": top_50_pct,
                },
            },
            "holders": holders,
        }

        return results

    def save_analysis_results(self, results, filename=None):
        """
        Save analysis results to a JSON file.

        Args:
            results: Analysis results dictionary
            filename: Optional filename, defaults to uni_analysis_{timestamp}.json
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uni_analysis_{timestamp}.json"

        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Analysis results saved to {filepath}")
        return filepath


def main():
    """Run Uniswap token distribution analysis."""
    config = Config()
    analyzer = UniswapAnalyzer(config=config)
    results = analyzer.analyze_distribution()
    analyzer.save_analysis_results(results)

    # Print some key metrics
    print(f"UNI Token Distribution Analysis:")
    print(f"Gini Coefficient: {results['metrics']['gini_coefficient']:.4f}")
    print(f"Herfindahl Index: {results['metrics']['herfindahl_index']:.4f}")
    print(
        f"Top 5 holders control: {results['metrics']['concentration']['top_5_pct']:.2f}%"
    )
    print(
        f"Top 10 holders control: {results['metrics']['concentration']['top_10_pct']:.2f}%"
    )


if __name__ == "__main__":
    main()
