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
except ImportError as exception:
    logger.error(f"Import error: {str(exception)}")
    # Fall back to relative imports if package is not installed
    try:
        from .core.advanced_metrics import calculate_all_concentration_metrics
        from .core.api_client import APIClient
        from .core.data_simulator import TokenDistributionSimulator
    except ImportError as exception:
        logger.error(f"Relative import error: {str(exception)}")
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

    except Exception as exception:
        logger.error(f"Analysis failed: {exception}")
        return {"error": str(exception), "protocol": token_name}


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

    logger.info(f"📊 Comparison complete! Results saved to data/{output_file}")

    if output_format == "report":
        # Generate a more human-readable report
        report_file = f"token_comparison_report_{timestamp}.txt"
        with open(os.path.join("data", report_file), "w") as f:
            f.write("GOVERNANCE TOKEN DISTRIBUTION COMPARISON\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")

            for token, data in results.items():
                f.write(f"TOKEN: {token.upper()}\n")
                f.write("-" * 30 + "\n")

                metrics = data.get("concentration_metrics", {})
                f.write(f"Gini Coefficient: {metrics.get('gini_coefficient', 'N/A'):.4f}\n")
                f.write(f"Nakamoto Coefficient: {metrics.get('nakamoto_coefficient', 'N/A')}\n")
                f.write(f"Top 10% Concentration: {data.get('top_10_concentration', 0):.2%}\n")
                f.write(f"Top 50% Concentration: {data.get('top_50_concentration', 0):.2%}\n")
                f.write("\n")

            f.write("\nCOMPARISON SUMMARY\n")
            f.write("-" * 30 + "\n")
            # Add a simple comparison summary
            gini_values = [
                (token, data.get("concentration_metrics", {}).get("gini_coefficient", 0))
                for token, data in results.items()
            ]
            gini_values.sort(key=lambda x: x[1], reverse=True)

            f.write("Most concentrated token (by Gini): ")
            if gini_values:
                f.write(f"{gini_values[0][0].upper()} ({gini_values[0][1]:.4f})\n")
            else:
                f.write("N/A\n")

        logger.info(f"📝 Report generated at data/{report_file}")

    return results


def analyze_proposal(
    protocol: str, proposal_id: int, output_format: str = "json"
) -> Dict[str, Any]:
    """Analyze voting patterns for a specific governance proposal.

    Args:
        protocol: Protocol name (compound, uniswap, aave)
        proposal_id: ID of the proposal to analyze
        output_format: Format for output ('json' or 'report')

    Returns:
        Dictionary with proposal analysis results

    """
    logger.info(f"Analyzing proposal {proposal_id} for {protocol}")

    # Create API client
    api_client = APIClient()

    try:
        # Get proposal details
        proposal = api_client.get_governance_proposal(
            protocol, proposal_id, use_real_data=True
        )
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found for {protocol}")
            return {"error": "Proposal not found"}

        # Get votes for the proposal
        votes = api_client.get_governance_votes(
            protocol, proposal_id, use_real_data=True
        )

        # Extract voting power for analysis
        for_votes = [v["votingPower"] for v in votes if v["support"] == 1]
        against_votes = [v["votingPower"] for v in votes if v["support"] == 0]
        abstain_votes = [v["votingPower"] for v in votes if v["support"] == 2]

        # Calculate voting power concentration
        for_metrics = calculate_all_concentration_metrics(for_votes) if for_votes else {}
        against_metrics = (
            calculate_all_concentration_metrics(against_votes) if against_votes else {}
        )

        # Prepare results
        results = {
            "protocol": protocol,
            "proposal_id": proposal_id,
            "title": proposal.get("title", f"Proposal {proposal_id}"),
            "status": proposal.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "total_votes": len(votes),
            "for_votes_count": len(for_votes),
            "against_votes_count": len(against_votes),
            "abstain_votes_count": len(abstain_votes),
            "for_votes_power": sum(for_votes),
            "against_votes_power": sum(against_votes),
            "abstain_votes_power": sum(abstain_votes),
            "for_votes_concentration": for_metrics,
            "against_votes_concentration": against_metrics,
            "top_voters": sorted(votes, key=lambda v: v["votingPower"], reverse=True)[
                :10
            ]
            if votes
            else [],
        }

        # Save results to file
        output_file = f"data/{protocol}_proposal_{proposal_id}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("data", exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"📊 Analysis complete! Results saved to {output_file}")

        # Display some key metrics
        total_power = (
            results["for_votes_power"]
            + results["against_votes_power"]
            + results["abstain_votes_power"]
        )
        if total_power > 0:
            logger.info(
                f"📈 Vote distribution: For {results['for_votes_power']/total_power:.1%}, "
                f"Against {results['against_votes_power']/total_power:.1%}, "
                f"Abstain {results['abstain_votes_power']/total_power:.1%}"
            )

        return results

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "protocol": protocol, "proposal_id": proposal_id}


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Governance Token Distribution Analyzer"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze token command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze a token's distribution"
    )
    analyze_parser.add_argument(
        "token", choices=["compound", "uniswap", "aave"], help="Token to analyze"
    )
    analyze_parser.add_argument(
        "--limit", type=int, default=100, help="Number of token holders to analyze"
    )
    analyze_parser.add_argument(
        "--format", choices=["json", "report"], default="json", help="Output format"
    )

    # Compare tokens command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare multiple token distributions"
    )
    compare_parser.add_argument(
        "--tokens",
        nargs="+",
        default=["compound", "uniswap", "aave"],
        help="Tokens to compare",
    )
    compare_parser.add_argument(
        "--limit", type=int, default=100, help="Number of token holders to analyze"
    )
    compare_parser.add_argument(
        "--format", choices=["json", "report"], default="json", help="Output format"
    )

    # Analyze proposal command
    proposal_parser = subparsers.add_parser(
        "proposal", help="Analyze a governance proposal"
    )
    proposal_parser.add_argument(
        "protocol", choices=["compound", "uniswap", "aave"], help="Protocol name"
    )
    proposal_parser.add_argument(
        "proposal_id", type=int, help="ID of the proposal to analyze"
    )
    proposal_parser.add_argument(
        "--format", choices=["json", "report"], default="json", help="Output format"
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command == "analyze":
        analyze_token(args.token, args.limit)
    elif args.command == "compare":
        compare_tokens(args.tokens, args.limit, args.format)
    elif args.command == "proposal":
        analyze_proposal(args.protocol, args.proposal_id, args.format)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
