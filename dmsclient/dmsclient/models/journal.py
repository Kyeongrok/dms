from datetime import datetime
import logging

from dmsclient.indices import Indices
from dmsclient.models import BaseModel
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Journal(BaseModel):
    """
    Represents a journal/log entry
    """

    TEMPLATE = Templates.TEMPLATE_JOURNAL
    INDEX = Indices.timebased(Indices.INDEX_JOURNAL_PREFIX)
    DOC_TYPE = 'journal'

    LOG_LEVEL = (logging.getLevelName(logging.INFO),
                 logging.getLevelName(logging.WARNING),
                 logging.getLevelName(logging.ERROR),
                 logging.getLevelName(logging.CRITICAL),
                 logging.getLevelName(logging.DEBUG))

    def __init__(self, log_level, ingest_station, context, message, updated_at=datetime.utcnow(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            assert log_level in self.LOG_LEVEL, 'log level must be one of the following: %s' % (self.LOG_LEVEL, )
        except AssertionError as e:
            raise ValueError(e)

        self.log_level = log_level
        self.ingest_station = ingest_station
        self.context = context
        self.message = message if isinstance(message, str) else str(message)
        self.updated_at = str_to_datetime(updated_at)
        self.extra_fields = kwargs

    @property
    def id(self):
        return None

    @property
    def timebased(self):
        return True
