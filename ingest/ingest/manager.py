import abc
import logging
import os

from dmsclient.client import DMSClient
from dmsclient.exceptions import DMSClientException
from ingest import util
from ingest.logger import ElasticsearchHandler, JournalFormatter


class AbstractIngestManager(abc.ABC):
    def __init__(self, config, mount_path, reader_id, cartridge_id):
        self.log = logging.getLogger('ingest.manager')
        self.config = config
        self.thread_count = config['general']['threads']
        self.check_mountpoints = config['general']['check_mountpoints']
        self.ignore_directories = config['general']['ignore_directories']
        self.log_to_es = config['general']['log_to_es']
        self.mount_path = mount_path
        self.reader_id = reader_id
        self.cartridge_id = cartridge_id
        self.client = DMSClient(es_endpoint=config['elasticsearch']['endpoint'],
                                es_user=config['elasticsearch']['user'],
                                es_password=config['elasticsearch']['password'],
                                create_templates=config['elasticsearch']['create_templates'],
                                verify_templates=config['elasticsearch']['verify_templates'])

        if self.log_to_es:
            handler = ElasticsearchHandler(self.client)
            formatter = JournalFormatter()
            handler.setFormatter(formatter)
            root_logger = logging.getLogger('ingest')
            root_logger.addHandler(handler)

        if not self.mount_path.startswith('rsync://'):
            try:
                self.mount_path = os.path.abspath(self.mount_path)
                self.__check_path(self.mount_path, readwrite=False)
            except Exception as e:
                self.log.error('Error checking the input path. {}'.format(str(e),))
                raise e

    def update_reader(self, message):
        if self.reader_id:
            self.client.readers.set_message(self.reader_id, message)

    def set_cartridge_workflow_type(self, cartridge_id, workflow_type):
        if self.cartridge_id:
            self.client.cartridges.set_workflow_type(self.cartridge_id, workflow_type)

    @abc.abstractmethod
    def run(self):
        pass

    def __check_path(self, path, readwrite=False):
        if path.startswith('rsync://'):
            return

        if readwrite:
            self.log.info("Checking write permissions on path '%s'" % (path,))
            if not util.isWritable(path):
                raise Exception('Cannot write to directory: %s' % (path,))
        else:
            self.log.info("Checking read permissions on path '%s'" % (path,))
            if not util.isReadable(path):
                raise Exception('Cannot read from directory: %s' % (path,))
