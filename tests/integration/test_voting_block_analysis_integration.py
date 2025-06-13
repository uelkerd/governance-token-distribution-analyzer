"""Integration tests for voting block analysis functionality.
"""

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from governance_token_analyzer.core.voting_block_analysis import (
    VotingBlockAnalyzer,
    analyze_proposal_influence,
    detect_voting_anomalies,
)


class TestVotingBlockAnalysisIntegration:
    """Integration tests for voting block analysis functionality."""

    @pytest.fixture
    def temp_data_dir(self, test_data_dir):
        """Fixture to create a temporary directory for test data."""
        temp_dir = test_data_dir / "voting_block_analysis"
        temp_dir.mkdir(exist_ok=True)
        yield temp_dir
        # We don't remove the directory to keep test artifacts for inspection

    @pytest.fixture
    def sample_proposals(self):
        """Generate a larger set of sample proposals for integration testing."""
        num_proposals = 10
        num_voters = 100
        num_blocks = 3

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

        return proposals

    @pytest.fixture
    def token_holders(self, sample_proposals):
        """Create token holders from sample proposals."""
        # Extract unique addresses and assign balances
        addresses = set()
        for proposal in sample_proposals:
            for vote in proposal["votes"]:
                addresses.add(vote["voter"])

        # Create token holders with balances
        holders = []
        total_balance = 0
        for i, address in enumerate(addresses):
            balance = 1000.0 / (i + 1)  # Decreasing balance distribution
            holders.append({"address": address, "balance": balance})
            total_balance += balance

        # Calculate percentages
        for holder in holders:
            holder["percentage"] = (holder["balance"] / total_balance) * 100

        return holders

    @pytest.fixture
    def token_balances(self, token_holders):
        """Create a dictionary mapping addresses to token balances."""
        return {holder["address"]: holder["balance"] for holder in token_holders}

    def test_end_to_end_voting_block_analysis(
        self, sample_proposals, token_balances, temp_data_dir
    ):
        """Test the entire voting block analysis workflow."""
        # Initialize analyzer
        analyzer = VotingBlockAnalyzer()

        # Load voting data
        analyzer.load_voting_data(sample_proposals)

        # Calculate voting similarity
        similarity_df = analyzer.calculate_voting_similarity(min_overlap=2)

        # Save similarity matrix for inspection
        similarity_df.to_csv(temp_data_dir / "similarity_matrix.csv")

        # Identify voting blocks
        voting_blocks = analyzer.identify_voting_blocks(similarity_threshold=0.7)

        # Save voting blocks for inspection
        with open(temp_data_dir / "voting_blocks.json", "w") as f:
            json.dump([list(block) for block in voting_blocks], f, indent=2)

        # Calculate voting power (method uses self.voting_blocks internally)
        block_power = analyzer.calculate_voting_power(token_balances)

        # Save block power data
        with open(temp_data_dir / "block_power.json", "w") as f:
            # Convert to serializable format
            serializable_power = {}
            for block_id, data in block_power.items():
                serializable_power[block_id] = {
                    "addresses": list(data["addresses"]),
                    "address_count": data["address_count"],
                    "total_tokens": float(data["total_tokens"]),
                    "percentage": float(data["percentage"]),
                }
            json.dump(serializable_power, f, indent=2)

        # Skip visualization test due to matplotlib/numpy compatibility issues
        # fig = analyzer.visualize_voting_blocks(token_balances)
        # fig.savefig(temp_data_dir / "voting_blocks_visualization.png")
        # plt.close(fig)

        # Verify results
        assert not similarity_df.empty, "Similarity matrix should not be empty"
        assert len(voting_blocks) > 0, "Should identify at least one voting block"
        assert len(block_power) == len(
            voting_blocks
        ), "Should calculate power for all blocks"

        # Verify block power calculations are reasonable
        total_percentage = sum(data["percentage"] for data in block_power.values())
        assert (
            total_percentage <= 100.1
        ), "Total block percentage should not exceed 100%"

    def test_proposal_influence_analysis(
        self, sample_proposals, token_balances, temp_data_dir
    ):
        """Test the proposal influence analysis functionality."""
        # Analyze proposal influence
        influence = analyze_proposal_influence(sample_proposals, token_balances)

        # Save influence data
        with open(temp_data_dir / "proposal_influence.json", "w") as f:
            # Convert to serializable format
            serializable_influence = {}
            for prop_id, data in influence.items():
                serializable_influence[prop_id] = {
                    k: (float(v) if isinstance(v, (np.float64, np.float32)) else v)
                    for k, v in data.items()
                    if k != "top_voters" and k != "all_voters"
                }
                # Handle nested dictionaries
                if "top_10_influence" in data:
                    serializable_influence[prop_id]["top_10_influence"] = {
                        k: (float(v) if isinstance(v, (np.float64, np.float32)) else v)
                        for k, v in data["top_10_influence"].items()
                    }
            json.dump(serializable_influence, f, indent=2)

        # Verify results
        assert len(influence) == len(sample_proposals), "Should analyze all proposals"

        # Check that each proposal has the expected fields
        for prop_id, data in influence.items():
            assert "outcome" in data, "Each proposal should have an outcome"
            assert (
                "participation_percentage" in data
            ), "Each proposal should have participation data"
            assert (
                "top_10_influence" in data
            ), "Each proposal should have top 10 influence data"

    def test_anomaly_detection(self, sample_proposals, token_holders, temp_data_dir):
        """Test the voting anomaly detection functionality."""
        # Detect voting anomalies
        anomalies = detect_voting_anomalies(sample_proposals, token_holders)

        # Save anomaly data
        with open(temp_data_dir / "voting_anomalies.json", "w") as f:
            # Convert to serializable format
            serializable_anomalies = {}
            for category, items in anomalies.items():
                serializable_anomalies[category] = [
                    {
                        k: (float(v) if isinstance(v, (np.float64, np.float32)) else v)
                        for k, v in item.items()
                    }
                    for item in items
                ]
            json.dump(serializable_anomalies, f, indent=2)

        # Verify results
        assert isinstance(anomalies, dict), "Should return a dictionary of anomalies"
        assert len(anomalies) > 0, "Should detect at least one type of anomaly"

    def test_error_handling(self, sample_proposals, token_balances):
        """Test error handling in the voting block analysis module."""
        # Test with empty proposals
        empty_result = analyze_proposal_influence([], token_balances)
        assert (
            isinstance(empty_result, dict) and len(empty_result) == 0
        ), "Should return empty dict for empty proposals"

        # Test with invalid proposals (it should skip them and not raise an error)
        invalid_proposals = [{"id": "PROP-X"}]  # Missing votes
        analyzer = VotingBlockAnalyzer()
        analyzer.load_voting_data(invalid_proposals)
        assert len(analyzer.voting_history) == 0, "Should skip invalid proposals"

        # Test handling for NaN values in token balances
        modified_balances = token_balances.copy()
        modified_balances[list(token_balances.keys())[0]] = float("nan")

        # This should not raise an exception but handle the NaN gracefully
        analyzer = VotingBlockAnalyzer()
        analyzer.load_voting_data(sample_proposals)
        analyzer.calculate_voting_similarity()
        blocks = analyzer.identify_voting_blocks()
        power_with_nan = analyzer.calculate_voting_power(modified_balances)
        assert isinstance(power_with_nan, dict), "Should handle NaN values gracefully"

        # Test with empty token balances
        analyzer = VotingBlockAnalyzer()
        analyzer.load_voting_data(sample_proposals)
        analyzer.calculate_voting_similarity()
        blocks = analyzer.identify_voting_blocks()
        empty_power = analyzer.calculate_voting_power({})
        assert isinstance(
            empty_power, dict
        ), "Should handle empty token balances gracefully"

    def test_cross_integration_with_historical_data(
        self, sample_proposals, token_balances, temp_data_dir
    ):
        """Test integration between voting block analysis and historical data tracking."""
        # Create snapshots of voting blocks over time
        snapshots = []

        # Simulate 3 snapshots with evolving voting patterns
        for i in range(3):
            # Modify some votes to simulate evolving patterns
            modified_proposals = self._modify_proposals_for_snapshot(
                sample_proposals, i
            )

            # Analyze voting blocks
            analyzer = VotingBlockAnalyzer()
            analyzer.load_voting_data(modified_proposals)
            analyzer.calculate_voting_similarity()
            blocks = analyzer.identify_voting_blocks()
            block_power = analyzer.calculate_voting_power(token_balances)

            # Save snapshot
            snapshot = {
                "timestamp": (
                    datetime.now() - timedelta(days=30 * (2 - i))
                ).isoformat(),
                "num_blocks": len(blocks),
                "total_addresses": sum(len(block) for block in blocks),
                "block_power": {
                    block_id: {
                        "percentage": float(data["percentage"]),
                        "address_count": data["address_count"],
                    }
                    for block_id, data in block_power.items()
                },
            }
            snapshots.append(snapshot)

        # Save snapshots
        with open(temp_data_dir / "voting_block_snapshots.json", "w") as f:
            json.dump(snapshots, f, indent=2)

        # Create a simple trend analysis
        trends = pd.DataFrame(
            [
                {
                    "timestamp": datetime.fromisoformat(s["timestamp"]),
                    "num_blocks": s["num_blocks"],
                    "total_addresses": s["total_addresses"],
                }
                for s in snapshots
            ]
        )

        # Save trend analysis
        trends.to_csv(temp_data_dir / "voting_block_trends.csv", index=False)

        # Verify results
        assert len(snapshots) == 3, "Should create 3 snapshots"
        assert not trends.empty, "Should create trend analysis"

        # Skip visualization due to matplotlib/numpy compatibility issues
        # fig, ax = plt.subplots(figsize=(10, 6))
        # ax.plot(trends['timestamp'], trends['num_blocks'], marker='o', label='Number of Voting Blocks')
        # ax.plot(trends['timestamp'], trends['total_addresses'], marker='s', label='Total Addresses in Blocks')
        # ax.set_title('Voting Block Trends Over Time')
        # ax.set_xlabel('Date')
        # ax.set_ylabel('Count')
        # ax.legend()
        # fig.savefig(temp_data_dir / "voting_block_trends.png")
        # plt.close(fig)

    def _modify_proposals_for_snapshot(self, proposals, snapshot_index):
        """Modify proposals for historical snapshots."""
        import copy

        modified = copy.deepcopy(proposals)

        # Modify votes based on snapshot index to simulate evolving patterns
        for proposal in modified:
            votes = proposal["votes"]

            # First snapshot: original
            if snapshot_index == 0:
                pass
            # Second snapshot: some voters change behavior
            elif snapshot_index == 1:
                for i, vote in enumerate(votes):
                    if i % 5 == 0:  # Every 5th voter changes
                        vote["support"] = 1 - vote["support"]  # Flip the vote
            # Third snapshot: more coordinated voting
            elif snapshot_index == 2:
                for i, vote in enumerate(votes):
                    addr = vote["voter"]
                    addr_num = (
                        int(addr.replace("0x", ""), 16) % 100
                    )  # Extract number from address

                    # Make votes more coordinated by block
                    if addr_num < 33:
                        vote["support"] = 1  # Block 1 votes yes
                    elif addr_num < 66:
                        vote["support"] = 0  # Block 2 votes no
                    else:
                        # Block 3 votes with the majority
                        yes_votes = sum(1 for v in votes if v.get("support") == 1)
                        no_votes = sum(1 for v in votes if v.get("support") == 0)
                        vote["support"] = 1 if yes_votes > no_votes else 0

        return modified
