import json
import logging
import time
from elasticsearch import Elasticsearch, exceptions
from kafka import KafkaConsumer
from multiprocessing import Process
from datetime import datetime

ES_SERVER = 'http://localhost:9200'
CLICKS_INDEX = 'clicks_index'
TRANSACTIONS_INDEX = 'transactions_index'

CLICKS_KAFKA_TOPIC = 'streaming.public.clicks'
TRANSACTIONS_KAFKA_TOPIC = 'streaming.public.transactions'


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
        bootstrap_servers='127.0.0.1:29092', api_version=(3, 5, 1),
        auto_offset_reset='earliest',
        group_id="elastic-group"
    )
    print(f'The consumer for {kafka_topic} is up and listening.')

    while True:
        try:
            # pull messages every 2 seconds
            consumer.poll(timeout_ms=2000)

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
