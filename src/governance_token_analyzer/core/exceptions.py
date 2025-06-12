"""Custom exceptions for the Governance Token Distribution Analyzer.

This module defines the custom exceptions used throughout the application
to provide clear and actionable error messages.
"""

class GovernanceAnalyzerError(Exception):
    """Base exception class for the Governance Token Distribution Analyzer."""
    pass


class DataAccessError(GovernanceAnalyzerError):
    """Exception raised when there are issues accessing data sources."""
    pass


class DataStorageError(GovernanceAnalyzerError):
    """Exception raised when there are issues storing data."""
    pass


class DataFormatError(GovernanceAnalyzerError):
    """Exception raised when data is not in the expected format."""
    pass


class ProtocolNotSupportedError(GovernanceAnalyzerError):
    """Exception raised when a requested protocol is not supported."""
    def __init__(self, protocol: str, supported_protocols: list = None):
        self.protocol = protocol
        self.supported_protocols = supported_protocols or []
        message = f"Protocol '{protocol}' is not supported."
        if self.supported_protocols:
            protocols_str = ", ".join(f"'{p}'" for p in self.supported_protocols)
            message += f" Supported protocols are: {protocols_str}."
        super().__init__(message)


class MetricNotFoundError(GovernanceAnalyzerError):
    """Exception raised when a requested metric is not found in the data."""
    def __init__(self, metric: str, available_metrics: list = None):
        self.metric = metric
        self.available_metrics = available_metrics or []
        message = f"Metric '{metric}' not found in data."
        if self.available_metrics:
            metrics_str = ", ".join(f"'{m}'" for m in self.available_metrics)
            message += f" Available metrics are: {metrics_str}."
        super().__init__(message)


class HistoricalDataError(GovernanceAnalyzerError):
    """Exception raised for issues related to historical data analysis."""
    pass


class VisualizationError(GovernanceAnalyzerError):
    """Exception raised for issues related to data visualization."""
    pass


class ConfigurationError(GovernanceAnalyzerError):
    """Exception raised for issues related to configuration."""
    pass


class AnalysisError(Exception):
    """Exception raised for errors during data analysis."""
    pass


class NetworkAnalysisError(Exception):
    """Exception raised for errors during network analysis."""
    pass
