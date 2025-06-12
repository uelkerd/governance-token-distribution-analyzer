# API Reference Documentation

This document provides detailed information about the modules, classes, and functions in the Governance Token Distribution Analyzer.

## Core Module

The core module contains the primary analysis functionality of the Governance Token Distribution Analyzer.

### Concentration Analysis

```python
from governance_token_analyzer.core.concentration_analysis import ConcentrationAnalyzer
```

#### Class: `ConcentrationAnalyzer`

A class that provides methods for analyzing token concentration across holder addresses.

**Methods:**

- `calculate_gini_coefficient(token_holders)`: Calculates the Gini coefficient for token distribution
- `calculate_herfindahl_index(token_holders)`: Calculates the Herfindahl-Hirschman Index for market concentration
- `calculate_concentration_ratio(token_holders, n=5)`: Calculates the concentration ratio for the top N token holders
- `detect_whale_addresses(token_holders, threshold=0.05)`: Identifies whale addresses that hold above the threshold percentage
- `generate_lorenz_curve_data(token_holders)`: Generates data for plotting a Lorenz curve of token distribution

### Participation Analysis

```python
from governance_token_analyzer.core.participation_analysis import ParticipationAnalyzer
```

#### Class: `ParticipationAnalyzer`

A class that analyzes governance participation metrics across token holders.

**Methods:**

- `calculate_participation_rate(governance_data)`: Calculates the overall participation rate in governance
- `analyze_voter_consistency(governance_data)`: Analyzes how consistently token holders participate in governance
- `segment_voters_by_activity(governance_data)`: Segments voters into categories based on their activity level
- `calculate_voter_turnout_over_time(governance_data)`: Tracks governance participation rates over time
- `identify_influential_voters(governance_data, token_holders)`: Identifies addresses with significant influence on governance outcomes

### Historical Data Analysis

```python
from governance_token_analyzer.core.historical_data import HistoricalDataAnalyzer
```

#### Class: `HistoricalDataAnalyzer`

A class for analyzing historical trends in token distribution and governance participation.

**Methods:**

- `analyze_distribution_changes(historical_data)`: Analyzes how token distribution has changed over time
- `detect_significant_transfers(historical_data)`: Identifies significant token transfers that affected distribution
- `calculate_historical_metrics(historical_data)`: Calculates various metrics over time (Gini, participation, etc.)
- `identify_distribution_patterns(historical_data)`: Identifies patterns in how token distribution evolves
- `segment_time_periods(historical_data)`: Segments the historical data into meaningful time periods

### Voting Block Analysis

```python
from governance_token_analyzer.core.voting_block_analysis import VotingBlockAnalyzer
```

#### Class: `VotingBlockAnalyzer`

A class for detecting and analyzing coordinated voting behavior in governance.

**Methods:**

- `detect_voting_blocks(voting_data)`: Identifies potential voting blocks based on similar voting patterns
- `calculate_block_cohesion(voting_blocks)`: Calculates how cohesively each voting block operates
- `measure_block_influence(voting_blocks, proposals)`: Measures the influence of each voting block on governance outcomes
- `visualize_voting_blocks(voting_blocks)`: Generates network visualization data for voting blocks
- `track_block_evolution(historical_voting_data)`: Tracks how voting blocks evolve over time

### Delegation Pattern Analysis

```python
from governance_token_analyzer.core.delegation_pattern_analysis import DelegationPatternAnalyzer
```

#### Class: `DelegationPatternAnalyzer`

A class for analyzing token delegation patterns in governance systems that support delegation.

**Methods:**

- `analyze_delegation_network(delegation_data)`: Analyzes the network structure of delegations
- `identify_key_delegatees(delegation_data)`: Identifies addresses that receive significant delegated voting power
- `calculate_delegation_metrics(delegation_data)`: Calculates various metrics about delegation patterns
- `detect_delegation_shifts(historical_delegation_data)`: Detects significant changes in delegation patterns over time
- `classify_delegation_behavior(delegation_data)`: Classifies delegation patterns into different behavioral categories

