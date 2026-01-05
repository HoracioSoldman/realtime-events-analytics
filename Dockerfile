FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY data ./data
COPY pub-sub ./pub-sub

# Default command runs both consumers in background and keeps container alive
CMD python pub-sub/kafka_consumer.py & python pub-sub/ingestion.py
