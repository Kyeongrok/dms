#!/usr/bin/python -tt

import json
from datetime import datetime 
from elasticsearch import Elasticsearch

# Connect to ES
es = Elasticsearch([{'host':'lglca219.lss.emc.com', 'port': 9200}])
v_index='volvo-mlb090-2017.08.28'
v_type='raw'
perma_dir='/ifs/data/z1/fieldtest/raw'
driver_id='adrian'

def insert_raw(doc_type, timestamp, car_id, date, drive_id, vpcap, tags):
    doc_id = vpcap
    return es.index(index=v_index, doc_type=doc_type, id=doc_id, body={
    "@timestamp": timestamp,
    "time_ingest": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
    "car_id": car_id,
    "ingest_station": "station-5",
    "drive_id": drive_id,
    "path": perma_dir + "/" + car_id + "/" + date + "/" + drive_id + "/" + vpcap,
    "tags": tags,
  })

def main():
  # drive 1
  vpcap = 'Z1_MLB090_CONT_20170630T153813-20170630T153842.vpcap'
  tags = ['sunny', 'road_work', 'u_turn']
  insert_raw('raw', '2017-06-30T15:38:13.000Z', 'MLB090', '20170630', 'Z1_MLB090_CONT_20170630T153813', vpcap, tags)
 
  vpcap = 'Z1_MLB090_CONT_20170630T153842-20170630T153812.vpcap'
  tags = ['sunny', 'accident', 'jaywalk']
  insert_raw('raw', '2017-06-30T15:38:42.000Z', 'MLB090', '20170630', 'Z1_MLB090_CONT_20170630T153813', vpcap, tags)

  vpcap = 'Z1_MLB090_CONT_20170630T153922-20170630T153942.vpcap'
  tags = ['sunny']
  insert_raw('raw', '2017-06-30T15:39:22.000Z', 'MLB090', '20170630', 'Z1_MLB090_CONT_20170630T153813', vpcap, tags)


  # drive 2
  vpcap = 'Z1_MLB090_CONT_20170701T153814-20170701T153843.vpcap'
  tags = ['sunny', 'road_work']
  insert_raw('raw', '2017-07-01T15:38:14.000Z', 'MLB090', '20170701', 'Z1_MLB090_CONT_20170701T153814', vpcap, tags)

  vpcap = 'Z1_MLB090_CONT_20170701T153843-20170630T153912.vpcap'
  tags = ['sunny', 'accident', 'jaywalk']
  insert_raw('raw', '2017-07-01T15:38:42.000Z', 'MLB090', '20170701', 'Z1_MLB090_CONT_20170701T153814', vpcap, tags)

  vpcap = 'Z1_MLB090_CONT_20170701T153912-20170701T153942.vpcap'
  tags = ['sunny']
  insert_raw('raw', '2017-07-01T15:39:12.000Z', 'MLB090', '20170701', 'Z1_MLB090_CONT_20170701T153814', vpcap, tags)

  # drive 3
  vpcap = 'Z1_PHL518_CONT_20170701T164413-20170701T164442.vpcap'
  tags = ['rainy', 'road_work']
  insert_raw('raw', '2017-07-01T16:44:13.000Z', 'PHL518',  '20170701', 'Z1_PHL518_CONT_20170701T164413', vpcap, tags)

  vpcap = 'Z1_PHL518_CONT_20170701T164442-20170630T164512.vpcap'
  tags = ['rainy', 'accident', 'jaywalk']
  insert_raw('raw', '2017-07-01T16:44:42.000Z', 'PHL518',  '20170701', 'Z1_PHL518_CONT_20170701T164413', vpcap, tags)

  vpcap = 'Z1_PHL518_CONT_20170701T164512-20170701T164543.vpcap'
  tags = ['rainy', 'police', 'road_block', 'u_turn']
  insert_raw('raw', '2017-07-01T16:45:12.000Z', 'PHL518',  '20170701', 'Z1_PHL518_CONT_20170701T164413', vpcap, tags)



if __name__ == '__main__':
  main()
