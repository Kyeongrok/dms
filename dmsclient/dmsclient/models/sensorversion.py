from datetime import datetime

from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.models.sensor import Sensor
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class SensorVersion(BaseModel):
    """
    Represents the result of a resimed sensor using a specific software version
    """

    TEMPLATE = Templates.TEMPLATE_RESIM
    INDEX = Indices.timebased(Indices.INDEX_RESIM_PREFIX)

    DOC_TYPE = 'sensorversion'

    class State(StrEnum):
        CREATED = 'created'
        REQUESTED = 'requested'  # external resim
        STARTED = 'started'  # internal resim
        FAILED = 'failed'
        COMPLETED = 'completed'

    INGEST_REGEX = Sensor.INGEST_REGEX[:-1] + "_(?P<version>\d{4})$"

    def __init__(self, sensorversion_id, sensor_id, segment_id, sensor_type, version, started_at, ended_at,
                 state=State.CREATED, drive_id=None, created_at=datetime.utcnow(),
                 updated_at=datetime.utcnow(), perm_path=None, output_path=None, resim_path=None, tags=[],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensorversion_id = sensorversion_id
        self.sensor_id = sensor_id
        self.segment_id = segment_id
        self.sensor_type = sensor_type
        self.version = version
        self.state = SensorVersion.State(state)
        self.drive_id = drive_id
        self.started_at = str_to_datetime(started_at) if started_at else None
        self.ended_at = str_to_datetime(ended_at) if ended_at else None
        self.created_at = str_to_datetime(created_at)
        self.updated_at = str_to_datetime(updated_at)
        self.perm_path = perm_path
        self.output_path = output_path
        self.resim_path = resim_path
        self.tags = tags
        self.extra_fields = kwargs

    @property
    def id(self):
        return self.sensorversion_id

    @property
    def timebased(self):
        return True

    @classmethod
    def from_sensor(cls, sensor, version, **kwargs):
        sensorversion_id = '%s_%s' % (sensor.sensor_id, version)
        return cls(sensorversion_id,
                   sensor_id=sensor.sensor_id,
                   segment_id=sensor.segment_id,
                   sensor_type=sensor.sensor_type,
                   version=version,
                   started_at=sensor.started_at,
                   ended_at=sensor.ended_at,
                   drive_id=sensor.drive_id,
                   perm_path=sensor.perm_path,
                   output_path=sensor.output_path,
                   resim_path=sensor.resim_path,
                   tags=sensor.tags,
                   **kwargs)
