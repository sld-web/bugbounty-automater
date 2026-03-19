FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://github.com/OWASP/Amass/releases/download/v3.25.0/amass_linux_amd64.zip -o /tmp/amass.zip && \
    unzip -q /tmp/amass.zip -d /usr/local/bin && \
    rm /tmp/amass.zip && \
    chmod +x /usr/local/bin/amass

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/app/run.py"]
