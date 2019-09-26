#!/bin/bash
########################################################################
# Boot script to configure Elasticsearch for Data Management System
########################################################################

set -ue

#BOOT_LOCATION=$( cd ${0%/*} && pwd -P )
BOOT_LOCATION=$( cd "$(dirname "$0")" && pwd -P )
source ${BOOT_LOCATION}/boot_lib.sh

log "############################### boot operation begin ############################"


log "Verify connection to Elasticsearch"
_validate_environment
log "All validations are complete. Going ahead with the configuration steps."

log "Enable dynamic mappings"
_enable_dynamic_mapping

log "Create navigation template"
_create_navigation_template

log "Load navigation category"
_create_navigation_category

log "Create DMS templates"
_create_dms_template

log "Create configuration index"
_create_configuration_index

log "Create kibana index for navigation"
_create_navigation_kibana_index

log "Create Kibana index for configuration"
_create_configuration_kibana_index

log "Create Kibana index for journal"
_create_journal_kibana_index

log "Create Kibana index for raw drive"
_create_raw_drive_kibana_index

log "Create Kibana index for resim output"
_create_resim_kibana_index

log "Set default Kibana index"
_set_kibana_default_index

log "Load Kibana visulization"
_import_kibana_visualization

log "Load Kibana search"
_import_kibana_search

log "Load Kibana dashboard"
_import_kibana_dashboard

#log "Create cluster configuration"
_create_cluster_configuration
