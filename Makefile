.PHONY: install test lint format clean build docs integration-test historical-data historical-report integration-test-cov integration-full end-to-end-test visualization-test

# Install the package in development mode
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run tests
test:
	python -m pytest tests/

# Run tests with coverage
test-cov:
	python -m pytest tests/ --cov=governance_token_analyzer

# Run linting
lint:
	black --check src/ tests/
	ruff src/ tests/

# Format code
format:
	black src/ tests/
	ruff --fix src/ tests/

# Clean build artifacts
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +

# Build package
build:
	python -m build

# Run CLI tool (requires installation)
run:
	token-analyzer --help

# Simulate distribution with the CLI tool
simulate:
	token-analyzer simulate power_law --holders 100

# Analyze token distribution with the CLI tool
analyze:
	token-analyzer analyze compound --limit 100

# Generate documentation using MkDocs
docs:
	mkdocs build

# Serve documentation locally
docs-serve:
	mkdocs serve

# Run integration tests
integration-test:
	python -m pytest tests/integration/ -v

# Run integration tests with coverage
integration-test-cov:
	python -m pytest tests/integration/ -v --cov=governance_token_analyzer --cov-report=xml --cov-report=term

# Run a full integration test suite
integration-full:
	python -m pytest tests/integration/ -v --cov=governance_token_analyzer --cov-report=html --html=reports/integration-report.html

# Run end-to-end tests
end-to-end-test:
	python -m pytest tests/integration/test_cli_integration.py -v

# Simulate historical data for a protocol
historical-data:
	token-analyzer historical simulate --protocol compound --num-snapshots 12 --interval-days 30

# Generate a historical data report
historical-report:
	token-analyzer historical generate-report --protocol compound --output-format html

# Compare multiple protocols
protocol-comparison:
	token-analyzer historical compare-protocols --protocols compound,uniswap,aave --metric gini_coefficient

# Generate a comparison report
comparison-report:
	token-analyzer historical generate-comparison-report --protocols compound,uniswap,aave

# Run visualization and reporting integration tests
visualization-test:
	python -m pytest tests/integration/test_visualization_and_reporting.py -v 