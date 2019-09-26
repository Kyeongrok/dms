from datetime import datetime
from decimal import Decimal

from dmsclient.models import BaseModel, StrEnum
from dmsclient.indices import Indices
from dmsclient.models.reader import Reader
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Cartridge(BaseModel):
    """
       Represents a cartridge from which drive data is ingested
    """
    TEMPLATE = Templates.TEMPLATE_CONFIG
    INDEX = Indices.INDEX_CONFIG
    DOC_TYPE = 'cartridge'

    class WorkflowType(StrEnum):
        INGESTION = 'CAR'
        FLC_INGESTION = 'FLC_INGEST'
        FLC_EGESTION = 'FLC_EGEST'

    def __init__(self, cartridge_id, device, ingest_station, usage,
                 workflow_type=WorkflowType.INGESTION,
                 ingest_state=Reader.IngestState.IDLE,
                 slot="",
                 updated_at=datetime.utcnow(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            assert isinstance(cartridge_id, str) and len(cartridge_id) > 0, 'cartridge_id must be a non-empty string'
            assert isinstance(device, str) and len(device) > 0, 'device must be a non-empty string'
            assert isinstance(ingest_station, str) and len(ingest_station) > 0, \
                'ingest_station must be a non-empty string'
            assert isinstance(usage, (int, float, Decimal)), 'usage must be a number'
            assert isinstance(slot, str), 'slot must be a string'
            assert isinstance(updated_at, datetime), 'updated_at must be of type datetime'
        except AssertionError as e:
            raise ValueError(e)

        self.cartridge_id = cartridge_id
        self.device = device
        self.ingest_station = ingest_station
        self.usage = usage
        self.workflow_type = Cartridge.WorkflowType(workflow_type)
        self.ingest_state = Reader.IngestState(ingest_state)
        self.slot = slot
        self.updated_at = updated_at
        self.extra_fields = kwargs

    @property
    def id(self):
        return self.cartridge_id

    @property
    def timebased(self):
        return False

    @classmethod
    def from_elasticsearch(cls, document):
        document['_source']['updated_at'] = str_to_datetime(document['_source']['updated_at'])
        return cls(**document['_source'])
