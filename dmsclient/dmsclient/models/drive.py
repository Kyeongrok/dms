import os
import re
from datetime import datetime, timezone

from dmsclient.exceptions import DMSInvalidFormat
from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Drive(BaseModel):
    """
    Represents a Drive
    """

    TEMPLATE = Templates.TEMPLATE_RAW
    INDEX = Indices.INDEX_RAW
    DOC_TYPE = 'drive'

    PROTECTED_ATTRIBUTES = ['drive_id',
                            'car_id',
                            'project_name',
                            'cluster_id',
                            'state',
                            'logged_at',
                            'updated_at',
                            'nfs_host',
                            'smb_host',
                            'smb_share',
                            'source_path',
                            'target_path',
                            'state',
                            'tags',
                            'size',
                            'file_count',
                            'ingest_duration']

    class State(StrEnum):
        CREATED = 'created'
        COPYING = 'copying'
        COPY_FAILED = 'copy_failed'
        COPIED = 'copied'
        PROCESSING = 'processing'
        PROCESSING_FAILED = 'processing_failed'
        PROCESSED = 'processed'
        VERIFIED = 'verified'
        KEEP = 'keep'
        DELETED = 'deleted'

    class FLCState(StrEnum):
        NOT_READY = 'not_ready'
        READY = 'ready'
        INVALID_DATA = 'invalid_data'
        SHIPPING = 'shipping'
        SHIPPED = 'shipped'
        SHIPPING_FAILED = 'shipping_failed'

    INGEST_REGEX = "^(?P<project_name>[A-Za-z0-9]+)_(?P<car_id>[A-Za-z0-9]+)_{1,2}CONT_(?P<year>[0-9]{4})" \
                   "(?P<month>[0-9]{2})(?P<day>[0-9]{2})T(?P<hour>[0-9]{2})(?P<minute>[0-9]{2})(?P<second>[0-9]{2})"

    def __init__(self, drive_id, car_id, project_name, cluster_id, ingest_station, logged_at, updated_at,
                 nfs_host, smb_host, smb_share, source_path, target_path=None,
                 state=State.CREATED, flc_state=FLCState.NOT_READY, tags=[], size=0, file_count=0,
                 ingest_duration=0, **kwargs):
        super().__init__(**kwargs)
        self.drive_id = drive_id
        self.car_id = car_id
        self.project_name = project_name
        self.cluster_id = cluster_id
        self.ingest_station = ingest_station
        self.logged_at = str_to_datetime(logged_at)
        self.updated_at = str_to_datetime(updated_at)
        self.nfs_host = nfs_host
        self.smb_host = smb_host
        self.smb_share = smb_share
        self.source_path = source_path
        self.target_path = target_path
        self.state = Drive.State(state)
        self.flc_state = Drive.FLCState(flc_state)
        self.tags = tags
        self.size = size
        self.file_count = file_count
        self.ingest_duration = ingest_duration
        self.extra_fields = kwargs

    @property
    def id(self):
        return self.drive_id

    @property
    def timebased(self):
        return False

    @classmethod
    def from_ingest(cls, cluster, dir_name, source_path, ingest_station, **kwargs):
        m = re.match(cls.INGEST_REGEX, dir_name)
        if not m:
            raise DMSInvalidFormat("Could not parse directory name '%s'" % (dir_name,))

        car_id = m.group('car_id')
        project_name = m.group('project_name')
        logged_at = datetime(
                       year=int(m.group('year')),
                       month=int(m.group('month')),
                       day=int(m.group('day')),
                       hour=int(m.group('hour')),
                       minute=int(m.group('minute')),
                       second=int(m.group('second')),
                       tzinfo=timezone.utc)
        rel_path = os.path.join(car_id,
                                logged_at.strftime("%Y%m"),
                                logged_at.strftime("%dT%H%M%S"))
        target_path = os.path.join(cluster.raw_mount, rel_path)
        raw_share = os.path.join(cluster.raw_share, rel_path, dir_name)

        return cls(drive_id=dir_name,
                   car_id=car_id,
                   project_name=project_name,
                   cluster_id=cluster.cluster_id,
                   ingest_station=ingest_station,
                   logged_at=logged_at,
                   updated_at=datetime.utcnow(),
                   nfs_host=cluster.nfs_host,
                   smb_host=cluster.smb_host,
                   smb_share=raw_share,
                   source_path=source_path,
                   target_path=target_path,
                   state=cls.State.CREATED,
                   tags=[],
                   **kwargs)
