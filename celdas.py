# --- Guarda de entorno --------------------------------------------------------
# Falla rápido y con un mensaje claro en vez de dejar que PySpark reviente 20
# líneas más abajo con un error que no menciona la causa real.
import os, shutil, sys

problemas = []

if not os.path.isdir("/opt/spark"):
    problemas.append("no existe /opt/spark: no estás en el contenedor del clúster")

if shutil.which("java") is None:
    problemas.append("no hay Java en el PATH: PySpark no puede arrancar la JVM")

try:
    import pyspark
    if not pyspark.__file__.startswith("/opt/spark/"):
        problemas.append(
            f"pyspark viene de {pyspark.__file__}\n"
            f"        (instalado por pip/conda) en vez de /opt/spark/python. "
            f"Esa copia no está alineada con el clúster.")
except ImportError:
    problemas.append("pyspark no es importable")

if problemas:
    print("=" * 72)
    print("ESTE NOTEBOOK NO ESTÁ CORRIENDO EN EL CLÚSTER")
    print("=" * 72)
    for p in problemas:
        print(f"  - {p}")
    print()
    print("  Ábrelo en el Jupyter DEL CLÚSTER:")
    print("      http://localhost:8889        (token: lab-sitio3)")
    print()
    print("  El del puerto 8888 es el entorno de la Fase 1. Monta esta misma")
    print("  carpeta, por eso ves el mismo archivo, pero no tiene Java ni")
    print("  conexión con los workers.")
    print("=" * 72)
    raise SystemExit("Entorno incorrecto: usa http://localhost:8889")

print(f"Entorno correcto")
print(f"  Python  : {sys.version.split()[0]}")
print(f"  Java    : {shutil.which('java')}")
print(f"  PySpark : {pyspark.__file__}")



#Celda 2
import os, time
from pyspark.sql import SparkSession, functions as F, Window
from pyspark.sql.types import (StructType, StructField, StringType,
                                DoubleType, LongType, TimestampType)

spark = (
    SparkSession.builder
    .appName("fase2-sitio3")
    .master(os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077"))
    # --- los tres parámetros críticos en Docker ---
    .config("spark.driver.host", os.environ.get("SPARK_DRIVER_HOST", "jupyter"))
    .config("spark.driver.bindAddress", "0.0.0.0")
    # --- memoria: debe caber en lo que declara cada worker (ver .env) ---
    .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "2g"))
    .config("spark.executor.memory", os.environ.get("SPARK_EXECUTOR_MEMORY", "2g"))
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

sc = spark.sparkContext
print(f"Spark          : {spark.version}")
print(f"Master         : {sc.master}")
print(f"Executors      : {sc._jsc.sc().getExecutorMemoryStatus().size() - 1}")
print(f"Paralelismo    : {sc.defaultParallelism} tareas simultáneas")
print(f"UI del driver  : http://localhost:4040")


.env.exapmle
# =============================================================================
#  Parámetros del clúster — Fase 2, Laboratorio de Programación Avanzada
# =============================================================================
#  Este archivo lo lee docker-compose automáticamente. Es el ÚNICO lugar que hay
#  que tocar para adaptar el clúster a la máquina de cada alumno.
# =============================================================================

# Versión de Spark. Debe existir como tag en https://hub.docker.com/r/apache/spark
#
# OJO: las imágenes oficiales de Spark 3.5.x traen Python 3.8 (sin soporte desde
# octubre de 2024, incompatible con pandas y JupyterLab actuales). La de 4.0.1 trae
# Python 3.10 sobre Ubuntu 22.04. Por eso el laboratorio usa la 4.
SPARK_VERSION=4.0.1

# -----------------------------------------------------------------------------
#  Dimensionamiento
# -----------------------------------------------------------------------------
#  Regla práctica: la suma de (WORKERS x WORKER_MEMORY) + DRIVER_MEMORY debe
#  quedar cómodamente por debajo de la RAM que Docker Desktop tiene asignada.
#  Si Spark se queda sin memoria, no falla limpio: empieza a volcar a disco
#  ("spill") y la práctica se vuelve lentísima sin decir por qué.
#
#  Perfiles sugeridos según la RAM que Docker tenga disponible:
#
#    Docker con  6 GB  ->  WORKERS=2  CORES=1  WORKER_MEMORY=1g  DRIVER_MEMORY=1g
#    Docker con  8 GB  ->  WORKERS=2  CORES=2  WORKER_MEMORY=2g  DRIVER_MEMORY=2g   <- por defecto
#    Docker con 16 GB  ->  WORKERS=3  CORES=2  WORKER_MEMORY=3g  DRIVER_MEMORY=3g
#    Docker con 32 GB  ->  WORKERS=4  CORES=3  WORKER_MEMORY=6g  DRIVER_MEMORY=4g
#
#  Para ver cuánta RAM tiene Docker:  docker info --format "{{.MemTotal}}"
# -----------------------------------------------------------------------------

SPARK_WORKERS=2
SPARK_WORKER_CORES=2
SPARK_WORKER_MEMORY=2g
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g

# -----------------------------------------------------------------------------
#  Puertos publicados en el host (cambiar solo si ya están ocupados)
# -----------------------------------------------------------------------------
PUERTO_MASTER_UI=8080
PUERTO_MASTER=7077
PUERTO_DRIVER_UI=4040
PUERTO_HISTORY_UI=18080

# 8889 y no 8888 A PROPÓSITO: si ya tienes un Jupyter instalado de forma nativa en
# tu máquina (como el de la Fase 1), está ocupando el 8888 y el contenedor no podrá
# arrancar — falla con "port is already allocated". Usando el 8889 conviven los dos:
#   localhost:8888 -> tu Jupyter de siempre (Fase 1)
#   localhost:8889 -> el Jupyter del clúster, con PySpark (Fase 2)
PUERTO_JUPYTER=8889

# -----------------------------------------------------------------------------
#  Token de acceso a JupyterLab.
#  Se usa un token fijo y legible porque es un laboratorio en una red local.
#  En cualquier entorno real: token aleatorio o autenticación de verdad.
# -----------------------------------------------------------------------------
JUPYTER_TOKEN=lab-sitio3
