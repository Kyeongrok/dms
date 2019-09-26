import os
import random
import shutil
import subprocess

import time
from retrying import retry

from dmsclient.exceptions import DMSDocumentNotFoundError
from dmsclient.models.drive import Drive
from dmsclient.models.sensor import Sensor
from ingest import util
from ingest.exceptions import EgestTruncatedError, IngestException
from ingest.sensor.abstract_worker import AbstractSensorWorker


class EgestSensorWorker(AbstractSensorWorker):
    def __init__(self, *args, **kwargs):
        super(EgestSensorWorker, self).__init__(*args, **kwargs)

    def process(self, drive):
        self.log.info("[%s] Processing drive '%s'" % (self.getName(), drive.drive_id,))

        # Sleep for some time to minimize conflicts with other processes
        time.sleep(random.randint(0, 30))

        try:
            # Get state again to verify it has not been processed by another ingest process
            flc_state = self.client.drives.get(drive.id).flc_state
            if flc_state != Drive.FLCState.READY:
                self.log.info("[%s] Skipping sensor '%s' with unexpected state '%s' (changed by another process)"
                              % (self.getName(), drive.id, flc_state))
                return

            self.client.drives.set_fields(drive.id, flc_state=Drive.FLCState.SHIPPING)

            self.egest_drive(drive)

            self.client.drives.set_fields(drive.id, flc_state=Drive.FLCState.SHIPPED)

        except EgestTruncatedError as e:
            # Drive not processed (disk is full)
            # Change flc_state back to ready to be egested to another cartridge
            self.client.drives.set_fields(drive.id, flc_state=Drive.FLCState.READY)
            raise e
        except Exception as e:
            self.client.drives.set_fields(drive.id, flc_state=Drive.FLCState.SHIPPING_FAILED)
            raise e

    def egest_drive(self, drive):
        # obtain all drive segments and associated FLC sensor documents
        segments = self.client.segments.find_by_fields(drive_id=drive.drive_id)
        sensors = []
        total_size = 0
        for segment in segments:
            try:
                sensor = self.client.sensors.get(segment.id + '_FLC')
            except DMSDocumentNotFoundError:
                self.log.warn("[%s] Could not find sensor document for segment '%s'"
                              % (self.getName(), segment.id))
                continue
            if sensor.state != Sensor.State.CREATED:
                raise IngestException("[%s] Error with sensor '%s': State is '%s'"
                                      % (self.getName(), sensor.sensor_id, sensor.state))
            try:
                sensor_path = self.get_sensor_path(sensor)
                file_size = os.path.getsize(sensor_path)
                total_size += file_size
            except OSError as e:
                raise IngestException("[%s] Error with sensor '%s': %s"
                                      % (self.getName(), sensor.sensor_id, e))
            sensors.append(sensor)

        if len(sensors) == 0:
            raise IngestException("[%s] Drive '%s' failed shipping. No sensor documents to egest."
                                  % (self.getName(), drive.id))

        self.log.info("[%s] Found %d sensor documents for drive '%s'."
                      % (self.getName(), len(sensors), drive.id))

        free_space = util.get_free_space(self.mount_path)
        if max(self.min_disk_space, total_size) > free_space:
            # Not enough space available. Skipping...
            self.log.info("[%s] Skipping drive '%s'. Not enough free space in disk (%d B free)."
                          % (self.getName(), drive.id, free_space))
            raise EgestTruncatedError()

        try:
            for sensor in sensors:
                self.copy_sensor(sensor)
        except Exception as e:
            self.log.error("[%s] Drive '%s' failed shipping. Error: %s" % (self.getName(), drive.id, e))
            raise e
        return

    def get_sensor_path(self, sensor):
        source_dir = sensor.perm_path
        if not os.path.exists(source_dir):
            raise IngestException("[%s] Perm directory does not exist '%s'"
                                  % (self.getName(), source_dir,))

        def filter_file(name):
            if name == sensor.sensor_id + '.dat':
                return True
            # Recreate the sensor_id in case it had the old format (dash instead of underscore)
            return name == ''.join([sensor.segment_id, '_', sensor.sensor_type, '.dat'])

        files = os.listdir(source_dir)
        files_filter = list(filter(filter_file, files))
        if len(files_filter) == 0:
            raise IngestException("[%s] Sensor file not found in directory '%s'"
                                  % (self.getName(), source_dir,))

        filename = files_filter[0]
        source_path = os.path.join(source_dir, filename)
        return source_path

    def copy_sensor(self, sensor):
        source_path = self.get_sensor_path(sensor)
        path_list = os.path.normpath(sensor.perm_path).split(os.path.sep)
        try:
            path_list = path_list[path_list.index('perm') - 1:]
        except ValueError:
            raise IngestException("[%s] Could not build destination path (sensor.perm_path='%s')"
                                  % (self.getName(), sensor.perm_path))

        dest_dir = os.path.join(self.mount_path, self.egest_dir, *path_list)
        dest_path = os.path.join(dest_dir, sensor.id + '.dat')

        os.makedirs(dest_dir, exist_ok=True)

        self.log.info("[%s] Copying sensor '%s' from '%s' to '%s" % (self.getName(),
                                                                     sensor.sensor_id,
                                                                     source_path,
                                                                     dest_path))
        self.__copy_data(source_path, dest_path)

        self.log.info("[%s] Sensor '%s' copied successfully" % (self.getName(), sensor.sensor_id))

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def __copy_data(self, source_path, dest_path):
        shutil.copyfile(source_path, dest_path)
