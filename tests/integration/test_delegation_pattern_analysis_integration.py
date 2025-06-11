"""
Integration tests for delegation pattern analysis functionality.
"""

import os
import json
import pytest
import tempfile
import networkx as nx
from datetime import datetime, timedelta

from governance_token_analyzer.core import delegation_pattern_analysis as dpa
from governance_token_analyzer.core import historical_data
from governance_token_analyzer.core.exceptions import DataFormatError, AnalysisError


class TestDelegationPatternAnalysisIntegration:
    """Integration tests for delegation pattern analysis."""
    
    @pytest.fixture
    def sample_delegation_data(self):
        """Create sample delegation data."""
        # Create token holders
        token_holders = [
            {
                'address': f'0xholder{i}',
                'balance': 100000 - (i * 10000),
                'percentage': (100000 - (i * 10000)) / 300000
            }
            for i in range(10)
        ]
        
        # Create delegations
        delegations = [
            {
                'delegator': '0xholder3',
                'delegatee': '0xholder0',
                'amount': token_holders[3]['balance']
            },
            {
                'delegator': '0xholder4',
                'delegatee': '0xholder1',
                'amount': token_holders[4]['balance']
            },
            {
                'delegator': '0xholder5',
                'delegatee': '0xholder0',
                'amount': token_holders[5]['balance']
            },
            {
                'delegator': '0xholder7',
                'delegatee': '0xholder2',
                'amount': token_holders[7]['balance']
            },
            {
                'delegator': '0xholder8',
                'delegatee': '0xholder2',
                'amount': token_holders[8]['balance']
            },
            {
                'delegator': '0xholder9',
                'delegatee': '0xholder0',
                'amount': token_holders[9]['balance']
            }
        ]
        
        # Create protocol data
        protocol_data = {
            'governance_data': {
                'token_holders': token_holders,
                'delegations': delegations,
                'participation_rate': 65.5
            }
        }
        
        return protocol_data
    
    @pytest.fixture
    def sample_historical_data(self, sample_delegation_data):
        """Create sample historical delegation data."""
        base_data = sample_delegation_data
        
        # Create snapshots at different timestamps
        snapshots = []
        
        for i in range(3):
            timestamp = (datetime.now() - timedelta(days=30 * (2 - i))).isoformat()
            
            # Make a deep copy of the base data
            snapshot_data = {
                'timestamp': timestamp,
                'data': json.loads(json.dumps(base_data))
            }
            
            # Modify the data slightly for each snapshot
            if i == 1:
                # Add a new delegation in snapshot 1
                snapshot_data['data']['governance_data']['delegations'].append({
                    'delegator': '0xholder6',
                    'delegatee': '0xholder1',
                    'amount': 40000
                })
            elif i == 2:
                # Change a delegation in snapshot 2
                snapshot_data['data']['governance_data']['delegations'][0]['delegatee'] = '0xholder1'
            
            snapshots.append(snapshot_data)
        
        return snapshots
    
    def test_analyze_delegation_patterns(self, sample_delegation_data):
        """Test that delegation patterns can be analyzed for a protocol."""
        # Analyze delegation patterns
        results = dpa.analyze_delegation_patterns(sample_delegation_data)
        
        # Verify results structure
        assert 'delegation_network' in results
        assert 'influential_delegators' in results
        
        # Verify delegation network analysis
        network = results['delegation_network']
        assert 'metrics' in network
        assert 'key_delegatees' in network
        assert 'patterns' in network
        assert 'graph' in network
        
        # Verify metrics
        metrics = network['metrics']
        assert 'delegation_rate' in metrics
        assert 'delegator_count' in metrics
        assert 'delegatee_count' in metrics
        
        # Verify key delegatees
        delegatees = network['key_delegatees']
        assert len(delegatees) > 0
        
        # Verify influential delegators
        delegators = results['influential_delegators']
        assert isinstance(delegators, list)
    
    def test_historical_delegation_analysis(self, sample_historical_data):
        """Test that historical delegation patterns can be analyzed."""
        # Analyze historical delegation patterns
        results = dpa.analyze_historical_delegation_patterns(
            sample_historical_data,
            min_threshold=0.01,
            shift_threshold=0.05
        )
        
        # Verify results structure
        assert 'comparison' in results
        assert 'shifts' in results
        
        # Verify comparison results
        comparison = results['comparison']
        assert 'snapshots' in comparison
        assert len(comparison['snapshots']) == 3
        
        # Verify shifts
        shifts = results['shifts']
        assert 'significant_shifts' in shifts
        assert 'shift_metrics' in shifts
    
    def test_delegation_network_creation(self, sample_delegation_data):
        """Test that a delegation network can be created and analyzed."""
        # Create analyzer
        analyzer = dpa.DelegationPatternAnalyzer()
        
        # Create delegation graph
        governance_data = sample_delegation_data['governance_data']
        graph = analyzer._create_delegation_graph(
            governance_data['delegations'],
            governance_data['token_holders']
        )
        
        # Verify graph properties
        assert isinstance(graph, nx.DiGraph)
        assert len(graph.nodes()) == 10  # All holders should be nodes
        assert len(graph.edges()) == 6   # All delegations should be edges
        
        # Verify node data
        for node in graph.nodes():
            assert 'balance' in graph.nodes[node]
        
        # Verify edge data
        for _, _, data in graph.edges(data=True):
            assert 'amount' in data
    
    def test_key_delegatee_identification(self, sample_delegation_data):
        """Test that key delegatees can be identified."""
        # Create analyzer
        analyzer = dpa.DelegationPatternAnalyzer()
        
        # Create delegation graph
        governance_data = sample_delegation_data['governance_data']
        graph = analyzer._create_delegation_graph(
            governance_data['delegations'],
            governance_data['token_holders']
        )
        
        # Identify key delegatees
        key_delegatees = analyzer._identify_key_delegatees(
            graph,
            governance_data['token_holders']
        )
        
        # Verify key delegatees
        assert len(key_delegatees) > 0
        
        # Verify delegatee data structure
        for delegatee in key_delegatees:
            assert 'address' in delegatee
            assert 'own_balance' in delegatee
            assert 'delegated_amount' in delegatee
            assert 'total_voting_power' in delegatee
            assert 'percentage_of_supply' in delegatee
            assert 'delegator_count' in delegatee
    
    def test_error_handling(self):
        """Test that appropriate errors are raised for invalid input."""
        # Create analyzer
        analyzer = dpa.DelegationPatternAnalyzer()
        
        # Test missing delegations
        with pytest.raises(DataFormatError):
            analyzer.analyze_delegation_network({
                'token_holders': []
            })
        
        # Test missing token holders
        with pytest.raises(DataFormatError):
            analyzer.analyze_delegation_network({
                'delegations': []
            })
        
        # Test invalid historical data
        with pytest.raises(DataFormatError):
            dpa.analyze_historical_delegation_patterns("not a list")
    
    def test_circular_delegations(self):
        """Test that circular delegations can be detected."""
        # Create token holders
        token_holders = [
            {'address': f'0xcircle{i}', 'balance': 10000} 
            for i in range(5)
        ]
        
        # Create circular delegations
        delegations = [
            {'delegator': '0xcircle0', 'delegatee': '0xcircle1', 'amount': 10000},
            {'delegator': '0xcircle1', 'delegatee': '0xcircle2', 'amount': 10000},
            {'delegator': '0xcircle2', 'delegatee': '0xcircle0', 'amount': 10000},
            {'delegator': '0xcircle3', 'delegatee': '0xcircle4', 'amount': 10000},
            {'delegator': '0xcircle4', 'delegatee': '0xcircle3', 'amount': 10000}
        ]
        
        # Create protocol data
        protocol_data = {
            'governance_data': {
                'token_holders': token_holders,
                'delegations': delegations
            }
        }
        
        # Analyze delegation patterns
        results = dpa.analyze_delegation_patterns(protocol_data)
        
        # Verify circular delegations
        patterns = results['delegation_network']['patterns']
        circles = patterns['circular_delegations']
        
        assert len(circles) >= 2  # Should detect at least 2 circular delegation patterns
    
    def test_with_data_manager_integration(self, sample_historical_data, tmp_path):
        """Test integration with the HistoricalDataManager."""
        # Create a temporary data directory
        data_dir = tmp_path / "delegation_test_data"
        data_dir.mkdir()
        
        # Create a data manager
        data_manager = historical_data.HistoricalDataManager(str(data_dir))
        
        # Use a supported protocol
        protocol = "compound"
        
        # Store sample data
        for snapshot in sample_historical_data:
            data_manager.store_snapshot(
                protocol=protocol,
                data=snapshot['data'],
                timestamp=snapshot['timestamp']
            )
        
        # Retrieve the stored snapshots
        stored_snapshots = data_manager.get_snapshots(protocol)
        
        # Analyze historical delegation patterns
        results = dpa.analyze_historical_delegation_patterns(
            stored_snapshots,
            min_threshold=0.01,
            shift_threshold=0.05
        )
        
        # Verify results
        assert 'comparison' in results
        assert 'shifts' in results
        assert len(results['comparison']['snapshots']) == 3 