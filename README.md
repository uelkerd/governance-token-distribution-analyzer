# Governance Token Distribution Analyzer

## Overview
The Governance Token Distribution Analyzer is a Python-based tool designed to analyze and compare token distribution patterns across major DeFi protocols. By examining how tokens are distributed and used for governance, the tool provides insights into the relationship between distribution mechanisms and governance outcomes.

## Value Proposition
This tool demonstrates practical understanding of blockchain governance by analyzing token distribution patterns across major DeFi protocols, providing actionable insights that crypto companies would value.

## Analyzed Protocols
- **Compound (COMP)**: Lending protocol with liquidity mining distribution
- **Uniswap (UNI)**: DEX with airdrop and liquidity provider rewards
- **Aave (AAVE)**: Lending protocol with staking and governance features

## Key Features
- **Distribution Concentration Analysis**: Calculate and visualize token ownership concentration across protocols
- **Governance Participation Metrics**: Track what percentage of token holders participate in governance votes
- **Cross-Protocol Comparison**: Generate side-by-side comparisons showing how different distribution methods affect governance outcomes

## Data Points Collected
- Total token supply and circulating supply
- Top holder addresses and their percentage ownership
- Governance proposal participation rates
- Voting power concentration (Gini coefficient)
- Token distribution timeline and major distribution events

## Technical Stack
- **Language**: Python 3.12
- **Data Processing**: Pandas, NumPy
- **API Interactions**: Requests
- **Visualizations**: Matplotlib, Seaborn
- **Data Sources**: Etherscan API, The Graph, Protocol-specific APIs

## Project Structure
```
governance-token-distribution-analyzer/
├── src/               # Source code
│   └── analyzer/      # Analysis modules
├── data/              # Data directory
│   └── sample_outputs/# Generated analysis outputs
├── docs/              # Documentation
├── tests/             # Test suite
├── .gitignore         # Git ignore file
├── LICENSE            # License file
├── README.md          # Project readme
└── requirements.txt   # Project dependencies
```

## Setup Instructions
1. Clone the repository
   ```
   git clone https://github.com/yourusername/governance-token-distribution-analyzer.git
   cd governance-token-distribution-analyzer
   ```

2. Create and activate a virtual environment
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Configure API keys
   Create a `.env` file with your API keys:
   ```
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ```

5. Run the analyzer
   ```
   python src/analyzer/main.py
   ```

## Sample Outputs
The tool generates various analytical outputs including:
- Token distribution visualizations
- Governance participation metrics
- Comparative analysis across protocols

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.