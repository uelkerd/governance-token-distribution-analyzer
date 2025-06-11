import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from .metrics import calculate_participation_rate, calculate_vote_distribution
from .metrics_collector import measure_api_call
from .logging_config import get_logger

# Configure logger
logger = get_logger(__name__)


@measure_api_call(protocol="<protocol_name>", method="analyze_governance_participation")
def analyze_governance_participation(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown"
) -> Dict[str, Any]:


@measure_api_call(protocol="<protocol_name>", method="analyze_participation_by_holder_size")
def analyze_participation_by_holder_size(
    governance_data: Dict[str, Any],
    token_holders: pd.DataFrame,
    protocol_name: str = "unknown"
) -> Dict[str, Any]:


@measure_api_call(protocol="<protocol_name>", method="compare_participation_metrics")
def compare_participation_metrics(
    protocol_results: Dict[str, Dict[str, Any]]
) -> pd.DataFrame: