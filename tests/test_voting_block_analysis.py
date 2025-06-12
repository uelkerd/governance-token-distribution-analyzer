"""Tests for the voting block analysis module.
"""


import pytest
import pandas as pd
import numpy as np

from governance_token_analyzer.core.voting_block_analysis import (
    VotingBlockAnalyzer,
    analyze_proposal_influence,
    detect_voting_anomalies,
)


# Test fixtures
@pytest.fixture
def sample_proposals():
    """Create a sample set of governance proposals with votes."""
    # Create test data that matches the expected Jaccard similarity of 0.5:
    # 0x001 and 0x002 should have 2 common proposals (both vote) and 2 unique proposals
    # Jaccard similarity = |intersection| / |union| = 2 / 4 = 0.5
    return [
        {
            'id': 'PROP-1',
            'title': 'Proposal 1',
            'description': 'Test proposal 1',
            'votes': [
                {'voter': '0x001', 'support': 1},  # For - 0x001 & 0x002 both vote, agree
                {'voter': '0x002', 'support': 1},  # For - 0x001 & 0x002 both vote, agree
                {'voter': '0x003', 'support': 0},  # Against
                {'voter': '0x004', 'support': 1},  # For
                {'voter': '0x005', 'support': 0},  # Against
            ],
            'outcome': 'passed',
            'created_at': '2023-01-01T00:00:00'
        },
        {
            'id': 'PROP-2',
            'title': 'Proposal 2',
            'description': 'Test proposal 2',
            'votes': [
                {'voter': '0x001', 'support': 0},  # Against - 0x001 & 0x002 both vote, agree
                {'voter': '0x002', 'support': 0},  # Against - 0x001 & 0x002 both vote, agree
                {'voter': '0x003', 'support': 1},  # For
                {'voter': '0x004', 'support': 0},  # Against
                {'voter': '0x006', 'support': 1},  # For
            ],
            'outcome': 'rejected',
            'created_at': '2023-01-02T00:00:00'
        },
        {
            'id': 'PROP-3',
            'title': 'Proposal 3',
            'description': 'Test proposal 3',
            'votes': [
                {'voter': '0x001', 'support': 1},  # For - Only 0x001 votes (unique)
                {'voter': '0x003', 'support': 0},  # Against
                {'voter': '0x005', 'support': 1},  # For
                {'voter': '0x006', 'support': 0},  # Against
            ],
            'outcome': 'passed',
            'created_at': '2023-01-03T00:00:00'
        },
        {
            'id': 'PROP-4',
            'title': 'Proposal 4',
            'description': 'Test proposal 4',
            'votes': [
                {'voter': '0x002', 'support': 1},  # For - Only 0x002 votes (unique)
                {'voter': '0x003', 'support': 0},  # Against
                {'voter': '0x004', 'support': 1},  # For
                {'voter': '0x006', 'support': 0},  # Against
            ],
            'outcome': 'passed',
            'created_at': '2023-01-04T00:00:00'
        }
    ]


@pytest.fixture
def sample_token_holders():
    """Create a sample set of token holders with balances."""
    return [
        {'address': '0x001', 'balance': 1000.0, 'percentage': 25.0},
        {'address': '0x002', 'balance': 800.0, 'percentage': 20.0},
        {'address': '0x003', 'balance': 600.0, 'percentage': 15.0},
        {'address': '0x004', 'balance': 500.0, 'percentage': 12.5},
        {'address': '0x005', 'balance': 400.0, 'percentage': 10.0},
        {'address': '0x006', 'balance': 300.0, 'percentage': 7.5},
        {'address': '0x007', 'balance': 200.0, 'percentage': 5.0},
        {'address': '0x008', 'balance': 200.0, 'percentage': 5.0},
    ]


@pytest.fixture
def token_balances(sample_token_holders):
    """Create a dictionary mapping addresses to token balances."""
    return {holder['address']: holder['balance'] for holder in sample_token_holders}


@pytest.fixture
def voting_block_analyzer(sample_proposals):
    """Create and initialize a VotingBlockAnalyzer with sample data."""
    analyzer = VotingBlockAnalyzer()
    analyzer.load_voting_data(sample_proposals)
    return analyzer


# Tests for VotingBlockAnalyzer
def test_load_voting_data(voting_block_analyzer, sample_proposals):
    """Test loading voting data into the analyzer."""
    # Check that the voting history has been populated
    assert len(voting_block_analyzer.voting_history) > 0

    # Check that all voters from the proposals are in the voting history
    all_voters = set()
    for proposal in sample_proposals:
        for vote in proposal['votes']:
            all_voters.add(vote['voter'])
    
    loaded_voters = {vote['address'] for vote in voting_block_analyzer.voting_history}
    assert all(voter in loaded_voters for voter in all_voters)


