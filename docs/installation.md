# Installation Guide

This guide will help you install the Governance Token Distribution Analyzer package.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation Methods

### Method 1: Install from Source (Development Mode)

This method is recommended for developers who want to modify the code.

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/governance-token-distribution-analyzer.git
   cd governance-token-distribution-analyzer
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Method 2: Install from PyPI (Once Published)

Once the package is published to PyPI, you can install it directly:

```bash
pip install governance-token-analyzer
```

## Environment Configuration

1. Create a `.env` file in the root directory with your API keys:
   ```
   ETHERSCAN_API_KEY=your_etherscan_api_key
   INFURA_API_KEY=your_infura_api_key
   ```

2. Copy the `env.example` file to create a `.env` file:
   ```bash
   cp env.example .env
   ```
   Then edit the `.env` file with your actual API keys.

## Verification

To verify that the installation was successful:

1. Run the CLI tool:
   ```bash
   token-analyzer --help
   ```

2. Run the tests:
   ```bash
   pytest tests/
   ```

## Troubleshooting

### Import Errors

If you encounter import errors, make sure:
1. The package is properly installed
2. Your virtual environment is activated (if using one)
3. You're running Python from the correct environment

### API Key Issues

If you get authentication errors when accessing APIs:
1. Check that your `.env` file is in the correct location
2. Verify that your API keys are valid and have the necessary permissions

## Next Steps

Once installed, proceed to the [Usage Guide](usage.md) to learn how to use the tool. 