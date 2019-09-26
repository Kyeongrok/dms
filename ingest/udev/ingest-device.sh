#!/bin/bash

set -u

# mdadm is in /usr/sbin on CentOS.
# ingest.py and dms_utils are assumed to be in the PATH or /opt/dms/bin
export PATH=$PATH:/usr/sbin

# Maybe needed to run for python click
#export LC_ALL=C.UTF-8
#export LANG=C.UTF-8
export LC_ALL=en_US.utf8
export LANG=en_US.utf8

# Config file passed from the udev rules in /etc/udev/rules.d
INGEST_CONF=$2

# device name, e.g., /dev/md123
CONTEXT="ingest.device"
DEVICE=$DEVNAME
HOST=`hostname`
READER_ID=${HOST}-${DEVICE}

ECHO() {
    echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"` $1"
}

log() {
    echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"` $1 "$HOST" context:"$CONTEXT" device:"$DEVICE" $$ $2" >> $LOG_FILE
}

wait_for_md_device() {
    # wait for about 2m for the OS to assemble md device
    DEVICE=$1
    MAX=24
    COUNT=0
    sleep 5
    while true
    do
        STATUS=`mdadm -D ${DEVICE} | grep "State :" | awk '{print $3}'`
        log "INFO" "line(${LINENO}): device status: $STATUS"

        if [ "$STATUS" = "${STATUS_CLEAN}" ]; then
            # status is clean
            break
        else
            # status not clean. wait
            sleep 5
            COUNT=`expr $COUNT + 1`
        fi
        if [ $COUNT -ge "$MAX" ]; then
            log "ERROR" "line(${LINENO}): device status is still $STATUS after two minutes"
            break
        fi
    done
}


