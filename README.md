# proyecto-tpc-fase1

Generador masivo de logs JSON Lines para el Sitio 3 del Terminal Puerto Coquimbo.

## Requisitos
- Python 3.11+
- Solo biblioteca estándar dentro del generador.
- `matplotlib` únicamente para gráficos de benchmarking.

## Ejecución

Desde la raíz:

```bash
python -m src.main --workers 8 --total-events 10000000 --output-dir data/raw --arch shard --batch-size 10000 --seed 42 --sim-days 9
```

Arquitectura alternativa:

```bash
python -m src.main --workers 8 --total-events 10000000 --output-dir data/raw --arch queue --batch-size 10000 --seed 42 --sim-days 9
```

## Validación

```bash
python bench/validar.py
```

También se puede comprobar el volumen con:

```bash
wc -l data/raw/*.jsonl
du -sh data/raw/
```

## Benchmarking

Realizar calentamiento y luego 3 corridas por configuración con 1, 2, 4, 8 y 16 trabajadores, manteniendo fijo el total de eventos. Registrar en `bench/mediciones.csv`:

`architecture,workers,run,duration_seconds,total_events,events_per_second,mb_per_second`

La mediana de las tres corridas es la medida principal. Calcular:

`S(n) = T(1) / T(n)`

`E(n) = S(n) / n`

## Reproducibilidad

Con la misma semilla y el mismo número de trabajadores se busca producir resultados reproducibles. La salida está separada por worker en la arquitectura `shard`.

## Git

`data/raw/` se ignora porque el dataset completo supera ampliamente el tamaño razonable para Git.
`data/muestra/` está destinada a una muestra versionada de 50.000 eventos.
