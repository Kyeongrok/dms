import socket
from logging import Handler, Formatter

from dmsclient.models.journal import Journal


class ElasticsearchHandler(Handler):
    def __init__(self, client):
        self.client = client
        super(ElasticsearchHandler, self).__init__()

    def emit(self, record):
        journal = self.format(record)
        self.client.journals.create(journal)


class JournalFormatter(Formatter):
    def format(self, record):
        journal = Journal(record.levelname,
                          socket.gethostname(),
                          record.name,
                          record.msg)
        return journal
