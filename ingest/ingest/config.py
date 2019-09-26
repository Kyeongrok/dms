import logging
import os
import time

import yaml
from click_configfile import ConfigFileReader, Param, SectionSchema
from click_configfile import matches_section

from ingest import PACKAGE_ROOT


def setup_logging(
        default_path=os.path.join(PACKAGE_ROOT, 'config', 'logging.yaml'),
        default_level=logging.INFO,
        env_key='LOG_CFG'):
    """Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

    # Set logging time to UTC
    logging.Formatter.converter = time.gmtime


class ConfigSectionSchema(object):
    """Describes all config sections of this configuration file."""

    @matches_section("general")
    class General(SectionSchema):
        rsync_args = Param(type=str, default='-rlptDv')
        ignore_directories = Param(type=str, multiple=True, default=[])
        fail_if_parse_error = Param(type=bool, default=False)
        check_mountpoints = Param(type=bool, default=True)
        threads = Param(type=int, default=4)
        log_to_es = Param(type=bool, default=False)

    @matches_section("sensor_mode")
    class SensorMode(SectionSchema):
        enabled = Param(type=bool, default=False)
        egest_directory = Param(type=str, default='egest')
        ingest_directory = Param(type=str, default='ingest')
        sensor_type = Param(type=str, default='FLC')
        min_disk_space = Param(type=int, default=107374182400)  # 100 GB

    @matches_section("elasticsearch")
    class Elasticsearch(SectionSchema):
        endpoint = Param(type=str, default='http://127.0.0.1:9200')
        user = Param(type=str, default='elastic')
        password = Param(type=str, default='changeme')
        create_templates = Param(type=bool, default=False)
        verify_templates = Param(type=bool, default=False)


class ConfigFileProcessor(ConfigFileReader):
    config_files = []
    config_section_schemas = [
        ConfigSectionSchema.General,
        ConfigSectionSchema.SensorMode,
        ConfigSectionSchema.Elasticsearch,
    ]

    @classmethod
    def get_storage_name_for(cls, section_name):
        return section_name
