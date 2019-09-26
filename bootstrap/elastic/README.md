# Elasticsearch Bootstrap
Bootstrap Elasticsearch (ES) for data management operations. The steps include, load templates and data mappings, create indices, load kibana dashboards, create cluster configuration, set initial state of ingest stations, etc.

## Initialize Elasticsearch
This step will create templates, indices, data mappings, and load default dashboards.
```
$ cd /root/dms/bootstrap/elastic/bin
$ export ES_ENDPOINT=http://<es_host>:9200
$ ./load.sh
```

## Kibana Configuration
* Copy /root/dms/bootstrap/elastic/kibana/kibana.yml to all Kibana nodes and place it at the Kibana conf directory, normally /etc/kibana
* Restart Kibana service

## Cluster Configuration
Place the following in a file and source it.
```
export ES_ENDPOINT=http://<es_host>:9200
export ES_USERNAME=<es_user>
export ES_PASSWORD=<es_password>
export NFS_HOST=<cluster_nfs_host>
export SMB_HOST=<cluster_smb_host>
```
Find the cluster id, e.g., for cluster 1, islp00001, run the following command
```
$ /root/dms/utils/cluster.py create --cluster-id=islp0001
```
Note that you can also specify all the parameters on the command line. See cluster.py --help and cluster.py create --help for more details.

Repeat the above two steps for all the cluster.

## Ingest Host Configuration
TBD
