FROM python:3.10

USER root

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY data pub_sub .

CMD python pub-sub/elastic_consumer.py & python pub-sub/ingestion.py
