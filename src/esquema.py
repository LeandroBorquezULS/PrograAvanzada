"""Construcción y validación del esquema mínimo de eventos."""

REQUIRED = {"timestamp", "sensor_id", "metric", "value", "unit", "worker_id"}
VALID_METRICS = {"temperature", "vibration", "current", "weight", "humidity"}

def construir_evento(timestamp, sensor_id, metric, value, unit, worker_id, seq=None):
    evento = {
        "timestamp": timestamp,
        "sensor_id": sensor_id,
        "metric": metric,
        "value": float(value),
        "unit": unit,
        "worker_id": int(worker_id),
    }
    if seq is not None:
        evento["seq"] = int(seq)
    return evento

def validar_evento(evento):
    if not REQUIRED.issubset(evento):
        return False
    if not isinstance(evento["timestamp"], str) or not evento["timestamp"].endswith("Z"):
        return False
    if not isinstance(evento["sensor_id"], str) or "_S3_" not in evento["sensor_id"]:
        return False
    if evento["metric"] not in VALID_METRICS:
        return False
    if not isinstance(evento["value"], (int, float)):
        return False
    if not isinstance(evento["unit"], str):
        return False
    if not isinstance(evento["worker_id"], int):
        return False
    return True
