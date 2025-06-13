import os
import sys
from pathlib import Path

import pytest

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")


def pytest_runtest_setup(item):
    """Skip tests based on environment variables."""
    # Skip live data tests if SKIP_LIVE_TESTS is set to true
    if os.environ.get("SKIP_LIVE_TESTS", "").lower() == "true" and (
        "test_live_data_integration" in item.nodeid or "TestLiveDataIntegration" in item.nodeid
    ):
        pytest.skip("Skipping live data tests as per environment configuration")

    # Skip performance tests in CI/CD environment
    if os.environ.get("TEST_MODE", "").lower() == "ci":
        for _ in item.iter_markers(name="performance"):
            pytest.skip("Skipping performance test in CI environment")


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
