# Realtime click events analytics

<!-- Add stack icons here -->
The current project captures live events from a database and displays the retrieved information on a visualisation tool for real time analytics. In essence, it utilises Change Data Capture (CDC) to listen for changes on an OLTP database then streams updates to intermediate components before making the data available on the final dashboard.


## Table of contents
- [Overview](#overview)
- [Data source](#data-source)
- [The stack](#the-stack)
  * [1. PostgreSQL](#1-postgresql)
  * [2. Debezium](#2-debezium)
  * [3. Apache Kafka](#3-apache-kafka)
  * [4. Elasticsearch](#4-elasticsearch)
  * [5. Kibana](#5-kibana)
  * [6. Docker and Docker compose](#6-docker-and-docker-compose)
  
- [Running the project](#running-the-project)
  * [1. Requierements](#1-requirements)
  * [2. Clone the repository](#2-clone-the-repository)
  * [3. Build a docker image for our python scripts](#3-build-a-docker-image-for-our-python-scripts)
  * [4. Run docker compose](#4-run-docker-compose)
  * [5. PostgreSQL](#5-postgresql)
  * [6. Debezium](#6-debezium)
  * [7. Elastic Consumer](#7-elastic-consumer)
  * [8. Create Dashboards on Kibana](#8-create-dashboards-on-kibana)
- [Limitations and future improvements](#limitations-and-future-improvements)

  * [1. Backfilling process](#1-backfilling-process)


## Overview
The following diagram shows a high-level architecture of the project.

![The architecture](/images/realtime_click_events_architecture.png "The Architecture")

<!-- ## Use case -->

## Data source

For the current project, we will use an e-commerce dataset that is available on Kaggle website through [this link](https://www.kaggle.com/datasets/latifahhukma/fashion-campus/). The platform may require a sign-in before giving access to the dataset download option. 

Once downloaded, the said dataset contains 6 csv files. At this stage, however, we will only process 2 of them:
- __click_stream_new.csv__
- __transaction_new.csv__

In a production environment, a website may record click stream and transaction events, then the generated data to an OLTP database. For this project though, we replay that real time data ingestion based on the `event-time` columns in these two files.


### Data preprocessing
Instead of taking all the records in these files, here we will only stream one-day clicks and transactions items, for simplicity. In the [data-exploration/most_active_day.ipynb](/data-exploration/most_active_day.ipynb) notebook, we searched for the most active day based on click events. Then we output the filtered records in the [data/processed/](/data/processed/) folder.
For the rest of the process, we will only utilise these preprocessed files. 


## The stack
For the project stack, we have selected several open and closed source tools to form the building blocks of our data pipeline.

### 1. PostgreSQL
[PostgreSQL](https://www.postgresql.org/) is a highly advanced open source relational database. We opted for this RDBMS as it supports enterprise-level applications with fast write/read events. Here we employ PostgreSQL to store click and transaction records from the 2 prepared csv files.

### 2. Debezium
[Debezium](https://debezium.io/) is an open source distributed platform for change data capture. In this project, Debezium captures low level changes on our tables in the `click_stream` database and sends the captured information to Kafka. 

### 3. Apache Kafka
[Apache Kafka](https://kafka.apache.org/) is another open-source platform which enables distributed event streaming, high-performance data pipelines, stream analytics as well as efficient data integrations. Here we utilise Kafka to guarantee the delivery of the streamed data to the right consumer groups before ingesting them to Elasticsearch.

### 4. Elasticsearch
[Elasticsearch](https://www.elastic.co/) is the **E** in the popular ELK stack which is a shorthand for Elasticsearch Logstash and Kibana. Elasticsearch is a powerful search engine software which provides a distributed and multitenant-capable full-text search. Although Elasticsearch does not belong to the open-source community, we chose to add it to our stack since it is an essential component allowing us to visualise our data in Kibana.    

### 5. Kibana
[Kibana](https://www.elastic.co/kibana) is a rich visualisation tool which enables data analytics at speed and scale for observability, security and search. Kibana is the **K** in the popular ELK stack. It enables us to visualise the streamed data in realtime.  

### 6. Docker and Docker compose
[Docker](https://www.docker.com/) is a set of platform as a service which containerises softwares, allowing them to act the same way across multiple platforms.

[Docker Compose](https://docs.docker.com/compose/) is a tool that helps defining and running multi-container applications. With Compose, we can create, start, visualise or stop our containers in a single command.



## Running the project
### 1. Requirements
* Docker and Docker Compose:

    The project relies heavily on Docker and docker compose to run most of its components. It is then advised to install these first in case they are not available yet in the environment we intend to run the project.


* A minimum RAM of 8Gb to spin up all the necessary containers described in the [docker-compose.yml](docker-compose.yml) file.


### 2. Clone the repository
```bash
git clone https://github.com/HoracioSoldman/realtime-events-analytics.git
```

### 3. Build a docker image for our python scripts 
```bash
docker build -t pub_sub .
```
As described in the [Dockerfile](Dockerfile), the image will contain the python scripts located in the [pub-sub](pub-sub/) folder. They will ingest data from a csv file to the postgres database and from Kafka to Elasticsearch.

Once the CDC part is set up, we will run the image in a container to start the data flow.


### 4. Run docker compose
```bash
docker compose up -d
```
At the very first time we run the above command, it may take some time to download all the Docker images described in the [docker-compose.yml](docker-compose.yml).

It might be also useful to watch the status of the containers once they are up and running. To do so, open a new terminal window or tab, then run:
```bash
watch docker ps
```
This command shows a fairly basic container monitoring with an auto-refresh for every 2 seconds.  


### 5. PostgreSQL
Once the containers are up and running, we need to make a little change in the Postgresql config file in order to capture the low-level change on the database.

- Go to the Postgres container using:
    ```bash
    docker exec -it pgdb_container /bin/bash
    ```

- Open the config file: `/var/lib/postgresql/data/postgresql.conf` using vi, nano or any text editor.

    Set the **wal_level** from `replica` to `logical`. 

- Logout from the container and Restart the Postgresql container
    ```bash
    docker restart pgdb_container
    ```
- Go to the pgAdmin UI on: [http://localhost:8088](http://localhost:8088), enter the relevant credentials mentioned in the [docker-compose.yml](docker-compose.yml) file, under the `pgadmin` service.

- Register a new server in PGAdmin with the following details:

    ![Register a server in PGAdmin](/images/register-server.png "New server register")


- Connect to the `click_stream` database.

- Once connected, review whether the change has been applied or not
    ```sql
    select * from pg_settings where name = 'wal_level'
    ``` 

- Create two tables in which we will insert clicks and transactions data.

    For that, simply copy and run the content of [click_stream.sql](sql/click_stream.sql) on PgAdmin.

### 6. Debezium

- Update the PostgreSQL credentials in the [debezium.json's](/debezium/debezium.json) based in what we previously added in the `.env` file.

- Create a Postgres Debezium connector

    To do so, we need to send a POST request to [http://localhost:8083/connectors](http://localhost:8083/connectors) via Postman or Insomnia.
    In the request, add the [debezium.json's](/debezium/debezium.json) content as its body. We should receive a 200 status.
    
    That request should also create two kafka topics listed in the json file (i.e streaming.public.clicks, streaming.public.transactions). 

- To check whether the connector was created, send a GET request to [http://localhost:8083/connectors](http://localhost:8083/connectors). If everything went well, the request should return the list of available connectors like `["click-stream-connector"]`.

- In order to verify whether the two kafka topics were also created or not, run
    
    ```bash
    docker exec -it kafka_container /bin/bash 
    ```
    Once inside the container, execute:
    ```bash
    /bin/kafka-topics --bootstrap-server=localhost:29092 --list
    ```
    The topics created from Debezium should be listed as a result of the above command.
    
    If that is not the case, log out of the container by pressing `Ctrl+D` then go to the Debezium container's log to look for the potential errors there.
    
    ```bash
    docker container logs -f debezium_container
    ```

### 7. Kafka Consumer
Once the building blocks of the infrastructure is up, we can start playing the data flow which involves capturing in real time changes from the `click-stream` database and displaying them to the Kibana dashboards.

Run the docker image we built at [step 3](#3-build-a-docker-image-for-our-python-scripts):
  ```bash
  docker run -it --network host pub_sub
  ```
  We should now see the following messages on the terminal:
  
  `The consumer for streaming.public.clicks is up and listening.`
  
  `The consumer for streaming.public.transactions is up and listening.`

What happened here is that we started listening to two Kafka topics (i.e clicks and transactions), then we also started ingesting data from csv files to the postgres database.

### 8. Create Dashboards on Kibana
In order to create a dashboard in Kibana. Head over to its local  address [http://localhost:5601](http://localhost:5601).

Until now, the process of discovering the data and creating dashboards on Kibana are still manual. Thus, we decided not to include how we can complete these tasks in this guide. 

Nevertheless, here is a quick and useful guide on how to get started with Kibana in the following Youtube video: [Creating your first visualisation with Kibana Lens](https://youtu.be/DzGwmr8nKPg?si=mv2tVYV6x3YwHXgJ). Hope it helps.

The next screenshot is part of our final dashboard on Kibana. It gets updated every 5 seconds.

![The final dashboard](/images/final-dashboard.png "The final dashboard on Kibana") 


## Limitations and future improvements

### 1. Backfilling process
There is a possibility that the pipeline may experience disruptions in the future. If such interruptions occur, the primary consequence will be a potential degradation in the quality of the data being observed and analysed on the Kibana dashboard.

To mitigate this risk, it is important to establish an alerting system as a preliminary measure. This alerting system will keep us informed of any potential downtime, enabling a proactive response. In addition to alerts, a well-defined backfilling process is also essential. This process will act as a mechanism to replenish or rectify any corrupted data resulting from the pipeline downtime, ensuring data integrity and reliability on the visualisation platform in the long run.


Feel free to open an issue for any suggestions or comments 😊
