import unittest
import sys
import os
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.aave_analysis import AaveAnalyzer

class TestAaveAnalyzer(unittest.TestCase):
    """Test the Aave token analyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock API client for testing
        self.mock_api = MagicMock()
        
        # Set up simulated token holder data
        self.simulated_holders = {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "TokenHolderAddress": "0x1111111111111111111111111111111111111111",
                    "TokenHolderQuantity": "1000000",
                    "TokenHolderPercentage": "10.0"
                },
                {
                    "TokenHolderAddress": "0x2222222222222222222222222222222222222222",
                    "TokenHolderQuantity": "800000",
                    "TokenHolderPercentage": "8.0"
                },
                {
                    "TokenHolderAddress": "0x3333333333333333333333333333333333333333",
                    "TokenHolderQuantity": "600000",
                    "TokenHolderPercentage": "6.0"
                }
            ]
        }
        
        # Configure the mock API to return our simulated data
        self.mock_api.get_token_holders.return_value = self.simulated_holders
        
        # Create the analyzer with our mock API
        self.analyzer = AaveAnalyzer(api_client=self.mock_api)
    
    def test_get_token_holders(self):
        """Test that the get_token_holders method works correctly."""
        # Call the method we're testing
        holders = self.analyzer.get_token_holders(limit=3)
        
        # Verify the API was called correctly
        self.mock_api.get_token_holders.assert_called_once_with(
            self.analyzer.AAVE_CONTRACT_ADDRESS, 3
        )
        
        # Verify the method returns the expected data
        self.assertEqual(holders, self.simulated_holders)
    
    def test_analyze_distribution(self):
        """Test that the analyze_distribution method computes metrics correctly."""
        # Call the method we're testing
        results = self.analyzer.analyze_distribution(limit=3)
        
        # Verify the API was called correctly
        self.mock_api.get_token_holders.assert_called_once()
        
        # Verify the results contain the expected fields
        self.assertEqual(results['token'], 'AAVE')
        self.assertEqual(results['contract_address'], self.analyzer.AAVE_CONTRACT_ADDRESS)
        self.assertIn('timestamp', results)
        
        # Verify metrics were calculated
        self.assertIn('metrics', results)
        self.assertIn('gini_coefficient', results['metrics'])
        self.assertIn('herfindahl_index', results['metrics'])
        self.assertIn('concentration', results['metrics'])
        
        # Verify AAVE-specific staking metrics are included
        self.assertIn('staking', results['metrics'])
        self.assertIn('staked_percentage', results['metrics']['staking'])
    
    def test_save_analysis_results(self):
        """Test that analysis results can be saved to a file."""
        # Create sample results to save
        results = {
            'token': 'AAVE',
            'metrics': {
                'gini_coefficient': 0.5,
                'staking': {'staked_percentage': 35.0}
            }
        }
        
        # Call the method with a temporary file
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            filepath = self.analyzer.save_analysis_results(results, "test_output.json")
        
        # Verify the file was opened for writing
        mock_file.assert_called_once_with(os.path.join('data', 'test_output.json'), 'w')
        
        # Verify json.dump was called with our results
        mock_file().write.assert_called()
        
        # Verify the filepath was returned
        self.assertEqual(filepath, os.path.join('data', 'test_output.json'))

if __name__ == '__main__':
    unittest.main() 