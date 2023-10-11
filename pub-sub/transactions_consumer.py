from kafka import KafkaConsumer

topic= 'streaming.public.transactions'

def run():

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers='127.0.0.1:29092', api_version=(3, 5, 1),
        auto_offset_reset='earliest',
        group_id='third-group-id'
    )
    
    print('Streaming Consumer Up..')

    # Pull messages every 2 seconds
    consumer.poll(timeout_ms=2000)

    # receive a test message
    for consumption in consumer:
        print('\n\n—---->Topic: ', consumption.topic)
        print('\n—------>Partition: ', consumption.partition)
        print('\n—------>Offset: ', consumption.offset)
        print('\nReceived message: ', str(consumption.value.decode('utf-8')))

if __name__ == '__main__':
    run()