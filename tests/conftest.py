import os
import sys
from pathlib import Path

import pytest

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
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
        for marker in item.iter_markers(name="performance"):
            pytest.skip("Skipping performance test in CI environment")
