"""Opción B: un archivo JSONL independiente por trabajador."""

import json
from pathlib import Path
from .simulador import SimuladorSitio3

def trabajador_shard(wid, n_eventos, carpeta, semilla, batch_size, sim_days=9):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"part-{wid:03d}.jsonl"
    sim = SimuladorSitio3(semilla + wid)
    buf = []
    escritos = 0
    seq = 0

    # Para el volumen exigido, los eventos se producen por tick de 15 s.
    # La marca temporal se avanza aritméticamente; no se llama datetime.now()
    # por cada evento.
    import datetime
    base_ms = int(datetime.datetime(2026, 8, 24, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    intervalo_ms = 15_000

    with open(ruta, "w", encoding="utf-8", newline="\n", buffering=4*1024*1024) as f:
        while escritos < n_eventos:
            tick_events = sim.tick(15)
            for sensor_id, metric, value, unit in tick_events:
                if escritos >= n_eventos:
                    break
                ts_ms = base_ms + seq * intervalo_ms
                ts = datetime.datetime.fromtimestamp(
                    ts_ms / 1000, tz=datetime.timezone.utc
                ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
                ev = {
                    "timestamp": ts, "sensor_id": sensor_id, "metric": metric,
                    "value": value, "unit": unit, "worker_id": wid, "seq": seq
                }
                buf.append(json.dumps(ev, separators=(",", ":")) + "\n")
                escritos += 1
                seq += 1
                if len(buf) >= batch_size:
                    f.writelines(buf)
                    buf.clear()
        if buf:
            f.writelines(buf)

    return {
        "worker_id": wid,
        "archivo": ruta.name,
        "eventos": escritos,
        "bytes": ruta.stat().st_size,
    }
