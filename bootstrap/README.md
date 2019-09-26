# Bootstrap for Data Management System

## Isilon NFS Exports and SMB Shares
Create directories and NFS exports. For example on cluster 1
```
/ifs/z1/islp00001/output
/ifs/z1/islp00001/perm
/ifs/z1/islp00001/resim
/ifs/z1/islp00001/raw
/ifs/z1/islp00001/useroutput     <--- only needed on cluster 1     
```
And then configure NFS exports and SMB shares for those directories. 
* example NFS mount point: <nfs_host>:/ifs/z1/islp00001/raw
* example SMB share: \\\\10.1.83.93/ifs/z1/islp00001/raw

Perform the steps for all the clusters.

## Ingest Station
### python and packages
The Ingest station runs Redhat/CentOS. The following packages must be installed and their respective services must be started (when applicable). Sample scripts can be at the bootstrap/centos folder.
* git, nfs-utils, gmartcontrol
* python3 and pip3
* python packages: click, pyyaml, tornado, click_configfile, retrying, flask

### User
Create "resim" group and "ingest" user
* name: ingest
* group: resim
* passwordless sudo

### NFS Mount
Create the following NFS mount path for the raw data on all ingest stations.
```
/dms/z1/islp0001/raw       owner: ingest, group: resim, mode: 640
/dms/z1/islp0002/raw       owner: ingest, group: resim, mode: 640
/dms/z1/islp0003/raw       owner: ingest, group: resim, mode: 640
/dms/z1/islp0004/raw       owner: ingest, group: resim, mode: 640
```

and mount it to their respective NFS mount points
```
/dms/z1/islp0001/raw    --> cluster1dns:/ifs/z1/islp00001/raw
/dms/z1/islp0002/raw    --> cluster1dns:/ifs/z1/islp00002/raw
/dms/z1/islp0003/raw    --> cluster1dns:/ifs/z1/islp00003/raw
/dms/z1/islp0004/raw    --> cluster1dns:/ifs/z1/islp00004/raw
```
### Log directory
Create DMS log directory:  /opt/dms/logs

### DMS Client
Download and install DMS client
```
$ cd /root
$ git clone https://github.com/EMCECS/dms
$ cd dms/dmsclient
$ python3 setup.py install
```

## Elasticsearch and Kibana
Follow the steps in bootstrap/elastic folder to set up Elasticsearch and Kibana for setting up Elasticsearch/Kibana for Data Management System.
