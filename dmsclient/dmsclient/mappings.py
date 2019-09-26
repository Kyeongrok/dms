import copy
from dmsclient.models.asdmoutput import AsdmOutput
from dmsclient.models.cartridge import Cartridge
from dmsclient.models.cluster import Cluster
from dmsclient.models.drive import Drive
from dmsclient.models.journal import Journal
from dmsclient.models.reader import Reader
from dmsclient.models.usbreader import USBReader
from dmsclient.models.scenario import Scenario
from dmsclient.models.segment import Segment
from dmsclient.models.sensor import Sensor
from dmsclient.models.sensorversion import SensorVersion
from dmsclient.templates import Templates
from dmsclient.indices import Indices

DYNAMIC_TEMPLATES = {
    'dynamic_templates': [
        {
            'suffix_long': {
                'match':   '*_long',
                'match_mapping_type': '*',
                'mapping': {'type': 'long'}
            }
        },
        {
            'suffix_int': {
                'match':   '.*(_int|_integer)$',
                'match_pattern': 'regex',
                'match_mapping_type': '*',
                'mapping': {'type': 'integer'}
            }
        },
        {
            'suffix_float': {
                'match':   '*_float',
                'match_mapping_type': '*',
                'mapping': {'type': 'float'}
            }
        },
        {
            'suffix_date': {
                'match':   '*_date',
                'match_mapping_type': '*',
                'mapping': {'type': 'date'}
            }
        },
        {
            'suffix_bool': {
                'match':   '.*(_bool|_boolean)$',
                'match_pattern': 'regex',
                'match_mapping_type': '*',
                'mapping': {'type': 'boolean'}
            }
        },
        {
            'suffix_kw': {
                'match':   '.*(_kw|_keyword)$',
                'match_pattern': 'regex',
                'match_mapping_type': '*',
                'mapping': {'type': 'keyword'}
            }
        },
        {
            'suffix_text': {
                'match':   '*_text',
                'match_mapping_type': '*',
                'mapping': {'type': 'text'}
            }
        },
        {
            'suffix_byte': {
                'match':   '*_byte',
                'match_mapping_type': '*',
                'mapping': {'type': 'byte'}
            }
        },
        {
            'suffix_double': {
                'match':   '*_double',
                'match_mapping_type': '*',
                'mapping': {'type': 'double'}
            }
        },
        {
            'suffix_short': {
                'match':   '*_short',
                'match_mapping_type': '*',
                'mapping': {'type': 'short'}
            }
        }
    ]
}

