FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_linux_amd64.zip -o /tmp/httpx.zip && \
    unzip -q /tmp/httpx.zip httpx && \
    mv httpx /usr/local/bin/ && \
    rm /tmp/httpx.zip && \
    chmod +x /usr/local/bin/httpx

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/app/run.py"]
