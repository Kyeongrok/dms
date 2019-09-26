import os
import re
from datetime import datetime, timezone

from dmsclient.exceptions import DMSInvalidFormat, DMSClientException
from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Segment(BaseModel):
    """
    Represents a drive segment
    """

    TEMPLATE = Templates.TEMPLATE_RESIM
    INDEX = Indices.timebased(Indices.INDEX_RESIM_PREFIX)

    DOC_TYPE = 'segment'

    PROTECTED_ATTRIBUTES = ['segment_id',
                            'drive_id',
                            'project_name',
                            'car_id',
                            'cluster_id',
                            'started_at',
                            'ended_at',
                            'created_at',
                            'updated_at',
                            'state',
                            'tags',
                            'nfs_host',
                            'smb_host',
                            'perm_export',
                            'output_export',
                            'resim_export',
                            'perm_share',
                            'output_share',
                            'resim_share',
                            'perm_path',
                            'output_path',
                            'resim_path']

    class State(StrEnum):
        CREATED = 'created'
        STARTED = 'started'
        COMPLETED = 'completed'
        FAILED = 'failed'
        DELETED = 'deleted'

    INGEST_REGEX = "^(?P<project_name>[A-Za-z0-9]+)_(?P<car_id>[A-Za-z0-9]+)_{1,2}CONT_(?P<start_year>[0-9]{4})" \
                   "(?P<start_month>[0-9]{2})(?P<start_day>[0-9]{2})" \
                   "T(?P<start_hour>[0-9]{2})(?P<start_minute>[0-9]{2})(?P<start_second>[0-9]{2})" \
                   "-(?P<end_year>[0-9]{4})" \
                   "(?P<end_month>[0-9]{2})(?P<end_day>[0-9]{2})" \
                   "T(?P<end_hour>[0-9]{2})(?P<end_minute>[0-9]{2})(?P<end_second>[0-9]{2})$"

    def __init__(self, segment_id, sequence, drive_id, project_name, car_id, cluster_id, started_at, ended_at,
                 created_at=datetime.utcnow(), updated_at=datetime.utcnow(), state=State.CREATED, tags=[],
                 nfs_host=None, smb_host=None, output_export=None, perm_export=None, resim_export=None,
                 output_share=None, perm_share=None, resim_share=None,
                 perm_path=None, output_path=None, resim_path=None, **kwargs):
        super(Segment, self).__init__(**kwargs)
        self.segment_id = segment_id
        self.sequence = sequence
        self.drive_id = drive_id
        self.project_name = project_name
        self.car_id = car_id
        self.cluster_id = cluster_id
        self.started_at = str_to_datetime(started_at)
        self.ended_at = str_to_datetime(ended_at)
        self.created_at = str_to_datetime(created_at)
        self.updated_at = str_to_datetime(updated_at)
        self.state = Segment.State(state)
        self.tags = tags
        self.nfs_host = nfs_host
        self.smb_host = smb_host
        self.output_export = output_export
        self.perm_export = perm_export
        self.resim_export = resim_export
        self.output_share = output_share
        self.perm_share = perm_share
        self.resim_share = resim_share
        self.perm_path = perm_path
        self.output_path = output_path
        self.resim_path = resim_path
        self.extra_fields = kwargs

    @property
    def id(self):
        return self.segment_id

    @property
    def timebased(self):
        return False

    @classmethod
    def from_drive(cls, segment_id, sequence, drive, cluster, **kwargs):
        m = re.match(cls.INGEST_REGEX, segment_id)
        if not m:
            raise DMSInvalidFormat("Could not parse segment_id '%s'" % (segment_id,))

        car_id = m.group('car_id')
        project_name = m.group('project_name')
        started_at = datetime(
            year=int(m.group('start_year')),
            month=int(m.group('start_month')),
            day=int(m.group('start_day')),
            hour=int(m.group('start_hour')),
            minute=int(m.group('start_minute')),
            second=int(m.group('start_second')),
            tzinfo=timezone.utc)
        ended_at = datetime(
            year=int(m.group('end_year')),
            month=int(m.group('end_month')),
            day=int(m.group('end_day')),
            hour=int(m.group('end_hour')),
            minute=int(m.group('end_minute')),
            second=int(m.group('end_second')),
            tzinfo=timezone.utc)

        if car_id != drive.car_id:
            raise DMSClientException('car_id mismatch between drive and segment [%s!=%s]'
                                     % (car_id, drive.car_id))

        if project_name != drive.project_name:
            raise DMSClientException('project_name mismatch between drive and segment [%s!=%s]'
                                     % (project_name, drive.project_name))

        path = os.path.join(drive.car_id,
                            drive.logged_at.strftime("%Y%m"),
                            drive.logged_at.strftime("%dT%H%M%S"),
                            str(sequence).zfill(4))

        perm_path = os.path.join(cluster.perm_mount, path)
        output_path = os.path.join(cluster.output_mount, path)
        resim_path = os.path.join(cluster.resim_mount, path)

        output_export = os.path.join(cluster.output_export, path)
        perm_export = os.path.join(cluster.perm_export, path)
        resim_export = os.path.join(cluster.resim_export, path)

        nfs_host = cluster.nfs_host
        smb_host = cluster.smb_host

        output_share = os.path.join(cluster.output_share, path)
        perm_share = os.path.join(cluster.perm_share, path)
        resim_share = os.path.join(cluster.resim_share, path)

        return cls(segment_id=segment_id,
                   sequence=sequence,
                   drive_id=drive.drive_id,
                   project_name=project_name,
                   car_id=car_id,
                   cluster_id=cluster.cluster_id,
                   started_at=started_at,
                   ended_at=ended_at,
                   nfs_host=nfs_host,
                   smb_host=smb_host,
                   output_export=output_export,
                   perm_export=perm_export,
                   resim_export=resim_export,
                   perm_path=perm_path,
                   output_path=output_path,
                   resim_path=resim_path,
                   perm_share=perm_share,
                   output_share=output_share,
                   resim_share=resim_share,
                   **kwargs)
