#!/bin/sh

host=${1:-dms}

curl -XPOST $host:9200/volvo-z1-resim-*/_delete_by_query -d '
{
  "query": { 
    "match": {
      "cluster_id": "islp00001"
    }
  }
}'
