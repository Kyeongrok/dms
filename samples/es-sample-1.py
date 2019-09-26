#!/usr/bin/python -tt

import json
from datetime import datetime 
from elasticsearch import Elasticsearch

# Connect to ES
es = Elasticsearch([{'host':'lglca219.lss.emc.com', 'port': 9200}])
v_index='volvo-MLB090-2017.08.28'
v_type='raw'
perma_dir='/ifs/data/z1/fieldtest/permanent'
driver_id='adrian'

# Create index and doc
def insert(id):
  return es.index(index=v_index, doc_type=v_type, id=id, body={
    "@timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
    "car_id": "car-" + id,
    "ingest_station": "station-5",
    "drive_id": "Z1_MLB090_CONT_20170630T153813",
    "segment_id": "segment-" + id + "-20170828-20170829",
    "file_location": "/ifs/data/z1/fieldtest/permanent/" + id + "raw/" + "Z1_MLB090_CONT_20170630T153813",
    "tags": ["sunny", "road_work"],
  })

def insert_raw(doc_type, timestamp, car_id, drive_id, vpcap, tags):
    return es.index(index=v_index, doc_type=v_type, id=id, body={
    "timestamp": "2017-08-21T23:59:59.000Z"
    "@time_ingest": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
    "car_id": car_id,
    "ingest_station": "station-5",
    "drive_id": drive_id,
    "path": perma_dir "/" + car_id + "/raw/" + vpcap,
    "tags": tags,
  })


# Get doc by id
def get(id):
  return es.get(index=v_index, doc_type=v_type, id=id)  

# Delete a doc
def delete(id):
  return es.delete(index=v_index, doc_type=v_type, id=id)

# Update a doc
def update(id, body):
  return es.update(index=v_index, doc_type=v_type, id=id, body=body)

# Search
def search(query):
  return es.search(index=v_index, body=query)

def main():
  id_1 = '123456'
  id_2 = '223456'
  res = insert(id_1)
  print(get(id_1))
  insert(id_2)
  
  # add a new field to the doc. Note the 'doc' is the key word.
  body2 = {"doc": {"new_field": "New Message"}}
  update(id_1, body2)
  print get(id_1)

  # append to tags.
  body3 = {
    "script" : {
      "inline": "ctx._source.tags.add(params.tag)",
      "lang": "painless",
      "params" : {
        "tag" : "gas_low"
      }
    }
  }

  update(id_1, body3)
  print get(id_1)

  print get(id_2)
  #print delete(id_2)

  # Search by tags
  query1 = {"query" : {"match": { "tags": "gas_low" } } }
  res = search(query1)
  print(res['hits']['hits'][0]['_source'])

if __name__ == '__main__':
  main()
