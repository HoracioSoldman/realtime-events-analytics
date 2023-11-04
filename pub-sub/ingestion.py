import pandas as pd
import psycopg2
import time
from multiprocessing import Process
import logging

CLICKS_SOURCE_PATH = '../data/processed/one-day-clicks.csv'
TRANSACTIONS_SOURCE_PATH = '../data/processed/one-day-transactions.csv'


def preprocessing(df, numerical_fields, categorical_fields, field_types):
    """
        Handle NaN values and data types in the df
    """
    df[numerical_fields] = df[numerical_fields].fillna('0')
    df[categorical_fields] = df[categorical_fields].fillna('')

    try:
        df = df.astype(field_types)
    except Exception as e:
        logging.exception('An error occured ', e)
        raise e

    return df


def create_connection():
    return psycopg2.connect(
        user='user_a',
        password='pwd_a',
        host='127.0.0.1',
        port=5454,
        database='click_stream'
    )


def insertion(df, query, insertion_type):
    """
        Insert df records in the database with resepect to the offset time values
    """
    global pg_connection, connection_cursor
    inserted_records = 0
    try:
        pg_connection = create_connection()
        connection_cursor = pg_connection.cursor()

        for i, row in df.iterrows():
            row_values = row.values.tolist()

            # wait for x seconds based on the offset value
            time.sleep(row_values[-1])

            print(f'Inserting a {insertion_type} record after {row_values[-1]} seconds.')
            connection_cursor.execute(query, row_values[:-1])
            pg_connection.commit()

            inserted_records += connection_cursor.rowcount

    except Exception as e:
        print('Insertion error:', e)
        raise e
    finally:
        if pg_connection:
            connection_cursor.close()
            pg_connection.close()
            print('PG Connection closed.')

    return inserted_records


def run():
    numerical_clicks_df_fields = ['product_id', 'quantity', 'item_price', 'promo_amount']
    categorical_clicks_df_fields = ['session_id', 'event_name', 'event_id', 'traffic_source',
                                    'payment_status', 'search_keywords', 'promo_code']
    clicks_df_data_types = {
        'session_id': str, 'event_name': str, 'event_id': str,
        'traffic_source': str, 'product_id': float, 'quantity': float,
        'item_price': float, 'payment_status': str, 'search_keywords': str,
        'promo_code': str, 'promo_amount': float, 'event_offset': float
    }

    clicks_insertion_query = '''
        insert into clicks(session_id, event_name, event_id, traffic_source, product_id, quantity,
        item_price, payment_status, search_keywords, promo_code, promo_amount)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''

    numerical_transacs_df_fields = ['customer_id', 'promo_amount', 'shipment_fee', 'total_amount',
                                    'product_id', 'quantity', 'item_price']
    categorical_transacs_df_fields = ['booking_id', 'session_id', 'payment_method', 'payment_status',
                                      'promo_code', 'shipment_location_lat', 'shipment_location_long']
    transacs_df_data_types = {
        'customer_id': float, 'booking_id': str, 'session_id': str, 'payment_method': str,
        'payment_status': str, 'promo_amount': float, 'promo_code': str, 'shipment_fee': float,
        'shipment_location_lat': str, 'shipment_location_long': str, 'total_amount': float,
        'product_id': float, 'quantity': float, 'item_price': float, 'event_offset': float
    }

    transactions_insertion_query = '''
        insert into transactions(customer_id, booking_id, session_id, payment_method,
        payment_status, promo_amount, promo_code, shipment_fee,
        shipment_location_lat, shipment_location_lon, total_amount,
        product_id, quantity, item_price)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''

    df_click_events = pd.read_csv(CLICKS_SOURCE_PATH)

    df_clicks_to_ingest = preprocessing(df_click_events, numerical_clicks_df_fields,
                                        categorical_clicks_df_fields, clicks_df_data_types)

    df_transacs = pd.read_csv(TRANSACTIONS_SOURCE_PATH)
    df_transactions_to_ingest = preprocessing(df_transacs, numerical_transacs_df_fields,
                                              categorical_transacs_df_fields, transacs_df_data_types)

    # start data ingestion with multiprocessing
    clicks_process = Process(target=insertion, args=(df_clicks_to_ingest, clicks_insertion_query, 'click'))

    transacs_process = Process(target=insertion,
                               args=(df_transactions_to_ingest, transactions_insertion_query, 'transaction'))

    clicks_process.start()
    transacs_process.start()
    clicks_process.join()
    transacs_process.join()


if __name__ == '__main__':
    run()
