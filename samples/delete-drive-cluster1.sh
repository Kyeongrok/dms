#!/bin/sh

host=${1:-dms}

curl -XPOST $host:9200/volvo-z1-raw-v1/_delete_by_query?pretty -d '
{
  "query": { 
    "match": {
      "cluster_id": "islp00001"
    }
  }
}'
