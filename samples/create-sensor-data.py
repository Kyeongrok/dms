#!/usr/bin/env python3
import configparser
import os
import subprocess
import sys

import click

from dmsclient.client import DMSClient
from dmsclient.exceptions import DMSClientException
from dmsclient.models.drive import Drive


class Config(object):
    def __init__(self, config_file, config):
        self.config_file = config_file
        self.config = config


@click.command()
@click.option('--config-file', '-c', default='/opt/dms/conf/ingest.conf',
              help='Path to the configuration file containing ingest configuration',
              type=click.Path(exists=True))
@click.option('--sensor-type',
              default='FLC',
              help='Sensor type to create')
@click.pass_context
def main(ctx, config_file, sensor_type):
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

    print("Looking for 'copied' drives")
    drives = list(client.drives.find_by_fields(state='copied'))

    print("Found %s drives" % (len(drives)))

    for drive in drives:
        print("[Drive '%s'] Processing...")
        files = [f for f in os.listdir(drive.target_path) if os.path.isfile(os.path.join(drive.target_path, f))]
        sequence = 1
        for filename in files:
            try:
                segment_id, _ = os.path.splitext(filename)
                print("[Drive '%s'] Creating segment '%s' (sequence: %d)" % (drive.drive_id, segment_id, sequence))
                segment = client.segments.create_from_drive(segment_id, sequence, drive)
                sequence += 1
                os.makedirs(segment.perm_path, exist_ok=True)
            except DMSClientException as e:
                if e.status_code != 409:
                    raise e
            except Exception as e:
                print("[Drive '%s'] Error in segment '%s': %s" % (drive.drive_id, filename, e))
                sys.exit(1)
        client.drives.set_fields(drive.id, flc_state=Drive.FLCState.READY)

    # Create sensor documents
    print("Looking for 'created' segments")
    segments = list(client.segments.find_by_fields(state='created'))
    print("Found %s segments" % (len(segments)))

    for segment in segments:
        print("[Segment '%s'] Creating sensor file" % (segment.segment_id,))
        filename = ''.join([segment.segment_id, '_', sensor_type, '.dat'])
        try:
            sensor = client.sensors.create_from_filename(filename)
        except DMSClientException as e:
            if e.status_code != 409:
                raise e
            sensor = list(client.sensors.find_by_segment_id(segment.segment_id))[0]
        path = os.path.join(sensor.perm_path, filename)
        subprocess.call("dd if=/dev/urandom of=%s bs=1M count=10" % (path,), shell=True)


if __name__ == '__main__':
    main()
