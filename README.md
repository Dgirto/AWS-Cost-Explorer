# Conector AWS Cost Explorer (CON-069)

Conector Ruvic de consulta de costos y uso de AWS. Permite consultar el
costo total por servicio, el costo agregado por período, y obtener una
previsión de gasto futuro. Es un conector **100% de solo lectura**: no
existe ninguna operación de escritura en la API de Cost Explorer.

## Instalación

```bash
pip install git+https://github.com/Dgirto/AWS-Cost-Explorer.git#subdirectory=lib
```

Python 3.10+. Dependencia única: `boto3>=1.34,<2.0`.

## Permisos requeridos en AWS (IAM)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
```

Cost Explorer no admite restricción de permisos por `Resource`
específico (siempre es `"*"`), pero al ser un servicio de solo lectura
no hay riesgo de que el conector modifique nada en la cuenta.

## Variables de entorno (`RUVIC_COST_EXPLORER_*`)

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_COST_EXPLORER_ACCESS_KEY_ID` | Sí | Access Key ID de AWS |
| `RUVIC_COST_EXPLORER_SECRET_ACCESS_KEY` | Sí | Secret Access Key de AWS |
| `RUVIC_COST_EXPLORER_CONNECT_TIMEOUT` | No (default `10`) | Timeout de conexión en segundos |

No hay campo de región: Cost Explorer es un servicio global, siempre se
consulta vía el endpoint de `us-east-1` sin importar en qué región
viven los recursos que generan el costo.

## Pruebas locales

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib

export RUVIC_COST_EXPLORER_ACCESS_KEY_ID=tu-access-key
export RUVIC_COST_EXPLORER_SECRET_ACCESS_KEY=tu-secret-key

python test_connection.py
python validate_local.py
```

## Notas de integración

- Cost Explorer solo tiene datos a partir de que se activó por primera
  vez en la cuenta — si la cuenta es nueva, algunos rangos históricos
  pueden devolver montos en cero.
- `get_cost_forecast` requiere que el rango consultado sea a futuro
  (desde hoy en adelante); no sirve para consultar previsiones de
  fechas pasadas.
- Los montos se redondean a 2 decimales; la moneda (`unit`) suele ser
  `"USD"` salvo que la cuenta tenga configurada otra moneda de
  facturación.
- `get_cost_by_service` agrupa por la dimensión `SERVICE` de AWS (ej.
  "Amazon EC2", "Amazon S3", "AWS Lambda").
