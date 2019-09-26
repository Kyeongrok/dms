import re
from datetime import datetime

from dmsclient.exceptions import DMSInvalidFormat
from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.models.segment import Segment
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Sensor(BaseModel):
    """
    Represents a particular sensor obtained from a segment
    """

    TEMPLATE = Templates.TEMPLATE_RESIM
    INDEX = Indices.timebased(Indices.INDEX_RESIM_PREFIX)

    DOC_TYPE = 'sensor'

    SENSOR_TYPES = ('FLC',
                    'FLR',
                    'FSRL',
                    'FSRR',
                    'SOD',
                    'EH')

    PROTECTED_ATTRIBUTES = ['sensor_id',
                            'segment_id',
                            'sensor_type',
                            'drive_id',
                            'project_name',
                            'car_id',
                            'cluster_id',
                            'created_at',
                            'updated_at',
                            'state',
                            'tags',
                            'perm_path',
                            'output_path',
                            'resim_path']

    class State(StrEnum):
        CREATED = 'created'
        SHIPPING = 'shipping'
        SHIPPED = 'shipped'
        SHIPPING_FAILED = 'shipping_failed'
        INVALID_DATA = 'invalid_data'

    INGEST_REGEX = Segment.INGEST_REGEX[:-1] + "_(?P<sensor_type>[A-Z]{2,4})$"

    def __init__(self, sensor_id, segment_id, sensor_type, project_name=None,
                 drive_id=None, car_id=None, cluster_id=None, started_at=None,
                 ended_at=None, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
                 state=State.CREATED, tags=[], perm_path=None, output_path=None,
                 resim_path=None, **kwargs):
        super(Sensor, self).__init__(**kwargs)
        self.sensor_id = sensor_id
        self.segment_id = segment_id
        self.sensor_type = sensor_type
        self.project_name = project_name
        self.drive_id = drive_id
        self.car_id = car_id
        self.cluster_id = cluster_id
        self.started_at = str_to_datetime(started_at) if started_at else None
        self.ended_at = str_to_datetime(ended_at) if ended_at else None
        self.created_at = str_to_datetime(created_at)
        self.updated_at = str_to_datetime(updated_at)
        self.state = Sensor.State(state)
        self.tags = tags
        self.perm_path = perm_path
        self.output_path = output_path
        self.resim_path = resim_path
        self.extra_fields = kwargs

    @property
    def id(self):
        return self.sensor_id

    @property
    def timebased(self):
        return True

    @classmethod
    def from_segment(cls, segment, sensor_type, **kwargs):
        sensor_id = '_'.join([segment.segment_id, sensor_type])

        m = re.match(cls.INGEST_REGEX, sensor_id)
        if not m:
            raise DMSInvalidFormat("Could not parse sensor_id '%s'" % (sensor_id,))

        if sensor_type not in cls.SENSOR_TYPES:
            raise ValueError("Sensor type not in %s" % (cls.SENSOR_TYPES,))

        return cls(sensor_id=sensor_id,
                   segment_id=segment.segment_id,
                   sensor_type=sensor_type,
                   tags=segment.tags,
                   project_name=segment.project_name,
                   drive_id=segment.drive_id,
                   car_id=segment.car_id,
                   cluster_id=segment.cluster_id,
                   started_at=segment.started_at,
                   ended_at=segment.ended_at,
                   perm_path=segment.perm_path,
                   output_path=segment.output_path,
                   resim_path=segment.resim_path,
                   **kwargs)
