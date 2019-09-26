import abc
import logging
import threading
from queue import Empty


class AbstractSensorWorker(abc.ABC, threading.Thread):

    def __init__(self, config, mount_path, client, input_q, error_q):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('ingest.sensor.worker')
        self.ingest_dir = config['sensor_mode']['ingest_directory']
        self.egest_dir = config['sensor_mode']['egest_directory']
        self.min_disk_space = config['sensor_mode']['min_disk_space']
        self.rsync_args = config['general']['rsync_args']
        self.mount_path = mount_path
        self.input_q = input_q
        self.error_q = error_q
        self.stoprequest = threading.Event()
        self.client = client

    def join(self, timeout=None):
        self.stoprequest.set()
        super(AbstractSensorWorker, self).join(timeout)

    def run(self):
        while not self.stoprequest.isSet():
            try:
                instance = self.input_q.get(True, 0.05)

                try:
                    self.process(instance)
                except Exception as e:
                    self.error_q.put((instance, e))

                self.input_q.task_done()
            except Empty:
                continue

    @abc.abstractmethod
    def process(self, instance):
        pass
