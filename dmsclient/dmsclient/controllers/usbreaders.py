from dmsclient.controllers.readers import ReaderController
from dmsclient.models.usbreader import USBReader


class USBReaderController(ReaderController):
    """
    Controller class for manipulating USB Reader documents
    Inherits from Reader but needs to define it's own model class
    """

    @property
    def model_class(self):
        return USBReader

    def set_mount_state(self, reader_id, mount_state):
        """
        Update the reader status for the document matching the given ID.

        :param reader_id: the reader ID to be updated
        :type reader_id: string
        :param mount_state: the desired mount state (valid states found in
        `dmsclient.models.reader.USBReader.MountState`)
        :type status: string
        :raises ValueError: if the mount_state is not valid
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(reader_id, {'mount_state': USBReader.MountState(mount_state)})
