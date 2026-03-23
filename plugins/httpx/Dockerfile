FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://github.com/projectdiscovery/httpx/releases/download/v1.6.8/httpx_1.6.8_linux_amd64.zip -o /tmp/httpx.zip && \
    unzip -q /tmp/httpx.zip httpx && \
    mv httpx /usr/local/bin/ && \
    rm /tmp/httpx.zip && \
    chmod +x /usr/local/bin/httpx

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /tmp && \
    chown -R appuser:appuser /app /tmp

USER appuser
ENV PATH="/usr/local/bin:${PATH}"
ENV TMPDIR=/tmp

CMD ["python", "/app/run.py"]
