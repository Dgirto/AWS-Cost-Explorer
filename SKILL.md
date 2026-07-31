---
name: cost_explorer
description: >
  Usa la librería ruvic_cost_explorer_connector para consultar costos y
  uso de AWS - costo total por servicio (get_cost_by_service), costo
  agregado por período (get_cost_by_period), y previsión de gasto
  futuro (get_cost_forecast). Úsala cuando el usuario pida revisar
  gasto, facturación o proyecciones de costo en AWS.
triggers:
- cost explorer
- costos aws
- gasto aws
- facturacion aws
- billing aws
---

# Conector AWS Cost Explorer (ruvic_cost_explorer_connector)

Librería Python de consulta de costos y uso de AWS. Está
**preinstalada en el runtime** cuando el conector está configurado (si
no, instálala con `pip install git+https://github.com/Dgirto/AWS-Cost-Explorer.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de
variables de entorno, disponibles cuando el conector `cost_explorer`
está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_COST_EXPLORER_ACCESS_KEY_ID` | Access Key ID de AWS |
| `RUVIC_COST_EXPLORER_SECRET_ACCESS_KEY` | Secret Access Key de AWS |
| `RUVIC_COST_EXPLORER_CONNECT_TIMEOUT` | (opcional) timeout en segundos |

Si estas variables NO existen, el conector no está configurado: no
generes código que lo use; indica al usuario que lo configure en
**Settings → Conectores**.

## Este conector es 100% de solo lectura

No existe ninguna operación de escritura en la API de Cost Explorer —
no hay riesgo de modificar nada en la cuenta de AWS al usarlo.

## Conexión (siempre igual)

```python
from ruvic_cost_explorer_connector import CostExplorerClient

client = CostExplorerClient()  # lee RUVIC_COST_EXPLORER_* del entorno automáticamente
```

## Capacidad 1 — Costo por servicio

```python
por_servicio = client.get_cost_by_service(days=30)
for s in por_servicio:
    print(s["service"], s["amount"], s["unit"])
```

## Capacidad 2 — Costo por período

```python
por_periodo = client.get_cost_by_period(days=7, granularity="DAILY")
```

## Capacidad 3 — Previsión de gasto

```python
forecast = client.get_cost_forecast(days_ahead=30, granularity="MONTHLY")
print(forecast["total_forecast"], forecast["unit"])
```

## Manejo de errores

```python
from ruvic_cost_explorer_connector import (
    CostExplorerAuthError, CostExplorerDataError, CostExplorerNetworkError,
)

try:
    client.get_cost_by_service()
except CostExplorerAuthError:
    print("Credenciales inválidas o sin permiso IAM suficiente")
except CostExplorerNetworkError:
    print("No se pudo alcanzar Cost Explorer — reintenta en unos segundos")
except CostExplorerDataError as e:
    print(f"Error de datos: {e}")
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_COST_EXPLORER_*` (el constructor de `CostExplorerClient` ya lo hace).
2. Nunca imprimas `RUVIC_COST_EXPLORER_SECRET_ACCESS_KEY` en logs ni en la salida.
3. No inventes montos si la API devuelve una lista vacía o en cero — repórtalo tal cual (puede ser una cuenta nueva sin historial de costos).
4. `get_cost_forecast` solo acepta rangos a futuro (desde hoy en adelante) — no lo uses para consultar el pasado, usá `get_cost_by_period` para eso.
5. Nunca redondees ni conviertas moneda por tu cuenta — reportá el `unit` (moneda) tal como lo devuelve la API.
