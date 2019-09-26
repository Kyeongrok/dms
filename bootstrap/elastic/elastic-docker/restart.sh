#!/bin/sh
# script to restart ES from scratch
docker-compose down
sudo rm -rf /data/volume0/elasticsearch/nodes
docker-compose up -d

while true
do
    curl -f localhost:9200
    if [ $? -eq 0 ]
    then
        break;
    else
        sleep 1
    fi
done

