"""
Configuration module for the Governance Token Distribution Analyzer.

This module handles loading environment variables and configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")

# Protocol Settings
PROTOCOLS = {
    "compound": {
        "token_address": "0xc00e94cb662c3520282e6f5717214004a7f26888",  # COMP token
        "name": "Compound",
        "symbol": "COMP",
    },
    "uniswap": {
        "token_address": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # UNI token
        "name": "Uniswap",
        "symbol": "UNI",
    },
    "aave": {
        "token_address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",  # AAVE token
        "name": "Aave",
        "symbol": "AAVE",
    },
}

# API Endpoints
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"
INFURA_BASE_URL = f"https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}"

# Default settings
DEFAULT_OUTPUT_DIR = "../data/sample_outputs" 