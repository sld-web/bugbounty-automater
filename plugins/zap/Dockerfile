FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ZAP_HOME=/zap

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN wget -q https://github.com/zaproxy/zaproxy/releases/download/v2.12.0/ZAP_2.12.0_Linux.tar.gz && \
    tar -xzf ZAP_2.12.0_Linux.tar.gz -C /opt && \
    rm ZAP_2.12.0_Linux.tar.gz && \
    ln -s /opt/ZAP_2.12.0 /zap && \
    mkdir -p /zap/scripts /zap/logs

WORKDIR /app
COPY . .

RUN chmod +x run.py

CMD ["python", "/app/run.py"]
