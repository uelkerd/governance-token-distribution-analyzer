#!/usr/bin/env python3
"""
Live Data Validation Script for Governance Token Distribution Analyzer

This script validates that live API integrations are working correctly
and can fetch real blockchain data from Etherscan, The Graph, and Alchemy.
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
import requests

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Custom exception for network-related errors."""
    pass


class LiveDataValidator:
    """Validates live data integration functionality."""

    def __init__(self):
        """Initialize the validator with API client."""
        self.api_client = APIClient()
        self.config = Config()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_keys_available": {},
            "token_holders": {},
            "governance_proposals": {},
            "governance_votes": {},
            "errors": [],
            "warnings": [],
        }

    def check_api_keys(self):
        """Check which API keys are available."""
        logger.info("Checking API key availability...")

        keys = {
            "etherscan": bool(self.api_client.etherscan_api_key),
            "graph": bool(self.api_client.graph_api_key),
            "alchemy": bool(self.api_client.alchemy_api_key),
            "infura": bool(self.api_client.infura_api_key),
        }

        self.results["api_keys_available"] = keys

        for service, available in keys.items():
            if available:
                logger.info(f"✓ {service.upper()} API key found")
            else:
                logger.warning(f"✗ {service.upper()} API key not found")
                self.results["warnings"].append(f"No {service.upper()} API key available")

        return keys

    def validate_token_holders(self, protocol: str, use_real_data: bool = True):
        """Validate token holder data fetching for a protocol."""
        logger.info(f"Validating token holders for {protocol}...")

        try:
            holders = self.api_client.get_token_holders(protocol, limit=10, use_real_data=use_real_data)

            if not holders:
                error_msg = f"No token holders returned for {protocol}"
                logger.error(error_msg)
                self.results["errors"].append(error_msg)
                return False

            # Validate data structure
            for i, holder in enumerate(holders[:3]):  # Check first 3
                required_fields = ["address", "balance"]
                for field in required_fields:
                    if field not in holder:
                        error_msg = f"Missing field '{field}' in {protocol} holder {i}"
                        logger.error(error_msg)
                        self.results["errors"].append(error_msg)
                        return False

                # Validate Ethereum address format
                address = holder["address"]
                if not address.startswith("0x") or len(address) != 42:
                    error_msg = f"Invalid address format for {protocol}: {address}"
                    logger.error(error_msg)
                    self.results["errors"].append(error_msg)
                    return False

            self.results["token_holders"][protocol] = {
                "count": len(holders),
                "largest_holder_balance": holders[0]["balance"] if holders else 0,
                "sample_address": holders[0]["address"] if holders else "",
                "success": True,
            }

            logger.info(f"✓ Successfully fetched {len(holders)} token holders for {protocol}")
            return True

        except (requests.ConnectionError, requests.Timeout, OSError) as net_err:
            logger.error(f"Network error: {net_err}")
            self.results["errors"].append(f"Network error for {protocol}: {str(net_err)}")
            self.results["token_holders"][protocol] = {"success": False, "error": str(net_err)}
            raise NetworkError(f"Network error: {net_err}")
        except Exception as e:
            error_msg = f"Error fetching token holders for {protocol}: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            self.results["token_holders"][protocol] = {"success": False, "error": str(e)}
            return False

    def run_comprehensive_validation(self):
        """Run comprehensive validation of all live data integration components."""
        logger.info("Starting comprehensive live data validation...")

        # Check API keys
        api_keys = self.check_api_keys()

        # Determine if we can test real data
        use_real_data = any(api_keys.values())

        if not use_real_data:
            logger.warning("No API keys available - testing fallback mechanisms only")

        protocols = ["compound", "uniswap", "aave"]

        # Test token holders
        logger.info("\n" + "=" * 50)
        logger.info("TESTING TOKEN HOLDERS")
        logger.info("=" * 50)
        for protocol in protocols:
            self.validate_token_holders(protocol, use_real_data)

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate a summary of validation results."""
        logger.info("\n" + "=" * 50)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 50)

        # Count successes and failures
        total_tests = 0
        successful_tests = 0

        for category in ["token_holders"]:
            for protocol, result in self.results.get(category, {}).items():
                total_tests += 1
                if result.get("success", False):
                    successful_tests += 1

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        logger.info(f"Errors: {len(self.results['errors'])}")
        logger.info(f"Warnings: {len(self.results['warnings'])}")

        # API Key Status
        logger.info("\nAPI Key Status:")
        for service, available in self.results["api_keys_available"].items():
            status = "✓" if available else "✗"
            logger.info(f"  {status} {service.upper()}")

        # Overall status
        if len(self.results["errors"]) == 0:
            logger.info("\n🎉 VALIDATION PASSED - Live data integration is working!")
        elif success_rate >= 70:
            logger.info("\n⚠️  VALIDATION PARTIAL - Some issues found but core functionality works")
        else:
            logger.info("\n❌ VALIDATION FAILED - Significant issues with live data integration")

        return self.results


def main():
    """Main function to run live data validation."""
    logger.info("Governance Token Distribution Analyzer - Live Data Validation")
    logger.info("=" * 70)

    validator = LiveDataValidator()

    try:
        validator.run_comprehensive_validation()

        # Exit with appropriate code
        if len(validator.results["errors"]) == 0:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Some failures

    except NetworkError as net_err:
        logger.error(f"Network error occurred: {net_err}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
