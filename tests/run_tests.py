#!/usr/bin/env python
"""
Test Runner for Governance Token Distribution Analyzer

This script discovers and runs all tests for the project.
Run this script from the project root directory.
"""

import unittest
import sys
import os
from pathlib import Path
import pytest

def run_unittest_tests():
    """Discover and run all tests in the tests directory using unittest."""
    # Add the project root to the Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Discover tests
    start_dir = Path(__file__).parent
    test_suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success or failure
    return 0 if result.wasSuccessful() else 1

def run_pytest_tests():
    """Run all tests using pytest."""
    # Add the project root to the Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Run pytest
    return pytest.main(["-v", str(Path(__file__).parent)])

if __name__ == '__main__':
    # Run tests using pytest by default
    if len(sys.argv) > 1 and sys.argv[1] == '--unittest':
        sys.exit(run_unittest_tests())
    else:
        sys.exit(run_pytest_tests()) 