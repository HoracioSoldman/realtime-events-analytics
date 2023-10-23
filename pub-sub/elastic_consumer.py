import json
import time
from elasticsearch import Elasticsearch, exceptions
from kafka import KafkaConsumer
from multiprocessing import Process

ES_SERVER = 'http://localhost:9200'
CLICKS_INDEX = 'clicks_index'
TRANSACTIONS_INDEX = 'transactions_index'

CLICKS_KAFKA_TOPIC= 'streaming.public.clicks'
TRANSACTIONS_KAFKA_TOPIC= 'streaming.public.transactions'


def enable_index(es, the_index):
    if not es.indices.exists(index=the_index):
        es.indices.create(index = the_index)


def kafka_consumer(kafka_topic, es, es_index):
    '''
        - Consume data from kafka topics
        - Insert new change in elasticsearch db
    '''
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers='127.0.0.1:29092', api_version=(3, 5, 1),
        auto_offset_reset='earliest',
        group_id="elastic-group"
    )
    print(f'The consumer for {kafka_topic} is up and listening.')

    while True:
        try:
            # Pull messages every 2 seconds
            consumer.poll(timeout_ms=2000)

            # receive messages
            for consumption in consumer:
                print('\n\n-----TOPIC: ', consumption.topic)
                print('\n—------PARTITION: ', consumption.partition)
                print('\n—------OFFSET: ', consumption.offset)
                dict_message =  dict(json.loads(str(consumption.value.decode('utf-8'))))
                new_change = dict_message['payload']['after']

                insert_result = es.index(index=es_index, document=new_change)
                if insert_result['result'] and insert_result['result'] == 'created':
                    print('\nNew Change Inserted: ', new_change)
        except Exception as e:
            print('ERROR : ', e)
            time.sleep(2)

def run():
    # connect to Elasticsearch
    es = Elasticsearch([ES_SERVER])
    if not es.ping():
        raise Exception('Unable to connect to Elasticsearch.')

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