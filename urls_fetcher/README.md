# urls fetcher

## problem

a user sends a single request that have
1. list of millions of urls
1. search term

the system needs to fetch said urls and return only those that their response bodies contain the seach term

## assumptions

* there are millions of urls
* there are small number of concurrent users
* the ratio between urls and urls that will match the search term is `log2`

## sequence diagram

```mermaid
sequenceDiagram
    autonumber
    participant client
    participant url_fetcher
    participant urls_topic
    participant workers
    participant responses_topic
    note over workers: group_id: worker
    note over urls_topic: partisions: 100
    note over responses_topic: created per client request
    client->>url_fetcher: POST /search
    Note over client,url_fetcher: {urls: [...],<br/>term: "..."}

    loop 
        url_fetcher->>url_fetcher: create request-id
    end

    url_fetcher->>urls_topic: publish message per url
    Note over url_fetcher,urls_topic: {action: "FETCH",<br/>url: "...",<br/>request_id: "..."}
    url_fetcher->>urls_topic: publish message per partition
    Note over url_fetcher,urls_topic: {action: "FIN",<br/>request_id: "..."}

    par
        urls_topic->>workers: consume
        note over urls_topic,workers: if action == "FETCH"<br>fetch url<br/>check if 'term' in response<br/>if so, publish to response topic<br>{action: "FOUND", url: ..."}
        note over urls_topic,workers: if action == "FIN"<br>publiush  to response topic<br>{action: "FIN", partition, $partition}

        url_fetcher->>client: 200 OK
        Note over client,url_fetcher: {"results": "ws://.../request-id"}

        workers->>responses_topic: publish

        client->>url_fetcher: ws connect
        note over client,url_fetcher: ws://.../request-id<br/>- waiting for results...
        url_fetcher->>responses_topic: subscribe
        note over url_fetcher,responses_topic: topic is the request-id (topic per client request)
        responses_topic->>url_fetcher: responses from workers
        note over responses_topic,url_fetcher: {action: "found", url: "abc.com"}<br/>{action: "FOUND", url: "xyz.org"}<br/>{action: "FIN", partition: 5}
        url_fetcher->client: responses stream
        note over url_fetcher,client: abc.com<br/>xyz.org<br/>
        url_fetcher->client: close
        note over url_fetcher,client: when getting FIN from all partitions
    end
```

# running containers

starting zookeeper
```bash
docker run --rm  --network app-tier --name zookeeper-server -e ALLOW_ANONYMOUS_LOGIN=yes bitnami/zookeeper:latest
```

starting kafka
```bash
docker run --name kafka-server --network app-tier -e ALLOW_PLAINTEXT_LISTENER=yes -e KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper-server:2181 bitnami/kafka:latest
```

creating a topic with many partitions
```bash
# docker exec into the kafka container and run this:

kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 100 --topic urls-topic
```

starting app
```bash
docker run -p 8000:8000 --network app-tier  -it sd-app uvicorn server:app --app-dir src --host 0.0.0.0
```
