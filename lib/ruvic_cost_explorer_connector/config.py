"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_COST_EXPLORER_.

Nota: la API de AWS Cost Explorer es un servicio global, siempre se
accede vía el endpoint de us-east-1 sin importar en qué región viven
los recursos que generan el costo — por eso este conector no expone un
campo de región.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_COST_EXPLORER_"


@dataclass(frozen=True)
class CostExplorerConfig:
    """Parámetros de conexión a AWS Cost Explorer."""

    access_key_id: str
    secret_access_key: str
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> "CostExplorerConfig":
        """Construye la configuración desde las variables RUVIC_COST_EXPLORER_*.

        Raises:
            ValueError: si falta alguna variable obligatoria.

        Ejemplo:
            >>> config = CostExplorerConfig.from_env()
            >>> config.access_key_id
            'AKIAIOSFODNN7EXAMPLE'
        """
        missing = [
            f"{ENV_PREFIX}{name}"
            for name in ("ACCESS_KEY_ID", "SECRET_ACCESS_KEY")
            if not os.environ.get(f"{ENV_PREFIX}{name}")
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno del conector cost_explorer: "
                + ", ".join(missing)
                + ". Configura el conector en Settings → Conectores."
            )
        return cls(
            access_key_id=os.environ[f"{ENV_PREFIX}ACCESS_KEY_ID"],
            secret_access_key=os.environ[f"{ENV_PREFIX}SECRET_ACCESS_KEY"],
            connect_timeout=int(os.environ.get(f"{ENV_PREFIX}CONNECT_TIMEOUT", "10")),
        )
