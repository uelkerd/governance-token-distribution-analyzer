# Governance Token Distribution Analyzer Examples

This directory contains example scripts demonstrating how to use the various components of the Governance Token Distribution Analyzer tool.

## Available Examples

### Voting Block Analysis

The [`voting_block_analysis_example.py`](./voting_block_analysis_example.py) script demonstrates how to use the voting block analysis module to identify coordinated governance participation and analyze voting patterns in DeFi protocols.

This example:
- Generates sample governance voting data
- Identifies voting blocks (groups of addresses that vote together)
- Calculates the voting power of each block
- Analyzes voting patterns for the blocks
- Visualizes the voting blocks as a network graph
- Analyzes the influence of large token holders on proposal outcomes
- Detects anomalies in voting patterns

### Running the Examples

To run any of the examples, make sure you've installed the package and its dependencies:

```bash
# From the repository root directory
pip install -e .
```

Then run the example script:

```bash
# From the repository root directory
python examples/voting_block_analysis_example.py
```

## Output

The examples will generate output files in the `examples/outputs` directory, including:
- Visualizations (PNG images)
- Data files (CSV, JSON)

## Creating Your Own Examples

You can use these examples as templates for creating your own analysis scripts. The examples demonstrate best practices for using the library's components. 