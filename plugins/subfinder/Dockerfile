FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -o /tmp/subfinder.zip && \
    unzip -q /tmp/subfinder.zip subfinder && \
    mv subfinder /usr/local/bin/ && \
    rm /tmp/subfinder.zip && \
    chmod +x /usr/local/bin/subfinder

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /tmp /home/appuser/.config/subfinder && \
    chmod 777 /home/appuser/.config/subfinder && \
    chown -R appuser:appuser /app /tmp /home/appuser

RUN echo '{}' > /home/appuser/.config/subfinder/config.yaml && \
    touch /home/appuser/.config/subfinder/provider-config.yaml && \
    chown -R appuser:appuser /home/appuser/.config/subfinder

USER appuser
ENV PATH="/usr/local/bin:${PATH}"
ENV HOME="/home/appuser"
ENV XDG_CONFIG_HOME="/home/appuser/.config"
ENV TMPDIR=/tmp

CMD ["python", "/app/run.py"]
