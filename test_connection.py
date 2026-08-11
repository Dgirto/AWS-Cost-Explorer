"""Prueba de conexión estándar del conector cost_explorer.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_COST_EXPLORER_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Conecta a Cost Explorer y consulta el costo de los últimos 7 días
    usando las env vars RUVIC_COST_EXPLORER_*."""
    try:
        from ruvic_cost_explorer_connector import (
            CostExplorerAuthError,
            CostExplorerClient,
            CostExplorerDataError,
            CostExplorerNetworkError,
        )
    except ImportError:
        return (
            False,
            (
                "La librería ruvic-cost-explorer-connector no está instalada. "
                "Instala con: pip install git+https://github.com/Dgirto/"
                "AWS-Cost-Explorer.git#subdirectory=lib"
            ),
        )

    try:
        client = CostExplorerClient()  # valida que existan las env vars
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except CostExplorerAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except CostExplorerNetworkError as exc:
        return False, f"Error de red: {exc}"
    except CostExplorerDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # noqa: BLE001 - red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return (True, "Conexión exitosa a AWS Cost Explorer")


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
