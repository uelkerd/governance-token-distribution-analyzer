"""Base Data Processor for Governance Token Distribution Analyzer.

This module provides the base DataProcessor class with common functionality
for processing governance token data.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class DataProcessor:
    """Base class for processing governance token data."""

    def __init__(self):
        """Initialize the data processor."""
        self._metrics_processor = None
        self._visualization_processor = None
        self._report_processor = None

    @property
    def metrics_processor(self):
        if self._metrics_processor is None:
            from .metrics_processor import MetricsProcessor
            self._metrics_processor = MetricsProcessor()
        return self._metrics_processor

    @property
    def visualization_processor(self):
        if self._visualization_processor is None:
            from .visualization_processor import VisualizationProcessor
            self._visualization_processor = VisualizationProcessor()
        return self._visualization_processor

    @property
    def report_processor(self):
        if self._report_processor is None:
            from .report_processor import ReportProcessor
            self._report_processor = ReportProcessor()
        return self._report_processor

    def process_token_data(self, protocol: str, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process token data for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            token_data: Token data from API client

        Returns:
            Processed token data with additional metrics
        """
        logger.info(f"Processing token data for {protocol}")

        # Validate input
        if not token_data:
            logger.warning(f"No token data provided for {protocol}")
            return {}

        # Extract token holders
        token_holders = token_data.get("token_holders", [])

        # Calculate basic metrics
        metrics = self.metrics_processor.calculate_distribution_metrics(token_holders)

        # Prepare result
        result = {
            "protocol": protocol,
            "token_holders": token_holders,
            "metrics": metrics,
        }

        return result

    def process_governance_data(self, protocol: str, governance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process governance data for a specific protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            governance_data: Governance data from API client

        Returns:
            Processed governance data with additional metrics
        """
        logger.info(f"Processing governance data for {protocol}")

        # Validate input
        if not governance_data:
            logger.warning(f"No governance data provided for {protocol}")
            return {}

        # Extract proposals and votes
        proposals = governance_data.get("governance_proposals", [])

        # Calculate governance metrics
        metrics = self.metrics_processor.calculate_governance_metrics(proposals)

        # Prepare result
        result = {
            "protocol": protocol,
            "proposals": proposals,
            "metrics": metrics,
        }

        return result

    def process_protocol_data(self, protocol: str, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process comprehensive protocol data.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            protocol_data: Protocol data from API client

        Returns:
            Processed protocol data with additional metrics and visualizations
        """
        logger.info(f"Processing comprehensive data for {protocol}")

        # Validate input
        if not protocol_data:
            logger.warning(f"No protocol data provided for {protocol}")
            return {}

        # Extract data components
        token_holders = protocol_data.get("token_holders", [])
        proposals = protocol_data.get("governance_proposals", [])
        protocol_info = protocol_data.get("protocol_info", {})

        # Process token distribution data
        distribution_result = self.process_token_data(protocol, {"token_holders": token_holders})

        # Process governance data
        governance_result = self.process_governance_data(protocol, {"governance_proposals": proposals})

        # Combine metrics
        combined_metrics = {
            **distribution_result.get("metrics", {}),
            **governance_result.get("metrics", {}),
        }

        # Generate visualizations
        visualizations = self.visualization_processor.generate_visualizations(
            protocol, token_holders, proposals, combined_metrics
        )

        # Prepare comprehensive result
        result = {
            "protocol": protocol,
            "token_holders": token_holders,
            "proposals": proposals,
            "protocol_info": protocol_info,
            "metrics": combined_metrics,
            "visualizations": visualizations,
        }

        return result

    def generate_report(self, protocol: str, processed_data: Dict[str, Any], output_path: str) -> str:
        """Generate a report for processed protocol data.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            processed_data: Processed protocol data
            output_path: Path to save the report

        Returns:
            Path to the generated report
        """
        logger.info(f"Generating report for {protocol}")

        return self.report_processor.generate_report(protocol, processed_data, output_path)

    def compare_protocols(self, protocol_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare data from multiple protocols.

        Args:
            protocol_data: Dictionary mapping protocol names to processed protocol data

        Returns:
            Comparison results
        """
        logger.info(f"Comparing protocols: {list(protocol_data.keys())}")

        # Validate input
        if not protocol_data:
            logger.warning("No protocol data provided for comparison")
            return {}

        # Extract metrics for each protocol
        protocol_metrics = {}
        for protocol, data in protocol_data.items():
            protocol_metrics[protocol] = data.get("metrics", {})

        # Calculate comparison metrics
        comparison_metrics = self.metrics_processor.calculate_comparison_metrics(protocol_metrics)

        # Generate comparison visualizations
        comparison_visualizations = self.visualization_processor.generate_comparison_visualizations(protocol_metrics)

        # Prepare comparison result
        result = {
            "protocols": list(protocol_data.keys()),
            "metrics": comparison_metrics,
            "visualizations": comparison_visualizations,
        }

        return result

    def generate_comparison_report(
        self, protocol_data: Dict[str, Dict[str, Any]], comparison_data: Dict[str, Any], output_path: str
    ) -> str:
        """Generate a comparison report for multiple protocols.

        Args:
            protocol_data: Dictionary mapping protocol names to processed protocol data
            comparison_data: Protocol comparison data
            output_path: Path to save the report

        Returns:
            Path to the generated report
        """
        logger.info(f"Generating comparison report for protocols: {list(protocol_data.keys())}")

        return self.report_processor.generate_comparison_report(protocol_data, comparison_data, output_path)
