FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app
COPY . .

RUN chmod +x run.py

CMD ["python", "/app/run.py"]
