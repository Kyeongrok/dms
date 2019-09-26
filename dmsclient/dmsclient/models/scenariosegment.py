from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.templates import Templates


class ScenarioSegment(BaseModel):
    """
    Represents a segment used in a particular user scenario
    """

    TEMPLATE = Templates.TEMPLATE_RESIM
    INDEX = Indices.timebased(Indices.INDEX_RESIM_PREFIX)
    DOC_TYPE = 'scenariosegment'

    class State(StrEnum):
        CREATED = 'created'
        RUNNING = 'running'
        FAILED = 'failed'
        COMPLETED = 'completed'

    def __init__(self, scenario_id, segment_id, state=State.CREATED, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_id = scenario_id
        self.segment_id = segment_id
        self.state = ScenarioSegment.State(state)

    @property
    def id(self):
        return '-'.join((self.scenario_id, self.segment_id))

    @property
    def timebased(self):
        return True
