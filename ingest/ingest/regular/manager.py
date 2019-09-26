import time
from queue import Queue

import logging

from dmsclient.models.cartridge import Cartridge
from dmsclient.exceptions import DMSClientException
from ingest.manager import AbstractIngestManager
from ingest.regular.worker import RegularWorker

from ingest import util


class RegularIngestManager(AbstractIngestManager):
    def __init__(self, config, mount_path, reader_id, cartridge_id):
        super(RegularIngestManager, self).__init__(config, mount_path, reader_id, cartridge_id)
        self.log = logging.getLogger('ingest.regular.manager')

        # set cartridge workflow type for regular ingestion
        self.set_cartridge_workflow_type(cartridge_id, Cartridge.WorkflowType.INGESTION)

        if self.check_mountpoints:
            self.log.info("Checking mount points")
            try:
                for cluster in self.client.hashring.get_instances():
                    if not util.is_mounted(cluster.raw_mount):
                        raise DMSClientException("'{}' is not mounted".format(str(cluster.raw_mount)))
            except Exception as e:
                self.log.error('Error checking the mount points', e)
                raise e

    def run(self):
        self.log.info("Scanning source directory '%s'" % (self.mount_path,))
        dirs = util.scan_directories(self.mount_path)
        self.log.info("Found %s directories" % (len(dirs),))

        # Create a single input and a single error queue for all threads
        input_q = Queue()
        error_q = Queue()

        # Create the thread pool
        self.log.info("Creating %d worker threads" % (self.thread_count,))
        pool = [RegularWorker(self.config, self.client, input_q, error_q)
                for _ in range(self.thread_count)]

        # Start all threads
        for worker in pool:
            worker.daemon = True
            worker.start()

        # Give each worker a directory to ingest
        for dir_ in dirs:
            if dir_[0] in self.ignore_directories:
                self.log.info("Ignoring directory '%s' based on 'ignore_directories' configuration value" % (dir_[0], ))
                continue
            input_q.put(dir_)

        # Wait until the workers have finished
        processed_elements = -1
        while not input_q.empty():
            if len(dirs) - input_q.qsize() != processed_elements:
                processed_elements = len(dirs) - input_q.qsize()
                self.update_reader("Drive ingestion in progress (%d/%d)" % (processed_elements, len(dirs)))
            time.sleep(10)

        # Ask threads to die and wait for them to do it
        for worker in pool:
            worker.join()

        # Check if there were errors
        errors = []
        while not error_q.empty():
            drive, error = error_q.get()
            errors.append("Drive '%s'. Error: %s" % (drive, error))
            error_q.task_done()

        self.update_reader("Drive ingestion done (total: %d, errors: %d)" % (len(dirs), len(errors)))
        self.log.info("Processed %d directories. Found %d errors" % (len(dirs), len(errors), ))

        if len(errors) > 0:
            raise Exception('Ingestion failed with the following errors: %s' % (str(errors),))
