import os
import sys
from pathlib import Path

import pytest

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture to provide the path to test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Fixture to set up the test environment."""
    # Create test data directory if it doesn't exist
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # Set up any environment variables needed for testing
    os.environ["GOVERNANCE_ANALYZER_ENV"] = "test"

    yield

    # Clean up after tests if needed
    # test_data_dir.rmdir()  # Uncomment if you want to clean up test data directory after tests
