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
    "size": 10,
    "query" : {
      "bool": {
        "must": [
          { "match": { "_type":   "permanent" }},
          { "match": { "tags":   "right_turn" }}
        ]
      }
    },
    "_source": [
      "@timestamp",
      "car_id",
      "seg_id",
      "path"
    ]
  } 
  
  res = search(raw_data_query)
  segments = {}
  for x in res['hits']['hits']:
    seg_id = x['_source']['seg_id']
    car_id = x['_source']['car_id']
    path = x['_source']['path']
    key = seg_id
    if key in segments:
      segments[key].append(path)
    else:
      segments[key] = [path]

  for key in segments:
    print key
    for x in sorted(segments[key]):
      print "  " + x

if __name__ == '__main__':
  main()
