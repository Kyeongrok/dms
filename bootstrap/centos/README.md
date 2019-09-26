# CentOS Bootstrap
A set of scripts to prepare CentOS for ingestion. They are provided for convenience.

The instruction assumes user logged in as root. Adjust accordingly if not.

## Clone dms repository
```
$ yum -y install git
$ cd /root
$ git clone https://github.com/EMCECS/dms
```

## Install tools and packages
Installed required tools and packages to run ingest script
```
$ cd /root/dms/bootstrap/centos
$ ./system-setup.sh
```

## Create user and group
Create **ingest** user in **resim** group. Enable passwordless sudo for the user. 
```
$ ./user-setup.sh
```

## Mount Isilon NFS exports
Mount NFS exports for **raw** data on the ingest station. The following env variable must be set
```
CL01_NFS_HOST 
CL02_NFS_HOST
CL03_NFS_HOST
CL04_NFS_HOST
```
```
$ ./mount-setup.sh
```

