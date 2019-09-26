from dmsclient.controllers import DMSController
from dmsclient.models.reader import Reader


class ReaderController(DMSController):
    """
    Controller class for manipulating Reader documents
    """

    @property
    def model_class(self):
        return Reader

    def set_ingest_state(self, reader_id, ingest_state):
        """
        Update the reader ingest state for the document matching the given ID.

        :param reader_id: the reader ID to be updated
        :type reader_id: string
        :param ingest_state: the desired ingest state (valid states found in
        `dmsclient.models.reader.Reader.INGEST_STATES`)
        :type ingest_state: string
        :raises ValueError: if the ingest state is not valid
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(reader_id, {'ingest_state': Reader.IngestState(ingest_state)})

    def set_status(self, reader_id, status):
        """
        Update the reader status for the document matching the given ID.

        :param reader_id: the reader ID to be updated
        :type reader_id: string
        :param status: the desired status (valid statuses found in
        `dmsclient.models.reader.Reader.STATUSES`)
        :type status: string
        :raises ValueError: if the status is not valid
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(reader_id, {'status': Reader.Status(status)})

    def set_message(self, reader_id, message):
        """
        Update the reader message for the document matching the given ID.

        :param reader_id: the reader ID to be updated
        :type reader_id: string
        :param message: the reader message to be updated
        :type message: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(reader_id, {'message': message})

    def set_mount(self, reader_id, mount):
        """
        Update the reader mount point for the document matching the given ID.

        :param reader_id: the reader ID to be updated
        :type reader_id: string
        :param mount: the reader mount point to be updated
        :type mount: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(reader_id, {'mount': mount})
