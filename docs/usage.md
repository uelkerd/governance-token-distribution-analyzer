# Usage Guide

This guide explains how to use the Governance Token Distribution Analyzer.

## Live Data vs. Fallback/Simulated Data

The analyzer is designed to fetch live blockchain data from multiple providers (Etherscan, The Graph, Alchemy, Infura). If a required API key is missing, a provider is rate-limited, or an endpoint is unavailable, the system will automatically log a warning and fall back to simulated or cached data. This ensures that analysis can proceed even in the absence of live data, though results may be less current.

All errors and warnings are logged with context. You can review logs to understand which data sources were used and whether any fallbacks occurred.

## Live Data Validation Script

A standalone script is provided to validate that live API integrations are working correctly:

```bash
python scripts/validate_live_data.py
```

This script will:
- Check for available API keys (Etherscan, The Graph, Alchemy, Infura)
- Attempt to fetch live token holder data for Compound, Uniswap, and Aave
- Validate the structure and quality of returned data
- Log all errors and warnings, and print a summary of validation results
- Exit with a nonzero code if any critical errors are detected

Use this script to verify your environment and API setup before running full analyses or deploying.

## Command Line Interface

The package provides a command-line tool `gova` for analyzing governance token distributions.

### General Help

To see all available commands:

```bash
gova --help
```

### Analyzing a Single Token

To analyze the distribution of a single token:

```bash
gova analyze --protocol compound --limit 100
```

Parameters:
- `token`: The token to analyze (choices: `compound`, `uniswap`, `aave`)
- `--limit`: Number of top holders to analyze (default: 100)

Example output:
```
=== COMPOUND Token Distribution Analysis ===
Analyzed 100 token holders
Gini Coefficient: 0.8423
Herfindahl Index: 0.0937

Concentration:
  Top 5 Holders: 45.32%
  Top 10 Holders: 57.89%
  Top 20 Holders: 67.54%
  Top 50 Holders: 84.21%
```

### Comparing Multiple Tokens

To compare distributions across multiple tokens:

```bash
gova compare-protocols --protocols compound,uniswap,aave --limit 100 --format html
```

Parameters:
- `tokens`: Tokens to compare (choices: `compound`, `uniswap`, `aave`)
- `--limit`: Number of top holders to analyze per token (default: 100)
- `--format`: Output format (choices: `json`, `report`, default: `json`)

When using the `report` format, an HTML report will be generated with visualizations.

### Generating Simulated Data

To simulate different token distribution patterns:

```bash
gova simulate power_law --holders 100 --output simulation.json
```

Parameters:
- `distribution_type`: Type of distribution to simulate (choices: `power_law`, `protocol_dominated`, `community`)
- `--holders`: Number of holders to simulate (default: 100)
- `--output`: Output filename (optional)

### Generating a Report

To generate a comprehensive HTML report:

```bash
gova report compound uniswap aave --output-dir reports
```

Parameters:
- `tokens`: Tokens to include in the report (choices: `compound`, `uniswap`, `aave`)
- `--output-dir`: Directory to save the report (optional)

The report includes visualizations, metrics, and comparisons between the selected tokens.

## Python API

You can also use the package programmatically in your Python code.

### Analyzing a Token

```python
from governance_token_analyzer.protocols.compound_analysis import CompoundAnalyzer

# Create analyzer
analyzer = CompoundAnalyzer()

# Analyze distribution
results = analyzer.analyze_distribution(limit=100)

# Print results
print(f"Gini Coefficient: {results['metrics']['gini_coefficient']}")
print(f"Top 10 Holders: {results['metrics']['concentration']['top_10_percentage']}%")
```

### Calculating Metrics

```python
from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics

# Token balances (can be from any source)
balances = [100, 50, 30, 20, 10, 5, 2, 1]

# Calculate metrics
metrics = calculate_all_concentration_metrics(balances)

# Access specific metrics
print(f"Gini coefficient: {metrics['gini_coefficient']}")
print(f"Nakamoto coefficient: {metrics['nakamoto_coefficient']}")
```

### Simulating Data

```python
from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator

# Create simulator
simulator = TokenDistributionSimulator(seed=42)

# Generate different distributions
power_law = simulator.generate_power_law_distribution(num_holders=100)
protocol = simulator.generate_protocol_dominated_distribution(num_holders=100)
community = simulator.generate_community_distribution(num_holders=100)

# Get response format
response = simulator.generate_token_holders_response(power_law)
```

### Generating a Report

```python
from governance_token_analyzer.generate_report import ReportGenerator

# Create report generator
generator = ReportGenerator(output_dir="reports")

# Generate report for specific tokens
report_path = generator.generate_full_report(["compound", "uniswap", "aave"])
print(f"Report generated at: {report_path}")
```

## Advanced Usage

### Working with Historical Data

```python
from governance_token_analyzer.protocols.historical_analysis import HistoricalAnalyzer

# Create historical analyzer
analyzer = HistoricalAnalyzer()

# Get historical distribution data
historical_data = analyzer.get_historical_distribution("compound", start_date="2020-06-01", end_date="2023-01-01")

# Analyze trends
trends = analyzer.analyze_concentration_trends(historical_data)
```

### Governance Effectiveness Analysis

```python
from governance_token_analyzer.core.governance_metrics import GovernanceEffectivenessAnalyzer

# Create governance analyzer
gov_analyzer = GovernanceEffectivenessAnalyzer()

# Analyze governance metrics for a protocol
metrics = gov_analyzer.analyze_governance_effectiveness("compound")

# Access specific governance metrics
print(f"Proposal Success Rate: {metrics['proposal_success_rate']}%")
print(f"Voter Participation Rate: {metrics['voter_participation_rate']}%")
```

## Next Steps

For more detailed information on specific components, refer to the [API Reference](api_reference.md). 