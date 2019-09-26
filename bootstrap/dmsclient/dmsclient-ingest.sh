#!/bin/bash
set -uex

DMS_DIR=/opt/dms
BINDIR=${DMS_DIR}/bin
SRCDIR=${1:-/dms}


# create dms directories
mkdir -p ${DMS_DIR}/logs
mkdir -p ${DMS_DIR}/bin
mkdir -p ${DMS_DIR}/conf

# install dmsclient
cd ${SRCDIR}/dmsclient 
pip3 install -r requirements.txt
python3 setup.py install

# install ingest
cd ${SRCDIR}/ingest
pip3 install -r requirements.txt
python3 setup.py install

# may not needed, just in case not covered in requirements.txt
pip3 install click
pip3 install pyyaml
pip3 install tornado
pip3 install click_configfile
pip3 install retrying
pip3 install flask

# set up links
DMS_UTIL=dms_utils
INGEST_DEVICE=ingest-device.sh
INGEST_LOCAL=ingest-local.sh
INGEST=ingest

cd $BINDIR
'rm' -f $DMS_UTIL $INGEST_DEVICE $INGEST_LOCAL ${INGEST}

ln -s $SRCDIR/ingest/utils/$DMS_UTIL
ln -s $SRCDIR/ingest/udev/$INGEST_DEVICE
ln -s $SRCDIR/ingest/udev/$INGEST_LOCAL
ln -s $SRCDIR/ingest/bin/$INGEST

# set up ingest.conf
# cp ${SRCDIR}/ingest/config.example.ini ${DMS_DIR}/conf/ingest.conf #origin
cp ${SRCDIR}/ingest/config.2nd.ini ${DMS_DIR}/conf/ingest.conf

# install udev rules
cd ${SRCDIR}/ingest/udev
'cp' -f *.rules /etc/udev/rules.d
udevadm control --reload
