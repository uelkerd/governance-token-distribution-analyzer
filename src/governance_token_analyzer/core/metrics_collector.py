#!/usr/bin/env python3
"""
Metrics Collector Module

Collects and processes metrics from various protocols for governance token analysis.
"""

from typing import Dict, List, Any, Optional, Callable
import logging
import time
import functools

from governance_token_analyzer.core.api_client import APIClient
from governance_token_analyzer.core.advanced_metrics import calculate_all_concentration_metrics
from governance_token_analyzer.core.data_simulator import TokenDistributionSimulator

logger = logging.getLogger(__name__)


def measure_api_call(func: Callable) -> Callable:
    """
    Decorator to measure API call performance and log results.
    
    Args:
        func: The function to measure
        
    Returns:
        Wrapped function with performance measurement
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # Log the performance metrics
        function_name = func.__name__
        logger.info(f"API call to {function_name} completed in {elapsed_time:.2f} seconds")
        
        # Add performance metadata to result if it's a dict
        if isinstance(result, dict):
            if "_metadata" not in result:
                result["_metadata"] = {}
            result["_metadata"]["execution_time"] = elapsed_time
            
        return result
    return wrapper


class MetricsCollector:
    """
    Collects and processes metrics for governance token analysis.
    """

    def __init__(self, use_live_data: bool = True):
        """
        Initialize the metrics collector.
        
        Args:
            use_live_data: Whether to use live blockchain data or simulated data
        """
        self.api_client = APIClient()
        self.simulator = TokenDistributionSimulator()
        self.use_live_data = use_live_data
        
    @measure_api_call
    def collect_protocol_data(self, protocol: str, limit: int = 1000) -> Dict[str, Any]:
        """
        Collect token distribution data for a specific protocol.
        
        Args:
            protocol: The protocol to analyze (e.g., 'compound', 'uniswap', 'aave')
            limit: Maximum number of token holders to analyze
            
        Returns:
            Dictionary containing protocol data and metrics
        """
        logger.info(f"Collecting data for {protocol} protocol (limit: {limit})")
        
        if self.use_live_data:
            logger.info("Using live blockchain data")
            data = self.api_client.get_protocol_data(protocol, limit=limit)
        else:
            logger.info("Using simulated data")
            data = self.simulator.generate_protocol_data(protocol, num_holders=limit)
            
        # Calculate metrics if token holders data is available
        if "token_holders" in data:
            balances = [float(holder.get("balance", 0)) for holder in data["token_holders"] 
                       if float(holder.get("balance", 0)) > 0]
            
            if balances:
                metrics = calculate_all_concentration_metrics(balances)
                data["metrics"] = metrics
                logger.info(f"Calculated metrics for {len(balances)} token holders")
            else:
                logger.warning("No positive balances found in the data")
        else:
            logger.warning("No token holders found in the data")
            
        return data
    
    @measure_api_call
    def collect_multi_protocol_data(self, protocols: List[str], limit: int = 1000) -> Dict[str, Dict[str, Any]]:
        """
        Collect data for multiple protocols.
        
        Args:
            protocols: List of protocols to analyze
            limit: Maximum number of token holders to analyze per protocol
            
        Returns:
            Dictionary mapping protocol names to their data
        """
        logger.info(f"Collecting data for multiple protocols: {protocols}")
        
        protocol_data = {}
        for protocol in protocols:
            try:
                data = self.collect_protocol_data(protocol, limit=limit)
                protocol_data[protocol] = data
            except Exception as e:
                logger.error(f"Error collecting data for {protocol}: {e}")
                protocol_data[protocol] = {"error": str(e)}
                
        return protocol_data
    
    @measure_api_call
    def compare_protocols(self, protocols: List[str], metric: str = "gini_coefficient") -> Dict[str, Any]:
        """
        Compare metrics across multiple protocols.
        
        Args:
            protocols: List of protocols to compare
            metric: Primary metric for comparison
            
        Returns:
            Dictionary containing comparison data
        """
        logger.info(f"Comparing {len(protocols)} protocols using {metric} metric")
        
        # Collect data for each protocol
        protocol_data = self.collect_multi_protocol_data(protocols)
        
        # Extract comparison metrics
        comparison_data = {}
        for protocol, data in protocol_data.items():
            if "metrics" in data:
                comparison_data[protocol] = {
                    "protocol": protocol,
                    metric: data["metrics"].get(metric, "N/A")
                }
                
                # Include all metrics for detailed view
                comparison_data[protocol].update(data["metrics"])
            else:
                comparison_data[protocol] = {
                    "protocol": protocol, 
                    metric: "N/A", 
                    "error": data.get("error", "Unknown error")
                }
                
        return comparison_data 