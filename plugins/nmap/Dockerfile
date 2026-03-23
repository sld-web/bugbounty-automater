FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /tmp && \
    chown -R appuser:appuser /app /tmp

USER appuser
ENV PATH="/usr/bin:/usr/local/bin:${PATH}"
ENV TMPDIR=/tmp

CMD ["python", "/app/run.py"]
