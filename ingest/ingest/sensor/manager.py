import logging
import os
import time
from queue import Queue
from random import shuffle

from dmsclient.exceptions import DMSClientException
from dmsclient.models.cartridge import Cartridge
from dmsclient.models.drive import Drive
from ingest import util
from ingest.exceptions import EgestTruncatedError
from ingest.manager import AbstractIngestManager
from ingest.sensor.egest_worker import EgestSensorWorker
from ingest.sensor.ingest_worker import IngestSensorWorker


class SensorManager(AbstractIngestManager):
    def __init__(self, config, mount_path, reader_id, cartridge_id):
        super(SensorManager, self).__init__(config, mount_path, reader_id, cartridge_id)
        self.log = logging.getLogger('ingest.sensor.manager')
        self.ingest_dir = config['sensor_mode']['ingest_directory']
        self.egest_dir = config['sensor_mode']['egest_directory']
        self.sensor_type = config['sensor_mode']['sensor_type']

        # set cartridge workflow type based on the sensor mode
        workflow_type = Cartridge.WorkflowType.FLC_INGESTION \
            if self.__is_ingest_mode() else Cartridge.WorkflowType.FLC_EGESTION
        self.set_cartridge_workflow_type(cartridge_id, workflow_type)

        if self.check_mountpoints:
            self.log.info("Checking mount points")
            try:
                for cluster in self.client.hashring.get_instances():
                    for mount in [cluster.perm_mount, cluster.resim_mount]:
                        if not util.is_mounted(mount):
                            raise DMSClientException("'{}' is not mounted".format(str(mount)))
            except Exception as e:
                self.log.error('Error checking the mount points', e)
                raise e

    def __is_ingest_mode(self):
        ingest_path = os.path.join(self.mount_path, self.ingest_dir)
        return os.path.exists(ingest_path) and len(os.listdir(ingest_path)) > 0

    def run(self):
        # Create a single input and a single error queue for all threads
        input_q = Queue()
        error_q = Queue()

        if self.__is_ingest_mode():
            self.log.info("Ingesting sensor data")
            self.update_reader("Starting FLC ingestion")
            worker_class = IngestSensorWorker
            ingest_path = os.path.join(self.mount_path, self.ingest_dir)
            self.log.info("Scanning source directory '%s'" % (ingest_path,))

            files = []
            g = os.walk(ingest_path)
            for root, d, f in g:
                if d:
                    continue
                for file in f:
                    files.append(os.path.join(root, file))

            self.log.info("Found %s files" % (len(files),))
            elements = list(map(lambda x: os.path.join(ingest_path, x), files))
        else:
            self.log.info("Egesting sensor data")
            self.update_reader("Starting FLC egestion")
            worker_class = EgestSensorWorker
            self.log.info("Looking for eligible Drives (flc_state: '%s')" % ('ready',))
            elements = list(self.client.drives.find_by_fields(flc_state=Drive.FLCState.READY))
            shuffle(elements)  # shuffle list so that different ingest processes ship drives in a different order
            self.log.info("Found %d drives" % (len(elements)))
            self.thread_count = min(2, self.thread_count)  # use a maximum of 2 copy threads for egest
            egest_path = os.path.join(self.mount_path, self.egest_dir)
            os.makedirs(egest_path, exist_ok=True)

        # Create the thread pool
        self.log.info("Creating %d worker threads" % (self.thread_count,))
        pool = [worker_class(self.config, self.mount_path, self.client, input_q, error_q)
                for _ in range(self.thread_count)]

        # Start all threads
        for worker in pool:
            worker.daemon = True
            worker.start()

        # Give each worker an element to process
        for e in elements:
            input_q.put(e)

        # Wait until the workers have finished
        processed_elements = -1
        while not input_q.empty():
            if len(elements) - input_q.qsize() != processed_elements:
                processed_elements = len(elements) - input_q.qsize()
                self.update_reader("%s in progress (processed: %d, total: %d)" % (self.mode(), processed_elements, len(elements)))
            time.sleep(10)

        # Ask threads to die and wait for them to do it
        for worker in pool:
            worker.join()

        # Check if there were errors
        errors = []
        while not error_q.empty():
            element, error = error_q.get()
            errors.append("'%s'. Error: %s" % (element, error))
            error_q.task_done()

        truncated = False
        if self.__is_ingest_mode():
            self.log.info("Purging ingest directory...")
            # Purge ingest directory recursively
            ingest_path = os.path.join(self.mount_path, self.ingest_dir)
            for r, x, y in os.walk(ingest_path, topdown=False):
                if r == ingest_path:
                    continue
                try:
                    os.rmdir(r)
                except OSError:
                    # Directory not empty
                    pass
        else:
            if len(errors) > 0:
                # Check if all errors are due to not enough space in disk
                errors = list(filter(lambda e: type(e) != EgestTruncatedError, errors))
                truncated = len(errors) == 0

        message = "%s done (total: %d, errors: %d)" % (self.mode(), len(elements), len(errors),)
        if truncated:
            message += " (truncated)"

        self.update_reader(message)
        self.log.info(message)

        if len(errors) > 0:
            raise Exception('Ingestion failed with the following errors: %s' % (str(errors),))

    def mode(self):
        return "FLC Ingestion" if self.__is_ingest_mode() else "FLC Egestion"