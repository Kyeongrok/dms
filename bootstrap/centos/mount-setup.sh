#!/bin/bash

# Install required packages on CentOS to run ingest service

set -uex

# create user and groups
USER=ingest
GROUP=resim

CL01_NFS_HOST=${CL01_NFS_HOST:-10.35.106.54} # original
CL02_NFS_HOST=${CL02_NFS_HOST:-10.35.106.35} # original
#CL01_NFS_HOST=${CL01_NFS_HOST:-10.35.102.187}
#CL02_NFS_HOST=${CL02_NFS_HOST:-10.35.102.188}
#CL03_NFS_HOST=${CL03_NFS_HOST:-10.246.157.204}
#CL04_NFS_HOST=${CL04_NFS_HOST:-nfs.islp00004.ent.autodrivecluster.com}

MOUNT_PREFIX=${MOUNT_PREFIX:-/dmsdemo/z1}
EXPORT_PREFIX=${EXPORT_PREFIX:-/ifs/z1}
RAW_DIR=raw

CL01=${CL01_NAME:-DMSPOC2}
CL02=${CL02_NAME:-DMSPOC}
#CL03=${CL03_NAME:-hop-isi-v}
#CL04=${CL04_NAME:-islp00004}

PATH_CL01=${CL01}/${RAW_DIR}
PATH_CL02=${CL02}/${RAW_DIR}
#PATH_CL03=${CL03}/${RAW_DIR}
#PATH_CL04=${CL04}/${RAW_DIR}

MOUNT_CL01=${MOUNT_PREFIX}/${PATH_CL01}
MOUNT_CL02=${MOUNT_PREFIX}/${PATH_CL02}
#MOUNT_CL03=${MOUNT_PREFIX}/${PATH_CL03}
#MOUNT_CL04=${MOUNT_PREFIX}/${PATH_CL04}

EXPORT_CL01=${EXPORT_PREFIX}/${PATH_CL01}
EXPORT_CL02=${EXPORT_PREFIX}/${PATH_CL02}
#EXPORT_CL03=${EXPORT_PREFIX}/${PATH_CL03}
#EXPORT_CL04=${EXPORT_PREFIX}/${PATH_CL04}

# create mount points
mkdir -p ${MOUNT_CL01}
mkdir -p ${MOUNT_CL02}
#mkdir -p ${MOUNT_CL03}
#mkdir -p ${MOUNT_CL04}

# umount existing mounts
set +e
umount ${MOUNT_CL01}
umount ${MOUNT_CL02}
#umount ${MOUNT_CL03}
#umount ${MOUNT_CL04}
set -e

# set user and group of the mount points
chown ${USER}:${GROUP} ${MOUNT_CL01}
chown ${USER}:${GROUP} ${MOUNT_CL02}
#chown ${USER}:${GROUP} ${MOUNT_CL03}
#chown ${USER}:${GROUP} ${MOUNT_CL04}

# set permission
chmod 640 ${MOUNT_CL01}
chmod 640 ${MOUNT_CL02}
#chmod 640 ${MOUNT_CL03}
#chmod 640 ${MOUNT_CL04}

# mount Isilon NFS exports
mount ${CL01_NFS_HOST}:${EXPORT_CL01} ${MOUNT_CL01}
mount ${CL02_NFS_HOST}:${EXPORT_CL02} ${MOUNT_CL02}
#mount ${CL03_NFS_HOST}:${EXPORT_CL03} ${MOUNT_CL03}
#mount ${CL04_NFS_HOST}:${EXPORT_CL04} ${MOUNT_CL04}
