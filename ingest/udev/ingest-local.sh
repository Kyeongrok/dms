#!/bin/bash

set -u

# mdadm is in /usr/sbin on CentOS. 
# ingest and dms_utils command are assumed to be in the PATH 
export PATH=$PATH:/usr/sbin

# Maybe needed to run on ubuntu
#export LC_ALL=C.UTF-8
#export LANG=C.UTF-8

# Config file passed from the udev rules in /etc/udev/rules.d
INGEST_CONF=$2

# device name, e.g., /dev/md123
CONTEXT=ingest.local
DEVICE=$DATADIR
HOST=`hostname`
READER_ID=${HOST}-${DEVICE}

ECHO() {
   echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"` $1"
}

log() {
  echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"` $1 $HOST context:"$CONTEXT" device:$DEVICE $2" >> $LOG_FILE
}

# Get config parameters from config file 
source <(grep = <(sed -n '/^\s*\[station_config\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))

# md device to be mount on directory $MOUNT_PREFIX/<device name>
MOUNT_PREFIX=${md_mount_prefix:-/volvo}
INGEST_USER=${ingest_user:-ingest}
INGEST_GROUP=${ingest_group:-resim}
LOG_FILE=${ingest_log:-/opt/dms/logs/ingest.log}

# make log file writable by ingest user
touch $LOG_FILE
chmod o+w $LOG_FILE

DMS_UTIL="dms_utils -c $INGEST_CONF"
INGEST_SCRIPT=ingest
LOG_TO_ES="${DMS_UTIL} journal_create -e device=$DEVICE -e reader_id=$READER_ID -e action=$ACTION"

# Get device status value from config file
source <(grep = <(sed -n '/^\s*\[reader_status\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))
STATUS_ACTIVE=${reader_active:-active}
STATUS_INACTIVE=${reader_inactive:-inactive}
STATUS_EMPTY=${reader_empty:-empty}
STATUS_CLEAN=${reader_clean:-clean}

# Get ingest state value from config file
source <(grep = <(sed -n '/^\s*\[ingest_state\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))
STATE_IDLE=${ingest_idle:-idle}
STATE_COPY=${ingest_copy:-processing}
STATE_DONE=${ingest_done:-processed}
STATE_FAILED=${ingest_failed:-failed}

MOUNT_DIR=${DEVICE}

SELF=$0

stop_ingest() {
    DATADIR=$1
    LEVEL=WARNING
    INFO_TEXT=`ps -aef | grep python3 | grep "m ${DATADIR}$"`
    MESSAGE="Received remove event, stop running ingestion\n: $INFO_TEXT"
    log "$LEVEL" "line(${LINENO}): ${MESSAGE}"
    ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
    ps -aef | grep python3 | grep "m ${DATADIR}$" | awk '{print $2}' | xargs -r kill -INT
}

case "$1" in
    add)

        # update ingest reader in ES
        LEVEL=INFO
        MESSAGE="create reader: host=$HOST, datadir=$DEVICE, id=$READER_ID"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} reader_create --host=${HOST} --device=${DEVICE} --mount=${MOUNT_DIR} --reader-id=${READER_ID} >> $LOG_FILE 2>&1

        # start copying data
        STATUS=$STATUS_ACTIVE
        INGEST_STATE=${STATE_COPY}
        MESSAGE="copy started. update reader: status=$STATUS, ingest_state=$INGEST_STATE"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1

        su -l $INGEST_USER -c "${INGEST_SCRIPT} -c ${INGEST_CONF} -m ${DATADIR} >> $LOG_FILE 2>&1" >> $LOG_FILE 2>&1

        if [ 0 -eq $? ]; then
            INGEST_STATE=${STATE_DONE}
            INFO_TEXT="ingestion finished"
            MESSAGE="status=$STATUS, ingest_state=$INGEST_STATE $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
        else
            LEVEL=ERROR
            INGEST_STATE=${STATE_FAILED}
            MESSAGE="ingestion failed. Exiting. status=$STATUS, ingest_state=$INGEST_STATE"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            INFO_TEXT="check $LOG_FILE"
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            exit 1
        fi

    ;;

    remove)
        # stop running ingestion
        stop_ingest $DATADIR
        # reset the reader
        LEVEL=INFO
        MESSAGE="reset reader: host=${HOST}, datadir=$DEVICE, id=${READER_ID}"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        # Ignore if reader does not exist.
        ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=empty
    ;;

    dispatch)

        LEVEL=INFO
        MESSAGE="ingest action started: ingest_action=$ACTION datadir=${DEVICE} reader_id=${READER_ID} ingest_log=${LOG_FILE}"

        # log to ES for troubleshooting
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

        # log to console for manual ingestion
        ECHO "$MESSAGE"

        # log to file
        log "$LEVEL" "line(${LINENO}): $MESSAGE"

        echo $SELF $ACTION $INGEST_CONF | /usr/bin/at now
    ;;
esac