### Cross-Protocol Comparison

```python
from governance_token_analyzer.core.cross_protocol_comparison import CrossProtocolAnalyzer
```

#### Class: `CrossProtocolAnalyzer`

A class for comparing governance metrics across different protocols.

**Methods:**

- `compare_concentration_metrics(protocol_data)`: Compares token concentration metrics across protocols
- `compare_participation_metrics(protocol_data)`: Compares governance participation metrics across protocols
- `identify_common_participants(protocol_data)`: Identifies addresses that participate in governance across multiple protocols
- `compare_governance_outcomes(protocol_data)`: Compares governance outcomes and effectiveness across protocols
- `generate_comparison_report(protocol_data)`: Generates a comprehensive comparison report across protocols

### Data Collection

```python
from governance_token_analyzer.core.data_collection import DataCollector
```

#### Class: `DataCollector`

A class for collecting token holder and governance data from various sources.

**Methods:**

- `collect_token_holders(protocol)`: Collects current token holder data for a specific protocol
- `collect_governance_proposals(protocol)`: Collects governance proposal data for a specific protocol
- `collect_voting_data(protocol)`: Collects voting data for a specific protocol
- `collect_historical_data(protocol, start_date, end_date)`: Collects historical data for a specific protocol
- `validate_collected_data(data)`: Validates collected data for consistency and completeness

### API Client

```python
from governance_token_analyzer.core.api_client import APIClient
```

#### Class: `APIClient`

A class for interacting with various blockchain data APIs.

**Methods:**

- `get_token_holders(protocol)`: Retrieves token holder data from the appropriate API
- `get_governance_proposals(protocol)`: Retrieves governance proposal data from the API
- `get_voting_data(protocol, proposal_id)`: Retrieves voting data for a specific proposal
- `get_historical_data(protocol, parameters)`: Retrieves historical data based on specified parameters
- `handle_rate_limiting(response)`: Handles API rate limiting with appropriate backoff strategies

### Metrics Collection

```python
from governance_token_analyzer.core.metrics_collector import MetricsCollector
```

#### Class: `MetricsCollector`

A class for collecting and tracking performance metrics within the application.

**Methods:**

- `record_api_call(endpoint, duration, success)`: Records metrics for an API call
- `record_analysis_duration(analysis_type, duration)`: Records the duration of an analysis operation
- `get_api_performance_metrics()`: Retrieves performance metrics for API calls
- `get_analysis_performance_metrics()`: Retrieves performance metrics for analysis operations
- `export_metrics(format='json')`: Exports collected metrics in the specified format

### Logging Configuration

```python
from governance_token_analyzer.core.logging_config import configure_logging
```

#### Function: `configure_logging`

Configures the logging system for the application.

**Parameters:**

- `log_level`: The logging level to use (default: INFO)
- `log_file`: The file path for log output (default: None, logs to console)
- `log_format`: The format string for log messages

## Visualization Module

The visualization module provides tools for generating visualizations of the analysis results.

### Charts

```python
from governance_token_analyzer.visualization.charts import ChartGenerator
```

#### Class: `ChartGenerator`

A class for generating various charts and visualizations of analysis data.

**Methods:**

- `create_distribution_chart(token_holders)`: Creates a chart visualizing token distribution
- `create_participation_chart(governance_data)`: Creates a chart visualizing governance participation
- `create_historical_trend_chart(historical_data)`: Creates a chart showing historical trends
- `create_voting_block_network(voting_blocks)`: Creates a network visualization of voting blocks
- `create_delegation_flow_visualization(delegation_data)`: Creates a visualization of delegation flows

### Historical Charts

```python
from governance_token_analyzer.visualization.historical_charts import HistoricalChartGenerator
```

#### Class: `HistoricalChartGenerator`

A class for generating time-series charts and visualizations of historical data.

**Methods:**

