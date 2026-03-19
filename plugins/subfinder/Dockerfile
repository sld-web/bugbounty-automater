FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -o /tmp/subfinder.zip && \
    unzip -q /tmp/subfinder.zip subfinder && \
    mv subfinder /usr/local/bin/ && \
    rm /tmp/subfinder.zip && \
    chmod +x /usr/local/bin/subfinder

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/app/run.py"]
