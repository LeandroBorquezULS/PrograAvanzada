"""Opción A: trabajadores producen lotes y un único proceso escribe."""

import json
import multiprocessing as mp
from datetime import datetime, timezone, timedelta
from .simulador import SimuladorSitio3

CENTINELA = "__FIN__"

def escritor(cola, ruta, n_workers):
    vivos = n_workers
    with open(ruta, "w", encoding="utf-8", newline="\n", buffering=1024*1024) as f:
        while vivos:
            lote = cola.get()
            if lote == CENTINELA:
                vivos -= 1
                continue
            f.writelines(lote)

def trabajador(cola, wid, n_eventos, semilla, batch_size):
    sim = SimuladorSitio3(semilla + wid)
    buf = []
    seq = 0
    base = datetime(2026, 8, 24, tzinfo=timezone.utc)
    while seq < n_eventos:
        for sensor_id, metric, value, unit in sim.tick(15):
            if seq >= n_eventos:
                break
            ts = (base + timedelta(seconds=15*seq)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            ev = {
                "timestamp": ts, "sensor_id": sensor_id, "metric": metric,
                "value": value, "unit": unit, "worker_id": wid, "seq": seq
            }
            buf.append(json.dumps(ev, separators=(",", ":")) + "\n")
            seq += 1
            if len(buf) >= batch_size:
                cola.put(buf)
                buf = []
    if buf:
        cola.put(buf)
    cola.put(CENTINELA)
