#!/usr/bin/env python
"""
Governance Token Distribution Analyzer CLI

This module provides a command-line interface for analyzing governance token
distributions across multiple DeFi protocols.
"""

import argparse
import logging
import sys
import os
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import analyzer modules
try:
    from src.token_analysis import CompoundAnalyzer, TokenAnalyzer
    from src.uniswap_analysis import UniswapAnalyzer
    from src.aave_analysis import AaveAnalyzer
    from src.analyzer.advanced_metrics import calculate_all_concentration_metrics
    from src.analyzer.data_simulator import TokenDistributionSimulator
    from src.analyzer.governance_metrics import GovernanceEffectivenessAnalyzer
    from src.generate_report import ReportGenerator
except ImportError:
    # Adjust path for running directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.token_analysis import CompoundAnalyzer, TokenAnalyzer
    from src.uniswap_analysis import UniswapAnalyzer
    from src.aave_analysis import AaveAnalyzer
    from src.analyzer.advanced_metrics import calculate_all_concentration_metrics
    from src.analyzer.data_simulator import TokenDistributionSimulator
    from src.analyzer.governance_metrics import GovernanceEffectivenessAnalyzer
    from src.generate_report import ReportGenerator

def analyze_token(token_name: str, limit: int = 100) -> Dict[str, Any]:
    """
    Analyze a specific token's distribution.
    
    Args:
        token_name: Name of the token to analyze (compound, uniswap, aave)
        limit: Number of token holders to analyze
        
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing {token_name} token distribution (top {limit} holders)")
    
    # Select the appropriate analyzer
    if token_name.lower() == 'compound':
        analyzer = CompoundAnalyzer()
    elif token_name.lower() == 'uniswap':
        analyzer = UniswapAnalyzer()
    elif token_name.lower() == 'aave':
        analyzer = AaveAnalyzer()
    else:
        raise ValueError(f"Unsupported token: {token_name}. Please use 'compound', 'uniswap', or 'aave'.")
    
    # Perform analysis
    results = analyzer.analyze_distribution(limit=limit)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{token_name.lower()}_analysis_{timestamp}.json"
    output_path = analyzer.save_analysis_results(results, filename)
    
    logger.info(f"Analysis results saved to {output_path}")
    return results

def compare_tokens(tokens: List[str], limit: int = 100, output_format: str = 'json') -> Dict[str, Dict[str, Any]]:
    """
    Compare distribution metrics across multiple tokens.
    
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
    
    with open(os.path.join('data', output_file), 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Comparison results saved to data/{output_file}")
    
    # Generate report if requested
    if output_format.lower() == 'report':
        try:
            generator = ReportGenerator()
            report_path = generator.generate_full_report(tokens)
            logger.info(f"Generated HTML report at {report_path}")
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
    
    return results

def generate_simulated_data(distribution_type: str, 
                          num_holders: int = 100, 
                          output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate simulated token distribution data for testing.
    
    Args:
        distribution_type: Type of distribution ('power_law', 'protocol_dominated', 'community')
        num_holders: Number of token holders to simulate
        output_file: Optional filename to save results
        
    Returns:
        Dictionary with simulated token holder data
    """
    logger.info(f"Generating simulated {distribution_type} distribution with {num_holders} holders")
    
    simulator = TokenDistributionSimulator(seed=42)  # Fixed seed for reproducibility
    
    # Generate the specified distribution
    if distribution_type == 'power_law':
        holders = simulator.generate_power_law_distribution(num_holders=num_holders)
    elif distribution_type == 'protocol_dominated':
        holders = simulator.generate_protocol_dominated_distribution(num_holders=num_holders)
    elif distribution_type == 'community':
        holders = simulator.generate_community_distribution(num_holders=num_holders)
    else:
        raise ValueError(f"Unsupported distribution type: {distribution_type}. "
                         f"Use 'power_law', 'protocol_dominated', or 'community'.")
    
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
            "advanced": advanced_metrics
        }
    }
    
    # Save to file if requested
    if output_file:
        output_path = os.path.join('data', output_file)
        os.makedirs('data', exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Simulated data saved to {output_path}")
    
    return result

def generate_report(tokens: List[str], output_dir: Optional[str] = None) -> str:
    """
    Generate a comprehensive HTML report for token distribution analysis.
    
    Args:
        tokens: List of token names to include in the report
        output_dir: Optional directory to save the report
        
    Returns:
        Path to the generated report
    """
    logger.info(f"Generating report for tokens: {', '.join(tokens)}")
    
    generator = ReportGenerator(output_dir=output_dir)
    report_path = generator.generate_full_report(tokens)
    
    logger.info(f"Report generated at {report_path}")
    return report_path

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Governance Token Distribution Analyzer')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Analyze a single token
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single token distribution')
    analyze_parser.add_argument('token', choices=['compound', 'uniswap', 'aave'], 
                                help='Token to analyze')
    analyze_parser.add_argument('--limit', type=int, default=100, 
                                help='Number of top holders to analyze')
    
    # Compare multiple tokens
    compare_parser = subparsers.add_parser('compare', help='Compare multiple token distributions')
    compare_parser.add_argument('tokens', nargs='+', choices=['compound', 'uniswap', 'aave'], 
                                help='Tokens to compare')
    compare_parser.add_argument('--limit', type=int, default=100, 
                                help='Number of top holders to analyze per token')
    compare_parser.add_argument('--format', choices=['json', 'report'], default='json',
                                help='Output format (default: json)')
    
    # Generate simulated data
    simulate_parser = subparsers.add_parser('simulate', 
                                           help='Generate simulated token distribution data')
    simulate_parser.add_argument('distribution_type', 
                                choices=['power_law', 'protocol_dominated', 'community'],
                                help='Type of distribution to simulate')
    simulate_parser.add_argument('--holders', type=int, default=100,
                                help='Number of holders to simulate')
    simulate_parser.add_argument('--output', type=str, 
                                help='Output filename')
    
    # Generate report
    report_parser = subparsers.add_parser('report', help='Generate analysis report')
    report_parser.add_argument('tokens', nargs='+', choices=['compound', 'uniswap', 'aave'],
                              help='Tokens to include in the report')
    report_parser.add_argument('--output-dir', type=str, default=None,
                              help='Directory to save the report')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        if args.command == 'analyze':
            results = analyze_token(args.token, args.limit)
            # Print a summary to console
            print(f"\n=== {args.token.upper()} Token Distribution Analysis ===")
            print(f"Analyzed {len(results.get('holders', []))} token holders")
            
            # Print key metrics
            if 'metrics' in results:
                metrics = results['metrics']
                if 'gini_coefficient' in metrics:
                    print(f"Gini Coefficient: {metrics['gini_coefficient']:.4f}")
                if 'herfindahl_index' in metrics:
                    print(f"Herfindahl Index: {metrics['herfindahl_index']:.4f}")
                if 'concentration' in metrics:
                    conc = metrics['concentration']
                    print("\nConcentration:")
                    for key, value in conc.items():
                        if key.startswith('top_'):
                            print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")
            
        elif args.command == 'compare':
            results = compare_tokens(args.tokens, args.limit, args.format)
            
            # Print a comparison summary to console
            print("\n=== Token Distribution Comparison ===")
            for token, data in results.items():
                print(f"\n{token.upper()}")
                if 'metrics' in data and 'gini_coefficient' in data['metrics']:
                    print(f"  Gini Coefficient: {data['metrics']['gini_coefficient']:.4f}")
                if 'metrics' in data and 'concentration' in data['metrics']:
                    print(f"  Top 10 Holders: {data['metrics']['concentration'].get('top_10_percentage', 0):.2f}%")
            
        elif args.command == 'simulate':
            output_file = args.output or f"simulated_{args.distribution_type}_{args.holders}.json"
            results = generate_simulated_data(args.distribution_type, args.holders, output_file)
            
            # Print simulation summary
            print(f"\n=== Simulated {args.distribution_type.capitalize()} Distribution ===")
            print(f"Generated {args.holders} token holders")
            
            # Print key metrics
            if 'metrics' in results:
                metrics = results['metrics']
                if 'advanced' in metrics:
                    advanced = metrics['advanced']
                    print("\nAdvanced Metrics:")
                    for key, value in advanced.items():
                        print(f"  {key.replace('_', ' ').title()}: {value:.4f}")
                if 'concentration' in metrics:
                    conc = metrics['concentration']
                    print("\nConcentration:")
                    for key, value in conc.items():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")
            
        elif args.command == 'report':
            report_path = generate_report(args.tokens, args.output_dir)
            print(f"\nReport generated: {report_path}")
            print(f"Open this file in a web browser to view the report.")
            
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 