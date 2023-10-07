from kafka import KafkaProducer
topic= 'test_topic'

def run():
    
    producer = KafkaProducer(bootstrap_servers = '127.0.0.1:29092', api_version=(3, 5, 1))
    print('Producer Up...')
    # publish a test message
    producer.send(topic, b'This is another test message :)')
    print('First message sent.')

if __name__ == '__main__':
    run()