FROM alpine:3.19

RUN apk add --no-cache nmap

WORKDIR /app

COPY run.py /app/run.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "/app/run.py"]
