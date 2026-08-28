"""Cliente de consulta de costos y uso para AWS Cost Explorer.

Capacidades:
- get_cost_by_service():  costo total por servicio de AWS en un rango.
- get_cost_by_period():   costo total agregado por período (día/mes).
- get_cost_forecast():    previsión de gasto futuro.

Las credenciales SIEMPRE provienen de variables de entorno
RUVIC_COST_EXPLORER_* (ver config.CostExplorerConfig.from_env).
Prohibido hardcodearlas.

Nota: la API de Cost Explorer es de solo lectura por naturaleza — no
existe ninguna operación de escritura en este servicio de AWS.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.config import Config as BotoConfig  # type: ignore[import-untyped]
from botocore.exceptions import (  # type: ignore[import-untyped]
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
)

from .config import CostExplorerConfig
from .exceptions import (
    CostExplorerAuthError,
    CostExplorerConnectorError,
    CostExplorerDataError,
    CostExplorerNetworkError,
)
from .logging_utils import get_logger

_AUTH_ERROR_CODES = {
    "UnrecognizedClientException",
    "InvalidClientTokenId",
    "InvalidSignatureException",
    "AccessDeniedException",
}
_VALID_GRANULARITIES = {"DAILY", "MONTHLY"}


def _require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CostExplorerDataError(f"{field} debe ser un entero, no {type(value).__name__}.")
    if value <= 0:
        raise CostExplorerDataError(f"{field} debe ser mayor a 0.")
    return value


def _validate_granularity(granularity: Any) -> str:
    if not isinstance(granularity, str) or granularity not in _VALID_GRANULARITIES:
        raise CostExplorerDataError(
            f"granularity debe ser uno de: {', '.join(sorted(_VALID_GRANULARITIES))}."
        )
    return granularity


def _wrap_client_error(exc: ClientError) -> CostExplorerConnectorError:
    """Traduce un error de la API de AWS a una excepción propia, sin
    dejar escapar nunca el tipo crudo del SDK."""
    code = exc.response.get("Error", {}).get("Code", "")
    if code in _AUTH_ERROR_CODES:
        return CostExplorerAuthError(
            "Credenciales inválidas o sin permiso IAM suficiente para esta "
            "operación. Revisa la policy adjunta al usuario o rol."
        )
    if code in ("ValidationException", "LimitExceededException"):
        return CostExplorerDataError(f"Parámetro inválido: {exc}")
    return CostExplorerDataError(f"Error de datos ({code}): {exc}")


class CostExplorerClient:
    """Cliente de consulta de costos y uso de AWS vía Cost Explorer.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_COST_EXPLORER_* (comportamiento
            estándar en el runtime de la plataforma).

    Ejemplo:
        >>> client = CostExplorerClient()  # lee RUVIC_COST_EXPLORER_* del entorno
        >>> client.get_cost_by_service()
        [{'service': 'Amazon EC2', 'amount': 123.45, 'unit': 'USD'}, ...]
    """

    def __init__(self, config: CostExplorerConfig | None = None) -> None:
        self.config = config or CostExplorerConfig.from_env()
        self._logger = get_logger()
        self._client: Any = None

    # ------------------------------------------------------------------ #
    # Conexión
    # ------------------------------------------------------------------ #

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        self._client = boto3.client(
            "ce",
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_access_key,
            region_name="us-east-1",  # Cost Explorer es un servicio global
            config=BotoConfig(
                connect_timeout=self.config.connect_timeout,
                read_timeout=max(self.config.connect_timeout, 30),
                retries={"max_attempts": 2, "mode": "standard"},
            ),
        )
        return self._client

    @staticmethod
    def _default_period(days: int) -> tuple[str, str]:
        end = datetime.now(UTC).date()
        start = end - timedelta(days=days)
        return start.isoformat(), end.isoformat()

    def ping(self) -> bool:
        """Verifica la conexión consultando el costo de los últimos 7 días.

        Returns:
            True si la conexión funciona.

        Raises:
            CostExplorerAuthError / CostExplorerNetworkError /
            CostExplorerDataError.
        """
        self.get_cost_by_period(days=7)
        self._logger.info("Ping exitoso a Cost Explorer")
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: costo por servicio
    # ------------------------------------------------------------------ #

    def get_cost_by_service(self, days: int = 30) -> list[dict[str, Any]]:
        """Consulta el costo total agrupado por servicio de AWS.

        Args:
            days: cantidad de días hacia atrás desde hoy (default 30).

        Returns:
            Lista de dicts: {"service", "amount", "unit"}, ordenada de
            mayor a menor costo.

        Ejemplo:
            >>> client.get_cost_by_service(days=7)
            [{'service': 'Amazon EC2', 'amount': 45.2, 'unit': 'USD'}, ...]
        """
        days = _require_positive_int(days, "days")
        start, end = self._default_period(days)
        client = self._get_client()
        try:
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
        except ClientError as exc:
            raise _wrap_client_error(exc) from exc
        except (EndpointConnectionError, BotoCoreError) as exc:
            raise CostExplorerNetworkError(f"No se pudo consultar el costo: {exc}") from exc

        totals: dict[str, float] = {}
        unit = "USD"
        for period in response.get("ResultsByTime", []):
            for group in period.get("Groups", []):
                service = group["Keys"][0]
                cost = group["Metrics"]["UnblendedCost"]
                amount = float(cost["Amount"])
                unit = cost.get("Unit", unit)
                totals[service] = totals.get(service, 0.0) + amount

        rows: list[dict[str, Any]] = [
            {"service": service, "amount": round(amount, 2), "unit": unit}
            for service, amount in totals.items()
            if amount > 0
        ]
        result = sorted(rows, key=lambda d: d["amount"], reverse=True)
        self._logger.info("Costo por servicio: %d servicio(s) con gasto", len(result))
        return result

    # ------------------------------------------------------------------ #
    # Capacidad 2: costo por período
    # ------------------------------------------------------------------ #

    def get_cost_by_period(self, days: int = 30, granularity: str = "DAILY") -> list[dict[str, Any]]:
        """Consulta el costo total agregado por período de tiempo.

        Args:
            days: cantidad de días hacia atrás desde hoy (default 30).
            granularity: "DAILY" o "MONTHLY" (default "DAILY").

        Returns:
            Lista de dicts: {"start", "end", "amount", "unit"}.

        Ejemplo:
            >>> client.get_cost_by_period(days=7)
            [{'start': '2026-07-24', 'end': '2026-07-25', 'amount': 12.3, 'unit': 'USD'}, ...]
        """
        days = _require_positive_int(days, "days")
        granularity = _validate_granularity(granularity)
        start, end = self._default_period(days)
        client = self._get_client()
        try:
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity=granularity,
                Metrics=["UnblendedCost"],
            )
        except ClientError as exc:
            raise _wrap_client_error(exc) from exc
        except (EndpointConnectionError, BotoCoreError) as exc:
            raise CostExplorerNetworkError(f"No se pudo consultar el costo: {exc}") from exc

        result = [
            {
                "start": period["TimePeriod"]["Start"],
                "end": period["TimePeriod"]["End"],
                "amount": round(float(period["Total"]["UnblendedCost"]["Amount"]), 2),
                "unit": period["Total"]["UnblendedCost"].get("Unit", "USD"),
            }
            for period in response.get("ResultsByTime", [])
        ]
        self._logger.info("Costo por período: %d intervalo(s)", len(result))
        return result

    # ------------------------------------------------------------------ #
    # Capacidad 3: previsión de gasto
    # ------------------------------------------------------------------ #

    def get_cost_forecast(self, days_ahead: int = 30, granularity: str = "MONTHLY") -> dict[str, Any]:
        """Obtiene la previsión de gasto para los próximos días.

        Args:
            days_ahead: cantidad de días hacia adelante desde hoy
                (default 30).
            granularity: "DAILY" o "MONTHLY" (default "MONTHLY").

        Returns:
            Dict con: start, end, total_forecast, unit.

        Ejemplo:
            >>> client.get_cost_forecast(days_ahead=30)
            {'start': '2026-07-31', 'end': '2026-08-30', 'total_forecast': 512.4, 'unit': 'USD'}
        """
        days_ahead = _require_positive_int(days_ahead, "days_ahead")
        granularity = _validate_granularity(granularity)
        start = datetime.now(UTC).date()
        end = start + timedelta(days=days_ahead)
        client = self._get_client()
        try:
            response = client.get_cost_forecast(
                TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
                Metric="UNBLENDED_COST",
                Granularity=granularity,
            )
        except ClientError as exc:
            raise _wrap_client_error(exc) from exc
        except (EndpointConnectionError, BotoCoreError) as exc:
            raise CostExplorerNetworkError(f"No se pudo obtener la previsión: {exc}") from exc

        total = response.get("Total", {})
        result = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "total_forecast": round(float(total.get("Amount", 0)), 2),
            "unit": total.get("Unit", "USD"),
        }
        self._logger.info("Previsión de gasto: %s %s", result["total_forecast"], result["unit"])
        return result
