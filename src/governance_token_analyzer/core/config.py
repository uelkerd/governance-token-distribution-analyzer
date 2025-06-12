"""Configuration module for the Governance Token Distribution Analyzer.

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
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.graph_api_key = os.getenv("GRAPH_API_KEY")

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
        self.infura_base_url = f"https://mainnet.infura.io/v3/{self.infura_project_id}" if self.infura_project_id else ""
        self.alchemy_base_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}" if self.alchemy_api_key else ""
        self.graph_base_url = "https://api.thegraph.com/subgraphs/name"

        # Default settings
        self.default_output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/sample_outputs")

    def get_api_key(self):
        """Get the Etherscan API key."""
        return self.etherscan_api_key

    def get_web3_provider_url(self):
        """Get the best available Web3 provider URL (prefer Alchemy over Infura)."""
        if self.alchemy_api_key:
            return self.alchemy_base_url
        elif self.infura_project_id:
            return self.infura_base_url
        else:
            return None

    def get_protocol_info(self, protocol_name):
        """Get information for a specific protocol."""
        return self.protocols.get(protocol_name.lower())

    def get_token_address(self, protocol_name):
        """Get the token contract address for a specific protocol."""
        protocol_info = self.get_protocol_info(protocol_name)
        return protocol_info["token_address"] if protocol_info else None


# For backwards compatibility, keep the original variables
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")

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
INFURA_BASE_URL = (
    f"https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}" if INFURA_PROJECT_ID else ""
)

# Default settings
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/sample_outputs")