BASE_MAPPINGS = {
    Indices.INDEX_CONFIG: {
        'template': Templates.TEMPLATE_CONFIG,
        'mappings': {
            Cluster.DOC_TYPE: {
                'properties': {
                    'cluster_id': {'type': 'keyword'},
                    'weight': {'type': 'float'},
                    'available': {'type': 'boolean'},
                    'updated_at': {'type': 'date'},
                    'raw_export': {'type': 'keyword'},
                    'perm_export': {'type': 'keyword'},
                    'resim_export': {'type': 'keyword'},
                    'output_export': {'type': 'keyword'},
                    'useroutput_export': {'type': 'keyword'},
                    'raw_mount': {'type': 'keyword'},
                    'perm_mount': {'type': 'keyword'},
                    'resim_mount': {'type': 'keyword'},
                    'output_mount': {'type': 'keyword'},
                    'useroutput_mount': {'type': 'keyword'},
                    'raw_share': {'type': 'keyword'},
                    'perm_share': {'type': 'keyword'},
                    'resim_share': {'type': 'keyword'},
                    'output_share': {'type': 'keyword'},
                    'useroutput_share': {'type': 'keyword'},
                    'nfs_host': {'type': 'keyword'},
                    'smb_host': {'type': 'keyword'},
                }
            },
            Reader.DOC_TYPE: {
                'properties': {
                    'reader_id': {'type': 'keyword'},
                    'hostname': {'type': 'keyword'},
                    'device': {'type': 'keyword'},
                    'mount': {'type': 'keyword'},
                    'port': {'type': 'keyword'},
                    'status': {'type': 'keyword'},
                    'ingest_state': {'type': 'keyword'},
                    'updated_at': {'type': 'date'}
                }
            },
            USBReader.DOC_TYPE: {
                'properties': {
                    'reader_id': {'type': 'keyword'},
                    'hostname': {'type': 'keyword'},
                    'device': {'type': 'keyword'},
                    'mount': {'type': 'keyword'},
                    'port': {'type': 'keyword'},
                    'ingest_state': {'type': 'keyword'},
                    'mount_state': {'type': 'keyword'},
                    'updated_at': {'type': 'date'}
                }
            },
            Cartridge.DOC_TYPE: {
                'properties': {
                    'cartridge_id': {'type': 'keyword'},
                    'device': {'type': 'keyword'},
                    'ingest_station': {'type': 'keyword'},
                    'usage': {'type': 'double'},
                    'slot': {'type': 'keyword'},
                    'workflow_type': {'type': 'keyword'},
                    'ingest_state': {'type': 'keyword'},
                    'updated_at': {'type': 'date'}
                }
            }

        }
    },
    Indices.INDEX_RAW: {
        'template': Templates.TEMPLATE_RAW,
        'settings': {
            'number_of_shards': Templates.SHARDS_RAW,
            'number_of_replicas': Templates.REPLICAS_RAW
        },
        'mappings': {
            Drive.DOC_TYPE: {
                'properties': {
                    'drive_id': {'type': 'keyword'},
                    'car_id': {'type': 'keyword'},
                    'project_name': {'type': 'keyword'},
                    'cluster_id': {'type': 'keyword'},
                    'ingest_station': {'type': 'keyword'},
                    'logged_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                    'nfs_host': {'type': 'keyword'},
                    'smb_host': {'type': 'keyword'},
                    'raw_export': {'type': 'keyword'},
                    'smb_share': {'type': 'keyword'},
                    'source_path': {'type': 'keyword'},
                    'target_path': {'type': 'keyword'},
                    'state': {'type': 'keyword'},
                    'flc_state': {'type': 'keyword'},
                    'size': {'type': 'long'},
                    'file_count': {'type': 'integer'},
                    'ingest_duration': {'type': 'integer'},
                    # 'tags': {'type': 'keyword'},
                }
            }
        }
    },
    Indices.INDEX_JOURNAL_PREFIX: {
        'template': Templates.TEMPLATE_JOURNAL,
        'mappings': {
            Journal.DOC_TYPE: {
                'properties': {
                    'context': {'type': 'keyword'},
                    'ingest_station': {'type': 'keyword'},
                    'log_level': {'type': 'keyword'},
                    'message': {'type': 'text'},
                    'tags': {'type': 'text'},
                    'updated_at': {'type': 'date'},
                }
            }
        }
    },
    Indices.INDEX_RESIM_PREFIX: {
        'template': Templates.TEMPLATE_RESIM,
        'settings': {
            'number_of_shards': Templates.SHARDS_RESIM,
            'number_of_replicas': Templates.REPLICAS_RESIM
        },
        'mappings': {
            Segment.DOC_TYPE: {
                'properties': {
                    'segment_id': {'type': 'keyword'},
                    'sequence': {'type': 'integer'},
                    'drive_id': {'type': 'keyword'},
                    'project_name': {'type': 'keyword'},
                    'car_id': {'type': 'keyword'},
                    'cluster_id': {'type': 'keyword'},
                    'index': {'type': 'keyword'},
                    'started_at': {'type': 'date'},
                    'ended_at': {'type': 'date'},
                    'created_at': {'type': 'date'},
                    'state': {'type': 'keyword'},
                    'nfs_host': {'type': 'keyword'},
                    'smb_host': {'type': 'keyword'},
                    'perm_share': {'type': 'keyword'},
                    'output_share': {'type': 'keyword'},
                    'resim_share': {'type': 'keyword'},
                    'perm_export': {'type': 'keyword'},
                    'output_export': {'type': 'keyword'},
                    'resim_export_': {'type': 'keyword'},
                    'perm_path': {'type': 'keyword'},
                    'output_path': {'type': 'keyword'},
                    'resim_path': {'type': 'keyword'},
                    # Mappings below were requested by Zenuity in issue #223
                    'Weather': {'type': 'keyword'},
                    'Temperature': {'type': 'float'},
                    'TimeOfDay': {'type': 'keyword'},
                    'Country': {'type': 'keyword'},
                    'SpeedLimit': {'type': 'integer'},
                    'Distance': {'type': 'float'},
                    'VelocityMax': {'type': 'float'},
                    'VelocityMin': {'type': 'float'},
                    'VelocityMean': {'type': 'float'},
                    'LatitudeMax': {'type': 'float'},
                    'LatitudeMin': {'type': 'float'},
                    'LongitudeMax': {'type': 'float'},
                    'LongitudeMin': {'type': 'float'},
                    'AltitudeMax': {'type': 'float'},
                    'AltitudeMin': {'type': 'float'},
                    'TimeLogged': {'type': 'date'},
                    'raw_vpcap_size': {'type': 'float'},
                    'is_first_segment': {'type': 'boolean'},
                    'is_last_segment': {'type': 'boolean'},
                }
            },
            Sensor.DOC_TYPE: {
                'properties': {
                    'sensor_id': {'type': 'keyword'},
                    'segment_id': {'type': 'keyword'},
                    'sensor_type': {'type': 'keyword'},
                    'drive_id': {'type': 'keyword'},
                    'project_name': {'type': 'keyword'},
                    'car_id': {'type': 'keyword'},
                    'cluster_id': {'type': 'keyword'},
                    'created_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                    'state': {'type': 'keyword'},
                    'started_at': {'type': 'date'},
                    'ended_at': {'type': 'date'},
                    'perm_path': {'type': 'keyword'},
                    'output_path': {'type': 'keyword'},
                    'resim_path': {'type': 'keyword'},
                }
            },
            SensorVersion.DOC_TYPE: {
                'properties': {
                    'sensorversion_id': {'type': 'keyword'},
                    'version': {'type': 'keyword'},
                    'sensor_type': {'type': 'keyword'},
                    'sensor_id': {'type': 'keyword'},
                    'segment_id': {'type': 'keyword'},
                    'drive_id': {'type': 'keyword'},
                    'created_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                    'state': {'type': 'keyword'},
                    'started_at': {'type': 'date'},
                    'ended_at': {'type': 'date'},
                    'perm_path': {'type': 'keyword'},
                    'output_path': {'type': 'keyword'},
                    'resim_path': {'type': 'keyword'},
                }
            },
            Scenario.DOC_TYPE: {
                'properties': {
                    'name': {'type': 'keyword'},
                    'user': {'type': 'keyword'},
                    'query': {'type': 'keyword'},
                    'sensor_versions': {
                        'type': 'nested',
                        'properties': {
                            'sensor': {'type': 'keyword'},
                            'version': {'type': 'keyword'}
                        }
                    },
                    # 'scenario_segments': {'type': 'array'},
                    'created_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                    'started_at': {'type': 'date'},
                    'ended_at': {'type': 'date'},
                    'state': {'type': 'keyword'},
                    'cpu_time': {'type': 'integer'},
                    'output_path': {'type': 'keyword'},
                }
            },
            AsdmOutput.DOC_TYPE: {
                'properties': {
                    'asdmoutput_id': {'type': 'keyword'},
                    'segment_id': {'type': 'keyword'},
                    'sensor_versions': {
                        'type': 'nested',
                        'properties': {
                            'sensor': {'type': 'keyword'},
                            'version': {'type': 'keyword'}
                        }
                    },
                    'asdm_version': {'type': 'keyword'},
                    'cluster_id': {'type': 'keyword'},
                    'created_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                    'nfs_host': {'type': 'keyword'},
                    'smb_host': {'type': 'keyword'},
                    'dat_file': {'type': 'keyword'},
                    'mat_file': {'type': 'keyword'},
                    'smb_share': {'type': 'keyword'},
                    'path': {'type': 'keyword'}
                }
            }
        }
    }
}

MAPPINGS = copy.deepcopy(BASE_MAPPINGS)

for k, v in MAPPINGS.items():
    MAPPINGS[k]['mappings']['_default_'] = DYNAMIC_TEMPLATES
