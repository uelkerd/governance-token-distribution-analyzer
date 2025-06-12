"""Historical analysis of governance token distribution.

This module enables time-series analysis of token distribution metrics
to track changes in concentration over time.

Example usage:
    python historical_analysis.py UNI --start-date 2022-01-01 --interval 30
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta

from analyzer.config import Config
from compound_analysis import CompoundAnalyzer
from uniswap_analysis import UniswapAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class HistoricalTokenAnalyzer:
    """Analyzer for historical token distribution data."""

    # Map token symbols to their analyzers
    TOKEN_ANALYZERS = {
        "COMP": CompoundAnalyzer,
        "UNI": UniswapAnalyzer,
        # Add more tokens here as they're implemented
    }

    def __init__(self, token_symbol, config=None):
        """Initialize the historical analyzer.

        Args:
            token_symbol: Symbol of the token to analyze (e.g., 'COMP', 'UNI')
            config: Configuration object
        """
        self.token_symbol = token_symbol.upper()
        self.config = config or Config()

        if self.token_symbol not in self.TOKEN_ANALYZERS:
            raise ValueError(
                f"Unsupported token: {token_symbol}. Supported tokens: {list(self.TOKEN_ANALYZERS.keys())}"
            )

        # Initialize the appropriate token analyzer
        self.analyzer = self.TOKEN_ANALYZERS[self.token_symbol](config=self.config)

        # Create directories for historical data
        self.data_dir = "data/historical"
        os.makedirs(self.data_dir, exist_ok=True)

    def analyze_at_date(self, target_date):
        """Analyze token distribution for a specific date.

        Args:
            target_date: Date for which to analyze the distribution (datetime object)

        Returns:
            Analysis results dictionary
        """
        logger.info(
            f"Analyzing {self.token_symbol} distribution for date: {target_date.strftime('%Y-%m-%d')}"
        )

        # Use the token-specific analyzer to get distribution data
        results = self.analyzer.analyze_distribution()

        # Override the timestamp with the target date
        results["timestamp"] = target_date.isoformat()
        results["analysis_date"] = datetime.now().isoformat()

        return results

    def save_historical_data(self, results, target_date):
        """Save historical analysis results to a JSON file.

        Args:
            results: Analysis results dictionary
            target_date: Date of the analysis

        Returns:
            Path to the saved file
        """
        date_str = target_date.strftime("%Y%m%d")
        filename = f"{self.token_symbol.lower()}_analysis_{date_str}.json"
        filepath = os.path.join(self.data_dir, filename)

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Historical analysis saved to {filepath}")
        return filepath

    def run_historical_analysis(self, start_date, end_date=None, interval_days=30):
        """Run historical analysis from start_date to end_date at specified intervals.

        Args:
            start_date: Start date for historical analysis (datetime object)
            end_date: End date for historical analysis, defaults to today (datetime object)
            interval_days: Interval in days between analyses

        Returns:
            List of file paths containing the analysis results
        """
        if end_date is None:
            end_date = datetime.now()

        logger.info(
            f"Running historical analysis for {self.token_symbol} from {start_date.strftime('%Y-%m-%d')} "
            f"to {end_date.strftime('%Y-%m-%d')} at {interval_days}-day intervals"
        )

        current_date = start_date
        result_files = []

        while current_date <= end_date:
            try:
                # Analyze for current date
                results = self.analyze_at_date(current_date)

                # Save results
                filepath = self.save_historical_data(results, current_date)
                result_files.append(filepath)

                # Move to next interval
                current_date += timedelta(days=interval_days)

                # Add a delay to avoid API rate limits
                time.sleep(1)

            except Exception as e:
                logger.error(
                    f"Error analyzing {self.token_symbol} for date {current_date.strftime('%Y-%m-%d')}: {str(e)}"
                )
                current_date += timedelta(days=interval_days)

        return result_files

    def compile_historical_metrics(self):
        """Compile historical metrics from saved analysis files.

        Returns:
            Dictionary with time series data for each metric
        """
        logger.info(f"Compiling historical metrics for {self.token_symbol}")

        # Pattern for historical data files
        file_pattern = f"{self.token_symbol.lower()}_analysis_*.json"

        # Find all historical data files
        file_paths = []
        for filename in os.listdir(self.data_dir):
            if filename.startswith(
                f"{self.token_symbol.lower()}_analysis_"
            ) and filename.endswith(".json"):
                file_paths.append(os.path.join(self.data_dir, filename))

        if not file_paths:
            logger.warning(f"No historical data found for {self.token_symbol}")
            return None

        # Sort files by date
        file_paths.sort()

        # Initialize time series data
        time_series = {
            "token": self.token_symbol,
            "dates": [],
            "gini_coefficient": [],
            "herfindahl_index": [],
            "top_5_pct": [],
            "top_10_pct": [],
            "top_20_pct": [],
            "top_50_pct": [],
        }

        # Extract metrics from each file
        for filepath in file_paths:
            try:
                with open(filepath) as f:
                    data = json.load(f)

                # Extract date from timestamp
                date = data["timestamp"].split("T")[0]
                time_series["dates"].append(date)

                # Extract metrics
                time_series["gini_coefficient"].append(
                    data["metrics"]["gini_coefficient"]
                )
                time_series["herfindahl_index"].append(
                    data["metrics"]["herfindahl_index"]
                )
                time_series["top_5_pct"].append(
                    data["metrics"]["concentration"]["top_5_pct"]
                )
                time_series["top_10_pct"].append(
                    data["metrics"]["concentration"]["top_10_pct"]
                )
                time_series["top_20_pct"].append(
                    data["metrics"]["concentration"]["top_20_pct"]
                )
                time_series["top_50_pct"].append(
                    data["metrics"]["concentration"]["top_50_pct"]
                )

            except Exception as e:
                logger.error(f"Error processing {filepath}: {str(e)}")

        # Save compiled metrics
        output_filepath = os.path.join(
            self.data_dir, f"{self.token_symbol.lower()}_historical_metrics.json"
        )
        with open(output_filepath, "w") as f:
            json.dump(time_series, f, indent=2)

        logger.info(f"Historical metrics compiled and saved to {output_filepath}")
        return time_series


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Historical analysis of token distribution"
    )
    parser.add_argument("token", help="Token symbol (e.g., COMP, UNI)")
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date for historical analysis (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        help="End date for historical analysis (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Interval in days between analyses"
    )
    return parser.parse_args()


def main():
    """Run historical token distribution analysis."""
    args = parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = (
        datetime.strptime(args.end_date, "%Y-%m-%d")
        if args.end_date
        else datetime.now()
    )

    # Initialize analyzer
    config = Config()
    analyzer = HistoricalTokenAnalyzer(args.token, config=config)

    # Run historical analysis
    analyzer.run_historical_analysis(start_date, end_date, args.interval)

    # Compile metrics
    time_series = analyzer.compile_historical_metrics()

    # Print summary
    if time_series and time_series["dates"]:
        print(f"\nHistorical Analysis Summary for {args.token}:")
        print(f"Period: {time_series['dates'][0]} to {time_series['dates'][-1]}")
        print(f"Data points: {len(time_series['dates'])}")

        # Calculate changes
        if len(time_series["gini_coefficient"]) >= 2:
            first_gini = time_series["gini_coefficient"][0]
            last_gini = time_series["gini_coefficient"][-1]
            gini_change = (last_gini - first_gini) / first_gini * 100

            first_top10 = time_series["top_10_pct"][0]
            last_top10 = time_series["top_10_pct"][-1]
            top10_change = last_top10 - first_top10

            print(
                f"Gini coefficient change: {gini_change:.2f}% ({first_gini:.4f} → {last_gini:.4f})"
            )
            print(
                f"Top 10 holders concentration change: {top10_change:.2f} percentage points ({first_top10:.2f}% → {last_top10:.2f}%)"
            )

            print(
                f"Gini coefficient change: {gini_change:.2f}% ({first_gini:.4f} → {last_gini:.4f})"
            )
            print(
                f"Top 10 holders concentration change: {top10_change:.2f} percentage points ({first_top10:.2f}% → {last_top10:.2f}%)"
            )


if __name__ == "__main__":
    main()
