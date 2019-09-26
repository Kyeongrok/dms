#!/bin/bash


set -u
# Maybe needed to run for python click
export LC_ALL=en_US.utf8
export LANG=en_US.utf8

# config file
INGEST_CONF=$2

# device name, e.g., /dev/md123
CONTEXT="ingest_usb.device"
DEVICE=$DEVNAME
HOST=`hostname`
READER_ID=${HOST}-${DEVICE}

ECHO() {
    echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"` $1"
}

log() {
    echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"` $1 "$HOST" context:"$CONTEXT" device:"$DEVICE" $$ $2" >> $LOG_FILE
}

unmount_device() {
    LEVEL=INFO
    mounted=$( mount | grep "^$1 on ${MOUNT_DIR} type" | wc -l )
    log "$LEVEL" "line(${LINENO}): mounted = $mounted"
    if [[ $mounted -ne 0 ]]; then
        INFO_TEXT=`umount ${MOUNT_DIR} 2>&1`
        if [ 0 -ne $? ]; then
            LEVEL=ERROR
            MESSAGE="unmount $DEVICE from ${MOUNT_DIR} failed: $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

            # update reader
		    MOUNT_STATE=${STATE_MOUNTED}
            MESSAGE="update reader: mount-state=$MOUNT_STATE"
            log "INFO" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "INFO" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            return 1
         else
            LEVEL=INFO
            MOUNT_STATE=${STATE_UNMOUNTED}
            MESSAGE="$DEVICE unmounted from $MOUNT_DIR"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "INFO" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
        fi
     fi
}

get_path() {

    mapping=$(echo -n ${HOSTNAME%%.*}_;echo $1  |/usr/bin/awk -F"/" ' { print $5"_"$6 } ')

    #lookup the value returned against the config file
    port=$(grep -Po "(?<=^$mapping).*" $INGEST_CONF | cut -d'=' -f2-)

    if [ -z  "$port" ] ; then
        echo "Unknown"
    else
        echo $port
    fi
}


