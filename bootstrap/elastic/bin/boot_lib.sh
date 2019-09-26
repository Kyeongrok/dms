#!/bin/sh
########################################################################
# Boot script to configure Elasticsearch
########################################################################

set -u

DASHBOARD_BASE=${BOOT_LOCATION}/..
VISUALIZATION_PATH=${DASHBOARD_BASE}/visualization
SEARCH_PATH=${DASHBOARD_BASE}/search
DASHBOARD_PATH=${DASHBOARD_BASE}/dashboard
TEMPLATE_PATH=${DASHBOARD_BASE}/index-template
NAVIGATION_INDEX=navigation
JOURNAL_INDEX=${JOURNAL_INDEX:-dms-z1-log-v1}
RAW_INDEX=${RAW_INDEX:-dms-z1-raw-v1}
PERM_INDEX=${PERM_INDEX:-dms-z1-perm-v1}
RESIM_INDEX=${RESIM_INDEX:-dms-z1-resim-v1}
CONFIG_INDEX=${CONFIG_INDEX:-dms-configuration-v1}
ES_ENDPOINT=${ES_ENDPOINT:-http://10.35.102.184:9200}
ES_VERSION=${ES_VERSION:-5.6.4}

ES_USERNAME=${ES_USERNAME:-elastic}
ES_PASSWORD=${ES_PASSWORD:-changeme}
#ES_LOGIN="--es-endpoint=$ES_ENDPOINT --es-username=$ES_USERNAME --es-password=$ES_PASSWORD"
ES_LOGIN=""
LOGIN=${ES_USERNAME}:${ES_PASSWORD}
CURL="curl -f -u $LOGIN"

log(){
    msg=" $*"
    echo "`date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"`": $msg
}

_create_index() {
    INDEX=$1
    SHARDS=$2
    REPLICAS=$3
    # create index if it does not exist.
    set +e
    set -x
    $CURL -I ${ES_ENDPOINT}/${INDEX}
    status=$?
    echo $status
    set +x
    set -e
    if [ 0 -eq $status ]; then
        log "index $INDEX exists"
    else
        log "create configuration index"
        set -x
        $CURL -XPUT ${ES_ENDPOINT}/${INDEX}?pretty  -d'
        {
            "settings" : {
                "index" : {
                    "number_of_shards" : "'${SHARDS}'",
                    "number_of_replicas" : "'${REPLICAS}'"
                }
            }
        }'
        status=$?
        set +x
        if [ 0 -eq $status ]; then
            log "create configuration index successfully"
        else
            log "failed to create configuration index. ${INDEX} may exist already."
        fi
    fi
}

# validate ES is reachable
_validate_environment() {
    log "validate if ES is reachable"
    set +e
    while true
    do
        $CURL -XGET ${ES_ENDPOINT}
        if [ $? -eq 0 ]
        then
            break;
        else
            echo "`date` waiting for Elasticsearch to start..."
            sleep 1
        fi
    done
    set -e
}

_enable_dynamic_mapping() {
    $CURL -XPUT ${ES_ENDPOINT}/_template/enable_dynamic_mappings?pretty -d '
    {
        "order": 0,
        "template": "*",
        "mappings": {
            "_default_": {
                "numeric_detection": true
            }
        } 
    }'
    status=$?
    if [ 0 -eq $status ]; then
        log "enable dynamic mapping successfully"
    else
        log "failed to enable dynamic mapping"
    fi
}

# create template for general navigation
_create_navigation_template() {
    log "create template for navigation"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/_template/navigation?pretty -d@${TEMPLATE_PATH}/navigation_template.json
    status=$?
    set +x
    if [ 0 -eq $status ]; then
       log "create template for navigation successfully"
    else
       log "failed to create template for navigation"
    fi
}

# create navigation category
_create_navigation_category() {
    log "create navigation category"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/_bulk?pretty  --data-binary @${TEMPLATE_PATH}/navigation_category.json
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "created navigation category successfully"
    else
        log "failed to create navigation category"
    fi
}

# create DMS template including configuration, raw, resim, journal
_create_dms_template() {
    log "create DMS templates"
    set -x
    dms_utils template_create
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "created DMS templates successfully"
    else
        log "failed to create DMS templates"
    fi
}

# create configuration index
_create_configuration_index() {
    # create index if it does not exist.
    set +e
    set -x
    $CURL -I ${ES_ENDPOINT}/${CONFIG_INDEX}
    status=$?
    echo $status
    set +x
    set -e
    if [ 0 -eq $status ]; then
        log "index $CONFIG_INDEX exists"
    else
        log "create configuration index"
        set -x
        $CURL -XPUT ${ES_ENDPOINT}/${CONFIG_INDEX}?pretty  -d'
        {
            "settings" : {
                "index" : {
                    "number_of_shards" : 1,
                    "number_of_replicas" : 2
                }
            }
        }'
        status=$?
        set +x
        if [ 0 -eq $status ]; then
            log "create configuration index successfully"
        else
            log "failed to create configuration index. ${CONFIG_INDEX} may exist already."
        fi
    fi
}

_create_navigation_kibana_index() {
    log "update kibana index for navigation"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/index-pattern/navigation?pretty -d@${TEMPLATE_PATH}/navigation_field_update.data
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "update kibana index for navigation successfully"
    else
        log "failed to update kibana index for navigation"
    fi
}

# create kibana index for configuration 
_create_configuration_kibana_index() {
    log "create index for configuration"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/index-pattern/${CONFIG_INDEX}?pretty -d@${TEMPLATE_PATH}/configuration-field-update.data
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "create kibana index for configuration successfully"
    else
        log "failed to create kibana index for configuration"
    fi
}

# create kibana index for journal
_create_journal_kibana_index() {
    log "create index for ingest log entries"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/index-pattern/${JOURNAL_INDEX}?pretty -d@${TEMPLATE_PATH}/journal-field-update.data
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "create kibana index for journal successfully"
    else
        log "failed to create kibana index for journal"
    fi
}


# create kibana index for raw drive
_create_raw_drive_kibana_index() {
    log "create index for raw drive"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/index-pattern/${RAW_INDEX}?pretty -d@${TEMPLATE_PATH}/raw-drive-field-update.data
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "create kibana index for raw drive successfully"
    else
        log "failed to create kibana index for raw drive"
    fi
}

# create kibana index for perm data
_create_perm_kibana_index() {
    log "create index for perm data"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/index-pattern/${PERM_INDEX}?pretty -d@${TEMPLATE_PATH}/perm-field-update.data
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "create kibana index for perm data successfully"
    else
        log "failed to create kibana index for perm data"
    fi
}

# create kibana index for resim output
_create_resim_kibana_index() {
    log "create index for resim output"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/index-pattern/${RESIM_INDEX}?pretty -d@${TEMPLATE_PATH}/resim-field-update.data
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "create kibana index for resim outpu successfully"
    else
        log "failed to create kibana index for resim output"
    fi
}


_set_kibana_default_index() {
    log "set kibana default index"
    set -x
    $CURL -XPUT ${ES_ENDPOINT}/.kibana/config/${ES_VERSION}?pretty -d '{"defaultIndex" : "'"${CONFIG_INDEX}"'"}'
    status=$?
    set +x
    if [ 0 -eq $status ]; then
        log "set kibana default index successfully"
    else
        log "failed to kibana default index for navigation"
    fi
}

_import_kibana_visualization() {
    log "import kibana visualization"
    cd ${VISUALIZATION_PATH}
    for i in `ls -1`; do
        local fname=`basename $i .json`
        set -x
        $CURL -XPUT ${ES_ENDPOINT}/.kibana/visualization/${fname}?pretty -d@$i
        status=$?
        set +x
        if [ 0 -ne $status ]; then
            log "failed to import kibana visualization"
            return
        fi
    done
    log "import kibana visualization successfully"
}

_import_kibana_search() {
    log "import kibana search"
    cd ${SEARCH_PATH}
    for i in `ls -1`; do
        local fname=`basename $i .json`
        set -x
        $CURL -XPUT ${ES_ENDPOINT}/.kibana/search/${fname}?pretty -d@$i
        status=$?
        set +x
        if [ 0 -ne $status ]; then
          log "failed to import kibana search"
          return
        fi
    done
    log "import kibana search successfully"
}

_import_kibana_dashboard() {
    log "import kibana dashboard"
    cd ${DASHBOARD_PATH}
    for i in `ls -1`; do
        local fname=`basename $i .json`
        set -x
        $CURL -XPUT ${ES_ENDPOINT}/.kibana/dashboard/${fname}?pretty -d@$i
        status=$?
        set +x
        if [ 0 -ne $? ]; then
          log "failed to import kibana dashboard"
          return
        fi
    done
    log "import kibana dashboard successfully"
}

_create_cluster_configuration() {
    log "create cluster configuration"
    #for i in `seq 1 3`
    #do 
        set -x
        set +u
        #cluster_prefix=islp0000
        #domain=${ENT_DOMAIN:-solarch.lab.emc.com}
        #nfs_prefix=${NFS_PREFIX:-nfs.${cluster_prefix}}
        #smb_prefix=${SMB_PREFIX:-smb.${cluster_prefix}}
        #nfs_host=${nfs_prefix}${i}.${domain}
        #smb_host=${smb_prefix}${i}.${domain}
        set -u
        dms_utils $ES_LOGIN cluster_create --nfs-host=10.35.106.54  --smb-host=10.35.106.54  --cluster-id=DMSPOC2
        dms_utils $ES_LOGIN cluster_create --nfs-host=10.35.106.35  --smb-host=10.35.106.35  --cluster-id=DMSPOC
        #dms_utils $ES_LOGIN cluster_create --nfs-host=n112.solarch.lab.emc.com --smb-host=n112.solarch.lab.emc.com --cluster-id=hop-isi-l
        status=$?
        set +x
        if [ 0 -ne $status ]; then
            log "failed to create cluster configuration"
            return
        fi
    #done
    log "create cluster configuration successfully"
}

