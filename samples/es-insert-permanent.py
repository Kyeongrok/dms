#!/usr/bin/python -tt

import json
from datetime import datetime 
from elasticsearch import Elasticsearch

# Connect to ES
es = Elasticsearch([{'host':'lglca219.lss.emc.com', 'port': 9200}])
v_index='volvo-mlb090-2017.08.28'
v_type='permanent'
perma_dir='/ifs/data/z1/fieldtest/permanent'

def insert_index(doc_type, timestamp, car_id, date, seg_id, sensors, sensor_file, tags):
  doc_id = car_id + "_" + date + "_" + seg_id + "_" + sensor_file 
  return es.index(index=v_index, doc_type=doc_type, id=doc_id, body={
    "@timestamp": timestamp,
    "time_ingest": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
    "car_id": car_id,
    "seg_id": car_id + "_" + seg_id,
    "sensors": sensors,
    "path": perma_dir + "/" + car_id + "/" + date + "/" + seg_id + "/" + sensor_file,
    "tags": tags,
    "type": doc_type,
  })

def insert_seg(seg):
  for x in seg:
    insert_index(v_type, x[0], x[1], x[2], x[3], x[4], x[5], x[6])

def main():
  seg_id = '20170630T153800'
  seg = [
    ['2017-06-30T15:38:13.000Z', 'MLB090', '20170630', seg_id, ['sensor1'], seg_id + '.sensor1', ['left_turn', 'red_light']],
    ['2017-06-30T15:38:13.000Z', 'MLB090', '20170630', seg_id, ['sensor2'], seg_id + '.sensor2', ['left_turn', 'red_light']],
    ['2017-06-30T15:38:13.000Z', 'MLB090', '20170630', seg_id, ['sensor3'], seg_id + '.sensor3', ['left_turn', 'red_light']]
  ]

  insert_seg(seg)

  seg_id = '20170630T153900'
  seg = [
    ['2017-06-30T15:39:13.000Z', 'MLB090', '20170630', seg_id, ['sensor4'], seg_id + '.sensor4', ['right_turn', 'red_light']],
    ['2017-06-30T15:39:13.000Z', 'MLB090', '20170630', seg_id, ['sensor5'], seg_id + '.sensor5', ['right_turn', 'red_light']],
    ['2017-06-30T15:39:13.000Z', 'MLB090', '20170630', seg_id, ['sensor6'], seg_id + '.sensor6', ['right_turn', 'red_light']]
  ]

  insert_seg(seg)

  seg_id = '20170630T164900'
  seg = [
    ['2017-06-30T16:49:15.000Z', 'PHL518', '20170630', seg_id, ['sensor12'], seg_id + '.sensor12', ['right_turn', 'red_light']],
    ['2017-06-30T16:49:15.000Z', 'PHL518', '20170630', seg_id, ['sensor8'], seg_id + '.sensor8', ['right_turn', 'red_light']],
    ['2017-06-30T16:49:15.000Z', 'PHL518', '20170630', seg_id, ['sensor7'], seg_id + '.sensor7', ['right_turn', 'red_light']]
  ]

  insert_seg(seg)

if __name__ == '__main__':
  main()
