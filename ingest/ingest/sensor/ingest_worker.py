import os
import shutil
import subprocess

from retrying import retry

from dmsclient.exceptions import DMSDocumentNotFoundError
from ingest.sensor.abstract_worker import AbstractSensorWorker
from ingest.util import sensorversionid_to_sensorid


class IngestSensorWorker(AbstractSensorWorker):
    def __init__(self, *args, **kwargs):
        super(IngestSensorWorker, self).__init__(*args, **kwargs)

    def process(self, path):
        self.log.info("[%s] Ingesting sensor file '%s'" % (self.getName(), path,))
        filename = os.path.basename(path)
        sensorversion_id = os.path.splitext(filename)[0]
        try:
            sensor_id, version = sensorversionid_to_sensorid(sensorversion_id)
        except Exception as e:
            raise Exception("Could not parse sensor version '%s'. Error: %s" % (sensorversion_id, str(e)))

        try:
            sensorversion = self.client.sensors.get_version(sensor_id, version)
        except DMSDocumentNotFoundError:
            self.log.info("[%s] SensorVersion with ID '%s' not found. Creating it..."
                          % (self.getName(), sensorversion_id,))
            sensorversion = self.client.sensors.create_version_from_filename(filename)

        try:
            os.makedirs(sensorversion.resim_path, exist_ok=True)

            dest_path = os.path.join(sensorversion.resim_path, filename)
            self.log.info('[{}] Copying sensorversion {} from {} to {}'.format(self.getName(),
                                                                               sensorversion_id,
                                                                               path,
                                                                               dest_path))
            self.__copy_data(path, dest_path)
            self.client.sensors.update_version(sensor_id, version, state='completed')
            os.remove(path)
            self.log.info("Removed sensorversion file '{}'".format(path))
            self.log.info("Sensorversion '{}' copied successfully".format(sensorversion_id))
        except Exception as e:
            self.log.error("Sensorversion '%s' failed. Error: %s" % (sensorversion_id, e))
            self.client.sensors.update_version(sensor_id, version, state='failed')
            raise e

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def __copy_data(self, source_path, dest_path):
        shutil.copyfile(source_path, dest_path)
