.PHONY: install test lint format clean build docs integration-test historical-data historical-report integration-test-cov integration-full end-to-end-test visualization-test lint-check format-check typecheck all-checks

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
	ruff governance_token_analyzer/ tests/ --fix
	ruff format governance_token_analyzer/ tests/

# Run linting check only (no fixes)
lint-check:
	ruff governance_token_analyzer/ tests/ --no-fix
	ruff format --check governance_token_analyzer/ tests/

# Format code
format:
	ruff format governance_token_analyzer/ tests/

# Format check only
format-check:
	ruff format --check governance_token_analyzer/ tests/

# Type check
typecheck:
	mypy --ignore-missing-imports governance_token_analyzer/

# Run all checks
all-checks: format-check lint-check typecheck test

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
	find . -name ".ruff_cache" -type d -exec rm -rf {} +
	find . -name ".mypy_cache" -type d -exec rm -rf {} +

# Build package
build:
	python -m build

# Run CLI tool (requires installation)
run:
	gova --help

# Simulate distribution with the CLI tool
simulate:
	gova simulate power_law --holders 100

# Analyze token distribution with the CLI tool
analyze:
	gova analyze compound --limit 100

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
	gova historical simulate --protocol compound --num-snapshots 12 --interval-days 30

# Generate a historical data report
historical-report:
	gova historical generate-report --protocol compound --output-format html

# Compare multiple protocols
protocol-comparison:
	gova historical compare-protocols --protocols compound,uniswap,aave --metric gini_coefficient

# Generate a comparison report
comparison-report:
	gova historical generate-comparison-report --protocols compound,uniswap,aave

# Run visualization and reporting integration tests
visualization-test:
	python -m pytest tests/integration/test_visualization_and_reporting.py -v 