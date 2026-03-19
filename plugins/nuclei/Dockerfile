FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://github.com/projectdiscovery/nuclei/releases/download/v3.2.0/nuclei_3.2.0_linux_amd64.zip -o /tmp/nuclei.zip && \
    unzip -q /tmp/nuclei.zip nuclei && \
    mv nuclei /usr/local/bin/ && \
    rm /tmp/nuclei.zip && \
    chmod +x /usr/local/bin/nuclei

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/app/run.py"]
