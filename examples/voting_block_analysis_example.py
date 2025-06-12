#!/usr/bin/env python3
"""
Voting Block Analysis Example

This example demonstrates how to use the voting block analysis module to identify
coordinated governance participation and analyze voting patterns in DeFi protocols.
"""

import os
import json
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to the path to import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from governance_token_analyzer.core.voting_block_analysis import (
    VotingBlockAnalyzer,
    analyze_proposal_influence,
    detect_voting_anomalies,
)
from governance_token_analyzer.core.historical_data import (
    HistoricalDataManager,
    simulate_historical_data,
)


def generate_sample_voting_data(num_proposals=10, num_voters=50, num_blocks=3):
    """Generate sample voting data for demonstration purposes."""
    proposals = []

    # Create voters with different voting behaviors based on blocks
    voters = []
    for i in range(num_voters):
        block_id = i % num_blocks
        voters.append(
            {
                "address": f"0x{i:040x}",
                "balance": 100 * (num_voters - i)
                + np.random.normal(0, 10),  # Larger balance for lower index
                "block": block_id,
            }
        )

    # Generate proposals with votes
    for i in range(num_proposals):
        votes = []
        participation_rate = np.random.uniform(0.3, 0.8)  # 30-80% participation

        # Decide outcome based on proposal number
        if i % 2 == 0:
            desired_outcome = "passed"
            base_support = 0.7  # 70% base support
        else:
            desired_outcome = "rejected"
            base_support = 0.3  # 30% base support

        # Create votes
        for voter in voters:
            # Skip some voters based on participation rate
            if np.random.random() > participation_rate:
                continue

            # Decide vote based on block and some randomness
            block_id = voter["block"]
            block_support_adjustment = 0.2 * (
                block_id - num_blocks // 2
            )  # Different blocks vote differently

            support_probability = base_support + block_support_adjustment
            support = 1 if np.random.random() < support_probability else 0

            votes.append(
                {
                    "voter": voter["address"],
                    "support": support,
                    "voting_power": voter["balance"],
                }
            )

        # Calculate actual outcome based on votes
        power_for = sum(v["voting_power"] for v in votes if v["support"] == 1)
        power_against = sum(v["voting_power"] for v in votes if v["support"] == 0)
        actual_outcome = "passed" if power_for > power_against else "rejected"

        proposals.append(
            {
                "id": f"PROP-{i + 1}",
                "title": f"Proposal {i + 1}",
                "description": f"This is a sample proposal {i + 1}",
                "votes": votes,
                "outcome": actual_outcome,
                "created_at": (
                    datetime.now() - timedelta(days=num_proposals - i)
                ).isoformat(),
            }
        )

    return proposals, [v for v in voters]


def main():
    """Run the voting block analysis example."""
    print("Governance Token Distribution Analysis Tool - Voting Block Analysis Example")
    print("=" * 80)

    # Generate sample data
    print("\n1. Generating sample voting data...")
    proposals, token_holders = generate_sample_voting_data(
        num_proposals=10, num_voters=50, num_blocks=3
    )

    print(
        f"  Generated {len(proposals)} proposals with {len(token_holders)} token holders"
    )

    # Create token balance map
    token_balances = {holder["address"]: holder["balance"] for holder in token_holders}

    # Initialize the voting block analyzer
    print("\n2. Analyzing voting blocks...")
    analyzer = VotingBlockAnalyzer()

    # Load voting data
    analyzer.load_voting_data(proposals)
    print(f"  Loaded voting data for {len(analyzer.voting_history)} addresses")

    # Calculate voting similarity
    similarity_df = analyzer.calculate_voting_similarity(min_overlap=2)
    print(f"  Calculated voting similarity matrix of shape {similarity_df.shape}")

    # Identify voting blocks
    voting_blocks = analyzer.identify_voting_blocks(similarity_threshold=0.7)
    print(f"  Identified {len(voting_blocks)} voting blocks:")
    for i, block in enumerate(voting_blocks):
        print(f"    Block {i + 1}: {len(block)} addresses")

    # Calculate voting power by block (method uses self.voting_blocks internally)
    block_power = analyzer.calculate_voting_power(token_balances)
    print("\n3. Voting block power analysis:")
    for block_id, data in block_power.items():
        print(
            f"  {block_id}: {data['address_count']} addresses, "
            f"{data['total_tokens']:.1f} tokens ({data['percentage']:.1f}% of total)"
        )

    # Analyze block voting patterns
    if voting_blocks:
        print("\n4. Analyzing voting patterns for the largest block...")
        largest_block = max(voting_blocks, key=len)
        patterns = analyzer.get_block_voting_patterns(largest_block)

        print(f"  Block size: {patterns['block_size']} addresses")
        print(f"  Average participation: {patterns['avg_participation']:.1f}%")
        print(f"  Average consensus: {patterns['avg_consensus']:.1f}%")
        print(f"  Voted on {len(patterns['proposals'])} proposals")

    # Visualize voting blocks
    print("\n5. Creating voting block visualization...")
    fig = analyzer.visualize_voting_blocks(token_balances)

    # Save the figure
    output_dir = "examples/outputs"
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(f"{output_dir}/voting_blocks.png")
    plt.close(fig)
    print(f"  Saved visualization to {output_dir}/voting_blocks.png")

    # Analyze proposal influence
    print("\n6. Analyzing proposal influence...")
    influence = analyze_proposal_influence(proposals, token_balances)

    print(f"  Analyzed influence for {len(influence)} proposals")
    for prop_id, data in list(influence.items())[:3]:  # Show first 3 proposals
        print(
            f"  {prop_id} ({data['outcome']}): "
            f"Participation: {data['participation_percentage']:.1f}%, "
            f"Top 10 influence: {data['top_10_influence']['percentage_of_supply']:.1f}% of supply"
        )

    # Detect voting anomalies
    print("\n7. Detecting voting anomalies...")
    anomalies = detect_voting_anomalies(proposals, token_holders)

    print(f"  Detected anomalies:")
    for category, items in anomalies.items():
        print(f"    {category}: {len(items)} instances")

    print("\nVoting block analysis complete!")


if __name__ == "__main__":
    main()
