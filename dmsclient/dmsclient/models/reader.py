from datetime import datetime

from dmsclient.indices import Indices
from dmsclient.models import BaseModel, StrEnum
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Reader(BaseModel):
    """
    Represents a cartridge reader located in an upload station
    """

    TEMPLATE = Templates.TEMPLATE_CONFIG
    INDEX = Indices.INDEX_CONFIG
    DOC_TYPE = 'reader'

    class Status(StrEnum):
        EMPTY = 'empty'
        ACTIVE = 'active'
        INACTIVE = 'inactive'

    class IngestState(StrEnum):
        IDLE = 'idle'
        PROCESSING = 'processing'
        FAILED = 'failed'
        PROCESSED = 'processed'

    def __init__(self, reader_id, hostname, device, status=Status.EMPTY, ingest_state='idle',
                 message="", mount="", port="", updated_at=datetime.utcnow(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            assert isinstance(reader_id, str) and len(reader_id) > 0, 'reader_id must be a non-empty string'
            assert isinstance(hostname, str) and len(hostname) > 0, 'hostname must be a non-empty string'
            assert isinstance(device, str) and len(device) > 0, 'device must be a non-empty string'
            assert isinstance(message, str), 'message must be a string'
            assert isinstance(mount, str), 'mount must be a string'
            assert isinstance(port, str), 'port must be a string'
            assert isinstance(updated_at, datetime), 'updated_at must be of type datetime'
        except AssertionError as e:
            raise ValueError(e)

        self.reader_id = reader_id
        self.hostname = hostname
        self.device = device
        self.status = Reader.Status(status)
        self.ingest_state = Reader.IngestState(ingest_state)
        self.message = message
        self.mount = mount
        self.port = port
        self.updated_at = updated_at

    @property
    def id(self):
        return self.reader_id

    @property
    def timebased(self):
        return False

    @classmethod
    def from_elasticsearch(cls, document):
        document['_source']['updated_at'] = str_to_datetime(document['_source']['updated_at'])
        return cls(**document['_source'])
