"""Conector Ruvic de consulta de costos y uso de AWS (Cost Explorer)."""

from .client import CostExplorerClient
from .config import ENV_PREFIX, CostExplorerConfig
from .exceptions import (
    CostExplorerAuthError,
    CostExplorerConnectorError,
    CostExplorerDataError,
    CostExplorerNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "CostExplorerAuthError",
    "CostExplorerClient",
    "CostExplorerConfig",
    "CostExplorerConnectorError",
    "CostExplorerDataError",
    "CostExplorerNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"
