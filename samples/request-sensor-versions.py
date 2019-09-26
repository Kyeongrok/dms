#!/usr/bin/env python3
import configparser
import os
import subprocess
from random import randint

import click

from dmsclient.client import DMSClient


class Config(object):
    def __init__(self, config_file, config):
        self.config_file = config_file
        self.config = config


@click.command()
@click.option('--config-file', '-c', default='/opt/dms/conf/ingest.conf',
              help='Path to the configuration file containing ingest configuration',
              type=click.Path(exists=True))
@click.option('--ingest-dir',
              help='Path to the sensor ingest directory',
              type=click.Path(exists=True))
@click.pass_context
def main(ctx, config_file, ingest_dir):
    """Helper to create fake sensor data and sensorversion documents based on current drives"""
    config = configparser.ConfigParser()
    config.read(config_file)
    ctx.obj = Config(config_file, config)

    es_endpoint = config['elasticsearch']['endpoint']
    es_username = config['elasticsearch']['user']
    es_password = config['elasticsearch']['password']
    client = DMSClient(es_endpoint=es_endpoint,
                       es_user=es_username,
                       es_password=es_password,
                       create_templates=False,
                       verify_templates=False,
                       initial_sync=False)

    print("Looking for 'shipped' sensors")
    sensors = client.sensors.find_by_fields(state='shipped')

    for sensor in sensors:
        sv = client.sensors.create_version(sensor, str(randint(1, 9999)).zfill(4))
        print("Requesting sensor version '%s' (version: %s)" % (sv.sensorversion_id, sv.version))

        path_list = os.path.normpath(sv.resim_path).split(os.path.sep)[-6:]
        dir_path = os.path.join(ingest_dir, *path_list)
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, sv.sensorversion_id + '.dat')
        subprocess.call("dd if=/dev/urandom of=%s bs=1M count=10" % (path,), shell=True)
        client.sensors.update_version(sv.sensor_id, sv.version, state='requested')

if __name__ == '__main__':
    main()
