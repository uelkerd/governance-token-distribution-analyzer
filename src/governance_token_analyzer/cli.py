#!/usr/bin/env python
"""Governance Token Distribution Analyzer CLI.

This module provides a command-line interface for analyzing governance token
distributions across multiple DeFi protocols.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import analyzer modules
try:
    from governance_token_analyzer.core.advanced_metrics import (
        calculate_all_concentration_metrics,
    )
    from governance_token_analyzer.core.api_client import APIClient
    from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    # Fall back to relative imports if package is not installed
    try:
        from .core.advanced_metrics import calculate_all_concentration_metrics
        from .core.api_client import APIClient
        from .core.data_simulator import TokenDistributionSimulator
    except ImportError as e:
        logger.error(f"Relative import error: {str(e)}")
        sys.exit(1)


def analyze_token(token_name: str, limit: int = 100) -> Dict[str, Any]:
    """Analyze a specific token's distribution.

    Args:
        token_name: Name of the token to analyze (compound, uniswap, aave)
        limit: Number of token holders to analyze

    Returns:
        Dictionary with analysis results

    """
    logger.info(f"Analyzing {token_name} token distribution (top {limit} holders)")

    # Create API client
    api_client = APIClient()

    # Display available APIs with their free tier limits
    logger.info("🔍 Available APIs for data fetching:")
    if (
        api_client.alchemy_api_key
        and api_client.alchemy_api_key != "your_alchemy_api_key"
    ):
        logger.info("  ✅ Alchemy (300M compute units/month - PRIORITIZED)")
    if api_client.graph_api_key:
        logger.info("  ✅ The Graph (generous query limits)")
    if api_client.moralis_api_key:
        logger.info("  ✅ Moralis (40k requests/month)")
    if api_client.etherscan_api_key:
        logger.info("  ✅ Etherscan (5 calls/sec free)")
    else:
        logger.info("  ⚠️  Etherscan API key not configured")

    # Get token holders data with real API calls prioritized
    try:
        holders_data = api_client.get_token_holders(
            token_name, limit=limit, use_real_data=True
        )

        # Extract balances for analysis
        balances = []
        for holder in holders_data:
            if isinstance(holder, dict):
                # Try different balance field names
                balance = (
                    holder.get("balance") or holder.get("TokenHolderQuantity") or 0
                )
                if isinstance(balance, str):
                    try:
                        balance = float(balance)
                    except ValueError:
                        balance = 0
                balances.append(float(balance))

        if not balances:
            logger.warning("No valid balances found, using simulated data")
            # Generate simulated data as fallback
            simulator = TokenDistributionSimulator()
            balances = simulator.generate_power_law_distribution(limit)

        # Calculate concentration metrics
        metrics = calculate_all_concentration_metrics(balances)

        # Add metadata
        data_source = (
            holders_data[0].get("data_source", "simulation")
            if holders_data
            else "simulation"
        )

        results = {
            "protocol": token_name,
            "timestamp": datetime.now().isoformat(),
            "total_holders_analyzed": len(balances),
            "data_source": data_source,
            "concentration_metrics": metrics,
            "top_10_concentration": sum(sorted(balances, reverse=True)[:10])
            / sum(balances)
            if balances
            else 0,
            "top_50_concentration": sum(sorted(balances, reverse=True)[:50])
            / sum(balances)
            if balances
            else 0,
            "holders_data": holders_data[:10]
            if holders_data
            else [],  # Include top 10 for reference
        }

        # Save results to file
        output_file = f"data/{token_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("data", exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        # Also save as latest
        latest_file = f"data/{token_name}_analysis_latest.json"
        with open(latest_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"📊 Analysis complete! Results saved to {output_file}")
        logger.info(f"📈 Data source: {data_source.upper()}")

        # Fix the formatting issue - check if gini_coefficient exists and is a number
        gini_coeff = metrics.get("gini_coefficient", "N/A")
        if isinstance(gini_coeff, (int, float)):
            logger.info(f"🎯 Gini coefficient: {gini_coeff:.4f}")
        else:
            logger.info(f"🎯 Gini coefficient: {gini_coeff}")

        logger.info(f"🏆 Top 10% concentration: {results['top_10_concentration']:.2%}")

        return results

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "protocol": token_name}


def compare_tokens(tokens: List[str], limit: int = 100, output_format: str = "json") -> Dict[str, Dict[str, Any]]:
    """Compare distribution metrics across multiple tokens.

    Args:
        tokens: List of token names to compare
        limit: Number of token holders to analyze per token
        output_format: Format for output ('json' or 'report')

    Returns:
        Dictionary mapping token names to their analysis results

    """
    logger.info(f"Comparing token distributions for: {', '.join(tokens)}")

    results = {}
    for token in tokens:
        try:
            token_results = analyze_token(token, limit)
            results[token] = token_results
        except Exception as e:
            logger.error(f"Error analyzing {token}: {str(e)}")

    # Save combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"token_comparison_{timestamp}.json"

    os.makedirs("data", exist_ok=True)
    with open(os.path.join("data", output_file), "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Comparison results saved to data/{output_file}")

    # Note about report generation
    if output_format.lower() == "report":
        logger.info(
            "HTML report generation is not available in this simplified CLI version"
        )

    return results


def generate_simulated_data(
    distribution_type: str, num_holders: int = 100, output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Generate simulated token distribution data for testing and analysis.

    Args:
        distribution_type: Type of distribution ('power_law', 'protocol_dominated', 'community')
        num_holders: Number of token holders to generate
        output_file: Optional filename to save the data

    Returns:
        Dictionary containing the simulated distribution data

    """
    logger.info(f"Generating simulated {distribution_type} distribution with {num_holders} holders")

    # Use different seeds for different distribution types to create variety
    seed_map = {"power_law": 42, "protocol_dominated": 123, "community": 456}
    seed = seed_map.get(distribution_type, 42)

    simulator = TokenDistributionSimulator(seed=seed)

    # Generate the specified distribution
    if distribution_type == "power_law":
        holders = simulator.generate_power_law_distribution(num_holders=num_holders)
    elif distribution_type == "protocol_dominated":
        holders = simulator.generate_protocol_dominated_distribution(num_holders=num_holders)
    elif distribution_type == "community":
        holders = simulator.generate_community_distribution(num_holders=num_holders)
    else:
        raise ValueError(
            f"Unsupported distribution type: {distribution_type}. "
            f"Use 'power_law', 'protocol_dominated', or 'community'."
        )

    # Format response
    response = simulator.generate_token_holders_response(holders)

    # Calculate advanced metrics
    quantities = [float(h["TokenHolderQuantity"]) for h in holders]
    advanced_metrics = calculate_all_concentration_metrics(quantities)

    # Create complete result with metadata
    result = {
        "token": f"Simulated_{distribution_type.capitalize()}",
        "distribution_type": distribution_type,
        "num_holders": num_holders,
        "timestamp": datetime.now().timestamp(),
        "holders": response["result"],
        "metrics": {
            "concentration": {
                "top_5_percentage": sum(float(h["TokenHolderPercentage"]) for h in holders[:5]),
                "top_10_percentage": sum(float(h["TokenHolderPercentage"]) for h in holders[:10]),
                "top_20_percentage": sum(float(h["TokenHolderPercentage"]) for h in holders[:20]),
                "top_50_percentage": sum(float(h["TokenHolderPercentage"]) for h in holders[:50]),
            },
            "advanced": advanced_metrics,
        },
    }

    # Save to file if requested
    if output_file:
        output_path = os.path.join("data", output_file)
        os.makedirs("data", exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        logger.info(f"Simulated data saved to {output_path}")

    return result


def generate_report(tokens: List[str], output_dir: Optional[str] = None) -> str:
    """Generate a simple text report for token distribution analysis.

    Args:
        tokens: List of token names to include in the report
        output_dir: Optional directory to save the report

    Returns:
        Path to the generated report

    """
    logger.info(f"Generating simple text report for tokens: {', '.join(tokens)}")

    # Analyze each token
    results = {}
    for token in tokens:
        try:
            results[token] = analyze_token(token)
        except Exception as e:
            logger.error(f"Error analyzing {token}: {str(e)}")

    # Generate simple text report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"token_report_{timestamp}.txt"

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, report_filename)
    else:
        os.makedirs("reports", exist_ok=True)
        report_path = os.path.join("reports", report_filename)

    with open(report_path, "w") as f:
        f.write("Governance Token Distribution Analysis Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for token, data in results.items():
            f.write(f"{token.upper()} Analysis\n")
            f.write("-" * 20 + "\n")

            if "metrics" in data:
                metrics = data["metrics"]
                f.write(
                    f"Gini Coefficient: {metrics.get('gini_coefficient', 'N/A'):.4f}\n"
                )
                f.write(
                    f"Herfindahl Index: {metrics.get('herfindahl_index', 'N/A'):.4f}\n"
                )

                if "concentration" in metrics:
                    conc = metrics["concentration"]
                    f.write("Concentration Metrics:\n")
                    for key, value in conc.items():
                        if key.startswith("top_"):
                            f.write(
                                f"  {key.replace('_', ' ').title()}: {value:.2f}%\n"
                            )

            f.write(f"Number of holders analyzed: {data.get('num_holders', 'N/A')}\n")
            f.write("\n")

    logger.info(f"Text report generated at {report_path}")
    return report_path


def main():
    """Execute the main CLI entry point."""
    parser = argparse.ArgumentParser(description="Governance Token Distribution Analyzer")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze a single token
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single token distribution")
    analyze_parser.add_argument("token", choices=["compound", "uniswap", "aave"], help="Token to analyze")
    analyze_parser.add_argument("--limit", type=int, default=100, help="Number of top holders to analyze")

    # Compare multiple tokens
    compare_parser = subparsers.add_parser("compare", help="Compare multiple token distributions")
    compare_parser.add_argument(
        "tokens",
        nargs="+",
        choices=["compound", "uniswap", "aave"],
        help="Tokens to compare",
    )
    compare_parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of top holders to analyze per token",
    )
    compare_parser.add_argument(
        "--format",
        choices=["json", "report"],
        default="json",
        help="Output format (default: json)",
    )

    # Generate simulated data
    simulate_parser = subparsers.add_parser("simulate", help="Generate simulated token distribution data")
    simulate_parser.add_argument(
        "distribution_type",
        choices=["power_law", "protocol_dominated", "community"],
        help="Type of distribution to simulate",
    )
    simulate_parser.add_argument("--holders", type=int, default=100, help="Number of holders to simulate")
    simulate_parser.add_argument("--output", type=str, help="Output filename")

    # Generate report
    report_parser = subparsers.add_parser("report", help="Generate analysis report")
    report_parser.add_argument(
        "tokens",
        nargs="+",
        choices=["compound", "uniswap", "aave"],
        help="Tokens to include in the report",
    )
    report_parser.add_argument("--output-dir", type=str, default=None, help="Directory to save the report")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    try:
        if args.command == "analyze":
            results = analyze_token(args.token, args.limit)
            # Print a summary to console
            print(f"\n=== {args.token.upper()} Token Distribution Analysis ===")
            print(f"Analyzed {len(results.get('holders', []))} token holders")

            # Print key metrics
            if "metrics" in results:
                metrics = results["metrics"]
                if "gini_coefficient" in metrics:
                    print(f"Gini Coefficient: {metrics['gini_coefficient']:.4f}")
                if "herfindahl_index" in metrics:
                    print(f"Herfindahl Index: {metrics['herfindahl_index']:.4f}")
                if "concentration" in metrics:
                    conc = metrics["concentration"]
                    print("\nConcentration:")
                    for key, value in conc.items():
                        if key.startswith("top_"):
                            print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")

        elif args.command == "compare":
            results = compare_tokens(args.tokens, args.limit, args.format)

            # Print a comparison summary to console
            print("\n=== Token Distribution Comparison ===")
            for token, data in results.items():
                print(f"\n{token.upper()}")
                if "metrics" in data and "gini_coefficient" in data["metrics"]:
                    print(f"  Gini Coefficient: {data['metrics']['gini_coefficient']:.4f}")
                if "metrics" in data and "concentration" in data["metrics"]:
                    print(f"  Top 10 Holders: {data['metrics']['concentration'].get('top_10_percentage', 0):.2f}%")

        elif args.command == "simulate":
            output_file = args.output or f"simulated_{args.distribution_type}_{args.holders}.json"
            results = generate_simulated_data(args.distribution_type, args.holders, output_file)

            # Print simulation summary
            print(f"\n=== Simulated {args.distribution_type.capitalize()} Distribution ===")
            print(f"Generated {args.holders} token holders")

            # Print key metrics
            if "metrics" in results:
                metrics = results["metrics"]
                if "advanced" in metrics:
                    advanced = metrics["advanced"]
                    print("\nAdvanced Metrics:")
                    for key, value in advanced.items():
                        print(f"  {key.replace('_', ' ').title()}: {value:.4f}")
                if "concentration" in metrics:
                    conc = metrics["concentration"]
                    print("\nConcentration:")
                    for key, value in conc.items():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")

        elif args.command == "report":
            report_path = generate_report(args.tokens, args.output_dir)
            print(f"\nReport generated: {report_path}")
            print("Open this file in a text editor to view the report.")

    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
