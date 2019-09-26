import logging
import os
import socket
import subprocess
import threading
import time
from queue import Empty

from retrying import retry

import dmsclient
import ingest
from dmsclient.exceptions import DMSClientException, DMSInvalidFormat
from ingest import util
from ingest.util import is_mounted


class RegularWorker(threading.Thread):
    def __init__(self, config, client, input_q, error_q):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('ingest.regular.worker')
        self.config = config
        self.input_q = input_q
        self.error_q = error_q
        self.stoprequest = threading.Event()
        self.client = client

    def join(self, timeout=None):
        self.stoprequest.set()
        super(RegularWorker, self).join(timeout)

    def run(self):
        while not self.stoprequest.isSet():
            try:
                dir_name, source_path = self.input_q.get(True, 0.05)
                self.log.info("[%s] Processing directory '%s'" % (self.getName(), dir_name,))

                try:
                    self.process_drive(dir_name, source_path)
                except DMSInvalidFormat as e:
                    if self.config['general']['fail_if_parse_error']:
                        self.error_q.put((dir_name, e))
                    else:
                        self.log.warning("Ignoring invalid directory: %s (%s)" % (dir_name, e))
                except Exception as e:
                    self.error_q.put((dir_name, e))

                self.input_q.task_done()
            except Empty:
                continue

    def process_drive(self, dir_name, source_path):
        start_time = time.time()
        drive = None

        try:
            total_size, file_count = util.get_dir_stats(source_path)
        except Exception as e:
            self.log.warning("[%s] Could not obtain drive size and file count: %s" % (self.getName(), e,))
            total_size, file_count = 0, 0

        hostname = socket.gethostname()

        try:
            drive = self.client.drives.create_from_ingest(
                dir_name=dir_name,
                source_path=source_path,
                ingest_station=hostname,
                size=total_size,
                file_count=file_count,
                ingest_version=ingest.__version__,
                dmsclient_version=dmsclient.__version__,
            )
        except DMSClientException as e:
            if e.status_code != 409:
                raise e

        if not drive:
            drive = self.client.drives.get(dir_name)
            # Need to update the source_path as it can be different from the source_path when it was created
            drive.source_path = source_path
            self.log.info("Drive '{}' (state: '{}') already existed. Reingesting...".format(dir_name, drive.state))

        if not is_mounted(drive.target_path) and self.config['general']['check_mountpoints']:
            self.client.drives.set_state(drive.drive_id, 'copy_failed')
            raise DMSClientException("No mount point found for path '{}'".format(drive.target_path))

        try:
            self.client.drives.set_state(drive.drive_id, 'copying')
            self.__copy_data(drive)
            ingest_duration = drive.ingest_duration + int(time.time() - start_time)
            self.client.drives.__update__(drive.drive_id,
                                          {'state': 'copied',
                                           'ingest_duration': ingest_duration,
                                           'ingest_version': ingest.__version__,
                                           'dmsclient_version': dmsclient.__version__,
                                           })
            self.log.info("Drive '{}' ingested successfully".format(dir_name))
        except Exception as e:
            self.client.drives.set_state(drive.drive_id, 'copy_failed')
            self.log.error("Drive '%s' failed. Error: %s" % (dir_name, e))
            raise e

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def __clean_target(self, drive):
        if not os.path.isdir(drive.target_path):
            # Exit if target path does not exist
            return

        for the_file in os.listdir(drive.target_path):
            file_path = os.path.join(drive.target_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                self.log.error("[%s] Error cleaning up target directory. File '%s'".format(self.getName(), drive.target_path))

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def __copy_data(self, drive):
        message = '[{}] Copying drive {} from {} to {}'.format(self.getName(),
                                                               drive.drive_id,
                                                               drive.source_path,
                                                               drive.target_path)
        self.log.info(message)

        if not os.path.exists(drive.target_path):
            os.makedirs(drive.target_path)

        rsync_args = self.config['general']['rsync_args'].split()
        source_path = os.path.join(drive.source_path, '') # append trailing slash to tell rsync to copy dir contents
        command = ['rsync'] + rsync_args + [source_path, drive.target_path]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = process.communicate()

        if process.returncode > 0:
            raise Exception(output)
