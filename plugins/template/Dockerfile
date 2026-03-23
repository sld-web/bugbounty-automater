FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY protos/ ./protos/
COPY plugins/sdk/ ./sdk/
RUN pip install --no-cache-dir -r requirements.txt grpcio grpcio-tools

RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /tmp && \
    chown -R appuser:appuser /app /tmp

USER appuser
ENV TMPDIR=/tmp
ENV CREDENTIAL_SERVER=host.docker.internal:50051
ENV PYTHONPATH=/app

CMD ["python", "/app/run.py"]
