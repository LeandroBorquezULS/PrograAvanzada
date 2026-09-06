"""Genera gráficos desde bench/mediciones.csv.
Ejecutar después de completar la campaña de benchmarking."""
import csv
import matplotlib.pyplot as plt
from pathlib import Path

path = Path("bench/mediciones.csv")
rows = list(csv.DictReader(path.open(encoding="utf-8")))
workers = sorted({int(r["workers"]) for r in rows})
medians = []
for w in workers:
    vals = sorted(float(r["duration_seconds"]) for r in rows if int(r["workers"]) == w)
    medians.append(vals[len(vals)//2])

t1 = medians[0]
speedup = [t1/t for t in medians]
ideal = workers

plt.figure()
plt.plot(workers, speedup, marker="o", label="Speedup medido")
plt.plot(workers, ideal, linestyle="--", label="Ideal")
plt.xlabel("Trabajadores")
plt.ylabel("Speedup")
plt.title("Escalabilidad")
plt.legend()
plt.grid(True)
plt.savefig("bench/speedup.png", dpi=160, bbox_inches="tight")
