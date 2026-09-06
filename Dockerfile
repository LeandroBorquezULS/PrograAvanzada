FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir matplotlib
COPY src/ ./src/
COPY bench/ ./bench/
COPY README.md .
RUN mkdir -p data/raw data/muestra
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--workers", "4", "--total-events", "10000000", "--output-dir", "data/raw", "--arch", "shard"]
