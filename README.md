# Realtime click events analytics

<!-- Add stack icons here -->
The current project performs a Change Data Capture (CDC) on a database and allows realtime analytics of the captured information with a set of several open source tools.

## Overview
The following diagram shows a high-level architecture of the project.

![The architecture](/images/realtime_click_events_architecture.png "The Architecture")

<!-- ## Use case -->

## Data source

For the current project, we will use an e-commerce dataset that is available on kaggle through [this link](https://www.kaggle.com/datasets/latifahhukma/fashion-campus/). The platform may require a sign-in before giving access to the download option. 

Once downloaded, the dataset contains 6 csv files. We will only process 4 of them: 
- __click_stream_new.csv__
- __customer.csv__
- __product.csv__
- __transaction_new.csv__

The ingestion of __click_stream_new.csv__ and __transaction_new.csv__ to the PostgreSQL database will be streamed in realtime. 


### Data preprocessing
For simplicity, we will only stream one-day clicks and transactions events from the two aforementioned files. In [data-exploration/most_active_day.ipynb](/data-exploration/most_active_day.ipynb), we searched for the most active day based on click events. Then we outputed the filtered records in the [data/processed/](/data/processed/) folder.

For the two remaining files: __customer.csv__ and __product.csv__, their contents  will be inserted in batch mode in the database.

## The stack
### 1. Postgresql
[Loading the content.. ]

### 2. Debezium
Debezium will capture the low level changes on our tables in the __click_strem__ database and send this information to Kafka. 


### 3. Apache Kafka
[Loading the content.. ]

### 4. Elasticsearch
[Loading the content.. ]

### 5. Kibana
[Loading the content.. ]

### 6. Docker and Docker ompose
[Loading the content.. ]

## Running the project
### 1. Requirements
* Docker and Docker Compose:

    The project relies heavily on Docker and docker compose to run most of its components. It is then advised to install these first in case they are not available yet in the environment we intent to run the project.

* Python 3.9+

    It is also required to have Python 3.9 or higher to execute the existing python scripts.

* A minimum RAM of 8Gb to spin up all the necessary containers described in the [docker-compose.yml](docker-compose.yml) file.


#### 1. Clone the repository
```bash
git clone https://github.com/HoracioSoldman/realtime-events-analytics.git
```

#### 2. Create a virtual environment
Create an environment
```bash
pip install virtualenv
```
```bash
python<version> -m venv <virtual-environment-name>
```

Enable the environment
```bash
source <virtual-environment-name>/bin/activate
```

Install python libraries
```bash
pip install -r requirements.txt
```

#### 3. Run docker compose
```bash
docker compose up -d
```
At the very first time we run the above command, it takes sometime to download all the Docker images depending on one's internet speed.

It might be also useful to watch the status of the containers once they are up and running. To do so, open a new terminal window and run:
```bash
watch docker ps
```
This command shows a fairly basic containers monitoring with an auto-refresh for every 2 seconds.  


#### 4. PostgreSQL
We need to make a little change in the Postgresql config file in order to capture the low-level change on the database.

- Go to the Postgres container using:
    ```bash
    docker exec -it pgdb_container /bin/bash
    ```

- Open the config file: `/var/lib/postgresql/data/postgresql.conf` using vi, nano or any text editor.

    Set the `wal_level` from __replica__ to __logical__. 

- Restart the Postgresql container
    ```bash
    docker restart pgdb_container
    ```
- Go to the pgAdmin UI on: [http://localhost:8088](http://localhost:8088), enter the relevant credentials mentioned in the [docker-compose.yml](docker-compose.yml) file, under the __pgadmin__ service.

- Register a new server in PGAdmin with the following details:

    ![Register a server in PGAdmin](/images/register-server.png "New server register")


- Connect to the `click_stream` database.

- Once connected, review whether the change has been applied ot not
    ```sql
    select * from pg_settings where name = 'wal_level'
    ``` 

- Create the two tables in which we will insert clicks and transactions data.

    For that, simply copy and run the content of [click_stream.sql](sql/click_stream.sql) on PgAdmin.

#### 5. Debezium

- Create a Postgres debezium connector

    To do so, simply send a POST request to [http://localhost:8083/connectors](http://localhost:8083/connectors) via Postman or Insomnia.
    In the request, add the [debezium.json's](/debezium/debezium.json) content as its body. 
    
    That request should also create two kafka topics listed in the json file (i.e streaming.public.clicks, streaming.public.transactions). 

- To check whether the connector was created, send a GET request to [http://localhost:8083/connectors](http://localhost:8083/connectors), it should return `["click-stream-connector"]`.

- Verify that the two kafka topics were also created successfully.
    
    ```bash
    docker exec -it kafka_container /bin/bash 
    ```
    Once inside the container, run:
    ```bash
    /bin/kafka-topics --bootstrap-server=localhost:29092 --list
    ```
    The topics created from Debezium should be listed as a result of the above command.
    
    If that is not the case, log out of the container by pressing `Ctrl+D` then go to the debezium container's log to look for the potential errors there.
    
    ```bash
    docker container logs -f debezium_container
    ```

#### 6. Elastic Consumer
Once the building blocks of the infrastructure is up, we can start playing the data flow which involves capturing in realtime changes from the `click-stream` database and displaying them to the Kibana dashboards.

* Open a new Terminal tab or window and run:
    ```bash
    python pub_sub/elastic_consumer.py
    ```
    We should see a message like:
    
    `The consumer for streaming.public.clicks is up and listening.`
    
    `The consumer for streaming.public.transactions is up and listening.`
* Open another Terminal tab or window and run:
    ```bash
    cd pub_sub && python ingestion.py
    ```
    The script should immediately start inserting clicks events in the database. At the same time, we should also see updated messages on the `elastic_consumer.py` terminal.
 

#### 7. Create Dashboards on Kibana
In order to create a dashboard in Kibana. Head up to its address [http://localhost:5601](http://localhost:5601). 

Follow a quick guide provided in [Creating your first visualization with Kibana Lens](https://youtu.be/DzGwmr8nKPg?si=mv2tVYV6x3YwHXgJ).

The following screenshot is part of the final dashboard which gets updated every 5 seconds.

![The final dashboard](/images/final-dashboard.png "The final dashboard on Kibana") 


### Limitations and future improvements
#### 1. No orchestration

So far, the project hasn't utilized any orchestration tools. The essential scripts, namely [ingestion.py](/pub-sub/ingestion.py) and [elastic_consumer.py](/pub-sub/elastic_consumer.py) responsible for initiating and terminating the real-time data flow, currently require manual activation. In a production setting, it's preferable to schedule the execution of these scripts. Furthermore, orchestration tools provide an intuitive web user interface, simplifying the monitoring of these processes. Incorporating an orchestration tool such as [Dagster](https://dagster.io/), [Prefect](https://www.prefect.io/) or [Airflow](https://airflow.apache.org/) is a potential enhancement to be considered in the future.


#### 2. Backfilling process
There is a possibility that the pipeline may experience disruptions in the future. If such interruptions occur, the primary consequence will be a potential degradation in the quality of the data being observed and analysed on the Kibana dashboard.

To mitigate this risk, it is important to establish an alerting system as a preliminary measure. This alerting system will keep us informed of any potential downtime, enabling a proactive response. In addition to alerts, a well-defined backfilling process is essential. This process will act as a mechanism to replenish or rectify any corrupted data resulting from the pipeline downtime, ensuring data integrity and reliability on the visualisation platform.


Feel free to open an issue for any suggestions or comments 😊



 

