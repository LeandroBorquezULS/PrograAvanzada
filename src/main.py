"""Punto de entrada del generador TPC Fase 1."""

import argparse
import json
import multiprocessing as mp
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .arquitectura_b import trabajador_shard
from .arquitectura_a import escritor, trabajador

def parse_args():
    p = argparse.ArgumentParser(description="Generador masivo de logs TPC Sitio 3")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--total-events", type=int, default=10_000_000)
    p.add_argument("--output-dir", default="data/raw")
    p.add_argument("--arch", choices=["queue", "shard"], default="shard")
    p.add_argument("--batch-size", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--sim-days", type=int, default=9)
    return p.parse_args()

def validate_args(a):
    cpu = os.cpu_count() or 1
    if a.workers < 1:
        raise SystemExit("--workers debe ser >= 1")
    if a.workers > cpu * 2:
        raise SystemExit(f"--workers={a.workers} es excesivo para {cpu} CPUs lógicas")
    if a.total_events < 1:
        raise SystemExit("--total-events debe ser >= 1")
    if a.batch_size < 1:
        raise SystemExit("--batch-size debe ser >= 1")

def write_manifest(out, metadata):
    with open(Path(out) / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def run_shard(a, out):
    per = a.total_events // a.workers
    rem = a.total_events % a.workers
    results = []
    ctx = mp.get_context("spawn")
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=ctx) as pool:
        futs = []
        for wid in range(a.workers):
            n = per + (1 if wid < rem else 0)
            futs.append(pool.submit(trabajador_shard, wid, n, out, a.seed,
                                    a.batch_size, a.sim_days))
        for f in as_completed(futs):
            results.append(f.result())
    elapsed = time.perf_counter() - start
    return results, elapsed

def run_queue(a, out):
    out_file = Path(out) / "eventos.jsonl"
    ctx = mp.get_context("spawn")
    q = ctx.Queue(maxsize=64)
    writer = ctx.Process(target=escritor, args=(q, str(out_file), a.workers))
    writer.start()

    per = a.total_events // a.workers
    rem = a.total_events % a.workers
    workers = []
    start = time.perf_counter()
    for wid in range(a.workers):
        n = per + (1 if wid < rem else 0)
        proc = ctx.Process(target=trabajador,
                           args=(q, wid, n, a.seed, a.batch_size))
        proc.start()
        workers.append(proc)

    for proc in workers:
        proc.join()
        if proc.exitcode != 0:
            writer.terminate()
            writer.join()
            raise RuntimeError(f"Worker terminó con código {proc.exitcode}")

    writer.join()
    if writer.exitcode != 0:
        raise RuntimeError(f"Escritor terminó con código {writer.exitcode}")

    elapsed = time.perf_counter() - start
    size = out_file.stat().st_size
    return [{"worker_id": i, "archivo": out_file.name, "eventos": per + (1 if i < rem else 0)}
            for i in range(a.workers)], elapsed

def main():
    a = parse_args()
    validate_args(a)
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results, elapsed = (run_queue(a, out) if a.arch == "queue" else run_shard(a, out))
    total = sum(r["eventos"] for r in results)
    files = sorted(str(p.name) for p in out.glob("*.jsonl"))
    bytes_written = sum(p.stat().st_size for p in out.glob("*.jsonl"))

    manifest = {
        "total_events": total,
        "files": files,
        "bytes_written": bytes_written,
        "seed": a.seed,
        "workers": a.workers,
        "architecture": a.arch,
        "batch_size": a.batch_size,
        "sim_days": a.sim_days,
        "duration_seconds": elapsed,
        "events_per_second": total / elapsed if elapsed else 0,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    write_manifest(out, manifest)
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
