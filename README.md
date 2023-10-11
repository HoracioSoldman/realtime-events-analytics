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