get_path() {
    # $ mdadm -D /dev/md127
    #   Number   Major   Minor   RaidDevice State
    #       0       8        0        0      active sync   /dev/sda
    #       1       8       48        1      active sync   /dev/sdd
    #       2       8       32        2      active sync   /dev/sdc
    #       3       8       16        3      active sync   /dev/sdb
    #
    # $ ls -l /dev/disk/by-path
    # lrwxrwxrwx. 1 root root  9 Nov 16 14:14 pci-0000:05:00.0-sas-phy0-lun-0 -> ../../sda
    # lrwxrwxrwx. 1 root root  9 Nov 16 14:14 pci-0000:05:00.0-sas-phy1-lun-0 -> ../../sdb
    # lrwxrwxrwx. 1 root root  9 Nov 16 14:14 pci-0000:05:00.0-sas-phy2-lun-0 -> ../../sdc
    # lrwxrwxrwx. 1 root root  9 Nov 16 14:14 pci-0000:05:00.0-sas-phy3-lun-0 -> ../../sdd

    # sleep for the md device to build up. TBD: handle this better
    sleep 2

    DEVICE=$1
    # get first disk in the array
    DISK1=`mdadm -D $DEVICE | grep /dev/sd | grep 0 | awk '{print $7}'`
    if [ "$DISK1" = "" ]; then
        # return empty string
        echo ""
    else
        # get path of the first disk
        PORT=`ls -l /dev/disk/by-path/ | grep "${DISK1:5}" | grep -E "sas-phy|scsi-" | awk '{print $9}'`

        # convert - to _
        PORT=${PORT//[-:.]/_}

        # replace port with mapping in conf file
        # sas_phy0=rack1_unit1
        MAP=`declare -p | grep $PORT | grep -v "PORT=" | cut -d "=" -f 2-2 | tr -d '"'`
        if [ "$MAP" = "" ]; then
           echo $PORT
        else
           echo $MAP
        fi
    fi
}

get_cartridge_id() {

    # build the cartridge ID from the serial number of the disks
    DEVICE=$1
    LEVEL=INFO
    MESSAGE="udevadm info --query=all --name=${DEVICE} | grep MD_DEVICE"
    log "$LEVEL" "line(${LINENO}): ${MESSAGE}"

    serial_ids=()
    disks=`udevadm info --query=all --name=${DEVICE} | grep MD_DEVICE | awk 'match($0, /MD_DEVICE_[a-z_]+_(DEV|ROLE)=([a-z0-9\/]+)/) {print substr($0, RSTART, RLENGTH)}'| awk '{split ($0, a, "="); print a[2] ;'} | awk 'ORS=NR%2?FS:RS' | sort -k2 | cut -d' ' -f1`

    # get the serial ID of each disk in the array
    if [ $? -eq 0 ]; then
        for disk in $disks ; do
            serial_id=`udevadm info --query all --name=$disk | grep -o 'ID_SERIAL_SHORT=.*' | cut -f2 -d=`
            serial_ids+=($serial_id)
        done
    fi

    # return the IDs concatenated with -
    num_disks=${#serial_ids[@]}
    if [[ $num_disks -ne 0 ]] ; then
        (IFS=-; echo "${serial_ids[*]}")
    else
        echo "NONE"
    fi
}

wait_for_mount_dir() {
    # wait 2m for mount point to be released
    MOUNT_DIR=$1
    MAX=24
    COUNT=0
    while true
    do
        LEVEL=INFO
        MESSAGE=`fuser $MOUNT_DIR 2>&1`
        CODE=$?
        log "$LEVEL" "line(${LINENO}): Wait for mount $MOUNT_DIR to be releasedi\n. Count=$COUNT fuser $MOUNT_DIR output\n: ${MESSAGE}"
        if [ $CODE -eq 0 ]; then
            # mount point still being used. Wait
            sleep 5
            COUNT=`expr $COUNT + 1`
        else
            # not used anymore
            #echo 0
            break
        fi

        if [ $COUNT -gt "$MAX" ]; then
            # max count reached. still used.
            #echo 1
            break
        fi
    done
}

stop_ingest() {
    MOUNT_DIR=$1
    LEVEL=WARNING
    INFO_TEXT=`ps -aef | grep python3 | grep "m ${MOUNT_DIR}$"`
    MESSAGE="Received remove event, stop running ingestion\n: $INFO_TEXT"
    log "$LEVEL" "line(${LINENO}): ${MESSAGE}"
    ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
    ps -aef | grep python3 | grep "m ${MOUNT_DIR}$" | awk '{print $2}' | xargs -r kill -INT
}

stop_rsync() {
    MOUNT_DIR=$1
    LEVEL=WARNING
    INFO_TEXT=`ps -aef | grep rsync | grep " ${MOUNT_DIR}/"`
    MESSAGE="received remove event, stop running rsync\n: $INFO_TEXT"
    log "$LEVEL" "line(${LINENO}): ${MESSAGE}"
    ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
    ps -aef | grep rsync | grep " ${MOUNT_DIR}/" | awk '{print $2}' | xargs -r kill
}

stop_md_device() {
    DEVICE=$1
    mdadm -D $DEVICE > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        LEVEL=INFO
        MESSAGE="received remove event. mdmdm --stop $DEVICE"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        mdadm --stop $DEVICE >> $LOG_FILE 2>&1
    fi
}

# Get config parameters from config file
source <(grep = <(sed -n '/^\s*\[station_config\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))

# md device to be mount on directory $MOUNT_PREFIX/<device name>
MOUNT_PREFIX=${md_mount_prefix:-/volvo}
INGEST_USER=${ingest_user:-ingest}
INGEST_GROUP=${ingest_group:-resim}
LOG_FILE=${ingest_log:-/opt/dms/logs/ingest.log}
AUTO_FORMAT=${auto_format:-False}
SENSOR_MODE=${enabled:-False}
FS_CHECK_RETRIES=${fs_check_retries:-10}
FS_CHECK_SLEEP=${fs_check_sleep:-15}

DMS_UTIL="dms_utils -c $INGEST_CONF"
INGEST_SCRIPT=ingest

# make log file writable by ingest user
touch $LOG_FILE
chmod o+w $LOG_FILE

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

MOUNT_DIR=${MOUNT_PREFIX}${DEVICE}

LOG_TO_ES="${DMS_UTIL} journal_create -e device=$DEVICE -e mount=$MOUNT_DIR -e reader_id=$READER_ID -e action=$ACTION"

SELF=$0

case "$1" in
    add)

        LOCK="/var/run/Ingestion-add-${DEVICE:5}.LCK";
        exec 8>$LOCK;

        if ! flock -n 8; then
            log "INFO" "line(${LINENO}): Received additional add event. Ignore.";
            exit 1
        fi

        # Wait for OS to assemble md device from the disks on cartridge
        wait_for_md_device $DEVICE

        # update ingest reader in ES
        LEVEL=INFO
        MESSAGE="initialize reader: host=$HOST, device=$DEVICE, reader_id=$READER_ID, status=empty, ingest_state=idle"
        log "$LEVEL" "line(${LINENO}): ${MESSAGE}"
        PORT=$(get_path $DEVICE)
        log "$LEVEL" "line(${LINENO}): PORT: ${PORT}"
        LOG_TO_ES="$LOG_TO_ES -e reader_port=$PORT"

         # get the cartridge detail
        LEVEL=INFO

        CARTRIDGE_ID=$(get_cartridge_id $DEVICE)
        log "$LEVEL" "line(${LINENO}): CARTRIDGE_ID: ${CARTRIDGE_ID}"
        LOG_TO_ES="$LOG_TO_ES -e cartridge_id=${CARTRIDGE_ID}"

        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} reader_create --host=${HOST} --device=${DEVICE} --mount=${MOUNT_DIR} --port="$PORT" --reader-id=${READER_ID} >> $LOG_FILE 2>&1

        if [ $CARTRIDGE_ID == "NONE" ]; then
            LEVEL=ERROR
            STATUS=${STATUS_INACTIVE}
            INFO_TEXT="Failed to get cartridge disk IDs"
            MESSAGE="Unable to obtain serial number of cartridge disk members"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} reader_update --reader-id=${READER_ID} --status=$STATUS --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            stop_md_device $DEVICE
            exit 1
        fi

        ${DMS_UTIL} cartridge_create --host=${HOST} --device=${DEVICE} --slot="$PORT" --cartridge-id=${CARTRIDGE_ID} --usage=-1 >> $LOG_FILE 2>&1

        # get device detail.
        INFO_TEXT="device detail from mdadm"
        MESSAGE=`mdadm -D ${DEVICE} 2>&1`
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "${INFO_TEXT}: $MESSAGE"
        log "$LEVEL" "line(${LINENO}): ${INFO_TEXT}"
        mdadm -D ${DEVICE} >> $LOG_FILE 2>&1

        # get device status.
        STATUS=`mdadm -D ${DEVICE} | grep "State :" | awk '{print $3}'`
        log "INFO" "line(${LINENO}): device status: $STATUS"

        if [ "$STATUS" = "${STATUS_CLEAN}" ]; then
            # clean maps to active in ES
            LEVEL=INFO
            STATUS=${STATUS_ACTIVE}
            MESSAGE="update reader: status=$STATUS"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            log "INFO" "line(${LINENO}): $MESSAGE"
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS >> $LOG_FILE 2>&1
        else
            # log error
            LEVEL=ERROR
            STATUS=${STATUS_INACTIVE}
            INFO_TEXT="check mdadm -D $DEVICE"
            MESSAGE="$DEVICE is $STATUS. $MESSAGE. Exiting. $INFO_TEXT "
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"

            # update reader
            LEVEL=INFO
            MESSAGE="update reader: status=$STATUS"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} reader_update --reader-id=${READER_ID} --status=$STATUS --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            stop_md_device $DEVICE
            exit 1
        fi


        sleep 15
        # check filesystem
        CMD="/sbin/fsck -vy $DEVICE"
        INFO_TEXT=`for i in $(seq 1 ${FS_CHECK_RETRIES}); do /sbin/fsck -vy $DEVICE 2>&1 && s=0 && break || s=$? && sleep ${FS_CHECK_SLEEP}; done; (exit $s)`
        if [ 0 -eq $? ]; then
            LEVEL=INFO
            MESSAGE="$CMD: ${DEVICE} is clean. $INFO_TEXT"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
        else
            # log error
            LEVEL=ERROR
            STATUS=${STATUS_INACTIVE}
            MESSAGE="$CMD failed. ${INFO_TEXT}"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            # update reader
            INFO_TEXT="filesystem check failed"
            ${DMS_UTIL} reader_update --reader-id=${READER_ID} --status=$STATUS --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            stop_md_device $DEVICE
            exit 1
        fi

        mounted=$( mount | grep "^${DEVICE} on" | wc -l )
        if [[ $mounted -ne 0 ]]; then
            # log error
            LEVEL=ERROR
            STATUS=${STATUS_INACTIVE}
            INGEST_STATE=${STATE_IDLE}
            INFO_TEXT=`mount | grep "^${DEVICE} on"`
            MESSAGE="${DEVICE} already mounted: ${INFO_TEXT}"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE -message="$INFO_TEXT" >> $LOG_FILE 2>&1
            stop_md_device $DEVICE
            exit 1
        fi

        # not mounted
        if [[ ! -d ${MOUNT_DIR} ]]; then
            LEVEL=INFO
            MESSAGE="create mount directory: ${MOUNT_DIR}"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            mkdir -p ${MOUNT_DIR} >> $LOG_FILE 2>&1

            MESSAGE="set ownership of ${MOUNT_DIR}: ${INGEST_USER}:${INGEST_GROUP}"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            /bin/chown -vR ${INGEST_USER}:${INGEST_GROUP} ${MOUNT_DIR} >> $LOG_FILE 2>&1
        fi

        INFO_TEXT=`mount -o noatime,nodiratime ${DEVICE} ${MOUNT_DIR} 2>&1`
        if [ 0 -ne $? ]; then
            # log error
            LEVEL=ERROR
            MESSAGE="mount ${DEVICE} on ${MOUNT_DIR} failed. Exiting. $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

            # update reader
            LEVEL=INFO
            STATUS=${STATUS_INACTIVE}
            INFO_TEXT="mount ${DEVICE} failed"
            MESSAGE="update reader: status=$STATUS $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --message="$INFO_TEXT" >> $LOG_FILE 2>&1

            stop_md_device $DEVICE
            exit 1
        fi

        # get usage of cartridge
        DEV_USED=`df -k | grep ${DEVICE} | awk {'print $3'}`
        DEV_USED_GB=$(awk -v DEV_USED=$DEV_USED 'BEGIN { print DEV_USED / 1024 / 1024}')


        if [ $DEV_USED_GB ==  0 ]; then
            # log a warning

            LEVEL=WARNING
            MESSAGE="Failed to obtain cartridge usage"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        else
            ${DMS_UTIL} cartridge_update  --cartridge-id=$CARTRIDGE_ID} --usage=$DEV_USED_GB >> $LOG_FILE 2>&1
        fi

        LEVEL=INFO
        MESSAGE="mount ${DEVICE} on ${MOUNT_DIR}"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

        # start copying data
        INGEST_STATE=${STATE_COPY}
        MESSAGE="ingestion started. update reader: status=$STATUS, ingest_state=$INGEST_STATE"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1
        ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1

        su -l $INGEST_USER -c "${INGEST_SCRIPT} -c ${INGEST_CONF} -m ${MOUNT_DIR} -r ${READER_ID} -cr ${CARTRIDGE_ID} >> $LOG_FILE 2>&1" >> $LOG_FILE 2>&1

        if [ 0 -ne $? ]; then
            # log error
            LEVEL=ERROR
            INGEST_STATE=${STATE_FAILED}
            INFO_TEXT="ingestion failed. check $LOG_FILE"
            MESSAGE="status=$STATUS ingest_state=$INGEST_STATE. $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

            # update reader
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1

            # unmount device
            umount ${MOUNT_DIR} 2>&1

            stop_md_device $DEVICE
            exit 1
        fi

        if [ "${SENSOR_MODE^^}" = "FALSE" ]; then
            # additional verification
            INFO_TEXT=`${DMS_UTIL} ingest_verify $MOUNT_DIR 2>&1`
            EXIT_CODE=$?
            if [ $EXIT_CODE -ne 0 ]; then
                # log error
                LEVEL=ERROR
                INGEST_STATE=${STATE_FAILED}
                MESSAGE="status=$STATUS ingest_state=$INGEST_STATE $INFO_TEXT"
                log "$LEVEL" "line(${LINENO}): $MESSAGE"
                ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
                # update reader
                if [ $EXIT_CODE -eq 11 ]; then
                    INFO_TEXT="no drive found"
                else
                    INFO_TEXT="verification failed"
                fi
                ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
                ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1
                stop_md_device $DEVICE
                exit $EXIT_CODE
            fi
        fi

        # unmount the device
        INFO_TEXT=`umount ${MOUNT_DIR} 2>&1`
        if [ $? -ne 0 ]; then
            LEVEL=ERROR
            INGEST_STATE=${STATE_FAILED}
            MESSAGE="status=$STATUS ingest_STATE=$INGEST_STATE umount $MOUNT_DIR: $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            # update reader
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1
            stop_md_device $DEVICE

            exit 1
        fi

        if [ "${AUTO_FORMAT^^}" = "TRUE" ]; then
            # format device
            LEVEL=INFO
            MESSAGE="Start formatting $DEVICE"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            INFO_TEXT=`echo y | ${DMS_UTIL} device_format $DEVICE 2>&1`
            if [ $? -ne 0 ]; then
                LEVEL=ERROR
                INGEST_STATE=${STATE_FAILED}
                MESSAGE="status=$STATUS ingest_STATE=$INGEST_STATE ingest verification: $INFO_TEXT"
                log "$LEVEL" "line(${LINENO}): $MESSAGE"
                ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
                # update reader
                INFO_TEXT="ingestion finished; device formatting failed"
                ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
                ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1
                stop_md_device $DEVICE
                exit 1
            fi

            # formatted device
            LEVEL=INFO
            INGEST_STATE=${STATE_DONE}
            MESSAGE="status=$STATUS, ingest_state=$INGEST_STATE ingestion finished; device formatted: $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

            INFO_TEXT="ingestion finished; device formatted"
            ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1
            stop_md_device $DEVICE
            exit 0
        fi

        # successful
        LEVEL=INFO
        INGEST_STATE=${STATE_DONE}
        INFO_TEXT="ingestion finished"
        MESSAGE="status=$STATUS ingest_state=$INGEST_STATE $INFO_TEXT"
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
        ${DMS_UTIL} cartridge_update  --cartridge-id=${CARTRIDGE_ID} --ingest-state=$INGEST_STATE >> $LOG_FILE 2>&1
        stop_md_device $DEVICE

    ;;

    remove)

        REMOVE_LOCK="/tmp/Ingestion-remove-${DEVICE:5}.LCK"
        exec 9>$REMOVE_LOCK;

        if ! flock -n 9; then
            log "INFO" "line(${LINENO}): Received additional remove event. Ignore.";
            exit 1
        fi

        log "INFO" "line(${LINENO}): Received remove event. Lock $REMOVE_LOCK."

        # clean up.
        stop_ingest $MOUNT_DIR
        #stop_rsync $MOUNT_DIR
        wait_for_mount_dir $MOUNT_DIR

        # unmount if the device is mounted, e.g., when cartridge is pulled during ingestion.
        mounted=$( mount | grep "^${DEVICE} on ${MOUNT_DIR} type" | wc -l )
        log "$LEVEL" "line(${LINENO}): mounted = $mounted"
        if [[ $mounted -ne 0 ]]; then
            INFO_TEXT=`umount ${MOUNT_DIR} 2>&1`
            if [ 0 -ne $? ]; then
                LEVEL=ERROR
                MESSAGE="unmount $DEVICE from ${MOUNT_DIR} failed: $INFO_TEXT"
                log "$LEVEL" "line(${LINENO}): $MESSAGE"
                ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

                # update reader
                STATUS=${STATUS_INACTIVE}
                MESSAGE="update reader: status=$STATUS"
                log "INFO" "line(${LINENO}): $MESSAGE"
                ${LOG_TO_ES} "INFO" "$HOST" "$CONTEXT" "$MESSAGE"
                ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --message="$INFO_TEXT" >> $LOG_FILE 2>&1
                exit 1
            fi
        fi

        # stop md device
        stop_md_device $DEVICE

        # device removed
        LEVEL=INFO
        STATUS=$STATUS_EMPTY
        INFO_TEXT="device removed"

        MESSAGE="${INFO_TEXT};  host=${HOST} device=$DEVICE id=${READER_ID}"
        log "${LEVEL}" "line(${LINENO}): ${MESSAGE}"
        ${LOG_TO_ES} $LEVEL $HOST $CONTEXT "$MESSAGE"
        ${DMS_UTIL} reader_update  --reader-id=${READER_ID} --status=$STATUS --message="$INFO_TEXT" >> $LOG_FILE 2>&1

    ;;

    dispatch)

        MESSAGE="Ingest action started: ingest_action=${ACTION} device=${DEVICE} reader_id=${READER_ID} md_mount=${MOUNT_DIR} ingest_user=${INGEST_USER} ingest_log=${LOG_FILE}"

        # log to ES for troubleshooting
        ${LOG_TO_ES} "INFO" "$HOST" "$CONTEXT" "$MESSAGE"

        # log to console for manual ingestion
        ECHO "$MESSAGE"

        # log to file
        log "INFO" "line(${LINENO}): $MESSAGE"
        echo $SELF $ACTION $INGEST_CONF | /usr/bin/at now
    ;;
esac
