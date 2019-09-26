import os
import re
import subprocess

import psutil

from dmsclient.models.segment import Segment
from dmsclient.models.sensor import Sensor


def isWritable(path):
    return os.access(path, os.W_OK | os.X_OK)


def isReadable(path):
    return os.access(path, os.R_OK)


def copy_only(adir, filenames):
    return [filename for filename in filenames if not filename.lower().endswith('.vpcap')]


def is_mounted(_dir):
    partitions = psutil.disk_partitions(all=True)
    nfs_partitions = list(filter(lambda x: x.fstype == 'nfs', partitions))
    for part in nfs_partitions:
        if _dir.startswith(part.mountpoint):
            return True
    return False


def scan_directories(path):
    if path.startswith('rsync://'):
        return scan_directories_rsync(path)
    else:
        return scan_directories_local(path)


def scan_directories_local(path):
    dirs = []

    for dir_name in os.listdir(path):
        source_path = os.path.join(path, dir_name)
        if not os.path.isdir(source_path):
            continue
        dirs.append((dir_name, source_path))
    return dirs


def scan_directories_rsync(path):
    # command = ['rsync', 'rsync://localhost:32768/data/samples/']
    command = ['rsync', '--list-only', path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()

    if process.returncode > 0:
        raise Exception(output)

    ls = output.splitlines()
    ls_dirs = list(filter(lambda x: x.decode('utf-8').startswith('d'), ls))

    dirs = []
    for ls_dir in ls_dirs:
        dir_name = ls_dir.decode('utf-8').split()[-1]
        if dir_name.startswith('.'):
            continue
        source_path = os.path.join(path, dir_name)
        dirs.append((dir_name, source_path))

    return dirs


def get_dir_stats(path):
    if path.startswith('rsync://'):
        return get_dir_stats_rsync(path)
    else:
        return get_dir_stats_local(path)


def get_dir_stats_local(path):
    files = os.listdir(path)
    dir_size = sum(os.path.getsize(os.path.join(path, f)) for f in files if os.path.isfile(os.path.join(path, f)))
    dir_count = len(files)
    return dir_size, dir_count


def get_dir_stats_rsync(path):
    command = ['rsync', '--list-only', os.path.join(path, '')]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()

    if process.returncode > 0:
        raise Exception(output)

    ls = output.splitlines()
    ls_files = list(filter(lambda x: x.decode('utf-8').startswith('-'), ls))

    dir_size = 0
    for ls_file in ls_files:
        file_size = ls_file.decode('utf-8').split()[1].replace(',', '')
        dir_size += int(file_size)

    return dir_size, len(ls_files)


def sensorid_to_segmentid(sensor_id):
    segmentid_split = sensor_id.split('_')[:-1]
    sensor_type = sensor_id.split('_')[-1]
    segment_id = '_'.join(segmentid_split)
    m = re.match(Segment.INGEST_REGEX, segment_id)
    if not m:
        raise Exception("Could not parse segment_id '%s'" % (sensor_id,))
    return segment_id, sensor_type


def sensorversionid_to_sensorid(sensorversion_id):
    sensorid_split = sensorversion_id.split('_')[:-1]
    version = sensorversion_id.split('_')[-1]
    sensor_id = '_'.join(sensorid_split)
    m = re.match(Sensor.INGEST_REGEX, sensor_id)
    if not m:
        raise Exception("Could not parse sensor_id '%s'" % (sensor_id,))
    return sensor_id, version


def get_free_space(path):
    r = os.statvfs(path)
    return r.f_bsize * r.f_bavail
