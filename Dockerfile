FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 
PYTHONUNBUFFERED=1 
PIP_NO_CACHE_DIR=1 
PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip install --no-cache-dir matplotlib

COPY src/ ./src/
COPY bench/ ./bench/
COPY README.md .

RUN mkdir -p data/raw data/muestra

RUN useradd --create-home --uid 1000 appuser && 
chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python", "-m", "src.main"]

CMD ["--workers", "4", "--total-events", "10000000", "--output-dir", "data/raw", "--arch", "shard"]