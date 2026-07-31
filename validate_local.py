"""Validación local del conector cost_explorer: ejercita las 3 capacidades.

Uso:
    python validate_local.py

Requiere las variables RUVIC_COST_EXPLORER_* exportadas en el entorno.
Es un conector 100% de solo lectura: no modifica nada en tu cuenta de AWS.
"""

from ruvic_cost_explorer_connector import CostExplorerClient, setup_logging

setup_logging("INFO")
client = CostExplorerClient()

print("== 1. Costo por servicio (últimos 30 días) ==")
por_servicio = client.get_cost_by_service(days=30)
for s in por_servicio[:5]:
    print(f"  {s['service']}: {s['amount']} {s['unit']}")

print("== 2. Costo por período (últimos 7 días) ==")
por_periodo = client.get_cost_by_period(days=7)
for p in por_periodo:
    print(f"  {p['start']} a {p['end']}: {p['amount']} {p['unit']}")

print("== 3. Previsión de gasto (próximos 30 días) ==")
forecast = client.get_cost_forecast(days_ahead=30)
print(f"  {forecast}")

print("\nTodo OK: get_cost_by_service, get_cost_by_period y get_cost_forecast funcionan.")
