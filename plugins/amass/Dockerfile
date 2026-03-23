FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://github.com/owasp-amass/amass/releases/download/v5.0.1/amass_linux_amd64.tar.gz -o /tmp/amass.tar.gz && \
    tar -xzf /tmp/amass.tar.gz -C /tmp && \
    mv /tmp/amass_linux_amd64/amass /usr/local/bin/ && \
    rm -rf /tmp/amass.tar.gz /tmp/amass_linux_amd64 && \
    chmod +x /usr/local/bin/amass

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
