# Integration Testing Strategy

This document outlines the integration testing strategy for the Governance Token Distribution Analyzer project, explaining the approach, test coverage, and best practices.

## Integration Testing Approach

Our integration testing approach focuses on ensuring that different components of the system work correctly together. Unlike unit tests, which verify individual functions and classes in isolation, integration tests validate that these components interact as expected when combined.

### Testing Layers

We organize our integration tests into several layers:

1. **Component Integration Tests**: Verify that related components within a single module work together correctly.
2. **Module Integration Tests**: Test interactions between different modules (e.g., historical data and visualization).
3. **End-to-End Tests**: Validate complete workflows from user input to final output.
4. **CLI Integration Tests**: Ensure the command-line interface correctly utilizes the underlying functionality.

### Test Organization

Integration tests are located in the `tests/integration/` directory and organized into files by functionality:

- `test_historical_data_integration.py`: Tests for historical data functionality
- `test_visualization_and_reporting.py`: Tests for visualization and reporting components
- `test_protocol_integration.py`: Tests for protocol-specific components
- `test_cli_integration.py`: Tests for CLI commands

## Key Integration Test Cases

### Historical Data and Visualization Integration

These tests verify that:

1. Historical data can be properly stored and retrieved
2. Time series data can be extracted from historical snapshots
3. Visualization components can correctly process and display historical data
4. Reports can be generated with historical analysis included

Example:
```python
def test_time_series_visualization(data_manager, sample_snapshots, temp_output_dir):
    """Test that historical data can be visualized in time series charts."""
    # Get time series data from snapshots
    time_series = data_manager.get_time_series_data('compound', 'gini_coefficient')
    
    # Create a visualization
    fig = historical_charts.plot_metric_over_time(
        time_series_data=time_series,
        metric_name='gini_coefficient',
        title='Gini Coefficient Over Time'
    )
    
    # Verify that a figure was created
    assert isinstance(fig, plt.Figure)
    
    # Save the figure
    output_path = os.path.join(temp_output_dir, 'gini_over_time.png')
    fig.savefig(output_path)
    
    # Verify that the file was created
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
```

### CLI Integration Tests

These tests verify that:

1. CLI commands correctly call the underlying functionality
2. Command arguments are properly parsed and validated
3. Output is generated in the expected format
4. Error handling works as expected

Example:
```python
def test_historical_analysis_command(sample_data, temp_output_dir):
    """Test that the historical-analysis command works correctly."""
    runner = CliRunner()
    
    # Create a test command
    cmd = [
        'historical-analysis',
        '--protocol', 'compound',
        '--metric', 'gini_coefficient',
        '--data-dir', sample_data,
        '--output-dir', temp_output_dir,
        '--format', 'png'
    ]
    
    # Run the command
    result = runner.invoke(main.cli, cmd)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that output files were created
    expected_output = os.path.join(
        temp_output_dir, 
        'compound_gini_coefficient_historical.png'
    )
    assert os.path.exists(expected_output)
```

### End-to-End Workflow Tests

These tests verify complete workflows from data collection to report generation:

```python
def test_full_workflow_integration(data_manager, temp_output_dir):
    """Test the full workflow from data collection to report generation."""
    # 1. Simulate data collection for a protocol
    snapshots = historical_data.simulate_historical_data(
        'compound',
        num_snapshots=12,
        interval_days=30,
        data_manager=data_manager
    )
    
    # 2. Extract time series data
    time_series = data_manager.get_time_series_data('compound', 'gini_coefficient')
    
    # 3. Create visualizations
    # ...
    
    # 4. Generate a comprehensive report
    # ...
    
    # 5. Verify the entire workflow produced the expected output
    # ...
```

## Test Fixtures

We use pytest fixtures extensively to set up the test environment:

1. **`temp_data_dir`**: Creates a temporary directory for storing historical data
2. **`temp_output_dir`**: Creates a temporary directory for output files
3. **`data_manager`**: Creates a HistoricalDataManager instance
4. **`sample_snapshots`**: Generates sample historical data for testing

## Continuous Integration

Integration tests are run automatically as part of our CI/CD pipeline using GitHub Actions:

```yaml
name: Integration Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10']

    steps:
    - uses: actions/checkout@v3
    
    # ...
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
        
    # ...
```

## Best Practices for Integration Testing

1. **Use Test Fixtures**: Create reusable fixtures for common setup and teardown operations
2. **Clean Up After Tests**: Ensure tests clean up any temporary files or directories
3. **Mock External Dependencies**: Use mocks for external APIs or services
4. **Test Real Workflows**: Focus on testing realistic user workflows
5. **Verify Outputs**: Check that files are created and contain expected content
6. **Test Error Handling**: Verify that errors are handled properly
7. **Use Parameterized Tests**: Test different inputs and configurations
8. **Document Test Purpose**: Clearly document what each test is verifying

## Integration Testing Coverage

Our integration tests cover the following critical integrations:

1. **Data Storage and Retrieval**: Testing that historical data can be stored and retrieved
2. **Data Processing and Visualization**: Testing that data can be processed and visualized
3. **CLI and Core Functionality**: Testing that CLI commands correctly utilize core functionality
4. **Report Generation**: Testing that reports can be generated with the correct content
5. **Cross-Protocol Integration**: Testing that multiple protocols can be compared

## Running Integration Tests

Integration tests can be run using the following commands:

```bash
# Run all integration tests
make integration-test

# Run with coverage
make integration-test-cov

# Run specific integration tests
python -m pytest tests/integration/test_visualization_and_reporting.py -v
```

## Troubleshooting Integration Tests

If integration tests are failing, consider the following:

1. **Check Dependencies**: Ensure all required dependencies are installed
2. **Check File Permissions**: Ensure the tests have permission to create and modify files
3. **Check Test Environment**: Ensure the test environment is properly set up
4. **Check Test Data**: Ensure test data is being generated correctly
5. **Increase Verbosity**: Run tests with the `-v` flag for more detailed output
6. **Isolate Failures**: Run specific failing tests to isolate the issue

## Future Improvements

1. **Increase Test Coverage**: Add more tests for edge cases and error conditions
2. **Add Performance Tests**: Test system performance under various loads
3. **Add Security Tests**: Test for security vulnerabilities
4. **Add Stress Tests**: Test system behavior under extreme conditions
5. **Add Regression Tests**: Ensure bugs don't reappear

## Live Data and Fallback Logic Testing

Integration tests now include validation of live data connectors and fallback logic. The system is tested to ensure that:
- Live data is fetched from Etherscan, The Graph, Alchemy, and Infura when API keys are available and providers are responsive.
- If any provider is unavailable, rate-limited, or missing an API key, the system logs a warning and automatically falls back to simulated or cached data.
- All errors and warnings are logged, and the system continues to function with available data sources.

A standalone validation script is provided:

```bash
python scripts/validate_live_data.py
```

This script checks API key availability, attempts live data fetches, validates data structure, and summarizes results. Use it to verify your environment and API setup before running full integration tests or deploying. 