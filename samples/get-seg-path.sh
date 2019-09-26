#!/bin/bash
host=${1:-localhost}
size=${2:-100}
curl -XGET ''"${host}"':9200/volvo-*/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "size": '"${size}"',
  "query": {
    "bool": {
      "must": [
        { "match": { "_type":   "permanent" }},
        { "match": { "tags":   "right_turn" }}
      ],
      "filter": [
        {
          "range": {
            "@timestamp" : {
              "gte": "2017-06-30T00:00:00.000",
              "lt":  "2017-08-04T23:59:59.000"
            }
          }
        }
      ]
    }
  },
  "_source": [
    "seg_id",
    "path"
  ]
}'

