import json
import logging
import time
import os
from elasticsearch import Elasticsearch, exceptions
from kafka import KafkaConsumer
from multiprocessing import Process
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Environment-configurable settings with sane defaults
ES_SERVER = os.getenv('ES_SERVER', 'http://127.0.0.1:9200')
CLICKS_INDEX = os.getenv('ES_CLICKS_INDEX', 'clicks_index')
TRANSACTIONS_INDEX = os.getenv('ES_TRANSACTIONS_INDEX', 'transactions_index')

CLICKS_KAFKA_TOPIC = os.getenv('CLICKS_KAFKA_TOPIC', 'streaming.public.clicks')
TRANSACTIONS_KAFKA_TOPIC = os.getenv('TRANSACTIONS_KAFKA_TOPIC', 'streaming.public.transactions')
KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP', '127.0.0.1:29092')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'elastic-group')
KAFKA_API_VERSION = tuple(
    int(x) for x in os.getenv('KAFKA_API_VERSION', '3,5,1').split(',')
)
KAFKA_POLL_TIMEOUT_MS = int(os.getenv('KAFKA_POLL_TIMEOUT_MS', '2000'))


def enable_index(es, the_index):
    if not es.indices.exists(index=the_index):
        es.indices.create(index=the_index)


def kafka_consumer(kafka_topic, es, es_index):
    """
        - Consume data from kafka topics
        - Insert new changes in elasticsearch db
    """
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=KAFKA_BOOTSTRAP, api_version=KAFKA_API_VERSION,
        auto_offset_reset='earliest',
        group_id=KAFKA_GROUP_ID
    )
    print(f'The consumer for {kafka_topic} is up and listening.')

    while True:
        try:
            # pull messages every 2 seconds
            consumer.poll(timeout_ms=KAFKA_POLL_TIMEOUT_MS)

            # receive messages
            for consumption in consumer:
                print('\n\n-----TOPIC: ', consumption.topic)
                print('\n—------PARTITION: ', consumption.partition)
                print('\n—------OFFSET: ', consumption.offset)
                dict_message = dict(json.loads(str(consumption.value.decode('utf-8'))))
                new_change = dict_message['payload']['after']
                if 'created_at' in new_change:
                    str_epoch = str(new_change['created_at'])[:10]
                    int_epoch = int(str_epoch)
                    creation_time = datetime.fromtimestamp(int_epoch).strftime('%Y-%m-%dT%H:%M:%S')
                    new_change['created_at'] = creation_time

                insert_result = es.index(index=es_index, document=new_change)
                if insert_result['result'] and insert_result['result'] == 'created':
                    print('\nNew Change Inserted: ', new_change)
        except Exception as e:
            error_message = f'ERROR : {e}'
            logging.exception(error_message)
            print(error_message)
            time.sleep(2)


def run():
    # connect to Elasticsearch
    es = Elasticsearch([ES_SERVER])
    if not es.ping():
        error_message = 'Unable to connect to Elasticsearch.'
        logging.error(error_message)
        raise ConnectionError(error_message)

    enable_index(es, CLICKS_INDEX)
    enable_index(es, TRANSACTIONS_INDEX)

    # create processes to consume data from kafka topics 
    clicks_process = Process(target=kafka_consumer, args=(CLICKS_KAFKA_TOPIC, es, CLICKS_INDEX))
    transacs_process = Process(target=kafka_consumer, args=(TRANSACTIONS_KAFKA_TOPIC, es, TRANSACTIONS_INDEX))

    clicks_process.start()
    transacs_process.start()
    clicks_process.join()
    transacs_process.join()


if __name__ == '__main__':
    run()
