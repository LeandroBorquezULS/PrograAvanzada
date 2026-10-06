"""
Verificación del clúster — Fase 2, Laboratorio de Programación Avanzada.

Se ejecuta ANTES de abrir el notebook. Si algo está mal montado, es mucho más
barato descubrirlo aquí que a mitad de la práctica con un error críptico.

    docker compose exec jupyter python3 verificar_cluster.py

Comprueba, en orden:
  1. Que el driver puede hablar con el master.
  2. Que hay executors vivos (y no solo el master registrado).
  3. Que los executors ven los MISMOS archivos que el driver.
  4. Que un job real se reparte entre los workers.
"""
from pyspark.sql import SparkSession
import os
import socket
import sys

RUTA_DATOS = "/opt/workspace/data/raw"

print("=" * 70)
print("VERIFICACIÓN DEL CLÚSTER SPARK — SITIO 3, FASE 2")
print("=" * 70)

# --- 1. Sesión --------------------------------------------------------------
# spark.driver.host es imprescindible: el driver corre dentro del contenedor
# 'jupyter' y los executors necesitan un nombre resoluble para devolverle los
# resultados. Sin esto el job se queda en RUNNING para siempre, sin error.
spark = (
    SparkSession.builder.appName("verificacion-cluster")
    .master(os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077"))
    .config("spark.driver.host", os.environ.get("SPARK_DRIVER_HOST", "jupyter"))
    .config("spark.driver.bindAddress", "0.0.0.0")
    .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "2g"))
    .config("spark.executor.memory", os.environ.get("SPARK_EXECUTOR_MEMORY", "2g"))
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

sc = spark.sparkContext
print(f"\n[1/4] Sesión creada")
print(f"      Spark   : {spark.version}")
print(f"      Python  : {sys.version.split()[0]}")
print(f"      Master  : {sc.master}")
print(f"      App ID  : {sc.applicationId}")

# --- 2. Executors -----------------------------------------------------------
# El driver aparece en esta lista como 'driver'; hay que descontarlo para saber
# cuántos executors reales hay. Si el resultado es 0, el clúster está levantado
# pero no te asignó recursos (típico: memoria pedida > memoria del worker).
info = sc._jsc.sc().getExecutorMemoryStatus()
n_executors = info.size() - 1
cores = sc.defaultParallelism
print(f"\n[2/4] Executors vivos : {n_executors}")
print(f"      Paralelismo     : {cores} tareas en paralelo")
if n_executors < 1:
    print("      ERROR: no hay executors. Revisa que SPARK_EXECUTOR_MEMORY no supere")
    print("             la memoria de cada worker (SPARK_WORKER_MEMORY en .env).")
    spark.stop()
    sys.exit(1)

# --- 3. ¿Los executors ven los mismos archivos? -----------------------------
# Con almacenamiento local (no HDFS/S3) cada executor abre el archivo por su
# cuenta. Si el volumen no está montado en los workers en la MISMA ruta, el
# driver lee bien y los executors fallan con FileNotFoundException.
def inspeccionar(_):
    return [(socket.gethostname(), os.path.isdir(RUTA_DATOS))]

vistas = sc.parallelize(range(cores * 4), cores * 4).mapPartitions(inspeccionar).distinct().collect()
print(f"\n[3/4] Visibilidad de {RUTA_DATOS} desde los executors:")
todo_ok = True
for host, ve_datos in sorted(vistas):
    print(f"      {host:<30} {'ve los datos' if ve_datos else 'NO VE LOS DATOS'}")
    todo_ok &= ve_datos
if not todo_ok:
    print("      ERROR: algún executor no ve la ruta. Revisa el volumen en docker-compose.yml:")
    print("             todos los servicios deben montar ./ en /opt/workspace.")
    spark.stop()
    sys.exit(1)

# --- 4. Job real sobre los datos de la Fase 1 -------------------------------
print(f"\n[4/4] Leyendo los datos crudos de la Fase 1...")
if not os.path.isdir(RUTA_DATOS):
    print(f"      AVISO: no existe {RUTA_DATOS}; se omite la prueba de lectura.")
else:
    df = spark.read.json(f"{RUTA_DATOS}/*.jsonl")
    n = df.count()
    print(f"      Registros leídos : {n:,}")
    print(f"      Particiones      : {df.rdd.getNumPartitions()}")
    print(f"      Columnas         : {', '.join(df.columns)}")

print("\n" + "=" * 70)
print("CLÚSTER OPERATIVO. Ya puedes abrir el notebook de la Fase 2.")
print("=" * 70)
spark.stop()
