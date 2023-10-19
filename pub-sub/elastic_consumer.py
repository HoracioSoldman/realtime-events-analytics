from elasticsearch import Elasticsearch, exceptions

es_server = 'http://localhost:9200'

index = 'clicks'

def run():
    es = Elasticsearch(hosts=es_server)

    try:
        print(es.ping())
        es.indices.create(index=index)
        print(f'Index: {index} created.')
    except exceptions.RequestError as e:
        if e.error == 'resource_already_exists_exception':
            print(f'Index: {index} already exists.')
        else:
            raise e
    


if __name__ == '__main__':
    run()