FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# /data is mounted as a volume on the VPS (SQLite + logs)
RUN mkdir -p /data/logs

CMD ["python", "main.py"]
