"""
Token Distribution Data Simulator

This module provides tools to generate simulated token distribution data
that mimics real-world patterns observed in governance tokens.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import random
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenDistributionSimulator:
    """
    Simulates realistic token distribution data for testing and analysis.
    
    This class can generate various distribution patterns commonly seen in 
    governance tokens, such as whale-dominated, community-distributed, 
    or protocol-owned distributions.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the simulator with an optional random seed.
        
        Args:
            seed: Optional random seed for reproducible simulations
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
    
    def generate_power_law_distribution(self, 
                                       num_holders: int = 100, 
                                       alpha: float = 1.5, 
                                       total_supply: int = 10_000_000) -> List[Dict[str, Any]]:
        """
        Generate a power-law distribution of token holders.
        
        Power-law distributions are common in token ecosystems where a small number
        of whales hold a large percentage of the tokens.
        
        Args:
            num_holders: Number of token holders to generate
            alpha: Power law exponent (higher = more unequal)
            total_supply: Total token supply
            
        Returns:
            List of dictionaries with token holder information
        """
        # Generate power-law distributed values
        weights = np.random.power(alpha, num_holders)
        
        # Normalize to total supply
        total_weight = sum(weights)
        quantities = [int(w / total_weight * total_supply) for w in weights]
        
        # Generate simulated addresses
        addresses = [f"0x{random.randint(0, 2**160):040x}" for _ in range(num_holders)]
        
        # Calculate percentages
        percentages = [q / total_supply * 100 for q in quantities]
        
        # Create holder data
        holders = [
            {
                "TokenHolderAddress": addr,
                "TokenHolderQuantity": str(qty),
                "TokenHolderPercentage": str(pct)
            }
            for addr, qty, pct in zip(addresses, quantities, percentages)
        ]
        
        # Sort by quantity in descending order
        holders.sort(key=lambda x: float(x["TokenHolderQuantity"]), reverse=True)
        
        return holders
    
    def generate_protocol_dominated_distribution(self, 
                                               num_holders: int = 100, 
                                               protocol_percentage: float = 30.0,
                                               total_supply: int = 10_000_000) -> List[Dict[str, Any]]:
        """
        Generate a distribution where protocol-owned wallets hold significant tokens.
        
        This mimics scenarios like DAO treasuries, development funds, or staking contracts
        holding large portions of the token supply.
        
        Args:
            num_holders: Number of token holders to generate
            protocol_percentage: Percentage held by protocol wallets
            total_supply: Total token supply
            
        Returns:
            List of dictionaries with token holder information
        """
        # Calculate how many tokens are held by protocol wallets
        protocol_tokens = int(total_supply * protocol_percentage / 100)
        community_tokens = total_supply - protocol_tokens
        
        # Create 3-5 protocol wallets with protocol_tokens distributed among them
        num_protocol_wallets = random.randint(3, 5)
        protocol_weights = np.random.dirichlet(np.ones(num_protocol_wallets))
        protocol_quantities = [int(w * protocol_tokens) for w in protocol_weights]
        
        # Generate protocol addresses
        protocol_addresses = [f"0x{random.randint(0, 2**160):040x}" for _ in range(num_protocol_wallets)]
        
        # Generate power-law distribution for community holders
        num_community_holders = num_holders - num_protocol_wallets
        community_weights = np.random.power(1.8, num_community_holders)
        
        # Normalize to community token supply
        total_weight = sum(community_weights)
        community_quantities = [int(w / total_weight * community_tokens) for w in community_weights]
        
        # Generate community addresses
        community_addresses = [f"0x{random.randint(0, 2**160):040x}" for _ in range(num_community_holders)]
        
        # Combine protocol and community holders
        quantities = protocol_quantities + community_quantities
        addresses = protocol_addresses + community_addresses
        
        # Calculate percentages
        percentages = [q / total_supply * 100 for q in quantities]
        
        # Create holder data
        holders = [
            {
                "TokenHolderAddress": addr,
                "TokenHolderQuantity": str(qty),
                "TokenHolderPercentage": str(pct)
            }
            for addr, qty, pct in zip(addresses, quantities, percentages)
        ]
        
        # Sort by quantity in descending order
        holders.sort(key=lambda x: float(x["TokenHolderQuantity"]), reverse=True)
        
        return holders
    
    def generate_community_distribution(self, 
                                      num_holders: int = 100, 
                                      gini_target: float = 0.6,
                                      total_supply: int = 10_000_000) -> List[Dict[str, Any]]:
        """
        Generate a more equal distribution typically seen in community-focused projects.
        
        This creates a distribution with a target Gini coefficient, mimicking
        projects that prioritize widespread token distribution.
        
        Args:
            num_holders: Number of token holders to generate
            gini_target: Target Gini coefficient (0 = perfect equality, 1 = perfect inequality)
            total_supply: Total token supply
            
        Returns:
            List of dictionaries with token holder information
        """
        # Tune the distribution to achieve the target Gini coefficient
        # We'll use a lognormal distribution and adjust parameters to hit target Gini
        
        sigma = 1.0  # Starting point
        mu = 0.0
        
        # Function to calculate Gini coefficient
        def gini(x):
            # Mean absolute difference
            mad = np.abs(np.subtract.outer(x, x)).mean()
            # Relative mean absolute difference
            rmad = mad / np.mean(x)
            # Gini coefficient
            return 0.5 * rmad
        
        # Generate and adjust until close to target
        for _ in range(10):  # Max 10 iterations
            quantities = np.random.lognormal(mu, sigma, num_holders)
            current_gini = gini(quantities)
            
            if abs(current_gini - gini_target) < 0.02:
                break  # Close enough
            
            # Adjust sigma based on difference
            if current_gini > gini_target:
                sigma *= 0.9  # Reduce inequality
            else:
                sigma *= 1.1  # Increase inequality
        
        # Normalize to total supply
        total_quantity = sum(quantities)
        quantities = [int(q / total_quantity * total_supply) for q in quantities]
        
        # Generate addresses
        addresses = [f"0x{random.randint(0, 2**160):040x}" for _ in range(num_holders)]
        
        # Calculate percentages
        percentages = [q / total_supply * 100 for q in quantities]
        
        # Create holder data
        holders = [
            {
                "TokenHolderAddress": addr,
                "TokenHolderQuantity": str(qty),
                "TokenHolderPercentage": str(pct)
            }
            for addr, qty, pct in zip(addresses, quantities, percentages)
        ]
        
        # Sort by quantity in descending order
        holders.sort(key=lambda x: float(x["TokenHolderQuantity"]), reverse=True)
        
        return holders
    
    def generate_token_holders_response(self, 
                                      holders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format holders data to match the API response structure.
        
        Args:
            holders: List of holder dictionaries
            
        Returns:
            Dictionary matching the format of API responses
        """
        return {
            "status": "1",
            "message": "OK",
            "result": holders
        }
    
    def generate_historical_distribution(self, 
                                       distribution_type: str = "power_law",
                                       num_periods: int = 12,
                                       num_holders: int = 100,
                                       start_date: Optional[datetime] = None,
                                       period_days: int = 30,
                                       total_supply: int = 10_000_000,
                                       concentration_trend: str = "decreasing") -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a time series of token distributions.
        
        This simulates how token distribution evolves over time, either becoming
        more concentrated or more distributed.
        
        Args:
            distribution_type: Type of distribution ("power_law", "protocol_dominated", "community")
            num_periods: Number of time periods to generate
            num_holders: Number of token holders per period
            start_date: Starting date for the time series
            period_days: Number of days between periods
            total_supply: Total token supply
            concentration_trend: Whether concentration is "increasing", "decreasing", or "stable"
            
        Returns:
            Dictionary mapping dates to token holder distributions
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=period_days * num_periods)
        
        historical_data = {}
        
        # Parameter adjustment based on trend
        if distribution_type == "power_law":
            # Alpha parameter determines inequality (higher = more equal)
            if concentration_trend == "increasing":
                alphas = np.linspace(1.8, 1.2, num_periods)  # Becoming more unequal
            elif concentration_trend == "decreasing":
                alphas = np.linspace(1.2, 1.8, num_periods)  # Becoming more equal
            else:  # stable
                alphas = [1.5] * num_periods
                
            for i in range(num_periods):
                current_date = start_date + timedelta(days=i * period_days)
                date_str = current_date.strftime("%Y-%m-%d")
                
                holders = self.generate_power_law_distribution(
                    num_holders=num_holders,
                    alpha=alphas[i],
                    total_supply=total_supply
                )
                
                historical_data[date_str] = self.generate_token_holders_response(holders)
                
        elif distribution_type == "protocol_dominated":
            # Protocol percentage parameter
            if concentration_trend == "increasing":
                percentages = np.linspace(20.0, 40.0, num_periods)  # Protocol gaining more control
            elif concentration_trend == "decreasing":
                percentages = np.linspace(40.0, 20.0, num_periods)  # Protocol distributing tokens
            else:  # stable
                percentages = [30.0] * num_periods
                
            for i in range(num_periods):
                current_date = start_date + timedelta(days=i * period_days)
                date_str = current_date.strftime("%Y-%m-%d")
                
                holders = self.generate_protocol_dominated_distribution(
                    num_holders=num_holders,
                    protocol_percentage=percentages[i],
                    total_supply=total_supply
                )
                
                historical_data[date_str] = self.generate_token_holders_response(holders)
                
        elif distribution_type == "community":
            # Gini target parameter
            if concentration_trend == "increasing":
                ginis = np.linspace(0.5, 0.7, num_periods)  # Becoming more unequal
            elif concentration_trend == "decreasing":
                ginis = np.linspace(0.7, 0.5, num_periods)  # Becoming more equal
            else:  # stable
                ginis = [0.6] * num_periods
                
            for i in range(num_periods):
                current_date = start_date + timedelta(days=i * period_days)
                date_str = current_date.strftime("%Y-%m-%d")
                
                holders = self.generate_community_distribution(
                    num_holders=num_holders,
                    gini_target=ginis[i],
                    total_supply=total_supply
                )
                
                historical_data[date_str] = self.generate_token_holders_response(holders)
        
        return historical_data

# Simple usage example
if __name__ == "__main__":
    simulator = TokenDistributionSimulator(seed=42)
    
    # Generate different distribution types
    power_law_holders = simulator.generate_power_law_distribution()
    protocol_holders = simulator.generate_protocol_dominated_distribution()
    community_holders = simulator.generate_community_distribution()
    
    # Generate a historical series
    historical = simulator.generate_historical_distribution(
        distribution_type="power_law",
        num_periods=6,
        concentration_trend="decreasing"
    )
    
    print(f"Power law distribution: {len(power_law_holders)} holders")
    print(f"Protocol dominated: {len(protocol_holders)} holders")
    print(f"Community distribution: {len(community_holders)} holders")
    print(f"Historical data: {len(historical)} time periods") 