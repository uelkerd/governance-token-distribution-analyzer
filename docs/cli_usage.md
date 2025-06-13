# CLI Usage Guide

The Governance Token Distribution Analyzer provides a command-line interface (CLI) for analyzing token distributions. This guide explains how to use the CLI commands and provides examples for common use cases.

## Live Data vs. Fallback/Simulated Data (CLI)

When running CLI commands, the analyzer will attempt to fetch live data from available providers (Etherscan, The Graph, Alchemy, Infura). If any required API key is missing, or a provider is rate-limited/unavailable, the CLI will log a warning and automatically fall back to simulated or cached data. This ensures CLI commands remain robust and usable even in restricted environments.

All errors and warnings are logged to the console. Review the output to determine if live or fallback data was used for your analysis.

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

Use this script to verify your environment and API setup before running CLI analyses or deploying.

## Installation

After installing the package, the `gova` command should be available in your environment:

```bash
# Install the package
pip install -e .

# Verify installation
gova --help
```

## Basic Commands

The CLI provides several commands for different analysis tasks:

- `analyze`: Analyze a single token distribution
- `compare`: Compare multiple token distributions
- `simulate`: Generate simulated token distribution data
- `report`: Generate comprehensive analysis reports

### Getting Help

To see all available commands:

```bash
gova --help
```

To get help for a specific command:

```bash
gova analyze --help
gova compare --help
gova simulate --help
gova report --help
```

## Command Details

### Analyze Command

The `analyze` command examines the distribution of a single token and calculates various concentration metrics.

```bash
gova analyze [token] [options]
```

Arguments:
- `token`: The token to analyze (choices: `compound`, `uniswap`, `aave`)

Options:
- `--limit`: Number of top holders to analyze (default: 100)

Examples:

```bash
# Analyze Compound token distribution (top 100 holders)
gova analyze compound

# Analyze Uniswap token distribution with top 200 holders
gova analyze uniswap --limit 200

# Analyze Aave token distribution
gova analyze aave
```

Output example:

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

### Compare Command

The `compare` command analyzes multiple tokens and compares their distribution patterns.

```bash
gova compare [tokens...] [options]
```

Arguments:
- `tokens`: Tokens to compare (choices: `compound`, `uniswap`, `aave`)

Options:
- `--limit`: Number of top holders to analyze per token (default: 100)
- `--format`: Output format (choices: `json`, `report`, default: `json`)

Examples:

```bash
# Compare Compound and Uniswap
gova compare compound uniswap

# Compare all three tokens with top 50 holders and generate a report
gova compare compound uniswap aave --limit 50 --format report

# Compare just Compound and Aave with JSON output
gova compare compound aave --format json
```

When using the `report` format, an HTML report will be generated with visualizations.

### Simulate Command

The `simulate` command generates simulated token distribution data for testing and educational purposes.

```bash
gova simulate [distribution_type] [options]
```

Arguments:
- `distribution_type`: Type of distribution to simulate (choices: `power_law`, `protocol_dominated`, `community`)

Options:
- `--holders`: Number of holders to simulate (default: 100)
- `--output`: Output filename (optional)

Examples:

```bash
# Generate power law distribution with 100 holders
gova simulate power_law

# Generate protocol-dominated distribution with 200 holders
gova simulate protocol_dominated --holders 200

# Generate community distribution and save to a specific file
gova simulate community --output community_simulation.json
```

The simulated data will include token holder addresses, quantities, percentages, and concentration metrics.

### Report Command

The `report` command generates comprehensive HTML reports with visualizations and analyses.

```bash
gova report [tokens...] [options]
```

Arguments:
- `tokens`: Tokens to include in the report (choices: `compound`, `uniswap`, `aave`)

Options:
- `--output-dir`: Directory to save the report (optional)

Examples:

```bash
# Generate a report for Compound
gova report compound

# Generate a comparative report for all three tokens
gova report compound uniswap aave

# Save the report to a specific directory
gova report compound uniswap --output-dir ~/my_reports
```

The report includes:
- Distribution visualizations
- Concentration metrics
- Comparative analyses
- Top holder information

## Environmental Variables

The CLI uses environmental variables for API keys and other settings. These can be set in a `.env` file:

```
ETHERSCAN_API_KEY=your_etherscan_api_key
INFURA_API_KEY=your_infura_api_key
```

## Redirecting Output

You can redirect the output to a file:

```bash
# Save analysis results to a file
gova analyze compound > compound_analysis.txt

# Save comparison results to a file
gova compare compound uniswap > comparison.txt
```

## Common Workflows

### Comprehensive Token Analysis

To perform a comprehensive analysis of a token:

```bash
# Step 1: Analyze the token distribution
gova analyze compound

# Step 2: Generate a detailed report
gova report compound

# Step 3: Simulate different distribution scenarios
gova simulate power_law --output compound_alternative.json
```

### Multi-Protocol Comparison

To compare multiple protocols:

```bash
# Step 1: Compare the tokens
gova compare compound uniswap aave

# Step 2: Generate a comparative report
gova report compound uniswap aave
```

## Troubleshooting

If you encounter issues:

1. Verify that your API keys are set correctly in the `.env` file
2. Check that you have an internet connection for accessing blockchain data
3. Ensure you're using the correct command syntax
4. Try reducing the `--limit` parameter if you're getting timeouts 