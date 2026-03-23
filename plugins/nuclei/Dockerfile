FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://github.com/projectdiscovery/nuclei/releases/download/v3.3.1/nuclei_3.3.1_linux_amd64.zip -o /tmp/nuclei.zip && \
    unzip -q /tmp/nuclei.zip && \
    mv nuclei /usr/local/bin/ && \
    rm /tmp/nuclei.zip && \
    chmod +x /usr/local/bin/nuclei

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
