#!/bin/bash
set -ue
# generate fake drive data

if [ $# -eq 0 ] ; then
    echo "Usage: gen-drive-data.sh DIRECTORY"
    exit 1
fi

DIR=${1%/}
if [ ! -d "${DIR}" ] ; then
    echo "$DIR not is a directory";
    exit 2
fi

YEAR=${YEAR:-2017}
SIZE_MB=${SIZE_MB:-1024}
NUM_DRIVES=${NUM_DRIVES:-2}
NUM_FILES=${NUM_FILES:-2}
VOLVO_PROJ=${VOLVO_PROJ:-Z1}

echo "Creating ${NUM_DRIVES} drive directories with ${NUM_FILES} segment files of size ${SIZE_MB}MB each"

DRIVE_COUNT=1
while [ $DRIVE_COUNT -le $NUM_DRIVES ]; do

    drive_time_s=`date -u +%s`
    let drive_time_s=${drive_time_s}+${DRIVE_COUNT}
    DRIVE_TIME=`date -u -d @$drive_time_s +"%Y%m%dT%H%M%S"`
    CAR=`cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 5 | head -n 1`
    DRIVE_NAME=${VOLVO_PROJ}_${CAR}_CONT_$DRIVE_TIME
    echo $DRIVE_NAME
    mkdir -p ${DIR}/$DRIVE_NAME

    FILE_COUNT=1
    while [ $FILE_COUNT -le $NUM_FILES ]; do
        start_time_s=`date -u +%s`
        let start_time_s=${start_time_s}+${FILE_COUNT}+${DRIVE_COUNT}
        START_TIME=`date -u -d @$start_time_s +"%Y%m%dT%H%M%S"`
        let end_time_s=$start_time_s+60
        END_TIME=`date -u -d @$end_time_s +"%Y%m%dT%H%M%S"`
        FILE_NAME=${VOLVO_PROJ}_${CAR}_CONT_${START_TIME}-${END_TIME}
        echo $FILE_NAME
        dd if=/dev/urandom of=${DIR}/${DRIVE_NAME}/${FILE_NAME}.vpcap bs=1M count=$SIZE_MB
        let FILE_COUNT=FILE_COUNT+1
    done
    let DRIVE_COUNT=DRIVE_COUNT+1
done
