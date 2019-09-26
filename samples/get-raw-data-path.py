#!/usr/bin/python -tt

import json
from elasticsearch import Elasticsearch

v_index = 'volvo-*'

# Connect to ES
es = Elasticsearch([{'host':'lglca219.lss.emc.com', 'port': 9200}])

# Search
def search(query):
  return es.search(index=v_index, body=query)

def main():

  # Search by type, return only 3 documents.
  raw_data_query = {
    "sort": [
      { "drive_id.keyword": { "order": "asc" }}
    ],
    "size": 10,
    "query" : {
      "bool": {
        "must": [
          { "match": { "_type":   "raw" }}
        ],
        "filter": [
          {
            "range": {
              "@timestamp" : {
                "gte": "2017-06-30T00:00:00.000",
                "lt":  "2017-08-04T23:59:59.000",
                "time_zone": "+05:00"
              }
            }
          }
        ]
      }
    },
    "_source": [
      "@timestamp",
      "car_id",
      "drive_id",
      "path"
    ]
  } 
  
  res = search(raw_data_query)
  drives = {}
  for x in res['hits']['hits']:
    drive_id = x['_source']['drive_id']
    path = x['_source']['path']
    if drive_id in drives:
      drives[drive_id].append(path)
    else:
      drives[drive_id] = [path]

  for key in drives:
    print key
    for x in sorted(drives[key]):
      print "  " + x

if __name__ == '__main__':
  main()
