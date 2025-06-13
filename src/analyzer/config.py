"""
Configuration module for the Governance Token Distribution Analyzer.

This module handles loading environment variables and configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the Governance Token Distribution Analyzer."""

    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        # API Keys
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
        self.infura_project_id = os.getenv("INFURA_PROJECT_ID")

        # Protocol Settings
        self.protocols = {
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
        self.etherscan_base_url = "https://api.etherscan.io/api"
        self.infura_base_url = (
            f"https://mainnet.infura.io/v3/{self.infura_project_id}" if self.infura_project_id else ""
        )

        # Default settings
        self.default_output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data/sample_outputs",
        )

    def get_api_key(self):
        """Return the Etherscan API key."""
        return self.etherscan_api_key

    def get_protocol_info(self, protocol_name):
        """Return information for a specific protocol."""
        return self.protocols.get(protocol_name.lower())

    def get_token_address(self, protocol_name):
        """Return the token contract address for a specific protocol."""
        protocol_info = self.get_protocol_info(protocol_name)
        return protocol_info["token_address"] if protocol_info else None


# For backwards compatibility, keep the original variables
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
INFURA_BASE_URL = f"https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}" if INFURA_PROJECT_ID else ""

# Default settings
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/sample_outputs")
