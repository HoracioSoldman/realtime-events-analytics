### Data source

For the current project, we will use an e-commerce dataset that is available on kaggle through [this link](https://www.kaggle.com/datasets/latifahhukma/fashion-campus/). The platform may require a sign-in before giving access to the download option. 

Once downloaded, the dataset contains 6 csv files. We will only process 4 of them: 
- __click_stream_new.csv__
- __customer.csv__
- __product.csv__
- __transaction_new.csv__

The ingestion of __click_stream_new.csv__ and __transaction_new.csv__ to the PostgreSQL database will be streamed in realtime. 


#### Data preprocessing
For simplicity, we will only stream one-day clicks and transactions events from the two aforementioned files. In [data-exploration/most_active_day.ipynb](/data-exploration/most_active_day.ipynb), we searched for the most active day based on click events. Then we outputed the filtered clicks and transactions records in the [data/processed/](/data/processed/) folder.

For the two remaining files: __customer.csv__ and __product.csv__, their contents  will be inserted in batch mode in the database.


### Postgresql
We need to make a little change in the Postgresql config file in order to capture the low-level change on the database.

- Go to the Postgres container using:
    ```bash
    docker exec -it pgdb_container bash
    ```

- Open the config file: `/var/lib/postgresql/data/postgresql.conf` using vi, nano or any editor of your choice.

    Set the `wal_level` from __replica__ to __logical__. 

- Restart the Postgresql container
    ```bash
    docker restart pgdb_container
    ```

- Review whether the change has been applied ot not
    ```sql
    select * from pg_settings where name = 'wal_level'
    ``` 

- Create the two tables in which we will insert clicks and transactions data.

For that, simply copy and run the content of [click_stream.sql](sql/click_stream.sql) on PgAdmin.