# Get config parameters from config file
source <(grep = <(sed -n '/^\s*\[station_config\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))

# md device to be mount on directory $MOUNT_PREFIX/<device name>
MOUNT_PREFIX=${md_mount_prefix:-/volvo}
INGEST_USER=${ingest_user:-ingest}
INGEST_GROUP=${ingest_group:-resim}


FS_CHECK_RETRIES=${fs_check_retries:-10}
FS_CHECK_SLEEP=${fs_check_sleep:-15}

# usb ingestion specific params
source <(grep = <(sed -n '/^\s*\[usb_ingestion\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))

LOG_FILE=${ingest_usb_log:-/opt/dms/logs/ingest-usb.log}
RUN_FSCK=${run_fsck:-False}
TARGET_CLUSTER=${target_cluster:-islp00001}


DMS_UTIL="dms_utils -c $INGEST_CONF"

# make log file writable by ingest user
touch $LOG_FILE
chmod o+w $LOG_FILE

# Get mounted state value from config file
source <(grep = <(sed -n '/^\s*\[mount_state\]/,/^\s*\[/p' $INGEST_CONF | sed 's/ *= */=/g'))
STATE_MOUNTED=${device_mounted:-mounted}
STATE_UNMOUNTED=${device_unmounted:-unmounted}



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

        # update ingest reader in ES
        LEVEL=INFO
        MESSAGE="initialize reader: host=$HOST, device=$DEVICE, reader_id=$READER_ID, mount_state=unmounted, ingest_state=idle"
        log "$LEVEL" "line(${LINENO}): ${MESSAGE}"
        PORT=$(get_path $DEVPATH)
        log "$LEVEL" "line(${LINENO}): PORT: ${PORT}"
        LOG_TO_ES="$LOG_TO_ES -e reader_port=$PORT"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE" 
        ${DMS_UTIL} usb_reader_create --host=${HOST} --device=${DEVICE} --mount=${MOUNT_DIR} --port="$PORT" --reader-id=${READER_ID} >> $LOG_FILE 2>&1

        
        # check filesystem if this option has been set (defaults to false)
        if [ "${RUN_FSCK^^}" = "TRUE" ]; then
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
                INGEST_STATE=${STATE_FAILED}
                MESSAGE="$CMD failed. ${INFO_TEXT}"
                log "$LEVEL" "line(${LINENO}): $MESSAGE"
                ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
                # update reader
                INFO_TEXT="filesystem check failed"
                ${DMS_UTIL} usb_reader_update --reader-id=${READER_ID} --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
                exit 1
            fi
         fi

        mounted=$( mount | grep "^${DEVICE} on" | wc -l )
        if [[ $mounted -ne 0 ]]; then
            # log error
            LEVEL=ERROR
            MOUNT_STATE=${STATE_UNMOUNTED}
            INGEST_STATE=${STATE_IDLE}
            INFO_TEXT=`mount | grep "^${DEVICE} on"`
            MESSAGE="${DEVICE} already mounted: ${INFO_TEXT}"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --ingest-state=$INGEST_STATE -message="$INFO_TEXT" >> $LOG_FILE 2>&1
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

        INFO_TEXT=`mount -t vfat ${DEVICE} ${MOUNT_DIR} 2>&1`
        if [ 0 -ne $? ]; then
            # log error
            LEVEL=ERROR
            MOUNT_STATE=${STATE_UNMOUNTED}
            INFO_TEXT="mount ${DEVICE} failed"
            MESSAGE="mount ${DEVICE} on ${MOUNT_DIR} failed. Exiting. $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            exit 1
        fi

        LEVEL=INFO

	      INGEST_STATE=${STATE_COPY}

        MOUNT_STATE=${STATE_MOUNTED}
        MESSAGE="mount ${DEVICE} on ${MOUNT_DIR}"
        INFO_TEXT="${DEVICE} mounted "
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1

        # extract car reg
        car_reg= 

        regex="[A-Z]{4}[0-9]{3}_([A-Z]{3}[0-9]{3})(\s*).txt$"


        for file in $MOUNT_DIR/* ; do
            if [[ $file =~ $regex  ]]; then
                car_reg=${BASH_REMATCH[1]}
            fi
        done

        if [ -z "$car_reg" ] ; then 
            LEVEL=ERROR
            INFO_TEXT="failed to extract car ID"
            INGEST_STATE=${STATE_FAILED}
            MESSAGE="unable to extract car ID from USB drive files"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            exit 1
        else
            LEVEL=INFO
            INFO_TEXT="extracted car ID ${car_reg}"
            MESSAGE="extracted car ID ${car_reg} from .txt file on USB device"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --message="$INFO_TEXT" >> $LOG_FILE 2>&1
        fi

        # get the path to where the data is to be copied

        isilon_path=`${DMS_UTIL} get_logs_target_cluster --cluster-id=${TARGET_CLUSTER} 2>&1`

        if [ ! -d "$isilon_path" ] ; then 
            LEVEL=ERROR
            INFO_TEXT="invalid Isilon target directory"
            MESSAGE="unable to obtain path to target directory on Isilon cluster"
            INGEST_STATE=${STATE_FAILED}
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID}  --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            exit 1
        else
            LEVEL=INFO
            MESSAGE="Retrieved path to Isilon cluster ${car_reg}"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        fi

        start_time=`date -u +"%Y%m%dT%H%M%S"`
        target_dir=${isilon_path}/${car_reg}/melco/LOG_$start_time
        LEVEL=INFO
        MESSAGE="creating target directory ${target_dir}  on Isilon cluster"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

        su $INGEST_USER -c "mkdir -p $target_dir"

        if su ${INGEST_USER} -c "[ ! -d $target_dir ]" ; then

            LEVEL=ERROR
            INFO_TEXT="mkdir -p ${target_dir} : failed"
            INGEST_STATE=${STATE_FAILED}
            MESSAGE="unable to create target directory $target_dir"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
            exit 1
        else
            LEVEL=INFO
            MESSAGE="Created target directory $target_dir"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        fi 

         # start copying data
        INGEST_STATE=${STATE_COPY}
        MOUNT_STATE=${STATE_MOUNTED}
        MESSAGE="ingestion started. update reader: mount_state=$MOUNT_STATE, ingest_state=$INGEST_STATE"
        INFO_TEXT="calling cp -R ${MOUNT_DIR}/LOG/*  $target_dir "
        log "$LEVEL" "line(${LINENO}): $MESSAGE"
        ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
        ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1

        su ${INGEST_USER} -c  "cp -R ${MOUNT_DIR}/LOG/*  $target_dir"

        if [ 0 -ne $? ]; then
            # log error
            LEVEL=ERROR
            INGEST_STATE=${STATE_FAILED}
            INFO_TEXT="ingestion failed. check $LOG_FILE"
            MESSAGE="ingest_state=$INGEST_STATE. $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"

            # update reader
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1

            unmount_device ${DEVICE}
            exit 1
        fi

       # additional verification
n
        result=$(su ${INGEST_USER} -c "/usr/bin/diff -r ${MOUNT_DIR}/LOG $target_dir | wc -l")

        if [ $result -ne 0 ] ; then
            LEVEL=ERROR
            INGEST_STATE=${STATE_FAILED}
            INFO_TEXT="diff -r ${MOUNT_DIR}/LOG $target_dir"
            MESSAGE="data validation failed $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1

            unmount_device ${DEVICE}
        fi 	

         # unmount the device
        unmount_device ${DEVICE}

        if [ $? -eq 0 ] ; then
            # successful
            LEVEL=INFO
            INGEST_STATE=${STATE_DONE}
            INFO_TEXT="ingestion finished"
            MOUNT_STATE=${STATE_UNMOUNTED}
            MESSAGE="ingest_state=$INGEST_STATE $INFO_TEXT"
            log "$LEVEL" "line(${LINENO}): $MESSAGE"
            ${LOG_TO_ES} "$LEVEL" "$HOST" "$CONTEXT" "$MESSAGE"
            ${DMS_UTIL} usb_reader_update  --reader-id=${READER_ID} --mount-state=$MOUNT_STATE --ingest-state=$INGEST_STATE --message="$INFO_TEXT" >> $LOG_FILE 2>&1
         fi
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
