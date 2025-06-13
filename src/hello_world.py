"""Hello World script to verify the environment is working correctly.

This script tests the basic functionality by making a simple API call
to Etherscan to get the ETH balance of the Ethereum Foundation address.
"""

import logging
import os

import dotenv
import matplotlib.pyplot as plt
import pandas as pd
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()


def main():
    """Execute the hello world test script."""
    logger.info("Starting Hello World test script")

    # Test API connection with Etherscan
    eth_address = "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"  # Ethereum Foundation

    # Get API key from environment variable
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    if not api_key:
        logger.warning("No Etherscan API key found. API call may be rate limited.")

    # Make API request to Etherscan
    logger.info(f"Fetching ETH balance for address: {eth_address}")
    url = "https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "balance",
        "address": eth_address,
        "tag": "latest",
        "apikey": api_key,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        data = response.json()
        if data["status"] == "1":
            # Convert wei to ETH
            balance_wei = int(data["result"])
            balance_eth = balance_wei / 1e18

            logger.info(f"ETH Balance: {balance_eth:.2f} ETH")

            # Create a simple DataFrame
            df = pd.DataFrame({"Entity": ["Ethereum Foundation"], "ETH Balance": [balance_eth]})

            logger.info("DataFrame created successfully:")
            logger.info(f"\n{df}")

            # Create a simple plot
            plt.figure(figsize=(8, 4))
            plt.bar(["Ethereum Foundation"], [balance_eth])
            plt.title("ETH Balance of Ethereum Foundation")
            plt.ylabel("ETH")
            plt.tight_layout()

            # Save the plot
            output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "eth_balance.png")
            plt.savefig(output_path)

            logger.info(f"Plot saved to {output_path}")

            logger.info("All tests passed successfully! Your environment is set up correctly.")
        else:
            logger.error(f"API Error: {data['message']}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
