"""Excepciones propias del conector AWS Cost Explorer.

Separan los tres tipos de fallo que el usuario debe distinguir:
autenticación, red/servidor y datos. Nunca exponemos excepciones
crípticas del SDK subyacente.
"""


class CostExplorerConnectorError(Exception):
    """Error base del conector."""


class CostExplorerAuthError(CostExplorerConnectorError):
    """Credenciales inválidas o permisos IAM insuficientes."""


class CostExplorerNetworkError(CostExplorerConnectorError):
    """No se pudo alcanzar el servicio Cost Explorer (red/timeout)."""


class CostExplorerDataError(CostExplorerConnectorError):
    """La operación es válida pero el parámetro/rango es inválido."""