- `create_metric_trend_chart(historical_data, metric)`: Creates a chart showing trends in a specific metric over time
- `create_distribution_evolution_chart(historical_data)`: Creates a chart showing how distribution has evolved
- `create_participation_evolution_chart(historical_data)`: Creates a chart showing how participation has evolved
- `create_voting_block_evolution_chart(historical_data)`: Creates a chart showing how voting blocks have evolved
- `create_governance_outcome_chart(historical_data)`: Creates a chart visualizing governance outcomes over time

### Report Generator

```python
from governance_token_analyzer.visualization.report_generator import ReportGenerator
```

#### Class: `ReportGenerator`

A class for generating comprehensive reports from analysis results.

**Methods:**

- `generate_concentration_report(token_holders)`: Generates a report on token concentration analysis
- `generate_participation_report(governance_data)`: Generates a report on governance participation analysis
- `generate_historical_report(historical_data)`: Generates a report on historical trend analysis
- `generate_voting_block_report(voting_blocks)`: Generates a report on voting block analysis
- `generate_comprehensive_report(all_data)`: Generates a comprehensive report including all analyses

## Protocols Module

The protocols module contains protocol-specific implementations for data collection and analysis.

### Compound Protocol

```python
from governance_token_analyzer.protocols.compound import CompoundProtocol
```

#### Class: `CompoundProtocol`

A class for interacting with Compound governance data.

**Methods:**

- `get_token_holders()`: Retrieves COMP token holder data
- `get_governance_proposals()`: Retrieves Compound governance proposal data
- `get_voting_data(proposal_id)`: Retrieves voting data for a specific Compound proposal
- `get_delegation_data()`: Retrieves delegation data for Compound governance

### Uniswap Protocol

```python
from governance_token_analyzer.protocols.uniswap import UniswapProtocol
```

#### Class: `UniswapProtocol`

A class for interacting with Uniswap governance data.

**Methods:**

- `get_token_holders()`: Retrieves UNI token holder data
- `get_governance_proposals()`: Retrieves Uniswap governance proposal data
- `get_voting_data(proposal_id)`: Retrieves voting data for a specific Uniswap proposal
- `get_delegation_data()`: Retrieves delegation data for Uniswap governance

### Aave Protocol

```python
from governance_token_analyzer.protocols.aave import AaveProtocol
```

#### Class: `AaveProtocol`

A class for interacting with Aave governance data.

**Methods:**

- `get_token_holders()`: Retrieves AAVE token holder data
- `get_governance_proposals()`: Retrieves Aave governance proposal data
- `get_voting_data(proposal_id)`: Retrieves voting data for a specific Aave proposal
- `get_delegation_data()`: Retrieves delegation data for Aave governance

## CLI Module

The CLI module provides command-line interfaces for interacting with the analyzer.

### Main CLI

```python
from governance_token_analyzer.cli.main import cli
```

#### Function: `cli`

The main entry point for the command-line interface.

**Commands:**

- `analyze`: Run analysis on token distribution and governance data
- `collect`: Collect data from specified protocols
- `visualize`: Generate visualizations from analysis results
- `report`: Generate reports from analysis results
- `compare`: Compare analysis results across protocols

### Historical Analysis CLI

```python
from governance_token_analyzer.cli.historical_analysis import historical_cli
```

#### Function: `historical_cli`

Command-line interface for historical data analysis.

**Commands:**

- `analyze`: Run historical analysis on token distribution and governance data
- `visualize`: Generate visualizations of historical trends
- `report`: Generate reports from historical analysis

### Data Collection CLI

```python
from governance_token_analyzer.cli.data_collection_cmd import data_collection_cli
```

#### Function: `data_collection_cli`

Command-line interface for data collection operations.

**Commands:**

- `token-holders`: Collect token holder data for specified protocols
- `governance`: Collect governance proposal data for specified protocols
- `voting`: Collect voting data for specified protocols
- `historical`: Collect historical data for specified protocols 