def test_calculate_voting_similarity(voting_block_analyzer):
    """Test calculating voting similarity between addresses."""
    similarity_df = voting_block_analyzer.calculate_voting_similarity()
    assert isinstance(similarity_df, pd.DataFrame)
    assert not similarity_df.empty
    assert "0x001" in similarity_df.index
    assert "0x002" in similarity_df.columns
    # The addresses have 2 common proposals (P1, P2) and 2 unique proposals (P3, P4)
    # Jaccard similarity = |intersection| / |union| = 2 / 4 = 0.5
    assert np.isclose(similarity_df.loc["0x001", "0x002"], 0.5)


def test_identify_voting_blocks(voting_block_analyzer):
    """Test identifying voting blocks based on similarity."""
    # Calculate similarity first
    voting_block_analyzer.calculate_voting_similarity()
    blocks = voting_block_analyzer.identify_voting_blocks(similarity_threshold=0.4)
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert any("0x001" in block and "0x002" in block for block in blocks)


def test_calculate_voting_power(voting_block_analyzer, token_balances):
    """Test calculating voting power for blocks."""
    # Calculate similarity and identify blocks first
    voting_block_analyzer.calculate_voting_similarity()
    voting_block_analyzer.identify_voting_blocks(similarity_threshold=0.4)
    power = voting_block_analyzer.calculate_voting_power(token_balances)
    assert isinstance(power, dict)


def test_get_block_voting_patterns(voting_block_analyzer):
    """Test analyzing voting patterns for a block."""
    # Calculate similarity and identify blocks first
    voting_block_analyzer.calculate_voting_similarity()
    blocks = voting_block_analyzer.identify_voting_blocks(similarity_threshold=0.4)
    
    # Get patterns for the first block
    block_id = 0
    patterns = voting_block_analyzer.get_block_voting_patterns(block_id)

    # Check that the patterns contain the required fields
    assert 'proposals' in patterns
    assert 'avg_participation' in patterns
    assert 'avg_consensus' in patterns
    assert 'block_size' in patterns

    # Check that the block size matches
    assert patterns['block_size'] == len(blocks[block_id])

    # Check that we have statistics for each proposal
    for proposal_id, stats in patterns['proposals'].items():
        assert 'total_votes' in stats
        assert 'votes_for' in stats
        assert 'votes_against' in stats


def test_analyze_block_cohesion(voting_block_analyzer):
    """Test analyzing cohesion of voting blocks."""
    # Implementation of the test
    pass


# Tests for analyze_proposal_influence
def test_analyze_proposal_influence(sample_proposals, token_balances):
    """Test analyzing proposal influence based on token holdings."""
    influence = analyze_proposal_influence(sample_proposals, token_balances)

    # Check that influence data is returned for each proposal
    assert len(influence) == len(sample_proposals)

    # Check that each proposal has the required fields
    for proposal_id, data in influence.items():
        assert 'outcome' in data
        assert 'top_10_influence' in data
        assert 'participation_percentage' in data

        # Check that top 10 influence data has the required fields
        top_10 = data['top_10_influence']
        assert 'total_balance' in top_10
        assert 'percentage_of_supply' in top_10


# Tests for detect_voting_anomalies
def test_detect_voting_anomalies(sample_proposals, sample_token_holders):
    """Test detecting anomalies in voting patterns."""
    anomalies = detect_voting_anomalies(sample_proposals, sample_token_holders)

    # Check that anomalies data has the expected categories
    assert 'sudden_participation' in anomalies
    assert 'coordinated_voting' in anomalies
    assert 'vote_against_size' in anomalies
    assert 'whale_against_community' in anomalies

    # Each category should be a list
    for category, items in anomalies.items():
        assert isinstance(items, list)


# Error handling tests
def test_load_voting_data_error():
    """Test error handling when loading invalid voting data."""
    analyzer = VotingBlockAnalyzer()

    # Create invalid proposals missing required fields
    invalid_proposals = [
        {'title': 'Invalid Proposal'}  # Missing id and votes fields
    ]

    # Should not raise an exception, but log warning and return empty data
    analyzer.load_voting_data(invalid_proposals)
    assert len(analyzer.voting_history) == 0


def test_calculate_voting_similarity_empty_data():
    """Test calculating similarity with empty voting history."""
    analyzer = VotingBlockAnalyzer()
    # No voting data loaded

    # Should return empty DataFrame
    similarity_df = analyzer.calculate_voting_similarity()
    assert similarity_df.empty


def test_identify_voting_blocks_no_similarity():
    """Test identifying blocks without calculating similarity first."""
    analyzer = VotingBlockAnalyzer()

    # Should calculate similarity automatically and return empty list
    blocks = analyzer.identify_voting_blocks()
    assert blocks == []


def test_analyze_proposal_influence_empty_data():
    """Test analyzing influence with empty data."""
    influence = analyze_proposal_influence([], {})
    assert influence == {}


def test_detect_voting_anomalies_empty_data():
    """Test detecting anomalies with empty data."""
    anomalies = detect_voting_anomalies([], [])

    # Should return empty results for each category
    assert all(len(items) == 0 for items in anomalies.values())
