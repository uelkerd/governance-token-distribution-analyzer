"""The Graph API Client for Governance Token Distribution Analyzer.

This module provides functionality for interacting with The Graph API
for querying governance data from various protocols.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests

# Configure logging
logger = logging.getLogger(__name__)


class TheGraphAPI:
    """Client for interacting with The Graph API."""

    def __init__(self, subgraph_url: str):
        """Initialize The Graph API client.

        Args:
            subgraph_url: URL of the subgraph to query
        """
        self.subgraph_url = subgraph_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "GovernanceTokenAnalyzer/1.0",
            }
        )
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests

    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against the subgraph.

        Args:
            query: GraphQL query string
            variables: Variables for the query

        Returns:
            Query response as dictionary
        """
        # Implement rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

        # Prepare request payload
        payload = {
            "query": query,
        }

        if variables:
            payload["variables"] = variables

        # Make the request
        try:
            response = self.session.post(self.subgraph_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            return {"errors": [{"message": str(e)}]}
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            return {"errors": [{"message": "Invalid JSON response"}]}
