from datetime import datetime

from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.models.scenariosegment import ScenarioSegment
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Scenario(BaseModel):
    """
    Represents a user scenario
    """

    TEMPLATE = Templates.TEMPLATE_RESIM
    INDEX = Indices.timebased(Indices.INDEX_RESIM_PREFIX)
    DOC_TYPE = 'scenario'

    PROTECTED_ATTRIBUTES = ['name',
                            'user',
                            'state',
                            'created_at',
                            'updated_at']

    class State(StrEnum):
        CREATED = 'created'
        RUNNING = 'running'
        FAILED = 'failed'
        COMPLETED = 'completed'

    def __init__(self, name, user, query, sensor_versions, scenario_segments=[], created_at=datetime.utcnow(),
                 updated_at=datetime.utcnow(), started_at=datetime.utcnow(), ended_at=datetime.utcnow(),
                 state=State.CREATED, cpu_time=0, output_path=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.user = user
        self.query = query
        self.sensor_versions = sensor_versions
        self.scenario_segments = scenario_segments
        self.created_at = str_to_datetime(created_at)
        self.updated_at = str_to_datetime(updated_at)
        self.started_at = str_to_datetime(started_at)
        self.ended_at = str_to_datetime(ended_at)
        self.state = Scenario.State(state)
        self.cpu_time = cpu_time
        self.output_path = output_path

    @property
    def id(self):
        return '-'.join((self.name, self.user))

    @property
    def timebased(self):
        return True

    @classmethod
    def from_segments(cls, name, user, query, sensor_versions, segments, **kwargs):
        scenario = cls(name=name,
                       user=user,
                       query=query,
                       sensor_versions=sensor_versions,
                       **kwargs)
        scenario.scenario_segments = [ScenarioSegment(scenario.id, s.segment_id) for s in segments]
        return scenario

    @classmethod
    def from_elasticsearch(cls, document):
        ss_list = document['_source'].pop('scenario_segments')
        scenario = super(Scenario, cls).from_elasticsearch(document)

        scenario_segments = []
        for ss in ss_list:
            scenario_segments.append(ScenarioSegment(scenario_id=ss['scenario_id'],
                                                     segment_id=ss['segment_id'],
                                                     state=ss['state']))
        scenario.scenario_segments = scenario_segments
        return scenario

    def to_dict(self):
        d = super(Scenario, self).to_dict()
        d['scenario_segments'] = list(map((lambda x: x.__dict__), d['scenario_segments']))
        d['query'] = str(d['query']) if isinstance(d['query'], dict) else d['query']
        return d
