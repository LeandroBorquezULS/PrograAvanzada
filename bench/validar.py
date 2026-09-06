import glob
import json
import sys

total = 0
for ruta in sorted(glob.glob("data/raw/*.jsonl")):
    with open(ruta, encoding="utf-8") as f:
        for i, linea in enumerate(f, 1):
            try:
                evento = json.loads(linea)
            except json.JSONDecodeError:
                raise SystemExit(f"Línea inválida en {ruta}:{i}")
            required = {"timestamp", "sensor_id", "metric", "value", "unit", "worker_id"}
            if not required.issubset(evento):
                raise SystemExit(f"Esquema inválido en {ruta}:{i}")
            total += 1

print("OK,", total, "eventos válidos")
if total < 10_000_000:
    sys.exit("ERROR: menos de 10 millones de eventos")
