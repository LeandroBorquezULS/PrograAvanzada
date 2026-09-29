# =============================================================================
#  Imagen única para los tres roles del clúster: master, worker y nodo Jupyter.
# =============================================================================
#
#  ¿Por qué UNA sola imagen y no una para Spark y otra para Jupyter?
#  Porque el driver de PySpark (que vive en el contenedor de Jupyter) y los
#  executors (que viven en los workers) se envían objetos Python serializados.
#  Si las versiones de Python o de Spark no coinciden EXACTAMENTE, Spark aborta con
#     "Python in worker has different version 3.10 than that in driver 3.11"
#  Con una imagen única ese error es imposible por construcción. Es el fallo más
#  común al seguir tutoriales que mezclan imágenes de distintos orígenes.
#
#  ¿Por qué Spark 4.0 y no 3.5?
#  Porque las imágenes oficiales de Spark 3.5.x vienen con Python 3.8, que dejó de
#  tener soporte en octubre de 2024 y ya no admite pandas ni JupyterLab modernos.
#  La de Spark 4.0.1 trae Python 3.10 sobre Ubuntu 22.04.
# =============================================================================

ARG SPARK_VERSION=4.0.1
FROM apache/spark:${SPARK_VERSION}

# La imagen de Apache corre como el usuario 'spark' (uid 185). Necesitamos root
# para instalar paquetes y para escribir sin fricción en el volumen montado desde
# Windows. Es una decisión de laboratorio: en producción NO se hace.
USER root

# La imagen base ya trae java 17, python3.10, pip, curl y ps: no hace falta apt-get.
# Evitarlo ahorra varios minutos de build y quita una fuente de fallos (repos caídos).
RUN pip install --no-cache-dir \
        "jupyterlab>=4.0,<5" \
        "pandas>=2.0,<3" \
        "pyarrow>=14" \
        "matplotlib>=3.7"

# Configuración de Spark compartida por todos los nodos.
COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf

# Carpeta de logs de eventos (la consume el History Server, servicio opcional).
RUN mkdir -p /opt/workspace /tmp/spark-events && chmod -R 777 /tmp/spark-events

# PYSPARK_PYTHON le dice a los EXECUTORS qué intérprete usar y PYSPARK_DRIVER_PYTHON
# hace lo propio con el DRIVER. Fijarlas evita que un nodo elija otro intérprete si
# hubiera más de uno instalado.
ENV PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3 \
    SPARK_HOME=/opt/spark \
    PATH="/opt/spark/bin:/opt/spark/sbin:${PATH}"

# La imagen trae Spark en /opt/spark, pero su módulo Python NO está en el PYTHONPATH:
# un 'import pyspark' falla con ModuleNotFoundError.
#
# Se registra mediante un archivo .pth en site-packages en lugar de hacer
# 'pip install pyspark' A PROPÓSITO: pip descargaría OTRA copia de Spark que podría
# quedar desalineada con la del clúster. Así el driver usa exactamente el mismo
# PySpark que ejecutan los workers.
#
# La ruta de py4j se descubre con un glob y no se escribe a mano, porque su versión
# cambia con cada versión de Spark y dejarla fija rompería el build al subir de versión.
RUN set -eux; \
    SITE="$(python3 -c 'import site; print(site.getsitepackages()[0])')"; \
    echo "/opt/spark/python" > "${SITE}/spark.pth"; \
    ls /opt/spark/python/lib/py4j-*-src.zip >> "${SITE}/spark.pth"; \
    cat "${SITE}/spark.pth"; \
    python3 -c "import pyspark; print('pyspark', pyspark.__version__, 'importable')"

WORKDIR /opt/workspace
