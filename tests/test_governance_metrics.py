import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.analyzer.governance_metrics import GovernanceEffectivenessAnalyzer


class TestGovernanceMetrics(unittest.TestCase):
    """Test the governance metrics analyzer functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = GovernanceEffectivenessAnalyzer()

        # Sample test data
        self.sample_proposals = [
            {
                "id": "PROP-1",
                "title": "Treasury Diversification",
                "status": "passed",
                "votes_cast": 1200000,
                "voter_addresses": ["0x123", "0x456", "0x789"],
                "voter_weights": [500000, 400000, 300000],
                "votes": ["for", "for", "against"],
                "proposer": "0x123",
                "comments": ["Great idea", "I support this", "Let's do it"],
                "revisions": 2,
                "passed_timestamp": datetime(2023, 1, 15).timestamp(),
                "implemented_timestamp": datetime(2023, 1, 25).timestamp(),
                "implemented": True,
                "protocol": "compound"
            },
            {
                "id": "PROP-2",
                "title": "Fee Adjustment",
                "status": "rejected",
                "votes_cast": 900000,
                "voter_addresses": ["0x123", "0x456", "0xabc"],
                "voter_weights": [500000, 300000, 100000],
                "votes": ["against", "against", "for"],
                "proposer": "0xabc",
                "comments": ["Not a good time", "Too aggressive"],
                "revisions": 0,
                "protocol": "compound"
            }
        ]

        self.token_distribution = [
            {"TokenHolderAddress": "0x123", "TokenHolderQuantity": "600000", "TokenHolderPercentage": "30.0"},
            {"TokenHolderAddress": "0x456", "TokenHolderQuantity": "400000", "TokenHolderPercentage": "20.0"},
            {"TokenHolderAddress": "0x789", "TokenHolderQuantity": "300000", "TokenHolderPercentage": "15.0"},
            {"TokenHolderAddress": "0xabc", "TokenHolderQuantity": "100000", "TokenHolderPercentage": "5.0"},
            {"TokenHolderAddress": "0xdef", "TokenHolderQuantity": "50000", "TokenHolderPercentage": "2.5"}
        ]

        self.total_eligible_votes = 2000000

    def test_calculate_voter_participation(self):
        """Test that voter participation metrics are calculated correctly."""
        # Create proposal votes data
        proposal_votes = [
            {
                "proposal_id": p["id"],
                "votes_cast": p["votes_cast"],
                "voter_addresses": p["voter_addresses"]
            }
            for p in self.sample_proposals
        ]

        # Calculate participation metrics
        metrics = self.analyzer.calculate_voter_participation(proposal_votes, self.total_eligible_votes)

        # Verify that all expected metrics are present
        self.assertIn("participation_rate", metrics)
        self.assertIn("average_votes_cast", metrics)
        self.assertIn("unique_voters_percentage", metrics)

        # Verify metric values
        # Average votes cast = (1200000 + 900000) / 2 = 1050000
        self.assertAlmostEqual(metrics["average_votes_cast"], 1050000)

        # Participation rate = (1050000 / 2000000) * 100 = 52.5%
        self.assertAlmostEqual(metrics["participation_rate"], 52.5)

        # Unique voters = {"0x123", "0x456", "0x789", "0xabc"} = 4
        # Unique voter percentage = (4 / 2000000) * 100 = 0.0002%
        # This is a simplification as we're treating each address as a token
        expected_unique_percentage = (4 / self.total_eligible_votes) * 100
        self.assertAlmostEqual(metrics["unique_voters_percentage"], expected_unique_percentage)

    def test_calculate_proposal_success_rate(self):
        """Test that proposal success rate metrics are calculated correctly."""
        # Calculate success metrics
        metrics = self.analyzer.calculate_proposal_success_rate(self.sample_proposals)

        # Verify that all expected metrics are present
        self.assertIn("proposal_success_rate", metrics)
        self.assertIn("proposal_implementation_rate", metrics)

        # Verify metric values
        # Success rate = (1 / 2) * 100 = 50%
        self.assertAlmostEqual(metrics["proposal_success_rate"], 50.0)

        # Implementation rate = (1 / 1) * 100 = 100%
        self.assertAlmostEqual(metrics["proposal_implementation_rate"], 100.0)

    def test_analyze_governance_effectiveness(self):
        """Test that the comprehensive governance effectiveness metrics are calculated correctly."""
        # Calculate all metrics
        all_metrics = self.analyzer.analyze_governance_effectiveness(
            self.sample_proposals,
            self.token_distribution,
            self.total_eligible_votes
        )

        # Verify that all expected metric categories are present
        self.assertIn("participation", all_metrics)
        self.assertIn("success", all_metrics)
        self.assertIn("timestamp", all_metrics)
        self.assertIn("protocol", all_metrics)

        # Verify protocol identification
        self.assertEqual(all_metrics["protocol"], "compound")

        # Verify participation metrics
        participation = all_metrics["participation"]
        self.assertIn("participation_rate", participation)
        self.assertIn("average_votes_cast", participation)
        self.assertIn("unique_voters_percentage", participation)

        # Verify success metrics
        success = all_metrics["success"]
        self.assertIn("proposal_success_rate", success)
        self.assertIn("proposal_implementation_rate", success)

    def test_empty_proposals(self):
        """Test that the analyzer handles empty proposal lists gracefully."""
        # Calculate metrics with empty proposals
        all_metrics = self.analyzer.analyze_governance_effectiveness(
            [],
            self.token_distribution,
            self.total_eligible_votes
        )

        # Verify that all expected metric categories are present but empty
        self.assertEqual(all_metrics["participation"], {})
        self.assertEqual(all_metrics["success"], {})
        self.assertIn("timestamp", all_metrics)
        self.assertEqual(all_metrics["protocol"], "unknown")

if __name__ == '__main__':
    unittest.main()
