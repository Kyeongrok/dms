#!/bin/bash

# Install required tools and packages for ingestion
set -ux

yum -y install epel-release
yum -y install python34
yum -y install python34-setuptools
yum -y install python34-pip
yum -y install gcc

# install header files needed for psutil
yum -y install python34-devel.x86_64

# install mdadm
yum -y install mdadm

# install nfs packages
yum -y install nfs-utils

# install atd
yum -y install at
service atd start

# install fuser
yum -y install psmisc

# install rsync
yum -y install rsync

